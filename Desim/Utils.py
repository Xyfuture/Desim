from typing import TypeVar, Generic, Callable
from sortedcontainers import SortedList

# 定义一个泛型 T
T = TypeVar("T")

class PriorityQueue(Generic[T]):
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
        if item in self._set:
            print(f"{item} 已存在，忽略添加。")
            return
        self._queue.add(item)
        self._set.add(item)

    def append(self, item: T):
        """
        添加一个元素到队列中，如果元素已经存在，重新加入，对优先级进行重新排序。
        :param item: 待加入的元素
        """
        if item in self._set:
            self.remove(item)
            self.add(item)
        else:
            self._queue.add(item)
            self._set.add(item)

        # print(f"添加: {item}，优先级: {self._key(item)}")

    def remove(self, item: T):
        """
        删除队列中的某个元素。
        :param item: 待删除的元素
        """
        if item not in self._set:
            print(f"{item} 不在队列中，无法删除。")
            return
        self._queue.remove(item)
        self._set.remove(item)
        print(f"已删除: {item}")

    def update(self, old_item: T, new_item: T):
        """
        更新某个元素，将其替换为新的值。
        :param old_item: 需要更新的旧元素
        :param new_item: 新的元素
        """
        if old_item not in self._set:
            print(f"{old_item} 不在队列中，无法更新。")
            return
        self.remove(old_item)
        self.append(new_item)
        print(f"已更新: {old_item} -> {new_item}")

    def pop(self) -> T:
        """
        弹出优先级最高的元素。
        :return: 优先级最高的元素
        """
        if not self._queue:
            raise IndexError("优先级队列为空！")
        item = self._queue.pop(0)  # 弹出优先级最高的元素
        self._set.remove(item)
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
    pq = PriorityQueue[Task]()

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