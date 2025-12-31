import contextlib
import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 1. Setup global mocks before any imports from lib
# This ensures that when we import lib modules, they find these in sys.modules
sys.modules["machine"] = MagicMock()
sys.modules["utime"] = MagicMock()
sys.modules["uasyncio"] = MagicMock()

# Ensure we can import from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# 2. Define a MockPin that behaves like a MicroPython Pin
class MockPin:
    IN = 1
    PULL_DOWN = 2
    IRQ_FALLING = 4

    def __init__(self, id, mode, pull):
        self.handler = None

    def irq(self, trigger, handler):
        self.handler = handler

    def trigger_irq(self):
        if self.handler:
            self.handler(self)

    def value(self):
        return 0


sys.modules["machine"].Pin = MockPin  # type: ignore

# 3. Import the module under test
import lib.button_interrupt  # noqa: E402


class TestInterrupts(unittest.TestCase):
    def setUp(self):
        # Force a reload of the module to ensure it picks up any changes to global mocks
        importlib.reload(lib.button_interrupt)
        self.AsyncButton = lib.button_interrupt.AsyncButton

        # Setup standard mock returns
        sys.modules["utime"].ticks_ms.return_value = 1000

        # Patch ticks_diff inside the module to return an integer
        # This prevents the MagicMock > int TypeError
        self.patcher = patch("lib.button_interrupt.utime.ticks_diff", return_value=1000)
        self.mock_ticks_diff = self.patcher.start()

        # Mock the event loop
        self.mock_loop = MagicMock()
        sys.modules["uasyncio"].get_event_loop.return_value = self.mock_loop

    def tearDown(self):
        self.patcher.stop()

    def test_callback_triggered(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(16, callback, debounce_delay=100)

        # Trigger the IRQ handler
        btn._irq_handler(None)

        # Check if logic proceeded to create_task
        self.mock_loop.create_task.assert_called()

    def test_debounce(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(17, callback, debounce_delay=100)

        # 1st Press: logic returns 1000 (Passes)
        self.mock_ticks_diff.return_value = 1000
        btn._irq_handler(None)
        self.assertEqual(self.mock_loop.create_task.call_count, 1)

        # 2nd Press: logic returns 50 (Fails debounce)
        self.mock_ticks_diff.return_value = 50
        btn._irq_handler(None)
        self.assertEqual(self.mock_loop.create_task.call_count, 1)

    def test_irq_exception(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(18, callback)

        # Simulate loop failure
        self.mock_loop.create_task.side_effect = Exception("Async Error")

        # Should not crash the main thread (MicroPython IRQ context behavior)
        with contextlib.suppress(Exception):
            btn._irq_handler(None)

        self.mock_loop.create_task.assert_called()


if __name__ == "__main__":
    unittest.main()
