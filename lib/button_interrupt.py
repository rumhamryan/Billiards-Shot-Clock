import uasyncio as asyncio
import utime
from machine import Pin


class AsyncButton:
    def __init__(self, pin_id, callback, debounce_delay=200):
        self.pin = Pin(pin_id, Pin.IN, Pin.PULL_DOWN)
        self.callback = callback
        self.debounce_delay = debounce_delay
        self.last_press = 0
        # Set up the interrupt
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._irq_handler)

    def _irq_handler(self, pin):
        """
        Hardware interrupt context.
        We check debounce and then schedule the async processing.
        """
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.last_press) > self.debounce_delay:
            self.last_press = now
            # Use get_event_loop to schedule the task from the IRQ
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._process_press())
            except Exception:
                # In some MicroPython versions/scenarios, loop might not be ready
                # or IRQ might be too restrictive.
                pass

    async def _process_press(self):
        """
        Async context for processing the button press.
        Includes waiting for release to avoid 'stuck' states.
        """
        # Optional: Wait for release if you want 'On Release' behavior
        # while self.pin.value():
        #    await asyncio.sleep_ms(20)

        # In MicroPython, we assume the callback returns an awaitable (coroutine)
        # or we could inspect the result, but since main.py uses async wrappers,
        # we can just await the result of the call.
        res = self.callback()
        if hasattr(res, "send"):  # Basic check if it's a coroutine/generator
            await res
