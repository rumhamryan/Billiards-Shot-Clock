import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock modules BEFORE importing anything from lib
sys.modules["machine"] = MagicMock()
sys.modules["utime"] = MagicMock()
sys.modules["utime"].ticks_diff.return_value = 1000
sys.modules["uasyncio"] = MagicMock()

# Ensure we can import from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Mock Pin class
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


class TestInterrupts(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        sys.modules["utime"].ticks_ms.reset_mock()
        sys.modules["utime"].ticks_ms.side_effect = None
        sys.modules["utime"].ticks_ms.return_value = 1000

        # Ensure we reload the module to use the latest mocks and avoid E402
        if "lib.button_interrupt" in sys.modules:
            del sys.modules["lib.button_interrupt"]
        import lib.button_interrupt

        self.AsyncButton = lib.button_interrupt.AsyncButton

        # Patch ticks_diff inside the module
        self.patcher = patch("lib.button_interrupt.utime.ticks_diff", return_value=1000)
        self.mock_ticks_diff = self.patcher.start()

        # Mock the event loop returned by uasyncio
        self.mock_loop = MagicMock()
        sys.modules["uasyncio"].get_event_loop.return_value = self.mock_loop

    def tearDown(self):
        self.patcher.stop()

    def test_callback_triggered(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(16, callback, debounce_delay=100)
        btn._irq_handler(None)
        self.mock_loop.create_task.assert_called()

    def test_debounce(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(17, callback, debounce_delay=100)

        # 1st Press
        self.mock_ticks_diff.return_value = 1000
        btn._irq_handler(None)
        self.assertEqual(self.mock_loop.create_task.call_count, 1)

        # 2nd Press (debounced)
        self.mock_ticks_diff.return_value = 50
        btn._irq_handler(None)
        self.assertEqual(self.mock_loop.create_task.call_count, 1)

    def test_irq_exception(self):
        callback = MagicMock(return_value=None)
        btn = self.AsyncButton(18, callback)
        self.mock_loop.create_task.side_effect = Exception("Boom")

        # Should not crash
        btn._irq_handler(None)
        self.mock_loop.create_task.assert_called()


if __name__ == "__main__":
    unittest.main()
