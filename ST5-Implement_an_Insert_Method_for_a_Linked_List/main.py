import sys
import os


class Node:
    def __init__(self, dataval=None):
        self.dataval = dataval
        self.nextval = None


class SLinkedList:
    def __init__(self):
        self.headval = None

    # Insert a new node after the first node with val_before
    def Insert(self, val_before, newdata):
        if val_before == None:
            print("No node to insert after")
            return

        if self.headval == None:
            print("Cannot insert: the list is empty")
            return

        current = self.headval
        while current != None and current.dataval != val_before:
            current = current.nextval

        if current == None:
            print(f"Cannot insert: node with value '{val_before}' not found")
            return

        new_node = Node(newdata)
        new_node.nextval = current.nextval
        current.nextval = new_node

    # Search
    def Search(self, val):
        current = self.headval
        while current != None:
            if current.dataval == val:
                return True
            current = current.nextval
        return False

    # Delete
    def Delete(self, val):
        if self.headval == None:
            return False

        # The head node itself must be deleted
        if self.headval.dataval == val:
            self.headval = self.headval.nextval
            return True

        # Search for the node
        prev = self.headval
        current = self.headval.nextval
        while current != None:
            if current.dataval == val:
                prev.nextval = current.nextval
                return True
            prev = current
            current = current.nextval
        return False

    # Existing printing logic
    def listprint(self):
        printval = self.headval
        while printval != None:
            print(printval.dataval)
            printval = printval.nextval

    def AtBeginning(self, newdata):
        NewNode = Node(newdata)

    def AtEnd(self, newdata):
        NewNode = Node(newdata)
        if self.headval == None:
            self.headval = NewNode
            return
        last = self.headval
        while last.nextval != None:
            last = last.nextval
        last.nextval = NewNode


list = SLinkedList()
list.headval = Node("Red")

e2 = Node("Orange")
e3 = Node("Yellow")
e4 = Node("Green")
e5 = Node("Blue")
e6 = Node("Violet")  # Indigo is missing

list.headval.nextval = e2
e2.nextval = e3
e3.nextval = e4
e4.nextval = e5
e5.nextval = e6

# Insert Indigo between Blue and Violet
list.Insert("Blue", "Indigo")
list.listprint()
