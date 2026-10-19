import sys
import os


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = [[0 for _ in range(vertices)] for _ in range(vertices)]

    # Prim's algorithm
    def primMST(self):
        key = [sys.maxsize] * self.V
        parent = [None] * self.V
        key[0] = 0
        mstSet = [False] * self.V
        parent[0] = -1

        for _ in range(self.V):
            u = self.minKey(key, mstSet)
            mstSet[u] = True

            for v in range(self.V):
                if (
                    self.graph[u][v] > 0
                    and mstSet[v] == False
                    and key[v] > self.graph[u][v]
                ):
                    key[v] = self.graph[u][v]
                    parent[v] = u

        self.printMST(parent)

    def minKey(self, key, mstSet):
        min_value = sys.maxsize
        min_index = -1
        for v in range(self.V):
            if key[v] < min_value and mstSet[v] == False:
                min_value = key[v]
                min_index = v
        return min_index

    def printMST(self, parent):
        # Collect edges
        edges = []
        for v in range(1, self.V):
            u = parent[v]
            w = self.graph[u][v]
            edges.append((u, v, w))

        # Sort edges
        edges.sort(key=lambda e: e[2])

        print("Prim's Algorithm Result")
        print("Edge    Weight")
        for u, v, w in edges:
            print(f"{u} - {v}       {w}")

        # Build the MST adjacency matrix
        mst_matrix = [[0] * self.V for _ in range(self.V)]
        for u, v, w in edges:
            mst_matrix[u][v] = w
            mst_matrix[v][u] = w

        print("\nMST Adjacency Matrix")
        # Header row
        header = "   | " + "  ".join(str(i) for i in range(self.V))
        print(header)
        print("-" * len(header))
        # Matrix rows
        for i in range(self.V):
            row_values = "  ".join(str(mst_matrix[i][j]) for j in range(self.V))
            print(f"{i} | {row_values}")

    # Validate the MST using union-find
    def validateMST(self, parent):
        if len(parent) != self.V:
            return False

        # union-find
        uf_parent = list(range(self.V))

        def find(x):
            while uf_parent[x] != x:
                uf_parent[x] = uf_parent[uf_parent[x]]
                x = uf_parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx == ry:
                return False
            uf_parent[ry] = rx
            return True

        edge_count = 0
        for v in range(1, self.V):
            u = parent[v]
            if u == None or u < 0:
                return False
            if not union(u, v):
                return False  # cycle detected
            edge_count += 1

        if edge_count != self.V - 1:
            return False

        # Check all vertices connected
        root = find(0)
        for v in range(1, self.V):
            if find(v) != root:
                return False
        return True


if __name__ == "__main__":
    g = Graph(5)
    g.graph = [
        [0, 2, 0, 6, 0],
        [2, 0, 3, 8, 5],
        [0, 3, 0, 0, 7],
        [6, 8, 0, 0, 9],
        [0, 5, 7, 9, 0],
    ]

    g.primMST()
