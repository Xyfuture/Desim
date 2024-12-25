from __future__ import annotations

from collections import deque
from typing import Callable, Optional, Deque
from greenlet import greenlet
from sortedcontainers import SortedList
from Desim.Utils import PriorityQueue,ClassProperty


class SimTime:
    def __init__(self, cycle: int = 0):
        if not isinstance(cycle, int):
            raise TypeError("cycle must be an int")
        self.cycle = cycle

    def __eq__(self, other):
        if isinstance(other, SimTime):
            return self.cycle == other.cycle
        return False

    def __ne__(self, other):
        if isinstance(other, SimTime):
            return self.cycle != other.cycle
        return True

    def __lt__(self, other):
        if isinstance(other, SimTime):
            return self.cycle < other.cycle
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, SimTime):
            return self.cycle <= other.cycle
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, SimTime):
            return self.cycle > other.cycle
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, SimTime):
            return self.cycle >= other.cycle
        return NotImplemented

    def __hash__(self):
        # Use the hash of the cycle for simplicity
        return hash(self.cycle)

    def __repr__(self):
        return f"SimTime({self.cycle})"
    
    def __add__(self, other):
        if isinstance(other, SimTime):
            return SimTime(self.cycle + other.cycle)
        return NotImplemented



class SimCoroutine(greenlet):
    def __init__(self,func:Callable):
        super(SimCoroutine, self).__init__(func,SimSession.scheduler.executor_coroutine)





class SimModule:
    def __init__(self):
        self._coroutines:set[SimCoroutine] = set() # method 会被改写为 coroutine

        SimSession.sim_modules.append(self)


    def register_coroutine(self,func:Callable,events:list[Event]):
        coroutine = SimCoroutine(func)
        self._coroutines.add(coroutine)
        for event in events:
            event.add_static_waiting_coroutine(coroutine)
        
        
    def register_method(self,func:Callable,events:list[Event]):
        pass


    @staticmethod
    def wait(*args,**kwargs):
        for event in args:
            assert isinstance(event,Event)
            # 注册 event 将当前的Coroutine加入到 event的列表中
            event.add_waiting_coroutine(greenlet.getcurrent()) 

        # 切换出 协程, 切换到指定的 scheduler 的线程
        SimSession.scheduler.executor_coroutine.switch()

        # 切换回来，取消event 当 wait 多个 event 的时候，只要一个 event 触发了，就结束了
        event:Event
        for event in args:
            event.remove_waiting_coroutine(greenlet.getcurrent())
        
        # 结束 wait 恢复到协程继续执行



    def _method_wrapper(self,func:Callable,events:list[Event]):
        def method_loop():
            pass
        return method_loop





class Event:
    def __init__(self):
        self.notify_time:SimTime = None

        self.static_waiting_coroutines:set[SimCoroutine] = set()
        self.waiting_coroutines:set[SimCoroutine] = set()

    def notify(self,delay_time:SimTime):
        # 调用此函数的时候将 event 插入到
        # 这个 time 是delay time

        self.notify_time = SimSession.sim_time + delay_time
        SimSession.scheduler.event_queue.append(self)



    def triggered(self)->bool:
        return SimSession.sim_time == self.notify_time

    def add_static_waiting_coroutine(self,*coroutines:SimCoroutine):
        for coroutine in coroutines:
            self.static_waiting_coroutines.add(coroutine)


    def add_waiting_coroutine(self,*coroutines:SimCoroutine):
        # dynamic
        for coroutine in coroutines:
            self.waiting_coroutines.add(coroutine)

    def remove_waiting_coroutine(self,*coroutines:SimCoroutine):
        for coroutine in coroutines:
            self.waiting_coroutines.remove(coroutine)

    def get_waiting_coroutines(self)->set[SimCoroutine]:
        return self.static_waiting_coroutines | self.waiting_coroutines
    

    def cancel(self):
        # 取消下一次的 notify 操作
        self.notify_time = SimTime()
        SimSession.scheduler.event_queue.remove(self)

    def clear_waiting_coroutine(self):
        self.waiting_coroutines = set()



class Scheduler:
    def __init__(self):
        self.runnable_queue:deque = deque()
        self.waiting_queue = None
        self.running_coroutine = None

        self.event_queue:PriorityQueue[Event] = PriorityQueue()

        # self.notified_events:deque[Event] = deque()


        self.sim_time:SimTime = SimTime(0)

        self.executor_coroutine:greenlet = None

        self.initialize_coroutine = greenlet(self.initialize)
        self.main_loop_coroutine = greenlet(self.main_loop)


    def run(self):
        self.initialize_coroutine.switch()
        self.main_loop_coroutine.switch()


    def initialize(self):
        self.executor_coroutine = greenlet.getcurrent()
        # 初始化所有的 coroutine
        for module in SimSession.sim_modules:
            for coroutine in module._coroutines:
                coroutine.switch()
        pass

    def main_loop(self):
        self.executor_coroutine = greenlet.getcurrent()

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
            for coroutine in notified_event.get_waiting_coroutines():
                self.runnable_queue.append(coroutine)

            # 可以考虑一个event 的特殊回调函数，实现值更新的功能

            # 清空状态
            notified_event.clear_waiting_coroutine()


class SimSession:
    scheduler:Optional[Scheduler] = None
    
    sim_modules:list[SimModule] = []


    @ClassProperty
    def sim_time(cls)->SimTime:
        return cls.scheduler.sim_time



    def __init__(self):
        pass

    @classmethod
    def reset(cls):
        cls.scheduler = None 
        cls.sim_modules = []

    @classmethod
    def init(cls):
        cls.scheduler = Scheduler()
        cls.sim_modules = []





# 缺少通信机制 实现 coroutine之间的通信  类似 FIFO 或者 signal 的操作
