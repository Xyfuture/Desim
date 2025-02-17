from __future__ import annotations

from collections import deque
from distutils.dep_util import newer
from typing import Callable, Optional, Deque, Literal
from greenlet import greenlet
from sortedcontainers import SortedList
from Desim.Utils import UniquePriorityQueue, ClassProperty, UniqueDeque


class SimTime:
    def __init__(self, cycle: int = 0, delta_cycle: int = 1):
        if not isinstance(cycle, int):
            raise TypeError("cycle must be an int")
        if not isinstance(delta_cycle, int):
            raise TypeError("delta_cycle must be an int")
        self.cycle = cycle
        self.delta_cycle = delta_cycle

    def __eq__(self, other):
        if isinstance(other, SimTime):
            return self.cycle == other.cycle and self.delta_cycle == other.delta_cycle
        return False

    def __ne__(self, other):
        if isinstance(other, SimTime):
            return self.cycle != other.cycle or self.delta_cycle != other.delta_cycle
        return True

    def __lt__(self, other):
        if isinstance(other, SimTime):
            if self.cycle == other.cycle:
                return self.delta_cycle < other.delta_cycle
            return self.cycle < other.cycle
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, SimTime):
            if self.cycle == other.cycle:
                return self.delta_cycle <= other.delta_cycle
            return self.cycle <= other.cycle
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, SimTime):
            if self.cycle == other.cycle:
                return self.delta_cycle > other.delta_cycle
            return self.cycle > other.cycle
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, SimTime):
            if self.cycle == other.cycle:
                return self.delta_cycle >= other.delta_cycle
            return self.cycle >= other.cycle
        return NotImplemented

    def __hash__(self):
        # Combine the hash of cycle and delta_cycle to ensure uniqueness
        return hash((self.cycle, self.delta_cycle))

    def __repr__(self):
        return f"SimTime(cycle={self.cycle}, delta_cycle={self.delta_cycle})"
    
    def __add__(self, other):
        # if isinstance(other, SimTime):
        #     new_cycle = self.cycle + other.cycle
        #     new_delta_cycle = self.delta_cycle + other.delta_cycle
        #     if new_delta_cycle >= 1:
        #         new_cycle += new_delta_cycle // 1
        #         new_delta_cycle = new_delta_cycle % 1
        #     return SimTime(new_cycle, new_delta_cycle)
        # return NotImplemented
        if isinstance(other,SimTime):
            if self.cycle == 0 or other.cycle == 0:
                new_cycle = self.cycle + other.cycle
                new_delta_cycle = self.delta_cycle + other.delta_cycle
            else:
                new_cycle = self.cycle + other.cycle 
                new_delta_cycle = 0
            
            return SimTime(new_cycle,new_delta_cycle)
        return NotImplemented


    def __sub__(self, other):
        if isinstance(other,SimTime):
            # delta cycle 是不能减少的
            if other.cycle == 0 :
                new_delta_cycle = self.delta_cycle
            else:
                new_delta_cycle = 0
            new_cycle = self.cycle - other.cycle
            return SimTime(new_cycle,new_delta_cycle)
        return NotImplemented


class SimCoroutine(greenlet):
    def __init__(self,func:Callable):
        super(SimCoroutine, self).__init__(func)





class SimModule:
    def __init__(self):
        self._coroutines:set[SimCoroutine] = set() # method 会被改写为 coroutine

        SimSession.sim_modules.append(self)


    def register_coroutine(self,func:Callable,*events:Event):
        coroutine = SimCoroutine(func)
        self._coroutines.add(coroutine)
        for event in events:
            event.add_static_waiting_coroutine(coroutine)
        
        
    def register_method(self,func:Callable,*events:Event):
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


    @staticmethod
    def wait_time(sim_time:SimTime):
        event = Event()
        event.notify(sim_time)
        SimModule.wait(event)






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
        # TODO 这里存在一个bug 如果这个event已经在 queue中了, 如果直接更新了 notify time queue就出错了, 会出现问题
        # self.notify_time = SimSession.sim_time + delay_time # 就是这行,不知直接暴力的更新
        # 简单处理可以先删除, 然后在加进去
        # SimSession.scheduler.event_queue.append(self)
        SimSession.scheduler.insert_event(self,SimSession.sim_time + delay_time)

    def wait(self,*args,**kwargs):
        SimModule.wait(*(self,*args),**kwargs)



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
            self.waiting_coroutines.discard(coroutine)

    def get_waiting_coroutines(self)->set[SimCoroutine]:
        return self.static_waiting_coroutines | self.waiting_coroutines
    

    def cancel(self):
        # 取消下一次的 notify 操作
        self.notify_time = SimTime()
        SimSession.scheduler.event_queue.remove(self)

    def clear_waiting_coroutine(self):
        self.waiting_coroutines = set()

    def __lt__(self, other):
        # if self.notify_time == other.notify_time:
        #     return id(self) < id(other)
        return self.notify_time < other.notify_time

    def __gt__(self, other):
        # if self.notify_time == other.notify_time:
        #     return id(self) > id(other)
        return self.notify_time > other.notify_time


    def __eq__(self, other):
        return self.notify_time == other.notify_time and (id(self) == id(other))


    def __le__(self, other):
        # if self.notify_time == other.notify_time:
        #     return id(self) <= id(other)
        return self.notify_time <= other.notify_time


    def __ge__(self, other):
        # if self.notify_time == other.notify_time:
        #     return id(self) >= id(other)
        return self.notify_time >= other.notify_time


    def __ne__(self, other):
        return self.notify_time != other.notify_time or (id(self) != id(other))

    def __hash__(self):
        return id(self)



class Scheduler:
    def __init__(self):
        self.runnable_queue:UniqueDeque[SimCoroutine] = UniqueDeque()
        self.waiting_queue = None
        self.running_coroutine = None

        self.event_queue:UniquePriorityQueue[Event] = UniquePriorityQueue()

        # self.notified_events:deque[Event] = deque()


        self.sim_time:SimTime = SimTime(0,0)

        self.executor_coroutine:greenlet = None

        self.initialize_coroutine = greenlet(self.initialize)
        self.main_loop_coroutine = greenlet(self.main_loop)

        self.status:Literal['uninitialized','initializing','initialized','running','finished'] = 'uninitialized'


    def run(self):
        self.initialize_coroutine.switch()
        self.status = 'initialized'
        self.main_loop_coroutine.switch()
        self.status = 'finished'

    def initialize(self):
        self.status = 'initializing'
        self.executor_coroutine = greenlet.getcurrent()
        # 初始化所有的 coroutine, 将所有的coroutine放入到 runnable queue中
        for module in SimSession.sim_modules:
            for coroutine in module._coroutines:
                # 需要指定 parent，这样 sim module的 Coroutine执行结束后，会回到mainloop 执行其他的 Coroutine
                coroutine.parent = self.main_loop_coroutine
                self.runnable_queue.append(coroutine)


    def main_loop(self):
        self.status = 'running'
        self.executor_coroutine = greenlet.getcurrent()

        # 执行主体的循环，直到所有的coroutine都执行完毕，才会退出
        while True:

            # 类似于systemc 的 evaluate 阶段
            # 遍历 runnable queue 中的线程，取出里面所有可跑的进程，依次执行
            while self.runnable_queue:
                coroutine = self.runnable_queue.pop()
                coroutine.switch()


            # 进入 update 阶段， 更新delta cycle 或者 sim cycle 推动时间前进
            # 类似 systemc 的 update 阶段

                # # 支持 delta cycle 功能  在这里进行delta cycle 的更新工作
                # self.handle_notified_events(self.sim_time) # 处理 delta cycle 的event 实现数据的更新

            # 检查 event queue，找到时间最小的 event，，作为新的时间，然后更新runnable queue，之后运行
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

    def insert_event(self,event:Event,new_notify_time:SimTime):
        if event in self.event_queue:
            self.event_queue.remove(event)
            event.notify_time = new_notify_time
            self.event_queue.add(event)
        else:
            event.notify_time = new_notify_time
            self.event_queue.add(event)


    # 受限于初始化机制，目前动态初始化需要借助特殊的函数进行。
    def dynamic_add_module(self, module:SimModule):
        for coroutine in module._coroutines:
            self.dynamic_add_coroutine(coroutine)

    def dynamic_add_coroutine(self,coroutine:SimCoroutine):
        # 手动执行类似初始化的操作
        if self.status == 'running':
            coroutine.parent = self.main_loop_coroutine
            self.runnable_queue.append(coroutine)
        else:
            assert False


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
