from Desim.Core import Event, SimModule, SimTime


class SimSemaphore:
    def __init__(self,value:int):
        self.free_ent:Event = Event()
        self.value:int = value

    def get_value(self):
        return self.value

    def try_wait(self)->bool:
        if self.in_use():
            return False
        self.value -= 1
        return True

    def wait(self):
        while self.in_use():
            SimModule.wait(self.free_ent)
        self.value -= 1

    def post(self):
        self.value += 1
        self.free_ent.notify(SimTime(0))

    def in_use(self)->bool:
        return self.value <= 0

