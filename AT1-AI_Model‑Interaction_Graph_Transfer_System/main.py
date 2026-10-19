import sys
import os
import json
import math
import heapq
import time
import tempfile
from collections import defaultdict, deque
from copy import deepcopy


class AIGraph:
    def __init__(self):
        self._nodes = {}  # node_id -> meta dict
        self._edges = {}  # (src, dst) -> meta dict
        self._out = defaultdict(set)  # src -> {dst}
        self._in = defaultdict(set)  # dst -> {src}
        self._version = 0
        self._deltas = []

    # Convenience
    def __repr__(self):
        return (
            f"AIGraph(nodes={len(self._nodes)}, "
            f"edges={len(self._edges)}, version={self._version})"
        )

    def __len__(self):
        return len(self._nodes)

    def __contains__(self, node_id):
        return node_id in self._nodes

    @property
    def version(self):
        return self._version

    # Node operations
    def add_node(self, node_id, **meta):
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id!r} already exists")
        self._nodes[node_id] = dict(meta)
        self._record("add_node", {"node_id": node_id, "meta": dict(meta)})

    def remove_node(self, node_id):
        # Remove a node and cascade-delete all its incident edges
        if node_id not in self._nodes:
            return False
        for dst in list(self._out.get(node_id, ())):
            self._remove_edge_raw(node_id, dst)
            self._record("remove_edge", {"src": node_id, "dst": dst})
        for src in list(self._in.get(node_id, ())):
            self._remove_edge_raw(src, node_id)
            self._record("remove_edge", {"src": src, "dst": node_id})
        del self._nodes[node_id]
        self._out.pop(node_id, None)
        self._in.pop(node_id, None)
        self._record("remove_node", {"node_id": node_id})
        return True

    def update_node(self, node_id, **meta):
        if node_id not in self._nodes:
            raise KeyError(node_id)
        self._nodes[node_id].update(meta)
        self._record("update_node", {"node_id": node_id, "meta": dict(meta)})

    def get_node(self, node_id):
        return dict(self._nodes.get(node_id, {}))

    def nodes(self):
        return list(self._nodes.keys())

    # Edge operations
    def add_edge(self, src, dst, **meta):
        # Add a directed edge with metadata
        if src not in self._nodes or dst not in self._nodes:
            raise KeyError("Both endpoints must exist")
        if (src, dst) in self._edges:
            raise ValueError(f"Edge {src!r}->{dst!r} already exists")
        if "confidence" in meta and not (0.0 < meta["confidence"] <= 1.0):
            raise ValueError("confidence must lie in (0, 1]")
        if "latency_ms" in meta and meta["latency_ms"] < 0:
            raise ValueError("latency_ms must be >= 0")
        if "cost_per_1k_tokens" in meta and meta["cost_per_1k_tokens"] < 0:
            raise ValueError("cost_per_1k_tokens must be >= 0")
        self._edges[(src, dst)] = dict(meta)
        self._out[src].add(dst)
        self._in[dst].add(src)
        self._record("add_edge", {"src": src, "dst": dst, "meta": dict(meta)})

    def remove_edge(self, src, dst):
        # Remove the edge (src, dst) if it exists
        if (src, dst) not in self._edges:
            return False
        self._remove_edge_raw(src, dst)
        self._record("remove_edge", {"src": src, "dst": dst})
        return True

    def update_edge(self, src, dst, **meta):
        # Update an edge's metadata
        if (src, dst) not in self._edges:
            raise KeyError((src, dst))
        self._edges[(src, dst)].update(meta)
        self._record("update_edge", {"src": src, "dst": dst, "meta": dict(meta)})

    def get_edge(self, src, dst):
        return dict(self._edges.get((src, dst), {}))

    def edges(self):
        return list(self._edges.keys())

    def _remove_edge_raw(self, src, dst):
        self._edges.pop((src, dst), None)
        self._out[src].discard(dst)
        self._in[dst].discard(src)

    # Reachability
    def reachable_from(self, src):
        if src not in self._nodes:
            return set()
        seen = set()
        q = deque([src])
        while q:
            u = q.popleft()
            for v in self._out.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        seen.discard(src)
        return seen

    # Dijkstra
    def _dijkstra(self, src, weight_fn):
        dist = {src: 0.0}
        prev = {src: None}
        pq = [(0.0, src)]
        settled = set()
        while pq:
            d, u = heapq.heappop(pq)
            if u in settled:
                continue
            settled.add(u)
            for v in self._out.get(u, ()):
                meta = self._edges.get((u, v))
                if meta == None:
                    continue
                w = weight_fn(meta)
                if w == None or not math.isfinite(w) or w < 0:
                    continue
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, prev

    @staticmethod
    def _reconstruct(prev, dst):
        path = []
        cur = dst
        while cur != None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    # Path queries
    def shortest_latency_path(self, src, dst):
        if src not in self._nodes or dst not in self._nodes:
            return None, math.inf
        dist, prev = self._dijkstra(src, lambda m: m.get("latency_ms", 0.0))
        if dst not in dist:
            return None, math.inf
        return self._reconstruct(prev, dst), dist[dst]

    def most_confident_path(self, src, dst):
        if src not in self._nodes or dst not in self._nodes:
            return None, 0.0

        def w(meta):
            c = meta.get("confidence", 1.0)
            if c <= 0.0:
                return None
            return -math.log(c)

        dist, prev = self._dijkstra(src, w)
        if dst not in dist:
            return None, 0.0
        path = self._reconstruct(prev, dst)
        conf = 1.0
        for a, b in zip(path, path[1:]):
            conf *= self._edges[(a, b)].get("confidence", 1.0)
        return path, conf

    def cost_optimal_path(self, src, dst):
        if src not in self._nodes or dst not in self._nodes:
            return None, math.inf
        dist, prev = self._dijkstra(src, lambda m: m.get("cost_per_1k_tokens", 0.0))
        if dst not in dist:
            return None, math.inf
        return self._reconstruct(prev, dst), dist[dst]

    # Top-K paths
    def _path_weight(self, path, weight_key):
        return sum(
            self._edges[(a, b)].get(weight_key, 0.0) for a, b in zip(path, path[1:])
        )

    def top_k_efficient_paths(self, src, dst, k=3, weight_key="latency_ms"):
        if src not in self._nodes or dst not in self._nodes or src == dst:
            return []

        first_dist, first_prev = self._dijkstra(src, lambda m: m.get(weight_key, 0.0))
        if dst not in first_dist:
            return []
        first_path = self._reconstruct(first_prev, dst)

        A = [first_path]
        B = []

        while len(A) < k:
            prev_path = A[-1]
            for i in range(len(prev_path) - 1):
                spur_node = prev_path[i]
                root_path = prev_path[: i + 1]

                removed = []
                for path in A:
                    if len(path) > i + 1 and path[: i + 1] == root_path:
                        e = (path[i], path[i + 1])
                        if e in self._edges and e not in [r[0] for r in removed]:
                            removed.append((e, self._edges.pop(e)))
                            self._out[e[0]].discard(e[1])
                            self._in[e[1]].discard(e[0])

                # Remove root-path edges
                for j in range(len(root_path) - 1):
                    e = (root_path[j], root_path[j + 1])
                    if e in self._edges and e not in [r[0] for r in removed]:
                        removed.append((e, self._edges.pop(e)))
                        self._out[e[0]].discard(e[1])
                        self._in[e[1]].discard(e[0])
                sdist, sprev = self._dijkstra(
                    spur_node, lambda m: m.get(weight_key, 0.0)
                )
                spur_path = self._reconstruct(sprev, dst) if dst in sdist else None

                # Restore removed edges
                for e, meta in removed:
                    self._edges[e] = meta
                    self._out[e[0]].add(e[1])
                    self._in[e[1]].add(e[0])

                if spur_path == None:
                    continue

                candidate = root_path[:-1] + spur_path
                if candidate not in A and candidate not in [b[2] for b in B]:
                    w = self._path_weight(candidate, weight_key)
                    heapq.heappush(B, (w, len(B), candidate))

            if not B:
                break
            _, _, next_path = heapq.heappop(B)
            A.append(next_path)

        return [(p, self._path_weight(p, weight_key)) for p in A]

    # Pareto frontier
    def pareto_frontier(self, src, dst, max_paths=50):
        if src not in self._nodes or dst not in self._nodes:
            return []
        results = []

        def is_dominated(lat, conf):
            for l, c, _ in results:
                if l <= lat and c >= conf and (l, c) != (lat, conf):
                    return True
            return False

        def dfs(u, path, lat, conf):
            if len(results) >= max_paths:
                return
            if u == dst:
                if not is_dominated(lat, conf) and (lat, conf) not in [
                    (l, c) for (l, c, _) in results
                ]:
                    results.append((lat, conf, list(path)))
                    # drop newly dominated paths
                    results[:] = [
                        (l, c, p)
                        for (l, c, p) in results
                        if not (lat <= l and conf >= c and (lat, conf) != (l, c))
                    ]
                return
            for v in self._out.get(u, ()):
                if v in path:
                    continue
                meta = self._edges[(u, v)]
                l2 = lat + meta.get("latency_ms", 0.0)
                c2 = conf * meta.get("confidence", 1.0)
                path.append(v)
                dfs(v, path, l2, c2)
                path.pop()

        dfs(src, [src], 0.0, 1.0)
        results.sort(key=lambda x: (x[0], -x[1]))
        return [(p, l, c) for (l, c, p) in results]

    # JSON serialisation
    def to_dict(self):
        return {
            "version": self._version,
            "nodes": {nid: dict(m) for nid, m in self._nodes.items()},
            "edges": [
                {"src": s, "dst": d, "meta": dict(m)}
                for (s, d), m in self._edges.items()
            ],
        }

    def to_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, data):
        g = cls()
        for nid, meta in data.get("nodes", {}).items():
            g._nodes[nid] = dict(meta)
        for e in data.get("edges", []):
            s, d, m = e["src"], e["dst"], dict(e.get("meta", {}))
            g._edges[(s, d)] = m
            g._out[s].add(d)
            g._in[d].add(s)
        g._version = data.get("version", 0)
        return g

    @classmethod
    def from_json(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # Graph exchange
    def _record(self, op, payload):
        self._version += 1
        self._deltas.append(
            {
                "version": self._version,
                "timestamp": time.time(),
                "op": op,
                "payload": payload,
            }
        )

    def delta_since(self, since_version):
        return [d for d in self._deltas if d["version"] > since_version]

    def export_delta_json(self, path, since_version=0):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.delta_since(since_version), f, indent=2)

    def apply_delta(self, delta):
        v = delta.get("version", 0)
        if v <= self._version:
            return False
        self._apply_delta_op(delta["op"], delta["payload"])
        self._version = v
        self._deltas.append(
            {
                "version": v,
                "timestamp": delta.get("timestamp", time.time()),
                "op": delta["op"],
                "payload": delta["payload"],
            }
        )
        return True

    def apply_delta_batch(self, deltas):
        applied = 0
        for d in sorted(deltas, key=lambda x: x["version"]):
            if self.apply_delta(d):
                applied += 1
        return applied

    def _apply_delta_op(self, op, payload):
        if op == "add_node":
            self._nodes[payload["node_id"]] = dict(payload["meta"])
        elif op == "remove_node":
            nid = payload["node_id"]
            self._nodes.pop(nid, None)
            self._out.pop(nid, None)
            self._in.pop(nid, None)
        elif op == "update_node":
            self._nodes.setdefault(payload["node_id"], {}).update(payload["meta"])
        elif op == "add_edge":
            s, d = payload["src"], payload["dst"]
            self._edges[(s, d)] = dict(payload["meta"])
            self._out[s].add(d)
            self._in[d].add(s)
        elif op == "remove_edge":
            s, d = payload["src"], payload["dst"]
            self._edges.pop((s, d), None)
            self._out[s].discard(d)
            self._in[d].discard(s)
        elif op == "update_edge":
            s, d = payload["src"], payload["dst"]
            self._edges.setdefault((s, d), {}).update(payload["meta"])

    # Diagnostics
    def summary(self):
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "version": self._version,
        }


# Simulate Transformer-based LLM inference pipeline
def build_demo_graph():
    g = AIGraph()
    # Nodes
    g.add_node(
        "STT",
        model_family="whisper-large-v3",
        parameters_b=1.55,
        quantization="fp16",
        context_window=448,
        max_output_tokens=448,
        framework="faster-whisper",
        gpu="L40S",
        tensor_parallel=1,
        throughput_tokens_per_sec=120.0,
        ttft_ms=45.0,
        status="active",
    )
    g.add_node(
        "Summariser",
        model_family="llama-3.1-8b",
        parameters_b=8.0,
        quantization="int4",
        context_window=128000,
        max_output_tokens=2048,
        framework="vllm",
        gpu="H100",
        tensor_parallel=1,
        throughput_tokens_per_sec=1500.0,
        ttft_ms=120.0,
        status="active",
    )
    g.add_node(
        "Sentiment Classifier",
        model_family="deberta-v3-large",
        parameters_b=0.435,
        quantization="fp16",
        context_window=512,
        max_output_tokens=8,
        framework="onnx",
        gpu="A100",
        tensor_parallel=1,
        throughput_tokens_per_sec=5000.0,
        ttft_ms=8.0,
        status="active",
    )
    g.add_node(
        "Topic Detector",
        model_family="bge-large-en-v1.5",
        parameters_b=0.335,
        quantization="fp16",
        context_window=512,
        max_output_tokens=512,
        framework="tgi",
        gpu="A100",
        tensor_parallel=1,
        throughput_tokens_per_sec=3000.0,
        ttft_ms=10.0,
        status="active",
    )
    g.add_node(
        "Recommendation Engine",
        model_family="custom-ranker",
        parameters_b=0.1,
        quantization="int8",
        context_window=1024,
        max_output_tokens=64,
        framework="onnx",
        gpu="L40S",
        tensor_parallel=1,
        throughput_tokens_per_sec=8000.0,
        ttft_ms=5.0,
        status="active",
    )
    g.add_node(
        "Safety Filter",
        model_family="llama-guard-3-8b",
        parameters_b=8.0,
        quantization="int4",
        context_window=8192,
        max_output_tokens=16,
        framework="vllm",
        gpu="H100",
        tensor_parallel=1,
        throughput_tokens_per_sec=2000.0,
        ttft_ms=95.0,
        status="active",
    )

    # Edges
    g.add_edge(
        "STT",
        "Summariser",
        transformation="prompt",
        latency_ms=150.0,
        payload_kb=32.0,
        confidence=0.95,
        input_tokens=8,
        output_tokens=200,
        cost_per_1k_tokens=0.0003,
        temperature=0.0,
        top_p=1.0,
        encrypted=True,
        cache_hit_ratio=0.0,
    )
    g.add_edge(
        "Summariser",
        "Sentiment Classifier",
        transformation="completion",
        latency_ms=90.0,
        payload_kb=4.0,
        confidence=0.90,
        input_tokens=180,
        output_tokens=4,
        cost_per_1k_tokens=0.0002,
        temperature=0.0,
        top_p=1.0,
        encrypted=True,
        cache_hit_ratio=0.7,
    )
    g.add_edge(
        "STT",
        "Topic Detector",
        transformation="embedding",
        latency_ms=55.0,
        payload_kb=6.0,
        confidence=0.92,
        input_tokens=8,
        output_tokens=1024,
        cost_per_1k_tokens=0.0001,
        temperature=0.0,
        top_p=1.0,
        encrypted=True,
        cache_hit_ratio=0.5,
    )
    g.add_edge(
        "Topic Detector",
        "Recommendation Engine",
        transformation="completion",
        latency_ms=40.0,
        payload_kb=2.0,
        confidence=0.88,
        input_tokens=64,
        output_tokens=16,
        cost_per_1k_tokens=0.00005,
        temperature=0.3,
        top_p=0.9,
        encrypted=True,
        cache_hit_ratio=0.6,
    )
    return g


def demo():
    g = build_demo_graph()

    print("Graph summary")
    print(g.summary())

    print("\nNodes")
    for nid in g.nodes():
        meta = g.get_node(nid)
        print(
            f"  {nid:<22} {meta['model_family']:<20} "
            f"{meta['parameters_b']:>6}B {meta['quantization']:<5} "
            f"{meta['framework']:<15} on {meta['gpu']}"
        )

    print("\nEdges")
    for s, d in g.edges():
        m = g.get_edge(s, d)
        print(
            f"  {s:<22} -> {d:<22} "
            f"lat={m['latency_ms']:>6.1f}ms conf={m['confidence']:.2f} "
            f"trans={m['transformation']}"
        )

    print("\nReachable from STT")
    print(sorted(g.reachable_from("STT")))

    print("\nLowest-latency path STT -> Sentiment Classifier")
    path, lat = g.shortest_latency_path("STT", "Sentiment Classifier")
    print(f"  path = {path}, total latency = {lat:.2f} ms")

    print("\nMost-confident path STT -> Sentiment Classifier")
    path, conf = g.most_confident_path("STT", "Sentiment Classifier")
    print(f"  path = {path}, product confidence = {conf:.4f}")

    print("\nCost-optimal path STT -> Sentiment Classifier")
    path, cost = g.cost_optimal_path("STT", "Sentiment Classifier")
    print(f"  path = {path}, total cost = {cost:.6f} per 1k tokens")

    print("\nTop-3 efficient paths STT -> Sentiment Classifier")
    for p, w in g.top_k_efficient_paths("STT", "Sentiment Classifier", k=3):
        print(f"  {p}  latency = {w:.2f} ms")

    print("\nPareto frontier STT -> Sentiment Classifier")
    for p, l, c in g.pareto_frontier("STT", "Sentiment Classifier"):
        print(f"  {p}  latency = {l:.2f} ms  confidence = {c:.4f}")

    print("\nJSON round-trip")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    try:
        g.to_json(tmp.name)
        g2 = AIGraph.from_json(tmp.name)
        print(f"  reloaded: {g2.summary()}")
    finally:
        os.unlink(tmp.name)

    print("\nDelta-based exchange")
    replica = AIGraph.from_dict(g.to_dict())
    v0 = replica.version
    print(f"  replica before: {replica.summary()}")

    g.add_node(
        "Moderation Head",
        model_family="roberta-toxicity",
        parameters_b=0.125,
        quantization="int8",
        context_window=512,
        max_output_tokens=2,
        framework="onnx",
        gpu="L40S",
        tensor_parallel=1,
        throughput_tokens_per_sec=10000.0,
        ttft_ms=4.0,
        status="active",
    )
    g.add_edge(
        "Sentiment Classifier",
        "Moderation Head",
        transformation="logits",
        latency_ms=15.0,
        payload_kb=0.5,
        confidence=0.99,
        input_tokens=4,
        output_tokens=2,
        cost_per_1k_tokens=0.00001,
        temperature=0.0,
        top_p=1.0,
        encrypted=True,
        cache_hit_ratio=0.8,
    )

    deltas = g.delta_since(v0)
    applied = replica.apply_delta_batch(deltas)
    print(f"  deltas transferred: {len(deltas)}, applied: {applied}")
    print(f"  replica after:      {replica.summary()}")
    print(f"  replica has 'Moderation Head': {'Moderation Head' in replica}")
    again = replica.apply_delta_batch(deltas)
    print(f"  idempotent re-apply: applied={again} (expected 0)")


if __name__ == "__main__":
    demo()
