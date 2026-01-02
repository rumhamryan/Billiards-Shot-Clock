import unittest
from unittest.mock import AsyncMock, MagicMock

import lib.button_logic as logic
from lib.models import Game_Stats, State_Machine


class TestTimeoutsModeMenu(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.game.profile_names = ["APA", "BCA", "WNT", "Timeouts Mode"]

    async def test_timeouts_mode_menu_items(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 3  # Timeouts Mode

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.selected_profile, "Timeouts Mode")
        self.assertEqual(self.game.menu_items, ["Exit Match", "Mute"])
        self.assertEqual(len(self.game.menu_values), 2)
        self.assertEqual(self.game.menu_values[1], self.game.speaker_muted)


if __name__ == "__main__":
    unittest.main()
