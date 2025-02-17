from typing import Callable
from Desim.Core import Event, SimModule, SimSession, SimTime
from Desim.Utils import UniquePriorityQueue


class SimSemaphore:
    def __init__(self,value:int):
        self.free_ent:Event = Event()
        self.value:int = value

    def get_value(self):
        return self.value

    def try_wait(self)->bool:
        if self.in_use():
            return False
        self.value -= 1
        return True

    def wait(self):
        # 能实现多个coroutine wait时，资源不足，多个coroutine都进入等待状态
        # value会一直保持0， 因为提前进入wait了
        # 唤醒的顺序是不能保证的， systemc 原版中也是随机进行唤醒的
        while self.in_use():
            SimModule.wait(self.free_ent)
        self.value -= 1

    def post(self):
        self.value += 1
        self.free_ent.notify(SimTime(0))

    def in_use(self)->bool:
        return self.value <= 0



class EventQueue(SimModule):
    # 实现一个类似 systemc中 event queue 的操作
    # 不同普通的event 只有一个 notify time， 这个queue有一系列notify time， 依次进行notify 操作
    def __init__(self):
        super().__init__()

        self.event = Event() # 对外的 event
 
        self.notify_time_queue = UniquePriorityQueue()
        
        self.update_event = Event()

        self.register_coroutine(self.update)
        self.register_coroutine(self.post_event)

    def next_notify(self,delay_time:SimTime):
        self.notify_time_queue.add(SimSession.sim_time + delay_time)
        self.update_event.notify(SimTime(0))

    
    def update(self):
        while True:
            SimModule.wait(self.update_event)

            if self.notify_time_queue:
                delay_time = self.notify_time_queue.peek() - SimSession.sim_time
                self.event.notify(delay_time)

    def post_event(self):
        # event 被触发之后进行的操作
        while True:
            SimModule.wait(self.event)
            assert self.notify_time_queue.peek().cycle == SimSession.sim_time.cycle
            self.notify_time_queue.pop()
            self.update_event.notify(SimTime(0))

class DelayHandler(SimModule):
    def __init__(self,callback:Callable):
        super().__init__()
        
        self.event_queue = EventQueue()

        self.trigger_ent = self.event_queue.event

        self.callback = callback

        self.register_coroutine(self.process)

    def delay_call(self,delay_time:SimTime):
        self.event_queue.next_notify(delay_time)

    def process(self):
        while True:
            SimModule.wait(self.trigger_ent)
            self.callback()


class SimDelaySemaphore(SimSemaphore):
    def __init__(self, value:int):
        super().__init__(value)
    
        self.delay_handler = DelayHandler(self._post)


    def _post(self):
        # 真正的 post 函数
        self.value += 1
        self.free_ent.notify(SimTime(0))
        

    def post(self,delay_time:SimTime=SimTime(0)):
        self.delay_handler.delay_call(delay_time)


        
        

