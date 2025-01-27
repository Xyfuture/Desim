# Test case for SimModule and coroutine interaction
from greenlet import greenlet

from Desim.Core import SimSession, SimModule, Event, SimTime
from Desim.Sync import SimSemaphore
import timeit

from Desim.module.FIFO import FIFO

def test_simulation():
    # Initialize simulation session
    SimSession.reset()
    SimSession.init()

    class MyModule(SimModule):
        def __init__(self):
            super().__init__()
            self.event1 = Event()
            self.event2 = Event()

            # Register two coroutines that depend on each other
            self.register_coroutine(self.producer )
            self.register_coroutine(self.consumer)

        def producer(self):
            for i in range(5):
                print(f"[Producer] Producing at time {SimSession.sim_time}")
                self.event1.notify(SimTime(1))  # Notify event1 after 1 cycle
                SimModule.wait(self.event2)  # Wait for event2

        def consumer(self):
            for i in range(5):
                SimModule.wait(self.event1)  # Wait for event1
                print(f"[Consumer] Consuming at time {SimSession.sim_time}")
                self.event2.notify(SimTime(1))  # Notify event2 after 1 cycle

    # Create and register the module
    module = MyModule()

    # Run the scheduler
    SimSession.scheduler.run()


def test_semaphore():
    class Trail(SimModule):
        def __init__(self):
            super().__init__()
            self.semaphore = SimSemaphore(3)

            self.register_coroutine(self.producer)
            self.register_coroutine(self.consumer)

        def producer(self):
            SimModule.wait_time(SimTime(5))
            for i in range(1000000):
                self.semaphore.post()
                # SimModule.wait_time(SimTime(2))
                # print(f"[Producer] Producing at time {SimSession.sim_time}")


        def consumer(self):
            for i in range(1000000):
                self.semaphore.wait()
                # print(f"[Consumer] Consuming at time {SimSession.sim_time}")


    SimSession.reset()
    SimSession.init()
    module = Trail()
    SimSession.scheduler.run()


def test_fifo():
    class FifoTest(SimModule):
        def __init__(self):
            super().__init__()

            self.fifo = FIFO(3)
            self.register_coroutine(self.producer)
            self.register_coroutine(self.consumer)

        def producer(self):

            for i in range(5):
                self.fifo.write(i)
                print(f"Producer Write {i} at {SimSession.sim_time}")
                SimModule.wait_time(SimTime(2))

        def consumer(self):
            for i in range(5):
                data = self.fifo.read()
                print(f"Consumer Read {data} at {SimSession.sim_time}")
                SimModule.wait_time(SimTime(10))
    
    SimSession.reset()
    SimSession.init()
    module = FifoTest()
    SimSession.scheduler.run()


if __name__ == '__main__':
    # Run the test
    # test_semaphore()
    # execution_time =timeit.timeit(test_semaphore,number=1)
    # print(f"Execution: {execution_time} s")
    # test_simulation()

    test_fifo()