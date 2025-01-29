from typing import Optional, Callable

from Desim.Core import SimModule, Event
from Desim.module.FIFO import FIFO


class PipeStage(SimModule):
    def __init__(self):
        super().__init__()

        self.times:int = -1
        self.start_event = Event()
        self.register_coroutine(self.process)

        self.input_fifo_map:Optional[dict[FIFO]] = None
        self.output_fifo_map:Optional[dict[FIFO]] = None

        self.handler:Optional[Callable[[dict[FIFO],dict[FIFO]], bool]] = None


    def process(self):
        # 两种模式，一种是 循环执行指定的次数，另一种是 无限执行下去
        while True:
            SimModule.wait(self.start_event)

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

    def config_handler(self,handler:Callable[[dict[FIFO],dict[FIFO]], bool],times:int):
        self.handler = handler
        self.times = times

    def config_fifo(self,input_fifo_map:dict[FIFO],output_fifo_map:dict[FIFO]):
        self.input_fifo_map = input_fifo_map
        self.output_fifo_map = output_fifo_map


class PipeGraph:
    def __init__(self):
        self.stages_dict:dict[str,PipeStage] = {}  # 记录所有的 vertex
        self.connection_next_dict:dict[str,list[str]] = {} # 记录 a->b  =>  dict[a] = b 这样的map
        self.connection_prev_dict:dict[str,list[str]] = {} # 记录 a->  =>  dict[b] = a 这样的map

        self.edges_dict:dict[tuple[str,str],FIFO] = {} # 对于 a->b dict[(a,b)] = fifo



    def add_stages_by_dict(self,stages_dict:dict[str,PipeStage]):
        self.stages_dict.update(stages_dict)

    def add_stage(self,stage:PipeStage,name:str):
        self.stages_dict[name] = stage

    def add_edges_by_dict(self):
        pass

    def add_edge(self,from_stage_name:str,to_stage_name:str,fifo_size:int,init_size:int=0):
        assert from_stage_name in self.stages_dict and to_stage_name in self.stages_dict
        if from_stage_name not in self.connection_next_dict:
            self.connection_next_dict[from_stage_name] = []
        if to_stage_name not in self.connection_prev_dict:
            self.connection_prev_dict[to_stage_name] = []

        self.connection_next_dict[from_stage_name].append(to_stage_name)
        self.connection_prev_dict[to_stage_name].append(from_stage_name)

        # 构建fifo
        fifo = FIFO(fifo_size,init_size)
        self.edges_dict[(from_stage_name,to_stage_name)]=fifo


    def add_edge_with_fifo(self):
        pass

    def check_connection(self)->bool:
        pass

