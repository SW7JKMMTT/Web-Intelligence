#!/bin/env python

import re
import os

class Node():
    def __init__(self, depth, final):
        self._children = []
        self.depth = depth
        self.final = final

    def matches(self, txt):
        raise NotImplementedError()

    def getDepth(self):
        return self.depth

    def getPerm(self):
        raise NotImplementedError()

    def add(self, child):
        self._children.append(child)

    def get(self, i):
        return self._children[i]

    def find(self, path):
        for child in self._children:
            if child.matches(path):
                return child
        return None

    def __iter__(self):
        return self._children.__iter__()

class TextNode(Node):
    def __init__(self, depth, txt, perm, final):
        super().__init__(depth, final)
        self.txt = txt
        self.perm = perm

    def matches(self, txt):
        if self.txt == txt:
            return True
        return False

    def getPerm(self):
        return self.perm

class RootNode(Node):
    def __init__(self, perm, final):
        super().__init__(0, final)
        self.perm = perm

    def getPerm(self):
        return self.perm

class WildcardNode(Node):
    def __init__(self, depth, perm, final):
        super().__init__(depth, final)
        self.perm = perm

    def matches(self, txt):
        return True

    def getPerm(self):
        return self.perm

class Robots():
    def __init__(self, root):
        self.root = root

rob = """ #WOW
          Allow: /a/b #ASASD
          Disallow: /a
          Disallow: /a/b/c
          Allow: /a/b/c
"""

def getParts(s):
    head, tail = os.path.split(s)
    parts = []
    while tail != "":
        parts.append(tail)
        head, tail = os.path.split(head)
    parts.reverse()
    return parts

root = RootNode(1, True)
for line in rob.split("\n"):
    line = re.sub(r'#.*', "", line)
    line = line.strip(" ")

    if line == "":
        continue

    s = line.split(":", 1)
    if s[0].lower() == "allow":
        print("A")
        curNode = root
        for part in getParts(s[1]):
            if part == " ":
                continue
            newNode = curNode.find(part)
            if newNode == None:
                newNode = TextNode(curNode.getDepth()+1, part, 1, False)
                curNode.add(newNode)
            curNode = newNode
            print(part)
        curNode.final = True
    elif s[0].lower() == "disallow":
        curNode = root
        for part in getParts(s[1]):
            if part == " ":
                continue
            newNode = curNode.find(part)
            if newNode == None:
                newNode = TextNode(curNode.getDepth()+1, part, 0, False)
                curNode.add(newNode)
            curNode = newNode
            print(part)
        print("Final: {}".format(curNode.txt))
        curNode.final = True
    print(line)

pp = ["a", "b"]

instance = [[]]
newInst = []
run = 0
maxDepth = 0
maxPerm = root.getPerm()
while len(instance) > 0:
    curNode = root
    for path in instance:
        print(path)
        for p in path:
            curNode = curNode.get(p)

        for k, c in enumerate(curNode):
            print("{} == {}".format(pp[run], c.txt))
            if c.matches(pp[run]):
                newPath = list(path)
                newPath.append(k)
                newInst.append(newPath)
                if maxDepth < c.depth and c.final:
                    maxDepth = c.depth
                    print("de {}".format(c.getPerm()))
                    maxPerm = c.getPerm()
    run += 1
    if run >= len(pp):
        break
    instance = newInst
    newInst = []
print("Perm: {} at Depth {}".format(maxPerm, maxDepth))
