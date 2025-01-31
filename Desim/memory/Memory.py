
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Optional
from Desim.Core import Event, SimModule


@dataclass
class DepMemoryRequest:
    command:Literal['write','read']
    addr:int 
    data:any
    clear:bool = False
    expect_tag:int = 0 
    read_finish_event:Optional[Event] = None



class DepMemory(SimModule):
    # 暂时只维护 读写的 正确顺序
    # 对于 带宽共享的情况不进行考虑
    
    def __init__(self):
        super().__init__()

        self.memory_data:dict[int,any] = {}
        self.memory_tag:dict[int,int] = {}

        # 仅仅是该周期到来的 request ,在这一周期必须被处理 
        # 要么成功返回, 要么进入 waiting 状态 等待后续的触发
        self.pending_write_reqs:defaultdict[int,DepMemoryRequest] = {}
        self.pending_read_reqs:defaultdict[int,DepMemoryRequest] = {} 

        self.waiting_read_reqs:defaultdict[int,DepMemoryRequest] = {} 

        # 可能会发生的事件
        self.process_trigger_event = Event()


        self.register_coroutine(self.process)


    def process(self):
        while True:
            SimModule.wait(self.process_trigger_event)

            # 首先处理 clear 解决没法 write 的问题 

            # 然后处理write, 同时唤醒等待 write 的 req
            # 这里要处理 WAW 异常 
            # 如果写了一个 有 tag 的地址, 那么要抛出异常

            # 最后处理read 操作, 保证 RAW 的正常 


    def schedule_request(self):
        pass 

    def handle_read_request(self):
        # for port use 
        pass

    def handle_write_request(self):
        pass 


class DepMemoryPort():
    def __init__(self):
        
        self.dep_memory:Optional[DepMemory] = None
        
        self.read_finish_event = Event()
        
        # 记录一下 是否正在读取或者写入 只允许一个并发的操作 

    def read(self,addr:int,tag_value:int=0,clear:bool=False)->any:
        pass

    def write(self,addr:int,data:any):
        pass 


