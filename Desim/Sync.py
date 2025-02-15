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
        while self.in_use():
            SimModule.wait(self.free_ent)
        self.value -= 1

    def post(self):
        self.value += 1
        self.free_ent.notify(SimTime(0))

    def in_use(self)->bool:
        return self.value <= 0



class EventQueue(SimModule):
    def __init__(self):
        super().__init__()

        self.event = Event() # 对外的 event
 
        self.notify_time_queue = UniquePriorityQueue()
        
        self.update_event = Event()

        self.register_coroutine(self.process)

    def next_notify(self,delay_time:SimTime):
        self.notify_time_queue.append(SimSession.sim_time + delay_time)
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
            assert self.notify_time_queue.peek() == SimSession.sim_time
            self.notify_time_queue.pop()
            self.update_event.notify(SimTime(0))

class DelayHandler(SimModule):
    def __init__(self,callback:Callable):
        super().__init__()
        
        self.event_queue = EventQueue()

        self.trigger_ent = self.event_queue.event

        self.callback = callback

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


        
        

