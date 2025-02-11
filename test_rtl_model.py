from Desim.Core import SimModule, SimSession, SimTime
from Desim.memory.Memory import DepMemory, DepMemoryPort
from Desim.module.Pipeline import PipeGraph


class SendModule(SimModule):
    def __init__(self):
        super().__init__()

        self.l3_memory_port = DepMemoryPort()
        self.l2_memory_port = DepMemoryPort()

        self.register_coroutine(self.process)


    def process(self):
        for i in range(8):
            data = self.l3_memory_port.read(i,1,False)
            # sim read memory latency 
            SimModule.wait_time(SimTime(2))

            # sim transfer latency
            SimModule.wait_time(SimTime(4))

            # sim write memory latency
            SimModule.wait_time(SimTime(2))
            self.l2_memory_port.write(i,data,False)
        
        print(f"Send Module finish at {SimSession.sim_time}")



class ComputeModule(SimModule):
    def __init__(self):
        super().__init__()

        self.l2_memory_read_port = DepMemoryPort()
        self.l2_memory_write_port = DepMemoryPort()

        self.register_coroutine(self.process)
    
    def process(self):
        for i in range(4):
            for j in range(2):
                self.l2_memory_read_port.read(i*2+j,1,False)
                SimModule.wait_time(SimTime(2))
            # compute 
            SimModule.wait_time(SimTime(8))

            for j in range(2):
                self.l2_memory_write_port.write(100+(i*2+j)*100,10)
                SimModule.wait_time(SimTime(2))
        print(f"Compute Module finish at {SimSession.sim_time}")


class ReceiveModule(SimModule):
    def __init__(self):
        super().__init__()
        self.l2_memory_port = DepMemoryPort()
        self.reduce_memory_port = DepMemoryPort()

        self.register_coroutine(self.process)
    
    def process(self):
        for i in range(8):
            data = self.l2_memory_port.read(i,1,False)
            SimModule.wait_time(SimTime(2))

            # 传输时间
            SimModule.wait_time(SimTime(4))

            self.reduce_memory_port.write(i,data)
            SimModule.wait_time(SimTime(2))


        print(f"Receive Module finish at {SimSession.sim_time}")
    

class Helper(SimModule):
    def __init__(self):
        super().__init__()

        self.l3_memory_port = DepMemoryPort()
        self.register_coroutine(self.process)


    def process(self):
        for i in range(8):
            self.l3_memory_port.write(i,i,False)



def test_core ():
    SimSession.reset()
    SimSession.init()

    l3_memory = DepMemory()
    l2_memory = DepMemory()
    reduce_memory = DepMemory()
    
    send_module = SendModule()
    compute_module = ComputeModule()
    receive_module = ReceiveModule()

    helper = Helper()


    send_module.l2_memory_port.config_dep_memory(l2_memory)
    send_module.l3_memory_port.config_dep_memory(l3_memory)

    compute_module.l2_memory_read_port.config_dep_memory(l2_memory)
    compute_module.l2_memory_write_port.config_dep_memory(l2_memory)

    receive_module.l2_memory_port.config_dep_memory(l2_memory)
    receive_module.reduce_memory_port.config_dep_memory(reduce_memory)

    helper.l3_memory_port.config_dep_memory(l3_memory)

    SimSession.scheduler.run()

if __name__ == "__main__":
    test_core()

