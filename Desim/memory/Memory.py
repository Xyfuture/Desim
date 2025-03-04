from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Literal, Optional
from Desim.Core import Event, SimModule, SimTime, SimSession
from Desim.Sync import EventQueue
from Desim.Utils import UniquePriorityQueue, UniqueDeque


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
                for write_req in write_req_deque:
                    if write_req.check_write_tag: 
                        if self.memory_tag[addr] != 0:
                            assert False, 'can not write data'
                        else:
                            self.memory_data[addr] = write_req.data
                            self.memory_tag[addr] += 1 
                    else:
                        self.memory_data[addr] = write_req.data
                        self.memory_tag[addr] += 1 
                    
                    write_req.write_finish_event.notify(SimTime(1))
                
                write_req_deque.clear()
                
                # 处理相应的 waiting req
                finish_waiting_reqs = []
                for waiting_req in self.waiting_read_reqs[addr]:
                    if self.memory_tag[addr] == waiting_req.expect_tag:
                        waiting_req.data = self.memory_data[addr]
                        if waiting_req.clear:
                            self.memory_tag[addr] = 0
                        finish_waiting_reqs.append(waiting_req)
                        waiting_req.read_finish_event.notify(SimTime(1))
                
                for finish_req in finish_waiting_reqs:
                    self.waiting_read_reqs[addr].remove(finish_req)
                
                    
                    
            # 最后处理read 操作, 保证 RAW 的正常 
            for addr,read_req_deque in self.pending_read_reqs.items():
                for write_req in read_req_deque:
                    if self.memory_tag[addr] == write_req.expect_tag :
                        write_req.data = self.memory_data[addr]
                        if write_req.clear:
                            self.memory_tag[addr] = 0 
                        write_req.read_finish_event.notify(SimTime(1))
                    else:
                        # 进入 waiting 状态
                        self.waiting_read_reqs[addr].append(write_req)
                read_req_deque.clear()


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
            read_finish_event=self.read_finish_event,
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





@dataclass
class ChunkMemoryConfig:
    pass



@dataclass
class ChunkPacket:
    payload: any = None

    num_elements: int = -1
    batch_size:int = -1
    element_bytes:int = -1


    @property
    def chunk_bytes(self):
        return self.num_elements * self.batch_size * self.element_bytes


@dataclass
class ChunkMemoryRequest(DepMemoryRequest):
    port:ChunkMemoryPort

    data:ChunkPacket = field(default_factory=lambda: ChunkPacket(
        payload=None,
        num_elements=128,
        batch_size=16,
        element_bytes=2
    ))

    # num_elements: int = 128 # 元素的个数
    # num_batch_size: int = 16
    # element_bytes: int = 1

    @property
    def chunk_bytes(self)->int:
        return self.data.num_elements*self.data.batch_size*self.data.element_bytes

    expect_finish_time:Optional[SimTime]=None
    status:Literal['waiting','running','finished']= 'waiting'


    def __eq__(self, other):
        return self.expect_finish_time == other.expect_finish_time and (id(self) == id(other))

    def __lt__(self, other):
        if self.expect_finish_time == other.expect_finish_time:
            return id(self) < id(other)
        return self.expect_finish_time < other.expect_finish_time

    def __gt__(self, other):
        if self.expect_finish_time == other.expect_finish_time:
            return id(self) > id(other)
        return self.expect_finish_time > other.expect_finish_time


    def __le__(self, other):
        if self.expect_finish_time == other.expect_finish_time:
            return id(self) <= id(other)
        return self.expect_finish_time <= other.expect_finish_time


    def __ge__(self, other):
        if self.expect_finish_time == other.expect_finish_time:
            return id(self) >= id(other)
        return self.expect_finish_time >= other.expect_finish_time


    def __hash__(self):
        return id(self).__hash__()




class ChunkMemory(SimModule):
    """
    基于DepMemory的依赖关系改造而来
    每个地址都表示一个chunk，一个chunk可以用 元素个数 batch size 和 datatype 来表示
    不同chunk之间的 实际大小 bytes 可能是不同的， 但是 element 数应该是一致的
    读取和写入的时间取决于 bytes的情况，与其他的无关
    """



    def __init__(self,bandwidth:int=16):
        super().__init__()

        self.bandwidth = bandwidth # bytes/cycle  每个 port 的

        self.memory_data:dict[int,any] = defaultdict(None)
        self.memory_tag:dict[int,int] = defaultdict(int)

        self.waiting_req_queue = deque()
        self.running_write_queue:UniquePriorityQueue[ChunkMemoryRequest] = UniquePriorityQueue()
        self.running_read_queue:UniquePriorityQueue[ChunkMemoryRequest] = UniquePriorityQueue()

        self.waiting_req_queue:UniqueDeque[ChunkMemoryRequest] = UniqueDeque()


        self._update_event_queue = EventQueue()
        self.update_event = self._update_event_queue.event
        self.register_coroutine(self.process)


    def process(self):
        while True:
            SimModule.wait(self.update_event)
            # running queue 或者 waiting queue 发生了变化 要在这里进行进一步处理

            # 首先处理 running queue 中已经结束的 req
            self.finish_running_reqs()

            # 之后不断从waiting queue 中取出新的 req，将其迁移到  running queue 中执行
            while self.schedule_one_waiting_req():
                pass


    def finish_running_reqs(self):
        """
        将当前cycle到期的req 清除出去
        """
        cur_time = SimSession.sim_time

        # 首先处理 read queue
        while self.running_read_queue:
            if self.running_read_queue.peek().expect_finish_time.cycle == cur_time.cycle:
                finished_req = self.running_read_queue.pop()
                finished_req.status = 'finished'
                # 唤醒相关进程
                finished_req.read_finish_event.notify(SimTime(0))
                # 如果 clear == True 需要设置 tag 的状态
                if finished_req.clear:
                    self.memory_tag[finished_req.addr] = 0

                finished_req.data.payload = self.memory_data[finished_req.addr]
            else:
                break

        # 然后处理write queue
        while self.running_write_queue:
            if self.running_write_queue.peek().expect_finish_time.cycle == cur_time.cycle:
                finished_req = self.running_write_queue.pop()
                finished_req.status = 'finished'
                # 唤醒相关的进程
                finished_req.write_finish_event.notify(SimTime(0))

                self.memory_data[finished_req.addr] = finished_req.data.payload
                self.memory_tag[finished_req.addr] += 1
            else:
                break


    def direct_write(self,addr:int,data:any,check_write_tag:bool=True,
                     num_elements:int=128,num_batch_size:int=1,element_bytes:int=1):
        """
        直接写入到内存, 用于开始仿真之前预先放置数据
        """
        if check_write_tag:
            assert self.memory_tag[addr] == 0

        self.memory_data[addr]  = data
        self.memory_tag[addr] += 1


    def schedule_one_waiting_req(self)->bool:
        """
        每次只发射一条 req， 通过多次调用实现完整的一个cycle的发射任务
        :return: 是否发射成功
        """

        def check_conflict(cur_req:ChunkMemoryRequest,pos:int)->bool:
            """
            有 conflict 返回一个true
            :param cur_req:
            :param pos:
            :return:
            """
            if cur_req.command == 'read':

                # 检查 waiting queue
                req:ChunkMemoryRequest
                for i,req in enumerate(self.waiting_req_queue):
                    if i >= pos:
                        break
                    # 开始检查
                    if req.addr == cur_req.addr:
                        if req.command == 'write': # RAW
                            return True
                        elif req.command == 'read' and req.clear == True: # RAR
                            return True

                # 检查 running queue
                for req in self.running_read_queue:
                    if req.addr == cur_req.addr and req.clear: # RAR
                        return True

                for req in self.running_write_queue:
                    if req.addr == cur_req.addr:
                        return True # WAR

                # 检查 tag
                if cur_req.expect_tag != self.memory_tag[cur_req.addr]:
                    return True


            elif cur_req.command == 'write':
                req:ChunkMemoryRequest
                for i,req in enumerate(self.waiting_req_queue):
                    if i >= pos:
                        break

                    if req.addr == cur_req.addr:
                        if req.command == 'write': return True
                        # if req.command == 'read' and req.clear == True:
                        #     if self.memory_tag[req.addr] == 0: return False
                        #     else: return True
                        # 这段应该是重复的

                for req in self.running_read_queue:
                    if req.addr == cur_req.addr:
                        return True

                for req in self.running_write_queue:
                    if req.addr == cur_req.addr:
                        return True

                # 检查TAG
                if cur_req.check_write_tag and self.memory_tag[cur_req.addr] !=0:
                    return True

            else:
                raise ValueError


            return False


        to_be_issue_req:Optional[ChunkMemoryRequest] = None

        req:ChunkMemoryRequest
        for i,req in enumerate(self.waiting_req_queue):
            if not check_conflict(req,i):
                to_be_issue_req = req
                break

        if to_be_issue_req:
            # 发射该条req

            # 首先删除 waiting queue
            self.waiting_req_queue.remove(to_be_issue_req)
            # 配置延迟信息
            latency = self.calc_latency(to_be_issue_req)
            to_be_issue_req.expect_finish_time = SimSession.sim_time + latency
            # 设定激发时间
            self._update_event_queue.next_notify(latency)

            to_be_issue_req.status = 'running'

            # 插入到队列中
            if to_be_issue_req.command == 'read':
                self.running_read_queue.add(to_be_issue_req)
            elif to_be_issue_req.command == 'write':
                self.running_write_queue.add(to_be_issue_req)

            return True

        return False


    def calc_latency(self,req:ChunkMemoryRequest)->SimTime:
        data_bytes = req.chunk_bytes

        latency = math.ceil(data_bytes/self.bandwidth)
        
        return SimTime(latency)




    def handle_read_request(self,read_req:ChunkMemoryRequest):
        self.waiting_req_queue.append(read_req)
        self._update_event_queue.next_notify(SimTime(1))



    def handle_write_request(self,write_req:ChunkMemoryRequest):
        self.waiting_req_queue.append(write_req)
        self._update_event_queue.next_notify(SimTime(1))



class ChunkMemoryPort(DepMemoryPort):
    def __init__(self,chunk_memory:Optional[ChunkMemory]=None):
        super().__init__()

        self.chunk_memory:Optional[ChunkMemory] = chunk_memory


    def config_chunk_memory(self,chunk_memory:ChunkMemory) -> None:
        self.chunk_memory = chunk_memory


    def read(self,addr:int,tag_value:int=0,clear:bool=False,
                num_elements:int=128,num_batch_size:int=16,element_bytes:int=1)->any:
        if self.read_busy:
            raise RuntimeError('read busy')

        self.read_busy = True

        read_req = ChunkMemoryRequest(
            port=self,
            command='read',
            addr=addr,
            read_finish_event=self.read_finish_event,
            expect_tag=tag_value,
            clear=clear,
            data=ChunkPacket(
                num_elements=num_elements,
                batch_size=num_batch_size,
                element_bytes=element_bytes
            )
        )

        self.chunk_memory.handle_read_request(read_req)
        SimModule.wait(self.read_finish_event)

        self.read_busy = False
        return read_req.data.payload


    def write(self,addr:int,data:any,check_write_tag:bool=True,
                num_elements:int=128,num_batch_size:int=16,element_bytes:int=1):
        if self.write_busy:
            raise RuntimeError('write busy')
        self.write_busy = True
        write_req = ChunkMemoryRequest(
            port=self,
            command='write',
            addr=addr,
            check_write_tag=check_write_tag,
            write_finish_event=self.write_finish_event,
            data=ChunkPacket(
                payload=data,
                num_elements=num_elements,
                batch_size=num_batch_size,
                element_bytes=element_bytes
            ),
        )

        self.chunk_memory.handle_write_request(write_req)
        SimModule.wait(self.write_finish_event)

        self.write_busy = False

