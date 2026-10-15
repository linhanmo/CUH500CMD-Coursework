# ASSESSED STANDARD TASK 3/5: Implement Graph as Adjacency Matrix

Your team is developing a lightweight internal tool to help model and analyse a company's transportation network. Each warehouse or delivery hub is represented by a **positive-integer ID**, and the relationships between them, such as direct routes or communication links, need to be stored in a clear, structured way. To support this, you've been asked to implement a graph using an **adjacency matrix**. The system should allow new locations to be added, direct connections between them to be created or removed, and the entire network to be displayed in a clean matrix format so analysts can quickly understand how different sites are linked.

## Expected matrix display for the locations

```text
      1   2   3   4   5   6
     ---------------------
1 |   0   1   1   0   0   0
2 |   1   0   1   0   0   0
3 |   1   1   0   1   0   0
4 |   0   0   1   0   0   0
5 |   0   0   0   0   0   0
6 |   0   0   0   0   0   0
```

> **Note:** Remember list indexing — this is 1 out, unless we start the matrix at 0 (not a +ve integer).

## Your required methods

The graph should support:

1. Adding a vertex
2. Adding an edge
3. Removing an edge
4. Printing the matrix

## IMPORTANT

- ⚫ The code as given may need altering to allow the new methods to be introduced.
- ⚫ Edges can be removed with no need to worry about vertices.

## Additional functions

You should also implement **two additional functions** that enhance the analytical capability or performance of your adjacency-matrix graph. This could include, but is not limited to:

- ⭕ computing the transitive closure using **Warshall's algorithm**;
- ⭕ checking whether the graph is **complete or symmetric**;
- ⭕ **counting triangles** using matrix multiplication. A triangle occurs when three vertices (nodes) are all connected to each other;
- ⭕ generating the **degree sequence**.

> **NOTE:** If you wish, you could implement the entire code as C++ instead of, or in addition to, Python. This is not mandatory for this task.

## REQUIRED CODE

```python
class Graph(object):
    
    def __init__(self, size):
        self.adjMatrix = []
        for i in range(size):
            self.adjMatrix.append([0 for i in range(size)])
        print(self.adjMatrix)
        self.size = size

    #methods for (1) adding a vertex; (2) adding an edge; (3) removing an edge; and (4) printing the
    #matrix should appear here




#remember list indexing - this is 1 out, unless we start the matrix at 0 (not a +ve integer)     
def main():
        g = Graph(6)

            
if __name__ == '__main__':
   main()
```
