# Test case for SimModule and coroutine interaction
from Desim.Core import SimSession, SimModule, Event, SimTime


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


# Run the test
test_simulation()
