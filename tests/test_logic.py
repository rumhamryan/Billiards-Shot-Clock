import json
import unittest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import lib.button_logic as logic
from lib.game_rules import EightBallRules, NineBallRules, StandardRules
from lib.models import Game_Stats, State_Machine


class TestButtonLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        # Default rules to avoid NoneType errors in generic tests
        self.game.rules = StandardRules()
        self.hw = MagicMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.hw.enter_shot_clock = AsyncMock()
        self.hw.render_menu = AsyncMock()
        self.hw.render_profile_selection = AsyncMock()
        self.hw.render_exit_confirmation = AsyncMock()
        self.hw.update_timer_display = AsyncMock()
        self.hw.render_skill_level_selection = AsyncMock()
        self.hw.render_victory = AsyncMock()
        self.hw.render_game_type_selection = AsyncMock()
        self.hw.render_wnt_target_selection = AsyncMock()
        self.hw.render_message = AsyncMock()

    # --- Profile Selection ---

    async def test_make_profile_selection_wnt(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_names = ["APA", "BCA", "WNT", "Timeouts Mode"]
        self.game.profile_selection_index = 2  # WNT

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.WNT_TARGET_SELECTION)
        self.assertFalse(self.sm.game_on)
        self.assertEqual(self.game.selected_profile, "WNT")
        self.hw.render_wnt_target_selection.assert_called_once()

    async def test_make_profile_selection_bca(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_names = ["APA", "BCA", "WNT", "Timeouts Mode"]
        self.game.profile_selection_index = 1  # BCA

        mock_rules = {"BCA": {"target": 16, "timeouts": 0}}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            await logic.handle_make(self.sm, self.game, self.hw)

        self.assertTrue(self.sm.game_on)
        self.assertEqual(self.game.selected_profile, "BCA")
        self.assertFalse(self.game.timeouts_only)
        self.assertEqual(self.game.player_1_target, 16)
        self.assertEqual(self.game.player_1_timeouts_per_rack, 0)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_profile_selection_apa_transitions_to_sl(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 0  # APA

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.APA_SKILL_LEVEL_P1)
        self.assertEqual(self.game.temp_setting_value, 3)
        self.hw.render_skill_level_selection.assert_called_with(self.sm, self.game, 1)

    # --- WNT Setup ---

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

    # --- APA Setup ---

    async def test_make_sl_p1_transitions_to_p2(self):
        self.sm.update_state(State_Machine.APA_SKILL_LEVEL_P1)
        self.game.temp_setting_value = 5

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_skill_level, 5)
        self.assertEqual(self.sm.state, State_Machine.APA_SKILL_LEVEL_P2)
        self.assertEqual(self.game.temp_setting_value, 3)
        self.hw.render_skill_level_selection.assert_called_with(self.sm, self.game, 2)

    async def test_make_sl_p2_transitions_to_game_type(self):
        self.sm.update_state(State_Machine.APA_SKILL_LEVEL_P2)
        self.game.player_1_skill_level = 5
        self.game.temp_setting_value = 4

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_2_skill_level, 4)
        self.assertEqual(self.sm.state, State_Machine.APA_GAME_TYPE_SELECTION)
        self.hw.render_game_type_selection.assert_called_once()

    async def test_make_game_type_selection_9ball(self):
        self.sm.update_state(State_Machine.APA_GAME_TYPE_SELECTION)
        self.game.temp_setting_value = 1  # 9-Ball
        self.game.player_1_skill_level = 5
        self.game.player_2_skill_level = 4

        # Mock rules in rules_config (Phase 0 refactor)
        self.game.rules_config = {
            "APA": {
                "9-Ball": {"targets": {"4": 31, "5": 38}, "timeouts": {"3": 2, "4": 1}}
            }
        }
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.match_type, "9-Ball")
        self.assertIsInstance(self.game.rules, NineBallRules)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()

    # --- Timeouts Mode ---

    async def test_timeouts_mode_menu_items(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 3  # Timeouts Mode

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.selected_profile, "Timeouts Mode")
        self.assertEqual(self.game.menu_items, ["Exit Match", "Mute"])
        self.assertEqual(len(self.game.menu_values), 2)

    # --- Game Logic & Regression ---

    async def test_regression_p1_miss_p2_win_awarded_correctly(self):
        # 1. Setup BCA
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 1  # BCA
        self.game.rules_config = {"BCA": {"target": 16, "timeouts": 0}}
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.inning_counter, 1.0)
        self.assertTrue(self.game.player_1_shooting)

        # 2. P1 Miss
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = EightBallRules()
        await logic.handle_miss(self.sm, self.game, self.hw)

        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.assertEqual(self.game.inning_counter, 1.5)
        self.assertTrue(self.game.player_2_shooting)

        # 3. Award Win (UP)
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.CONFIRM_RACK_END)

        # 4. Confirm Win (MAKE)
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_2_score, 1)
        self.assertEqual(self.game.player_1_score, 0)

    async def test_lose_rack_switches_shooter(self):
        self.sm.update_state(State_Machine.CONFIRM_RACK_END)
        self.game.pending_rack_result = "lose"
        self.game.inning_counter = 1.0
        self.game.player_1_target = 5
        self.game.player_2_target = 5

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_2_score, 1)
        self.assertEqual(self.game.inning_counter, 1.5)
        self.assertTrue(self.game.player_2_shooting)

    # --- Menu & Editing ---

    async def test_make_menu_enter_edit(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.current_menu_index = 1
        self.game.rack_counter = 5
        self.game.menu_values = [1, 5, False, None]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.EDITING_VALUE)
        self.assertEqual(self.game.temp_setting_value, 5)

    async def test_make_edit_save_apa(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.selected_profile = "APA"
        self.game.current_menu_index = 0
        self.game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        self.game.temp_setting_value = 15
        self.game.menu_values = [0, 0, None, False]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 15)
        self.assertEqual(self.game.menu_values[0], 15)

    # --- Error Handling ---

    async def test_calculate_apa_targets_fallback(self):
        self.game.match_type = "9-Ball"
        self.game.rules_config = {}
        logic._calculate_apa_targets(self.game)
        self.assertEqual(self.game.player_1_target, 14)

    async def test_init_wnt_selection_fallback(self):
        self.game.rules_config = {}
        await logic._init_wnt_selection(self.sm, self.game, self.hw)
        self.assertEqual(self.game.temp_setting_value, 9)


if __name__ == "__main__":
    unittest.main()
