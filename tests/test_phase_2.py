import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure we can import from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# --- Mocks for MicroPython modules ---
class MockPin:
    IN = 1
    PULL_DOWN = 2
    IRQ_FALLING = 4

    def __init__(self, id, mode, pull):
        self.id = id
        self.mode = mode
        self.pull = pull
        self.handler = None
        self._value = 0

    def irq(self, trigger, handler):
        self.handler = handler

    def value(self):
        return self._value

    def trigger_irq(self):
        if self.handler:
            self.handler(self)


mock_machine = MagicMock()
mock_machine.Pin = MockPin

mock_utime = MagicMock()
mock_utime.ticks_ms = MagicMock(side_effect=[1000, 2000, 3000, 4000, 5000])
mock_utime.ticks_diff = lambda a, b: a - b

# Inject mocks
sys.modules["machine"] = mock_machine
sys.modules["utime"] = mock_utime
sys.modules["uasyncio"] = asyncio

# Import the class under test
from lib.button_interrupt import AsyncButton


class TestPhase2Input(unittest.IsolatedAsyncioTestCase):
    async def test_button_callback_triggered(self):
        callback_called = False

        def test_callback():
            nonlocal callback_called
            callback_called = True

        btn = AsyncButton(16, test_callback, debounce_delay=100)

        # Simulate button press via IRQ
        btn.pin.trigger_irq()

        # Give the event loop a moment to run the scheduled task
        await asyncio.sleep(0.01)

        self.assertTrue(callback_called, "Callback should have been triggered")

    async def test_button_debounce(self):
        call_count = 0

        def test_callback():
            nonlocal call_count
            call_count += 1

        btn = AsyncButton(16, test_callback, debounce_delay=100)

        # Simulate two rapid presses
        # Mock ticks_ms to return values close together
        with patch("utime.ticks_ms", side_effect=[1000, 1050]):
            btn.pin.trigger_irq()  # T=1000
            btn.pin.trigger_irq()  # T=1050 (should be debounced)

        await asyncio.sleep(0.01)
        self.assertEqual(call_count, 1, "Second press should have been debounced")


if __name__ == "__main__":
    unittest.main()
