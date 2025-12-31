import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

# Ensure we can import from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.button_logic import handle_make, handle_up
from lib.models import Game_Stats, State_Machine


class TestPhase3Logic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state_machine = State_Machine()
        self.game = Game_Stats()
        self.hw_module = MagicMock()
        self.hw_module.enter_idle_mode = AsyncMock()
        self.hw_module.enter_shot_clock = AsyncMock()
        self.hw_module.render_menu = AsyncMock()
        self.hw_module.render_profile_selection = AsyncMock()
        self.hw_module.update_timer_display = AsyncMock()

    async def test_profile_selection_to_idle(self):
        # Start in Profile Selection
        self.state_machine.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 0  # APA by default in list

        await handle_make(self.state_machine, self.game, self.hw_module)

        # Check that we tried to enter idle mode
        self.hw_module.enter_idle_mode.assert_called_once()
        self.assertEqual(self.game.selected_profile, "APA")
        self.assertEqual(self.game.profile_based_countdown, 20)

    async def test_idle_to_shot_clock(self):
        self.state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)

        await handle_make(self.state_machine, self.game, self.hw_module)

        self.hw_module.enter_shot_clock.assert_called_once()

    async def test_running_to_reset(self):
        self.state_machine.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.profile_based_countdown = 30
        self.game.countdown = 15

        await handle_make(self.state_machine, self.game, self.hw_module)

        self.assertEqual(self.game.countdown, 30)
        self.hw_module.enter_idle_mode.assert_called_once()

    async def test_menu_navigation(self):
        self.state_machine.update_state(State_Machine.MENU)
        self.game.current_menu_index = 0  # "Rack"

        await handle_up(self.state_machine, self.game, self.hw_module)

        # In Game_Stats, menu is ["Rack", "Mute", "Inning"]
        # Index 0 - 1 = 2 (Inning)
        self.assertEqual(self.game.current_menu_index, 2)
        self.hw_module.render_menu.assert_called_once()

    async def test_menu_edit_flow(self):
        # 1. Enter Menu
        self.state_machine.update_state(State_Machine.MENU)
        self.game.current_menu_index = 0  # Rack
        self.game.rack_counter = 1
        self.game.menu_values = [1, False, 1]

        # 2. Press Make to edit
        await handle_make(self.state_machine, self.game, self.hw_module)
        self.assertEqual(self.state_machine.state, State_Machine.EDITING_VALUE)
        self.assertEqual(self.game.temp_setting_value, 1)

        # 3. Press Up to increment
        await handle_up(self.state_machine, self.game, self.hw_module)
        self.assertEqual(self.game.temp_setting_value, 2)

        # 4. Press Make to save
        await handle_make(self.state_machine, self.game, self.hw_module)
        self.assertEqual(self.state_machine.state, State_Machine.MENU)
        self.assertEqual(self.game.rack_counter, 2)
        self.assertEqual(self.game.menu_values[0], 2)


if __name__ == "__main__":
    unittest.main()
