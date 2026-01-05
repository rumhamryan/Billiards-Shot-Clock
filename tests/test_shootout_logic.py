import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from lib import button_logic
from lib.models import Game_Stats, State_Machine


class TestShootoutLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock utime and uasyncio
        self.mock_utime = MagicMock()
        self.mock_utime.ticks_ms.return_value = 1000
        self.mock_utime.ticks_diff.side_effect = lambda a, b: a - b

        self.mock_asyncio = AsyncMock()

        # Patch sys.modules
        self.patcher = patch.dict(
            sys.modules, {"utime": self.mock_utime, "uasyncio": self.mock_asyncio}
        )
        self.patcher.start()

        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.render_shootout_stopwatch = AsyncMock()
        self.hw.render_victory = AsyncMock()
        self.hw.render_shootout_announcement = AsyncMock()
        self.game.selected_profile = "Ultimate Pool"

    def tearDown(self):
        self.patcher.stop()

    async def test_shootout_transitions(self):
        # Start at Announcement
        self.sm.update_state(State_Machine.SHOOTOUT_ANNOUNCEMENT)

        # Press MAKE -> P1 WAIT
        self.mock_utime.ticks_ms.return_value = 2000
        await button_logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.SHOOTOUT_P1_WAIT)
        self.hw.render_shootout_stopwatch.assert_called_with(self.sm, self.game, 0)

        # Press MAKE -> P1 RUNNING
        self.mock_utime.ticks_ms.return_value = 3000
        await button_logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.SHOOTOUT_P1_RUNNING)
        self.assertEqual(self.game.shootout_start_tick, 3000)

        # Wait a bit and press MAKE -> P2 WAIT
        self.mock_utime.ticks_ms.return_value = 10000  # 7 seconds later
        await button_logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.SHOOTOUT_P2_WAIT)
        self.assertEqual(self.game.p1_shootout_time, 7000)
        self.hw.render_shootout_stopwatch.assert_called_with(self.sm, self.game, 0)

        # Press MAKE -> P2 RUNNING
        self.mock_utime.ticks_ms.return_value = 11000
        await button_logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.SHOOTOUT_P2_RUNNING)
        self.assertEqual(self.game.shootout_start_tick, 11000)

        # Press MAKE -> VICTORY
        self.game.p1_shootout_time = 10000  # 10s
        self.mock_utime.ticks_ms.return_value = 23000  # 12 seconds later (11000 to 23000)

        await button_logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.VICTORY)
        self.assertEqual(self.game.p2_shootout_time, 12000)
        # Verify final time was rendered BEFORE the pause
        self.hw.render_shootout_stopwatch.assert_called_with(self.sm, self.game, 12000)
        # P1 (10s) < P2 (12s), so P1 wins
        self.assertEqual(self.game.winner, 1)
        self.hw.render_victory.assert_called_with(self.sm, self.game, 1)
        # Verify pause
        self.mock_asyncio.sleep.assert_called_with(2)


if __name__ == "__main__":
    unittest.main()
