from typing import Optional
from collections import deque

from Desim.Core import Event, SimTime, SimModule
from Desim.Sync import SimDelaySemaphore, SimSemaphore


class FIFO:
    def __init__(self,fifo_size:int,init_size:int=0,init_data:Optional[list]=None):
        self.fifo_size = fifo_size

        self.fifo_data = deque(maxlen=fifo_size)

        self.empty_semaphore = SimSemaphore(init_size)
        self.full_semaphore = SimSemaphore(fifo_size - init_size)

        self.is_empty_event = Event()
        self.is_full_event = Event()

        if init_size != 0 :
            assert init_size == len(init_data)
            for item in init_data:
                self.fifo_data.append(item)


    def read(self):
        self.empty_semaphore.wait()
        self.full_semaphore.post()
        if self.empty_semaphore.get_value() == 0:
            self.is_empty_event.notify(SimTime(1))

        front_data = self.fifo_data.popleft()
        return front_data


    def write(self,data):
        self.full_semaphore.wait()
        self.empty_semaphore.post()

        if self.full_semaphore.get_value() == 0:
            self.is_full_event.notify(SimTime(1))

        self.fifo_data.append(data)

    def direct_read(self):
        if self.empty_semaphore.get_value() == 0:
            return None
        data = self.fifo_data.popleft()
        return data

    def direct_write(self,data)->bool:
        """
        直接写入可能会失败, 因此返回bool 表示操作成功或失败
        """
        if self.full_semaphore.get_value() == 0:
            return False
        self.fifo_data.append(data)
        return True


    def wait_full(self):
        if self.full_semaphore.get_value() != 0:
            SimModule.wait(self.is_full_event)


    def wait_empty(self):
        if self.empty_semaphore.get_value() != 0:
            SimModule.wait(self.is_empty_event)

    def is_empty(self)->bool:
        return self.empty_semaphore.get_value() == 0

    def is_full(self)->bool:
        return self.full_semaphore.get_value() == 0



class DelayFIFO(FIFO):
    # 支持延迟写入的功能 
    def __init__(self,fifo_size:int,init_size:int=0):
        super().__init__(fifo_size,init_size)
        self.empty_semaphore = SimDelaySemaphore(init_size)




    def delay_write(self,data:any,delay_time:SimTime):
        self.full_semaphore.wait()
        self.empty_semaphore.post(delay_time)

        if self.full_semaphore.get_value() == 0:
            self.is_full_event.notify(SimTime(0))
        
        self.fifo_data.append(data)