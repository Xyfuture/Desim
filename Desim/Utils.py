from typing import TypeVar, Generic, Callable, Deque, Set
from sortedcontainers import SortedList
from collections import deque 

# 定义一个泛型 T
T = TypeVar("T")

class UniquePriorityQueue(Generic[T]):
    def __init__(self):
        """
        初始化优先级队列，元素按照 key 提取的优先级排序。
        :param key: 一个函数，用于从元素中提取优先级。
        """
        # self._key = key  # 用于提取优先级的函数
        self._queue = SortedList()  # 使用 key 排序
        self._set = set()  # 用于检查去重

    def add(self, item: T):
        """
        添加一个元素到队列中，如果元素已经存在，则忽略。
        :param item: 待加入的元素
        """
        if __debug__:
            self.valid_check()

        if item in self._set:
            # raise ValueError(f"{item} already exists")
            return
        self._queue.add(item)
        self._set.add(item)

        if __debug__:
            self.valid_check()

    # 这个函数没什么用， 因为 更改了value之后 堆就不对了，得在更新前就把原来的item删除
    # def append(self, item: T):
    #     """
    #     添加一个元素到队列中，如果元素已经存在，重新加入，对优先级进行重新排序。
    #     :param item: 待加入的元素
    #     """
    #     if __debug__:
    #         self.valid_check()
    #
    #     if item in self._set:
    #         self.remove(item) # 首先删除， 之后再次插入就是新的order了
    #         self.add(item)
    #     else:
    #         self._queue.add(item)
    #         self._set.add(item)
    #
    #     if __debug__:
    #         self.valid_check()
    #
    #     # print(f"添加: {item}，优先级: {self._key(item)}")

    def remove(self, item: T):
        """
        删除队列中的某个元素。
        :param item: 待删除的元素
        """
        if __debug__:
            self.valid_check()

        if item not in self._set:
            print(f"{item} 不在队列中，无法删除。")
            return
        self._queue.remove(item)
        self._set.remove(item)

        if __debug__:
            self.valid_check()
        # print(f"已删除: {item}")

    def update(self, old_item: T, new_item: T):
        """
        更新某个元素，将其替换为新的值。
        :param old_item: 需要更新的旧元素
        :param new_item: 新的元素
        """
        if old_item not in self._set:
            return
        self.remove(old_item)
        self.add(new_item)

    def pop(self) -> T:
        """
        弹出优先级最高的元素。
        :return: 优先级最高的元素
        """
        if __debug__:
            self.valid_check()

        if not self._queue:
            raise IndexError("优先级队列为空！")
        item = self._queue.pop(0)  # 弹出优先级最高的元素
        self._set.remove(item)

        if __debug__:
            self.valid_check()

        return item

    def peek(self) -> T:
        """
        返回优先级最高的元素但不移除。
        :return: 优先级最高的元素
        """
        if not self._queue:
            raise IndexError("优先级队列为空！")
        return self._queue[0]

    def __len__(self) -> int:
        """
        返回队列长度。
        """
        return len(self._queue)

    def __bool__(self) -> bool:
        """
        当队列非空时返回 True，空时返回 False。
        """
        return len(self._queue) > 0

    def valid_check(self)->bool:
        # True for valid / False for invalid
        for item in self._queue:
            if item not in self._set:
                assert False
        for item in self._set:
            if item not in self._queue:
                assert False
        tmp_set = set()
        for item in self._queue:
            if item in tmp_set:
                assert False
            tmp_set.add(item)
        self._queue._check()
        return True

    def __contains__(self, item):
        return item in self._set

    def __iter__(self):
        return iter(self._queue)



class UniqueDeque(Generic[T]):
    def __init__(self) -> None:
        self.deque: Deque[T] = deque()
        self.set: Set[T] = set()

    def append(self, item: T) -> None:
        if __debug__:
            self.valid_check()

        if item not in self.set:
            self.set.add(item)
            self.deque.append(item)

        if __debug__:
            self.valid_check()

    def appendleft(self, item: T) -> None:
        if item not in self.set:
            self.set.add(item)
            self.deque.appendleft(item)

    def pop(self) -> T:
        if __debug__:
            self.valid_check()

        item = self.deque.pop()
        self.set.remove(item)

        if __debug__:
            self.valid_check()

        return item

    def popleft(self) -> T:
        item = self.deque.popleft()
        self.set.remove(item)
        return item

    def remove(self, item: T) -> None:
        if __debug__:
            self.valid_check()

        self.deque.remove(item)
        self.set.remove(item)

        if __debug__:
            self.valid_check()

    def __contains__(self, item: T) -> bool:
        return item in self.set

    def __len__(self) -> int:
        return len(self.deque)

    def __repr__(self) -> str:
        return repr(self.deque)

    def __iter__(self):
        return iter(self.deque)


    def valid_check(self)->bool:
        for item in self.deque:
            if item not in self.set:
                assert False
        for item in self.set:
            if item not in self.deque:
                assert False

        return True




U = TypeVar('U')  # 改为 U，表示描述符的泛型类型

# class ClassProperty(Generic[U]):
#     def __init__(self, value: U):
#         self.value = value
#
#     def __get__(self, instance, owner) -> U:  # 返回值类型为 U
#         return self.value()

class ClassProperty(Generic[U]):
    def __init__(self, method: Callable[..., U]):
        self.method = method
        # functools.update_wrapper(self, method) # type: ignore

    def __get__(self, obj, cls=None) -> U:
        if cls is None:
            cls = type(obj)
        return self.method(cls)




# 示例用法
if __name__ == "__main__":
    # 定义一个数据类或简单对象，包含优先级信息
    class Task:
        def __init__(self, name: str, priority: int):
            self.name = name
            self.priority = priority

        def __repr__(self):
            return f"Task(name={self.name}, priority={self.priority})"

    # 创建一个 PriorityQueue[Task]，从 Task 中提取优先级
    pq = UniquePriorityQueue[Task]()

    pq.append("Task 1")
    pq.append("Task 2")
    pq.append("Task 1")
    pq.append("Task 2")
    # pq.append(Task("task1", 2))  # task1 已存在，忽略
    # pq.append(Task("task3", 3))

    print(f"优先级最高的元素: {pq.peek()}")
    print(f"弹出: {pq.pop()}")
    print(f"弹出: {pq.pop()}")
    # print(f"弹出: {pq.pop()}")
