import bisect
from typing import Any, List, Optional, Tuple, Union, Dict, Generic, TypeVar, cast, NewType
from py_btrees.disk import DISK, Address
from py_btrees.btree_node import BTreeNode, KT, VT, get_node
import pickle

"""
----------------------- Starter code for your B-Tree -----------------------

Helpful Tips (You will need these):
1. Your tree should be composed of BTreeNode objects, where each node has:
    - the disk block address of its parent node
    - the disk block addresses of its children nodes (if non-leaf)
    - the data items inside (if leaf)
    - a flag indicating whether it is a leaf

------------- THE ONLY DATA STORED IN THE `BTree` OBJECT SHOULD BE THE `M` & `L` VALUES AND THE ADDRESS OF THE ROOT NODE -------------
-------------              THIS IS BECAUSE THE POINT IS TO STORE THE ENTIRE TREE ON DISK AT ALL TIMES                    -------------

2. Create helper methods:
    - get a node's parent with DISK.read(parent_address)
    - get a node's children with DISK.read(child_address)
    - write a node back to disk with DISK.write(self)
    - check the health of your tree (makes debugging a piece of cake)
        - go through the entire tree recursively and check that children point to their parents, etc.
        - now call this method after every insertion in your testing and you will find out where things are going wrong
3. Don't fall for these common bugs:
    - Forgetting to update a node's parent address when its parent splits
        - Remember that when a node splits, some of its children no longer have the same parent
    - Forgetting that the leaf and the root are edge cases
    - FORGETTING TO WRITE BACK TO THE DISK AFTER MODIFYING / CREATING A NODE
    - Forgetting to test odd / even M values
    - Forgetting to update the KEYS of a node who just gained a child
    - Forgetting to redistribute keys or children of a node who just split
    - Nesting nodes inside of each other instead of using disk addresses to reference them
        - This may seem to work but will fail our grader's stress tests
4. USE THE DEBUGGER
5. USE ASSERT STATEMENTS AS MUCH AS POSSIBLE
    - e.g. `assert node.parent != None or node == self.root` <- if this fails, something is very wrong

--------------------------- BEST OF LUCK ---------------------------
"""

# Complete both the find and insert methods to earn full credit
class BTree:
    def __init__(self, M: int, L: int):
        """
        Initialize a new BTree.
        You do not need to edit this method, nor should you.
        """
        self.root_addr: Address = DISK.new()   # Remember, this is the ADDRESS of the root node
        # DO NOT RENAME THE ROOT MEMBER -- LEAVE IT AS self.root_addr
        DISK.write(self.root_addr, BTreeNode(self.root_addr, None, None, True))
        self.M = M   # M will fall in the range 2 to 99999
        self.L = L   # L will fall in the range 1 to 99999

    def insert(self, key: KT, value: VT) -> None:
        value = str(value)
        current_node = self.find_leaf(key)
        idx = current_node.find_idx(key)
        if idx < len(current_node.keys) and current_node.keys[idx] == key:
            current_node.data[idx] = value
        else:
            current_node.keys.insert(idx, key)
            current_node.data.insert(idx, value)

            if len(current_node.keys) > self.L:
                node1_addr = DISK.new()
                node1 = BTreeNode(node1_addr, None, None, True)
                self.split_leaf(current_node, node1)
            else:
                current_node.write_back()

    def find_leaf(self, key: KT) -> BTreeNode:
        current_node = DISK.read(self.root_addr)

        while not current_node.is_leaf:
            idx = current_node.find_idx(key)
            if idx == len(current_node.keys) or key < current_node.keys[idx]:
                current_node = current_node.get_child(idx)
            else:
                current_node = current_node.get_child(idx + 1)

        return current_node

    def split_leaf(self, node: BTreeNode, node1: BTreeNode) -> None:
        split_idx = (self.L+1) // 2
        split_key = node.keys[split_idx]

        node1.keys = node.keys[split_idx:]
        node1.data = node.data[split_idx:]
        node1.parent_addr = node.parent_addr  # Update parent pointer

        del node.keys[split_idx:]
        del node.data[split_idx:]

        if node.parent_addr is not None:
            parent = DISK.read(node.parent_addr)
            idx = parent.find_idx(split_key)

            parent.keys.insert(idx, split_key)
            parent.children_addrs.insert(idx + 1, node1.my_addr)

            if len(parent.keys) > self.M:
                parent1_addr = DISK.new()
                parent1 = BTreeNode(parent1_addr, parent.parent_addr, None, False)
                self.split_node(parent, parent1)
                parent.write_back()
                parent1.write_back()
                node.write_back()
                node1.write_back()
            elif len(parent.children_addrs) < self.M // 2:
                self.redistribute_children(parent, node, node1, idx)
                parent.write_back()
                node.write_back()
                node1.write_back()
            else:
                node.index_in_parent = idx
                node1.index_in_parent = idx + 1
                node.write_back()
                node1.write_back()
        else:
            root_addr = DISK.new()
            root = BTreeNode(root_addr, None, None, False)
            self.root_addr = root_addr
            root.keys = [split_key]
            root.children_addrs = [node.my_addr, node1.my_addr]
            node.parent_addr = root_addr
            node.index_in_parent = 0
            node1.parent_addr = root_addr
            node1.index_in_parent = 1
            root.write_back()
            node.write_back()
            node1.write_back()

    def split_node(self, parent: BTreeNode, parent1: BTreeNode) -> None:
        split_idx = self.M // 2
        split_key = parent.keys[split_idx]

        parent1.keys = parent.keys[split_idx:]
        parent1.children_addrs = parent.children_addrs[split_idx:]
        parent1.parent_addr = parent.parent_addr  # Update parent pointer

        del parent.keys[split_idx:]
        del parent.children_addrs[split_idx:]

        if parent.parent_addr is not None:
            grandparent = DISK.read(parent.parent_addr)
            idx = grandparent.find_idx(split_key)

            grandparent.keys.insert(idx, split_key)
            grandparent.children_addrs.insert(idx + 1, parent1.my_addr)

            if len(grandparent.keys) > self.M:
                grandparent1_addr = DISK.new()
                grandparent1 = BTreeNode(grandparent1_addr, parent.parent_addr, None, False)
                self.split_node(grandparent, grandparent1)
                grandparent.write_back()
                grandparent1.write_back()
                parent.write_back()
                parent1.write_back()
            elif len(grandparent.children_addrs) < self.M // 2:
                self.redistribute_children(grandparent, parent, parent1, idx)
                grandparent.write_back()
                parent.write_back()
                parent1.write_back()
            else:
                parent.index_in_parent = idx
                parent1.index_in_parent = idx + 1
                parent.write_back()
                parent1.write_back()
        else:
            root_addr = DISK.new()
            root = BTreeNode(root_addr, None, None, False)
            self.root_addr = root_addr
            root.keys = [split_key]
            root.children_addrs = [parent.my_addr, parent1.my_addr]
            parent.parent_addr = root_addr
            parent.index_in_parent = 0
            parent1.parent_addr = root_addr
            parent1.index_in_parent = 1
            root.write_back()
            parent.write_back()
            parent1.write_back()

    def redistribute_children(self, parent: BTreeNode, node: BTreeNode, node1: BTreeNode, idx: int) -> None:
        total_children = len(parent.children_addrs)
        half_children = self.M // 2

        if len(node.children_addrs) < half_children:
            left_sibling_idx = idx - 1
            left_sibling_addr = parent.children_addrs[left_sibling_idx]
            left_sibling = DISK.read(left_sibling_addr)

            if len(left_sibling.children_addrs) > half_children:
                borrowed_child = left_sibling.children_addrs.pop()
                left_sibling_key = left_sibling.keys.pop()
                left_sibling_data = left_sibling.data.pop()

                parent.keys[idx - 1] = left_sibling_key
                node.keys.insert(0, left_sibling_key)
                node.data.insert(0, left_sibling_data)
                node.children_addrs.insert(0, borrowed_child)

                left_sibling.write_back()
                node.write_back()
                parent.write_back()

        elif len(node1.children_addrs) < half_children:
            right_sibling_idx = idx + 1
            right_sibling_addr = parent.children_addrs[right_sibling_idx]
            right_sibling = DISK.read(right_sibling_addr)

            if len(right_sibling.children_addrs) > half_children:
                borrowed_child = right_sibling.children_addrs.pop(0)
                right_sibling_key = right_sibling.keys.pop(0)
                right_sibling_data = right_sibling.data.pop(0)

                parent.keys[idx] = right_sibling_key
                node1.keys.insert(0, right_sibling_key)
                node1.data.insert(0, right_sibling_data)
                node1.children_addrs.insert(0, borrowed_child)

                right_sibling.write_back()
                node1.write_back()
                parent.write_back()

    def find(self, key: KT) -> Optional[VT]:
        current_node = self.find_leaf(key)
        idx = current_node.find_idx(key)
        if idx < len(current_node.keys) and current_node.keys[idx] == key:
            return current_node.data[idx]
        else:
            return None

    def delete(self, key: KT) -> None:
        current_node = self.find_leaf(key)
        idx = current_node.find_idx(key)

        if idx < len(current_node.keys) and current_node.keys[idx] == key:
            del current_node.keys[idx]
            del current_node.data[idx]
            current_node.write_back()

            while len(current_node.keys) < self.L // 2:
                if current_node.parent_addr is not None:
                    parent = DISK.read(current_node.parent_addr)
                    idx_in_parent = current_node.index_in_parent

                    if idx_in_parent > 0:
                        left_sibling_addr = parent.children_addrs[idx_in_parent - 1]
                        left_sibling = DISK.read(left_sibling_addr)

                        if len(left_sibling.keys) > self.L // 2:
                            current_node.keys.insert(0, parent.keys[idx_in_parent - 1])
                            current_node.data.insert(0, left_sibling.data.pop())
                            parent.keys[idx_in_parent - 1] = left_sibling.keys.pop()
                            left_sibling.write_back()
                            current_node.write_back()
                            parent.write_back()
                        else:
                            left_sibling.keys.extend(current_node.keys)
                            left_sibling.data.extend(current_node.data)
                            parent.keys.pop(idx_in_parent - 1)
                            parent.children_addrs.pop(idx_in_parent)
                            left_sibling.write_back()
                            parent.write_back()
                            current_node = parent
                    else:
                        right_sibling_addr = parent.children_addrs[1]
                        right_sibling = DISK.read(right_sibling_addr)
                        if len(right_sibling.keys) > self.L // 2:
                            current_node.keys.append(parent.keys[0])
                            current_node.data.append(right_sibling.data.pop(0))
                            parent.keys[0] = right_sibling.keys.pop(0)
                            right_sibling.write_back()
                            current_node.write_back()
                            parent.write_back()
                        else:
                            current_node.keys.extend(right_sibling.keys)
                            current_node.data.extend(right_sibling.data)
                            parent.keys.pop(0)
                            parent.children_addrs.pop(1)
                            right_sibling.write_back()
                            parent.write_back()
                            current_node = parent
                    continue
                elif current_node.my_addr == self.root_addr:
                    current_node.is_leaf = True
                    if len(current_node.keys) > 0 and current_node.keys[idx] == key:
                        del current_node.keys[idx]
                        del current_node.data[idx]
                        current_node.write_back()
                    else:
                        print("The key doesn't exist in the tree.")
                    break
                else:
                    print("The key doesn't exist in the tree.")
                    break
        else:
            print("The key doesn't exist in the tree.")


