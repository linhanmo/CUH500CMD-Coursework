# ASSESSED STANDARD TASK 5/5: Implement an Insert Method for a Linked List

For this task:

- ⭕ You will need to have studied the lecture **Data Structures 2**, on Aula, **Week 5, Slides 52 to 83**.

You must extend the linked-list implementation provided in the folder **LINKED-LIST-STD-TASK-5**, but with additional complexity beyond simply inserting the missing colour. The code you are given already constructs a linked list representing the colours of the rainbow, but it is missing **Indigo**, which should appear **between Blue and Violet**.

Your task is to implement a fully functional `Insert` method that can correctly insert a new node **after any specified existing node**, not just in this one case. The method must correctly handle edge cases such as:

- attempting to insert after a value that does not exist,
- attempting to insert after the final node,
- attempting to insert when the list is empty.

You must then use this method to insert the missing colour **Indigo** into the correct position in the rainbow sequence. The insertion command must be added **before** the existing call to `list.listprint()`, and the final output must show the colours in the correct order:

```text
Red, Orange, Yellow, Green, Blue, Indigo, Violet
```

You may **not** modify the existing node-creation code or the list-printing logic; your solution must work by adding the `Insert` method and calling it appropriately.

## Current output

The code currently outputs the following:

```text
Red
Orange
Yellow
Green
Blue
Violet
```

So we need to add 'Indigo'.

## Starter code

To do this, create an insert method. Here is some code to get you started. You'll need to add code after the `else`:

```python
def Insert(self, val_before, newdata):
    if val_before is None:
        print("No node to insert after")
        return
    else:
        # your code here
```

## Expected result

```text
Red
Orange
Yellow
Green
Blue
Indigo
Violet
```

## Additional functions

You should also implement **two additional advanced functions** that increase the robustness of your linked-list implementation. These could be, but are not limited to:

- ⭕ **Delete:** Remove a node by value. This tests pointer handling, empty-list cases, deleting the head, and deleting the last node.
- ⭕ **Search:** Return whether a value exists in the list. Useful for validation before insertions.
- ⭕ **Length:** Count the number of nodes. Helps with debugging and validating operations.
- ⭕ **Reverse:** Reverse the entire list in place.
- ⭕ **GetNodeAt:** Retrieve a node by index.

> **Please note:** if you wish you can implement this linked list from scratch using C++.

## SUPPORT CODE

```python
class Node:
    def __init__(self, dataval = None):
        self.dataval = dataval
        self.nextval = None

class SLinkedList:
    def __init__(self):
        self.headval = None

    def listprint(self):
        printval = self.headval
        while printval is not None:
            print(printval.dataval)
            printval = printval.nextval
            
    def AtBeginning(self,newdata):
        NewNode = Node(newdata)

    def AtEnd(self, newdata):
        NewNode = Node(newdata)
        if self.headval is None:
            self.headval = NewNode
            return
        last = self.headval
        while(last.nextval):
            last = last.nextval
        last.nextval = NewNode
        

# Create the linked list
list = SLinkedList()
list.headval = Node("Red")

e2 = Node("Orange")
e3 = Node("Yellow")
e4 = Node("Green")
e5 = Node("Blue")
e6 = Node("Violet")   # Indigo is missing

list.headval.nextval = e2
e2.nextval = e3
e3.nextval = e4
e4.nextval = e5
e5.nextval = e6

list.listprint()
```
