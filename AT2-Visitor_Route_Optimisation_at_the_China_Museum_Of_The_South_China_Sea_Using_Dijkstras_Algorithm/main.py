import sys
import os
from collections import defaultdict
import sys


class Graph:

    def __init__(self, size):
        self.edges = defaultdict(list)  # node -> list of neighbours
        self.weights = {}
        self.size = size
        self.dist = [sys.maxsize] * size
        self.previous = [None] * size
        self.Q = []
        self.unpoppedQ = []

    # Graph construction
    def add_edge(self, from_node, to_node, weight):
        # Add a bidirectional edge with the given weight
        self.edges[from_node].append(to_node)
        self.edges[to_node].append(from_node)
        self.weights[(from_node, to_node)] = weight
        self.weights[(to_node, from_node)] = weight

    def getIndex(self, neighbour):
        for i in range(len(self.unpoppedQ)):
            if neighbour == self.unpoppedQ[i]:
                return i
        return -1

    def findSmallestNode(self):
        # Index of the Q-node
        smallest = sys.maxsize
        result = -1
        for i in range(len(self.unpoppedQ)):
            node = self.unpoppedQ[i]
            if node in self.Q and self.dist[i] < smallest:
                smallest = self.dist[i]
                result = i
        return result

    def getPopPosition(self, uNode):
        # Position of uNode
        for i in range(len(self.Q)):
            if self.Q[i] == uNode:
                return i
        return 0

    def getUnvisitedNodes(self, uNode):
        # Neighbours of uNode
        resultList = []
        for neighbour in self.edges[uNode]:
            if neighbour in self.Q:
                resultList.append(neighbour)
        return resultList

    def _reset(self, start):
        self.Q = list(self.edges.keys())
        self.unpoppedQ = list(self.Q)
        n = len(self.unpoppedQ)
        self.dist = [sys.maxsize] * n
        self.previous = [None] * n
        self.dist[self.getIndex(start)] = 0

    # Main Dijkstra
    def dijsktra(self, start, end, collect_history=True, track_relaxations=False):
        self._reset(start)

        explored = []
        ignored = []
        history = []
        relaxations = []

        while self.Q:
            u = self.findSmallestNode()
            if u == -1:
                break
            uNode = self.unpoppedQ[u]
            if self.dist[u] == sys.maxsize:
                # Remaining Q nodes are unreachable from start
                break

            self.Q.remove(uNode)
            explored.append(uNode)

            if collect_history:
                history.append(
                    {node: self.dist[self.getIndex(node)] for node in self.unpoppedQ}
                )

            if uNode == end:
                break

            for v in self.getUnvisitedNodes(uNode):
                v_idx = self.getIndex(v)
                old = self.dist[v_idx]
                new_dist = self.dist[u] + self.weights[(uNode, v)]
                if new_dist < old:
                    self.dist[v_idx] = new_dist
                    self.previous[v_idx] = uNode
                    if track_relaxations:
                        relaxations.append((uNode, v, old, new_dist))
                else:
                    ignored.append(v)

        # Path reconstruction
        shortest_path = [end]
        u_idx = self.getIndex(end)
        while self.previous[u_idx] != None:
            shortest_path.insert(0, self.previous[u_idx])
            u_idx = self.getIndex(self.previous[u_idx])

        total_cost = self.dist[self.getIndex(end)]

        return {
            "path": shortest_path,
            "cost": total_cost,
            "explored": explored,
            "ignored": ignored,
            "history": history,
            "relaxations": relaxations,
        }

    # All-pairs shortest path matrix
    def all_pairs_shortest_paths(self):
        nodes = list(self.edges.keys())
        n = len(nodes)
        matrix = [[sys.maxsize] * n for _ in range(n)]
        for i, s in enumerate(nodes):
            self._reset(s)
            while self.Q:
                u = self.findSmallestNode()
                if u == -1:
                    break
                uNode = self.unpoppedQ[u]
                if self.dist[u] == sys.maxsize:
                    break
                self.Q.remove(uNode)
                for v in self.getUnvisitedNodes(uNode):
                    v_idx = self.getIndex(v)
                    nd = self.dist[u] + self.weights[(uNode, v)]
                    if nd < self.dist[v_idx]:
                        self.dist[v_idx] = nd
                        self.previous[v_idx] = uNode
            for j in range(n):
                matrix[i][j] = self.dist[j]
        return nodes, matrix

    # Reachability matrix
    def reachability_matrix(self):
        nodes, dist_matrix = self.all_pairs_shortest_paths()
        n = len(nodes)
        matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j or dist_matrix[i][j] < sys.maxsize:
                    matrix[i][j] = 1
        return nodes, matrix


def fmt(d):
    return "inf" if d == sys.maxsize else d


def print_result(name, res):
    print(f"{name}")
    print(f"Shortest path : {res['path']}")
    print(f"Total cost    : {res['cost']}")
    print(f"Explored      : {res['explored']}")
    print(f"Ignored       : {sorted(set(res['ignored']))}")
    print("\nDistance table after each iteration:")
    for it, table in enumerate(res["history"], start=1):
        row = "  ".join(f"{k}={fmt(v)}" for k, v in table.items())
        print(f"  Iter {it:>2}: {row}")
    print()


def print_matrix(title, nodes, matrix):
    print(title)
    header = "     " + "  ".join(f"{n:>3}" for n in nodes)
    print(header)
    for i, n in enumerate(nodes):
        row = "  ".join(f"{matrix[i][j]:>3}" for j in range(len(nodes)))
        print(f"  {n:>2} | {row}")
    print()


# The museum graph from the task
def demo_museum():
    g = Graph(8)
    edges = [
        ("O", "A", 2),
        ("O", "B", 5),
        ("O", "C", 4),
        ("A", "B", 2),
        ("A", "D", 7),
        ("A", "F", 12),
        ("B", "C", 1),
        ("B", "D", 4),
        ("B", "E", 3),
        ("C", "E", 4),
        ("D", "E", 1),
        ("D", "T", 5),
        ("E", "T", 7),
        ("F", "T", 3),
    ]
    for e in edges:
        g.add_edge(*e)

    res = g.dijsktra("O", "T", collect_history=True, track_relaxations=True)
    print_result("Graph 1: China Museum Of The South China Sea (O -> T)", res)

    nodes, reach = g.reachability_matrix()
    print_matrix("Reachability matrix (1 = reachable, 0 = not reachable)", nodes, reach)

    nodes, dist = g.all_pairs_shortest_paths()
    print_matrix(
        "All-pairs shortest-path distance matrix (inf = unreachable)",
        nodes,
        [[fmt(v) if v == sys.maxsize else v for v in row] for row in dist],
    )


# An additional weighted graph with more than six nodes
def demo_custom():
    g = Graph(9)
    edges = [
        ("S1", "S2", 4),
        ("S1", "S3", 2),
        ("S2", "S3", 1),
        ("S2", "S4", 5),
        ("S3", "S5", 8),
        ("S4", "S5", 2),
        ("S4", "S6", 6),
        ("S5", "S6", 3),
        ("S5", "S7", 7),
        ("S6", "S8", 4),
        ("S7", "S8", 1),
        ("S7", "S9", 5),
        ("S8", "S9", 2),
    ]
    for e in edges:
        g.add_edge(*e)

    res = g.dijsktra("S1", "S9", collect_history=True)
    print_result("Graph 2: Custom Telecom Backbone (S1 -> S9)", res)

    nodes, reach = g.reachability_matrix()
    print_matrix("Reachability matrix (custom graph)", nodes, reach)


if __name__ == "__main__":
    demo_museum()
    demo_custom()
