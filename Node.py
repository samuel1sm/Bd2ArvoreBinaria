class Node:
    def __init__(self, data):
        self.left_node = None
        self.right_node = None
        self.data = data

    def add_child(self, child):
        if not self.left_node:
            self.left_node = child
        elif not self.right_node:
            self.right_node = child

    def add_children(self, child1, child2):
        self.left_node = child1
        self.right_node = child2

if __name__ == '__main__':
    import os
    if os.path.exists("plot.png"):

        os.remove("plot.png")
