from Desim.Core import SimSession, SimModule
from Desim.Sync import SimSemaphore, SimOrderedSemaphore
from Desim.Core import SimTime


class TestSemaphore(SimModule):
    def __init__(self):
        super().__init__()

        # self.semaphore = SimSemaphore(1)
        self.semaphore = SimOrderedSemaphore(1)


        self.register_coroutine(self.poster)

        for i in range(5):
            self.register_coroutine(self.waiter_helper(SimTime(i*10),f"Waiter {i}"))


    def waiter_helper(self,start_time:SimTime, name:str):
        def waiter():
            SimModule.wait_time(start_time)
            print(f"{name} start wait at {SimSession.sim_time}")
            self.semaphore.wait()
            print(f"{name} finish wait at {SimSession.sim_time}")


        return waiter


    def poster(self):
        SimModule.wait_time(SimTime(100))
        for i in range(10):
            self.semaphore.post()
            SimModule.wait_time(SimTime(10))





if __name__ == '__main__':
    SimSession.reset()
    SimSession.init()

    module = TestSemaphore()


    SimSession.scheduler.run()
    print(f'Finished at {SimSession.sim_time}')



