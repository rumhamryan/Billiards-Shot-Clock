import json
import unittest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import lib.button_logic as logic
from lib.game_rules import EightBallRules
from lib.models import Game_Stats, State_Machine


class TestWntUpdate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.hw.render_wnt_target_selection = AsyncMock()
        self.hw.render_profile_selection = AsyncMock()
        self.hw.render_message = AsyncMock()
        self.game.profile_names = ["APA", "BCA", "WNT", "Timeouts Mode"]

    async def test_select_wnt_transitions_to_target_selection(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 2  # WNT

        mock_rules = {"WNT": {"targets": [5, 7, 9, 11, 13]}}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.WNT_TARGET_SELECTION)
        self.assertEqual(self.game.temp_setting_value, 9)
        self.hw.render_wnt_target_selection.assert_called_once()

    async def test_wnt_target_selection_up_down(self):
        self.sm.update_state(State_Machine.WNT_TARGET_SELECTION)
        self.game.temp_setting_value = 9

        mock_rules = {"WNT": {"targets": [5, 7, 9, 11, 13]}}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            # UP
            await logic.handle_up(self.sm, self.game, self.hw)
            self.assertEqual(self.game.temp_setting_value, 11)

            # DOWN
            await logic.handle_down(self.sm, self.game, self.hw)
            self.assertEqual(self.game.temp_setting_value, 9)

    async def test_confirm_wnt_target_setup(self):
        self.sm.update_state(State_Machine.WNT_TARGET_SELECTION)
        self.game.temp_setting_value = 7
        self.game.selected_profile = "WNT"

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_target, 7)
        self.assertEqual(self.game.player_2_target, 7)
        self.assertEqual(self.game.player_1_timeouts_remaining, 1)
        self.assertEqual(self.game.player_2_timeouts_remaining, 1)
        self.assertIsInstance(self.game.rules, EightBallRules)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_wnt_up_triggers_confirmation(self):
        # Setup WNT Idle
        self.game.selected_profile = "WNT"
        self.game.rules = EightBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.player_1_shooting = True

        # Press UP
        await logic.handle_up(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.CONFIRM_RACK_END)
        self.assertEqual(self.game.pending_rack_result, "win")
        self.hw.render_message.assert_called_with(self.sm, self.game, "Confirm Win?")

    async def test_wnt_down_idle_does_nothing(self):
        # Setup WNT Idle
        self.game.selected_profile = "WNT"
        self.game.rules = EightBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

        # Press DOWN
        await logic.handle_down(self.sm, self.game, self.hw)

        # Verify state remains IDLE and no pending result
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.assertIsNone(self.game.pending_rack_result)
        self.hw.render_message.assert_not_called()

    async def test_wnt_confirm_win_increments_score(self):
        self.game.selected_profile = "WNT"
        self.game.rules = EightBallRules()
        self.sm.update_state(State_Machine.CONFIRM_RACK_END)
        self.game.pending_rack_result = "win"
        self.game.player_1_shooting = True
        self.game.player_1_score = 0
        self.game.player_1_target = 9
        self.game.player_2_target = 9
        self.game.menu_values = [0, 0, None, False]
        self.game.player_1_timeouts_per_rack = 1

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 1)
        self.assertEqual(self.game.menu_values[0], 1)
        self.assertEqual(self.game.player_1_timeouts_remaining, 1)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)


if __name__ == "__main__":
    unittest.main()
