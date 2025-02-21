


from Desim.Core import SimModule, SimSession, SimTime
from Desim.memory.Memory import DepMemory, DepMemoryPort, ChunkMemory, ChunkMemoryPort


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
            print(f"Consumer read addr {i} value {value} at time {SimSession.sim_time}")
    


class TestChunkMemory(SimModule):
    def __init__(self):
        super().__init__()

        self.memory = ChunkMemory()
        self.producer_port = ChunkMemoryPort()
        self.consumer_port = ChunkMemoryPort()

        self.producer_port.config_chunk_memory(self.memory)
        self.consumer_port.config_chunk_memory(self.memory)

        self.register_coroutine(self.producer)
        self.register_coroutine(self.consumer)


    def producer(self):
        for i in range(5):
            self.producer_port.write(i,i)
            print(f"Producer write addr {i} value {i} at time {SimSession.sim_time}")

        SimModule.wait_time(SimTime(2000))
        for i in range(5):
            self.producer_port.write(i, i)
            print(f"Producer write addr {i} value {i} at time {SimSession.sim_time}")

    def consumer(self):
        for i in reversed(range(5)):
            value = self.consumer_port.read(i,tag_value=1)
            print(f"Consumer read addr {i} value {value} at time {SimSession.sim_time}")

        SimModule.wait_time(SimTime(100))
        for i in range(5):
            value = self.consumer_port.read(i,tag_value=1,clear=True)
            print(f"Consumer read addr {i} value {value} - clear at time {SimSession.sim_time}")

        SimModule.wait_time(SimTime(100))
        for i in range(5):
            value = self.consumer_port.read(i,tag_value=1)
            print(f"Consumer read addr {i} value {value} at time {SimSession.sim_time}")

if __name__ == '__main__':
    SimSession.reset()
    SimSession.init()

    # module = TestMemory()
    module = TestChunkMemory()

    SimSession.scheduler.run()

    print("Finished")
