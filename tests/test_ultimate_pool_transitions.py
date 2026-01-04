import unittest
from unittest.mock import MagicMock

from lib import ui
from lib.models import Game_Stats, State_Machine


class TestUltimatePoolTransitions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.oled = MagicMock()
        self.oled.black = 0
        self.oled.white = 1
        self.game.selected_profile = "Ultimate Pool"

    async def test_enter_idle_from_profile_selection(self):
        # SETUP: State is PROFILE_SELECTION
        self.sm.update_state(State_Machine.PROFILE_SELECTION)

        # ACT
        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        # ASSERT: "everything" cleared
        self.oled.rect.assert_any_call(0, 0, 128, 64, 0, True)

    async def test_enter_idle_from_game_state(self):
        # SETUP: State is e.g. COUNTDOWN_COMPLETE
        self.sm.update_state(State_Machine.COUNTDOWN_COMPLETE)

        # ACT
        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        # ASSERT: "shot_clock_full" cleared (0, 0, 128, 56)
        # We need to check that "everything" (0, 0, 128, 64) was NOT called
        calls = self.oled.rect.call_args_list
        everything_cleared = any(c.args == (0, 0, 128, 64, 0, True) for c in calls)
        self.assertFalse(everything_cleared, "Should not clear everything")

        shot_clock_cleared = any(c.args == (0, 0, 128, 56, 0, True) for c in calls)
        self.assertTrue(shot_clock_cleared, "Should clear shot_clock_full")

    async def test_enter_idle_standard_profile(self):
        # SETUP: Standard profile
        self.game.selected_profile = "APA"
        self.sm.update_state(State_Machine.COUNTDOWN_COMPLETE)

        # ACT
        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        # ASSERT: "everything" cleared regardless of prev state
        self.oled.rect.assert_any_call(0, 0, 128, 64, 0, True)


if __name__ == "__main__":
    unittest.main()
