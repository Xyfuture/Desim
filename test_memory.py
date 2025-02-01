


from Desim.Core import SimModule, SimSession
from Desim.memory.Memory import DepMemory, DepMemoryPort


class TestMemory(SimModule):
    def __init__(self):
        super().__init__()

        self.memory = DepMemory()

        self.producer_port = DepMemoryPort()
        self.consumer_port = DepMemoryPort()

        self.producer_port.config_dep_memory(self.memory)
        self.consumer_port.config_dep_memory(self.memory)

        self.register_coroutine(self.producer)
        self.register_coroutine(self.consumer)
        
        

    def producer(self):
        for i in range(5):
            self.producer_port.write(i,i)
            print(f"Producer write addr {i} value {i} at time {SimSession.sim_time}") 

    def consumer(self):
        for i in reversed(range(5)):
            value = self.consumer_port.read(i,tag_value=1)
            print(f"Conumer read addr {i} value {value} at time {SimSession.sim_time}")
    

if __name__ == '__main__':
    SimSession.reset()
    SimSession.init()

    module = TestMemory()

    SimSession.scheduler.run()

