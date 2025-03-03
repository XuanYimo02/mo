# -*- coding: utf-8 -*-


class Node(object):
    def __init__(self, data=None):
        self.data = data
        self.pre = None
        self.nex = None


class LinkedList(object):
    def __init__(self):
        """初始化链表"""
        self.head = None
        self.index = 0

    def __len__(self):
        pre = self.head
        length = 0
        while pre:
            length += 1
            pre = pre.nex
        return length

    def is_empty(self):
        return False if len(self) > 0 else True

    def append(self, data):
        """
        1.head 为none :head-->node
        2.tail.nex-->node
        :param data:
        :return:
        """
        node = Node(data)
        if self.head == None:
            self.head = node
        else:
            pre = self.head
            while pre.nex:
                pre = pre.nex
            pre.nex = node

    def insert(self, index, data):
        """
        1.index 插入节点位置包括正负数
        2.找到index-1-->pre_node的节点
        3.pre_node.next-->node
          node.next-->pre_node.next.next
        4.head
        :param index:
        :param data:
        :return:
        """
        node = Node(data)
        if abs(index + 1) > len(self):
            return False
        index = index if index >= 0 else len(self) + index + 1
        if index == 0:
            node.nex = self.head
            self.head = node
        else:
            pre = self.get_index(index - 1)
            if pre:
                nex = pre.nex
                pre.nex = node
                node.nex = nex
            else:
                return False
        return node

    def __reversed__(self):
        """
        1.pre-->next 转变为 next-->pre
        2.pre 若是head 则把 pre.nex --> None
        3.tail-->self.head
        :return:
        """

        def reverse(pre_node, node):
            if pre_node is self.head:
                pre_node.nex = None
            if node:
                next_node = node.nex
                node.nex = pre_node
                return reverse(node, next_node)
            else:
                self.head = pre_node

        return reverse(self.head, self.head.nex)

    def get_index(self, index):
        """
        :param index:
        :return:
        """
        index = index if index >= 0 else len(self) + index
        if len(self) < index or index < 0:
            return None
        pre = self.head
        while index:
            pre = pre.nex
            index -= 1
        return pre

    def get(self) -> Node:
        """
        获取当前对象的默认index循环
        :return:
        """
        length = len(self)
        # print('current index :', self.index)
        # print(length)
        if length <= 2:
            if self.index == length:
                self.index = 0
                node = self.get_index(self.index)
                self.index += 1
            else:
                node = self.get_index(self.index)
                self.index += 1
            return node
        if self.index == length:
            self.index = 0
            node = self.get_index(self.index)
            self.index +=1
        else:
            node = self.get_index(self.index)
            self.index += 1
        return node

    def set(self, index, data):
        node = self.get_index(index)
        if node:
            node.data = data
        return node

    def delete(self, index):
        """
        指定下标删除
        :param index:
        :return:
        """
        f = index if index > 0 else abs(index + 1)
        if len(self) <= f:
            return False
        pre = self.head
        index = index if index >= 0 else len(self) + index
        prep = None
        while index:
            prep = pre
            pre = pre.nex
            index -= 1
        if not prep:
            self.head = pre.nex
        else:
            prep.nex = pre.nex
        return pre.data

    def remove(self, elem):
        """从链表中删除第一个值为elem的元素"""
        cur = self.head
        pre = None
        while cur is not None:
            if cur.data == elem:
                if cur == self.head:
                    self.head = cur.nex
                else:
                    pre.nex = cur.nex
                break
            else:
                pre = cur
                cur = cur.nex

    def clear(self):
        self.head = None

    def show(self):
        pre = self.head
        while pre:
            print(pre.data, end=" ")
            pre = pre.nex


if __name__ == '__main__':
    dl = LinkedList()
    for i in range(9):
        # print(i)
        dl.append(i)

    # dl.remove(10)
    dl.show()
    print(dl.get_index(0).data)
    # print(len(dl))
    for _ in range(11):
        print(dl.get().data)
