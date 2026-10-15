import sys
import os


class Graph(object):
    def __init__(self, size):
        self.size = size
        self.adjMatrix = [[0] * size for _ in range(size)]

    # Add a vertex
    def add_vertex(self, vertex_id=None):
        if vertex_id is None:
            vertex_id = self.size + 1

        if vertex_id <= 0:
            raise ValueError("Vertex id must be a positive integer.")

        if vertex_id <= self.size:
            return False

        # Expand matrix to size vertex_id
        new_size = vertex_id
        for row in self.adjMatrix:
            row.extend([0] * (new_size - self.size))
        for _ in range(new_size - self.size):
            self.adjMatrix.append([0] * new_size)

        self.size = new_size
        return True

    # Add an edge
    def add_edge(self, v1, v2):
        """Add an undirected edge between vertices v1 and v2 (1-based ids)."""
        self._check_vertex(v1)
        self._check_vertex(v2)
        if v1 == v2:
            raise ValueError("Self-loops are not allowed.")
        self.adjMatrix[v1 - 1][v2 - 1] = 1
        self.adjMatrix[v2 - 1][v1 - 1] = 1

    # Remove an edge
    def remove_edge(self, v1, v2):
        self._check_vertex(v1)
        self._check_vertex(v2)
        self.adjMatrix[v1 - 1][v2 - 1] = 0
        self.adjMatrix[v2 - 1][v1 - 1] = 0

    # Print the matrix
    def print_matrix(self):
        # Header row
        header = "    " + "".join(f"{i:4d}" for i in range(1, self.size + 1))
        print(header)
        print("    " + "-" * (4 * self.size))

        for i in range(self.size):
            row_label = f"{i + 1:<3}|"
            row_values = "".join(f"{self.adjMatrix[i][j]:4d}" for j in range(self.size))
            print(row_label + row_values)

    def _check_vertex(self, v):
        """Raise ValueError if v is not a valid vertex id."""
        if not isinstance(v, int) or v < 1 or v > self.size:
            raise ValueError(f"Invalid vertex id: {v}")

    # Warshall's transitive closure

    def transitive_closure(self):
        n = self.size
        closure = [row[:] for row in self.adjMatrix]  # copy

        for k in range(n):
            for i in range(n):
                if closure[i][k]:
                    for j in range(n):
                        if closure[k][j]:
                            closure[i][j] = 1
        return closure

    def print_transitive_closure(self):
        n = self.size
        closure = self.transitive_closure()
        header = "    " + "".join(f"{i:4d}" for i in range(1, n + 1))
        print(header)
        print("    " + "-" * (4 * n))
        for i in range(n):
            row_label = f"{i + 1:<3}|"
            row_values = "".join(f"{closure[i][j]:4d}" for j in range(n))
            print(row_label + row_values)

    # Degree sequence
    def degree_sequence(self, descending=True):
        degrees = [sum(self.adjMatrix[i]) for i in range(self.size)]
        if descending:
            return sorted(degrees, reverse=True)
        return degrees


def main():
    g = Graph(6)

    # Build the graph
    edges = [(1, 2), (1, 3), (2, 3), (3, 4)]
    for v1, v2 in edges:
        g.add_edge(v1, v2)

    print("Initial matrix:")
    g.print_matrix()

    print("\nAdding vertex 7 and connecting 4-7:")
    g.add_vertex(7)
    g.add_edge(4, 7)
    g.print_matrix()

    print("\nRemoving edge (1, 3):")
    g.remove_edge(1, 3)
    g.print_matrix()

    print("\nTransitive closure:")
    g.print_transitive_closure()

    print("\nDegree sequence (descending):", g.degree_sequence())
    print("\nDegree sequence (vertex order):", g.degree_sequence(descending=False))


if __name__ == "__main__":
    main()
