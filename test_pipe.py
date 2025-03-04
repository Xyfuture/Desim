from typing import Optional

from Desim.Core import SimModule, SimSession, SimTime
from Desim.module.FIFO import FIFO
from Desim.module.Pipeline import PipeGraph, PipeStage


def a_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]])->bool:
    for i in range(5):
        output_fifo_map['a-b'].write(i)
        print(f"a handler write value {i}")
        SimModule.wait_time(SimTime(1))
    return False

def b_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]])->bool:
    for i in range(5):
        value = input_fifo_map['a-b'].read()
        print(f"b handler read and write value {value}")
        output_fifo_map['b-c'].write(value)
        SimModule.wait_time(SimTime(1))
    return False

def c_handler(input_fifo_map:Optional[dict[str,FIFO]],output_fifo_map:Optional[dict[str,FIFO]])->bool:
    for i in range(5):
        value = input_fifo_map['b-c'].read()
        print(f'c handler read value {value}')
    return False


def build_pipe_graph():
    graph = PipeGraph()

    a_pipe_stage = PipeStage(a_handler)
    b_pipe_stage = PipeStage(b_handler)
    c_pipe_stage = PipeStage(c_handler)



    graph.add_stage(a_pipe_stage,'a')
    graph.add_stage(b_pipe_stage,'b')
    graph.add_stage(c_pipe_stage,'c')

    graph.add_edge('a','b','a-b',1,0)
    graph.add_edge('b','c','b-c',1,0)

    graph.build_graph()
    graph.config_sink_stage_names(['c'])
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




class TestLinearPipe(SimModule):
    def __init__(self):
        super().__init__()

        stage_a = PipeStage()
        stage_b = PipeStage()
        stage_c = PipeStage()

        stage_a.config_handler(a_handler,-1)
        stage_b.config_handler(b_handler,-1)
        stage_c.config_handler(c_handler,-1)

        self.pipe_line = PipeGraph.construct_linear_pipeline(
            ['a','b','c'],[stage_a,stage_b,stage_c]
        )

        self.register_coroutine(self.process)

    def process(self):
        SimModule.wait_time(SimTime(1))
        print(f"in process at {SimSession.sim_time} start pipe")
        self.pipe_line.start_pipe_graph()
        self.pipe_line.wait_pipe_graph_finish()

        print(f'graph finish at time {SimSession.sim_time}')


class TestSinkPipe(SimModule):
    def __init__(self):
        super().__init__()

        stage_a = PipeStage(self.a_handler)
        stage_b = PipeStage(self.b_handler)
        stage_c = PipeStage(self.c_handler)

        self.pipe_graph = PipeGraph()
        self.pipe_graph.add_stage(stage_a,'a')
        self.pipe_graph.add_stage(stage_b,'b')
        self.pipe_graph.add_stage(stage_c,'c')

        self.pipe_graph.add_edge('a','b','a-b',1,0)
        self.pipe_graph.add_edge('a','c','a-c',1,0)

        self.pipe_graph.build_graph()
        self.pipe_graph.config_sink_stage_names(['b','c'])

        self.register_coroutine(self.process)

    def process(self):
        SimModule.wait_time(SimTime(1))
        print(f"in process at {SimSession.sim_time} start pipe")
        self.pipe_graph.start_pipe_graph()
        self.pipe_graph.wait_pipe_graph_finish()
        print(f'graph finish at time {SimSession.sim_time}')

    def a_handler(self,input_fifo_map: Optional[dict[str, FIFO]], output_fifo_map: Optional[dict[str, FIFO]]) -> bool:
        for i in range(5):
            output_fifo_map['a-b'].write(i)
            output_fifo_map['a-c'].write(i)
            print(f"a handler write value {i}")
            SimModule.wait_time(SimTime(1))
        return False

    def b_handler(self,input_fifo_map: Optional[dict[str, FIFO]], output_fifo_map: Optional[dict[str, FIFO]]) -> bool:
        for i in range(5):
            value = input_fifo_map['a-b'].read()
            print(f"b handler read and write value {value}")
            SimModule.wait_time(SimTime(1))
        return False

    def c_handler(self,input_fifo_map: Optional[dict[str, FIFO]], output_fifo_map: Optional[dict[str, FIFO]]) -> bool:
        for i in range(5):
            value = input_fifo_map['a-c'].read()
            print(f'c handler read value {value}')
            SimModule.wait_time(SimTime(1))
        return False


if __name__ == "__main__":
    SimSession.reset()
    SimSession.init()
    
    # module = TestPipe()
    # module = TestLinearPipe()
    module = TestSinkPipe()

    SimSession.scheduler.run()