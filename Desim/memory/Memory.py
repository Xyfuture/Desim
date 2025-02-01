from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Literal, Optional
from Desim.Core import Event, SimModule, SimTime


@dataclass
class DepMemoryRequest:
    port:DepMemoryPort 
    command:Literal['write','read']
    addr:int 
    data:any = None
    clear:bool = False # 读完之后,最后进行进行 clear 操作
    expect_tag:int = 0 
    read_finish_event:Optional[Event] = None
    write_finish_event:Optional[Event] = None 
    check_write_tag:bool = True


class DepMemory(SimModule):
    # 暂时只维护 读写的 正确顺序
    # 对于 带宽共享的情况不进行考虑
    
    def __init__(self):
        super().__init__()

        self.memory_data:dict[int,any] = defaultdict(None)
        self.memory_tag:dict[int,int] = defaultdict(int)

        # 仅仅是该周期到来的 request ,在这一周期必须被处理 
        # 要么成功返回, 要么进入 waiting 状态 等待后续的触发
        self.pending_write_reqs:defaultdict[int,deque[DepMemoryRequest]] = defaultdict(deque)
        self.pending_read_reqs:defaultdict[int,deque[DepMemoryRequest]] = defaultdict(deque) 

        self.waiting_read_reqs:defaultdict[int,deque[DepMemoryRequest]] = defaultdict(deque)

        # 可能会发生的事件
        self.process_trigger_event = Event()


        self.register_coroutine(self.process)


    def process(self):
        while True:
            SimModule.wait(self.process_trigger_event)
            # 处理write, 同时唤醒等待 write 的 req
            # 这里要处理 WAW 异常 
            # 如果写了一个 有 tag 的地址, 那么要抛出异常
            
            for addr,write_req_deque in self.pending_write_reqs.items():
                for req in write_req_deque:
                    if req.check_write_tag: 
                        if self.memory_tag[addr] != 0:
                            assert False, 'can not write data'
                        else:
                            self.memory_data[addr] = req.data
                            self.memory_tag[addr] += 1 
                    else:
                        self.memory_data[addr] = req.data
                        self.memory_tag[addr] += 1 
                    
                    req.write_finish_event.notify(SimTime(1))
                
                
                # 处理相应的 waiting req
                finish_waiting_reqs = []
                for waiting_req in self.waiting_read_reqs[addr]:
                    if self.memory_tag[addr] == waiting_req.expect_tag:
                        req.data = self.memory_data[addr]
                        if req.clear:
                            self.memory_tag[addr] = 0
                        finish_waiting_reqs.append(req)
                        req.read_finish_event.notify(SimTime(1))
                
                for finish_req in finish_waiting_reqs:
                    self.waiting_read_reqs[addr].remove(finish_req)
                
                    
                    
            # 最后处理read 操作, 保证 RAW 的正常 
            for addr,read_req_deque in self.pending_read_reqs.items():
                for req in read_req_deque:
                    if self.memory_tag[addr] == req.expect_tag :
                        req.data = self.memory_data[addr]
                        if req.clear:
                            self.memory_tag[addr] = 0 
                        req.read_finish_event.notify(SimTime(1))
                    else:
                        # 进入 waiting 状态
                        self.waiting_read_reqs[addr].append(req)



    def shcedule_pending_read_reqs(self):
        pass 

    def schedule_write_reqs(self):
        pass 


    def handle_read_request(self,read_req:DepMemoryRequest):
        # for port use 
        if read_req.addr not in self.pending_read_reqs:
            self.pending_read_reqs[read_req.addr] = deque()
        self.pending_read_reqs[read_req.addr].append(read_req)
        self.process_trigger_event.notify(SimTime(1))

    def handle_write_request(self,write_req:DepMemoryRequest):
        if write_req.addr not in self.pending_read_reqs:
            self.pending_write_reqs[write_req.addr] = deque()
        self.pending_write_reqs[write_req.addr].append(write_req)
        self.process_trigger_event.notify(SimTime(1))


class DepMemoryPort():
    def __init__(self):
        
        self.dep_memory:Optional[DepMemory] = None
        
        self.read_finish_event = Event()
        self.write_finish_event = Event()
        
        # 记录一下 是否正在读取或者写入 只允许一个并发的操作 
        self.read_busy:bool = False
        self.write_busy:bool = False

    def read(self,addr:int,tag_value:int=0,clear:bool=False)->any:
        if self.read_busy:
            assert False,'read port busy'
        
        self.read_busy = True

        read_req = DepMemoryRequest(
            port=self,
            command='read',
            addr=addr,
            expect_tag=tag_value,
            clear=clear
        )

        self.dep_memory.handle_read_request(read_req)
        SimModule.wait(self.read_finish_event)

        self.read_busy = False
        return read_req.data

    def write(self,addr:int,data:any,check_write_tag:bool=True):
        
        if self.write_busy:
            assert False,'write port busy'
        
        self.write_busy = True

        write_req = DepMemoryRequest(
            port=self,
            command='write',
            addr=addr,
            data=data,
            check_write_tag=check_write_tag,
            write_finish_event=self.write_finish_event
        )
        
        self.dep_memory.handle_write_request(write_req)
        SimModule.wait(self.write_finish_event)

        self.write_busy = False

    

    def config_dep_memory(self,dep_memory:DepMemory):
        self.dep_memory = dep_memory