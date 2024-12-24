from __future__ import annotations

from collections import deque
from typing import Callable, Optional, Deque
from greenlet import greenlet
from sortedcontainers import SortedList

from Desim.Utils import PriorityQueue


class SimTime:
    def __init__(self):
        pass

    def __add__(self, other):
        pass

class SimCoroutine(greenlet):
    def __init__(self):
        super(SimCoroutine, self).__init__()




class SimModule:
    def __init__(self):
        pass

    def register_coroutine(self,func:Callable,events:list[Event]):
        pass

    def register_method(self,func:Callable,events:list[Event]):
        pass


    @staticmethod
    def wait(*args,**kwargs):
        for event in args:
            assert isinstance(event,Event)
            # 注册 event

        # 切换出 协程, 切换到指定的 scheduler 的线程
        SimSession.scheduler.executor.switch()

        # 切换回来，取消event
        for event in args:
            pass


        pass





    def _method_wrapper(self,func:Callable,events:list[Event]):
        def method_loop():
            pass
        return method_loop





class Event:
    def __init__(self):
        self.notify_time:SimTime = None

        self.static_waiting_coroutines:list[SimCoroutine] = []
        self.waiting_coroutines:list[SimCoroutine] = []

    def notify(self,delay_time:SimTime):
        # 调用此函数的时候将 event 插入到
        # 这个 time 是delay time

        self.notify_time = SimSession.sim_time + delay_time
        SimSession.scheduler.event_queue.append(self)



    def triggered(self)->bool:
        return SimSession.sim_time == self.notify_time

    def add_static_waiting_coroutine(self,*coroutines:SimCoroutine):
        for coroutine in coroutines:
            self.static_waiting_coroutines.append(coroutine)


    def add_waiting_coroutine(self,*coroutines:SimCoroutine):
        # dynamic
        for coroutine in coroutines:
            self.waiting_coroutines.append(coroutine)

    def cancel(self):
        # 取消下一次的 notify 操作
        SimSession.scheduler.event_queue.remove(self)

    def clear_waiting_coroutine(self):
        self.waiting_coroutines = []



class Scheduler:
    def __init__(self):
        self.runnable_queue:deque = deque()
        self.waiting_queue = None
        self.running_coroutine = None

        self.event_queue:PriorityQueue[Event] = PriorityQueue()

        # self.notified_events:deque[Event] = deque()


        self.sim_time:SimTime = SimTime()

        self.executor:greenlet = None



    def initialize(self):
        # 初始化所有的 coroutine
        pass

    def main_loop(self):
        # 从 runnable queue 中取出一个 coroutine 运行
        while True:

            # 遍历 runnable queue 中的线程
            while self.runnable_queue:
                coroutine = self.runnable_queue.pop()
                coroutine.switch()
                # 支持 delta cycle 功能  在这里进行delta cycle 的更新工作
                self.handle_notified_events(self.sim_time) # 处理 delta cycle 的event 实现数据的更新


            # 当前时间点运行结束，更新时间 advance time
            # 检查 event queue，找到时间最小的 event，作为新的时间，然后更新runnable queue，之后运行
            if self.event_queue:
                # 更新时间
                assert self.event_queue.peek().notify_time > self.sim_time
                self.sim_time = self.event_queue.peek().notify_time

                self.handle_notified_events(self.sim_time)

            else:
                # 没有新的event了，退 main loop
                break


        pass

    def handle_notified_events(self,time:SimTime):
        while self.event_queue and self.event_queue.peek().notify_time == time:
            notified_event:Event = self.event_queue.pop()

            # 使所有的 coroutine 都设置为runnable 状态
            for coroutine in notified_event.static_waiting_coroutines:
                self.runnable_queue.append(coroutine)

            for coroutine in notified_event.waiting_coroutines:
                self.runnable_queue.append(coroutine)

            # 可以考虑一个event 的特殊回调函数，实现值更新的功能

            # 清空状态
            notified_event.clear_waiting_coroutine()


class SimSession:
    scheduler:Optional[Scheduler] = None

    @classmethod
    @property
    def sim_time(cls)->SimTime:
        return cls.scheduler.sim_time

    def __init__(self):
        pass



# 缺少通信机制 实现 coroutine之间的通信  类似 FIFO 或者 signal 的操作
