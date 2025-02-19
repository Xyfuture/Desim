from Desim.Core import SimModule, SimTime, SimSession
from Desim.module.FIFO import DelayFIFO


class TestDelayFifo(SimModule):
    def __init__(self):
        super().__init__()

        self.delay_fifo = DelayFIFO(4,0)

        self.register_coroutine(self.producer)
        self.register_coroutine(self.consumer)


    def producer(self):
        for i in range(10):
            self.delay_fifo.delay_write(i,SimTime(2))
            print(f"[Producer] write {i} at time {SimSession.sim_time}")
            SimModule.wait_time(SimTime(1))

    def consumer(self):
        for i in range(10):
            data = self.delay_fifo.read()
            print(f"[Consumer] read {data} at time {SimSession.sim_time}")
            SimModule.wait_time(SimTime(1))


if __name__ == '__main__':
    SimSession.reset()
    SimSession.init()

    test = TestDelayFifo()

    SimSession.scheduler.run()




