from typing import Optional
from Desim.Core import SimModule, SimSession, SimTime
from Desim.module.FIFO import FIFO
from Desim.module.Pipeline import PipeGraph, PipeStage


def a_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]]):
    for i in range(5):
        output_fifo_map['a-b'].write(i)
        print(f"a handler write value {i}")
        SimModule.wait_time(SimTime(1))

def b_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]]):
    for i in range(5):
        value = input_fifo_map['a-b'].read()
        print(f"b handler read and write value {value}")
        output_fifo_map['b-c'].write(value)
        SimModule.wait_time(SimTime(1)) 

def c_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]]):
    for i in range(5):
        value = input_fifo_map['b-c'].read()
        print(f'c handler read value {value}')


def build_pipe_graph():
    graph = PipeGraph()

    a_pipe_stage = PipeStage()
    b_pipe_stage = PipeStage()
    c_pipe_stage = PipeStage()

    a_pipe_stage.config_handler(a_handler,-1)
    b_pipe_stage.config_handler(b_handler,-1)
    c_pipe_stage.config_handler(c_handler,-1)

    graph.add_stage(a_pipe_stage,'a')
    graph.add_stage(b_pipe_stage,'b')
    graph.add_stage(c_pipe_stage,'c')

    graph.add_edge('a','b','a-b',1,0)
    graph.add_edge('b','c','b-c',1,0)

    graph.build_graph()
    graph.config_sink_stage_name('c')
    return graph


class TestPipe(SimModule):
    def __init__(self):
        super().__init__()

        self.graph = build_pipe_graph()

        self.register_coroutine(self.process)
    
    def process(self):
        SimModule.wait_time(SimTime(1))
        print(f"in process at {SimSession.sim_time} start pipe")
        self.graph.start_pipe_graph()
        self.graph.wait_pipe_graph_finish()

        print(f'graph finish at time {SimSession.sim_time}')




if __name__ == "__main__":
    SimSession.reset()
    SimSession.init()
    
    module = TestPipe()
    SimSession.scheduler.run()