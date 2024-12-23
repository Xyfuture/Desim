from greenlet import greenlet


class SimCoroutine(greenlet):
    def __init__(self):
        super(SimCoroutine, self).__init__()




class Event:
    def __init__(self):
        pass


class Scheduler:
    def __init__(self):
        self.runnable_queue = None
        self.waiting_queue = None
        self.running_coroutine = None

        self.event_queue = None

        self.sim_time = None



    def initialize(self):
        # 初始化所有的 coroutine
        pass

    def main_loop(self):
        pass



class SimSession:
    def __init__(self):
        pass

