from typing import Optional, Callable

from Desim.Core import SimModule, Event, SimTime, SimSession
from Desim.Sync import SimSemaphore
from Desim.module.FIFO import FIFO


class PipeStage(SimModule):
    def __init__(self,handler:Optional[Callable[[dict[str,FIFO],dict[str,FIFO]], bool]]=None,time:int=-1):
        super().__init__()

        self.times:int = time
        # self.start_event = Event()
        # self.end_event = Event()

        self.start_semaphore = SimSemaphore(0)
        self.end_semaphore = SimSemaphore(0)

        self.register_coroutine(self.process)

        self.input_fifo_map:Optional[dict[str,FIFO]] = {}
        self.output_fifo_map:Optional[dict[str,FIFO]] = {}

        self.handler:Optional[Callable[[dict[str,FIFO],dict[str,FIFO]], bool]] = handler


    def process(self):
        # 两种模式，一种是 循环执行指定的次数，另一种是 无限执行下去
        while True:
            # SimModule.wait(self.start_event)
            self.start_semaphore.wait()

            if self.times == -1 :
                # run until mode
                while self.handler(self.input_fifo_map, self.output_fifo_map):
                    pass
            elif self.times > 0 :
                # run times
                for i in range(self.times):
                    if not self.handler(self.input_fifo_map, self.output_fifo_map):
                        break
            else:
                assert False
            
            # self.end_event.notify(SimTime(0))
            self.end_semaphore.post()

    def config_handler(self,handler:Callable[[dict[str,FIFO],dict[str,FIFO]], bool],times:int):
        self.handler = handler
        self.times = times

    def config_fifo(self,input_fifo_map:dict[FIFO],output_fifo_map:dict[FIFO]):
        self.input_fifo_map = input_fifo_map
        self.output_fifo_map = output_fifo_map
    
    def add_input_fifo(self,fifo_name:str,fifo:FIFO):
        self.input_fifo_map[fifo_name] = fifo

    def add_output_fifo(self,fifo_name:str,fifo:FIFO):
        self.output_fifo_map[fifo_name] = fifo

    @staticmethod
    def dynamic_create(handler:Optional[Callable[[dict[str,FIFO],dict[str,FIFO]], bool]]=None, times:int=-1):
        pipe_stage = PipeStage(handler,times)
        SimSession.scheduler.dynamic_add_module(pipe_stage)

        return pipe_stage


class PipeGraph:
    def __init__(self):
        self.stages_dict:dict[str,PipeStage] = {}  # 记录所有的 vertex
        self.connection_next_dict:dict[str,list[str]] = {} # 记录 a->b  =>  dict[a] = b 这样的map 
        self.connection_prev_dict:dict[str,list[str]] = {} # 记录 a->  =>  dict[b] = a 这样的map

        self.edges_dict:dict[tuple[str,str],tuple[str,FIFO]] = {} # 对于 a->b dict[(a,b)] = fifo

        self.sink_stages_name:set[str] = set() # 特殊的 stage 用于作为结束的stage

    def add_stages_by_dict(self,stages_dict:dict[str,PipeStage]):
        self.stages_dict.update(stages_dict)

    def add_stage(self,stage:PipeStage,name:str):
        self.stages_dict[name] = stage

    def add_edges_by_list(self,edges_list:list[tuple[str,str,int,int]]):
        # 一次性插入所有的 边 
        for edge in edges_list:
            self.add_edge(*edge)

    def add_edge(self,from_stage_name:str,to_stage_name:str,fifo_name:str,fifo_size:int,init_size:int=0):
        assert from_stage_name in self.stages_dict and to_stage_name in self.stages_dict
        if from_stage_name not in self.connection_next_dict:
            self.connection_next_dict[from_stage_name] = []
        if to_stage_name not in self.connection_prev_dict:
            self.connection_prev_dict[to_stage_name] = []

        self.connection_next_dict[from_stage_name].append(to_stage_name)
        self.connection_prev_dict[to_stage_name].append(from_stage_name)

        # 构建fifo
        fifo = FIFO(fifo_size,init_size)
        self.edges_dict[(from_stage_name,to_stage_name)]=(fifo_name,fifo)

    def add_edge_with_fifo(self,from_stage_name:str,to_stage_name:str,fifo_name:str,fifo:FIFO):
        assert from_stage_name in self.stages_dict and to_stage_name in self.stages_dict

        if from_stage_name not in self.connection_next_dict:
            self.connection_next_dict[from_stage_name] = []
        if to_stage_name not in self.connection_prev_dict:
            self.connection_prev_dict[to_stage_name] = []

        self.connection_next_dict[from_stage_name].append(to_stage_name)
        self.connection_prev_dict[to_stage_name].append(from_stage_name)

        self.edges_dict[(from_stage_name,to_stage_name)] = (fifo_name,fifo)

    def check_connection(self)->bool:
        pass
 
    # 设置开始和结束条件
    def start_pipe_graph(self):
        # 启动所有的 pipe stage
        for name,stage in self.stages_dict.items():
            # stage.start_event.notify(SimTime(0))
            stage.start_semaphore.post()


    def wait_pipe_graph_finish(self):
        for stage_name in self.sink_stages_name:
            assert stage_name in self.stages_dict
            sink_stage = self.stages_dict[stage_name]
            sink_stage.end_semaphore.wait()


    def config_sink_stage_names(self,names:list[str]):
        self.sink_stages_name.update(names)

    def add_sink_stage_by_name(self,name:str):
        self.sink_stages_name.add(name)

    def remove_sink_stage_by_name(self,name:str):
        self.sink_stages_name.discard(name)

    def build_graph(self):
        # 为 stage 构建其需要的 fifo
        for stage_name,edge_fifo in self.edges_dict.items():
            from_stage_name,to_stage_name = stage_name
            fifo_name,fifo = edge_fifo

            self.stages_dict[from_stage_name].add_output_fifo(fifo_name,fifo)
            self.stages_dict[to_stage_name].add_input_fifo(fifo_name,fifo)

    @staticmethod
    def construct_linear_pipeline(stage_names:list[str],stages:list[PipeStage]):
        # 最简单的方式构建一个 线性的,首尾连接的pipeline

        pipe_graph = PipeGraph()

        stages_dict = dict(zip(stage_names,stages))
        pipe_graph.add_stages_by_dict(stages_dict)

        # 构建连接关系
        for i in range(len(stage_names) - 1):
            pipe_graph.add_edge(stage_names[i],stage_names[i+1],f"{stage_names[i]}-{stage_names[i+1]}",1,0)

        pipe_graph.build_graph()
        pipe_graph.config_sink_stage_names([stage_names[-1]])

        return pipe_graph
            
