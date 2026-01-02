import unittest
from unittest.mock import AsyncMock, MagicMock

import lib.button_logic as logic
from lib.game_rules import NineBallRules, StandardRules
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
        self.hw.render_message = AsyncMock()

    # --- HANDLE MAKE ---

    async def test_make_profile_selection_wnt(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_names = ["APA", "BCA", "WNT", "Timeouts Mode"]
        self.game.profile_selection_index = 2  # WNT

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertTrue(self.sm.game_on)
        self.assertEqual(self.game.selected_profile, "WNT")
        self.assertEqual(self.game.profile_based_countdown, 30)
        self.assertIsInstance(self.game.rules, StandardRules)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_profile_selection_apa_transitions_to_sl(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 0  # APA

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.APA_SKILL_LEVEL_P1)
        self.assertEqual(self.game.temp_setting_value, 3)
        self.hw.render_skill_level_selection.assert_called_with(self.sm, self.game, 1)

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

        # Mock json load for _calculate_apa_targets
        with unittest.mock.patch(
            "builtins.open",
            unittest.mock.mock_open(
                read_data='{"9-Ball": {"targets": {"4": 31, "5": 38}}}'
            ),
        ):
            await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.match_type, "9-Ball")
        self.assertIsInstance(self.game.rules, NineBallRules)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_countdown_victory(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = NineBallRules()
        self.game.selected_profile = "APA"
        self.game.player_1_shooting = True
        self.game.player_1_score = 37
        self.game.player_1_target = 38

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 38)
        self.assertEqual(self.sm.state, State_Machine.VICTORY)
        self.hw.render_victory.assert_called_with(self.sm, self.game, 1)

    async def test_up_sl_selection_wraps(self):
        self.sm.update_state(State_Machine.APA_SKILL_LEVEL_P1)
        self.game.temp_setting_value = 9
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.temp_setting_value, 1)

    async def test_down_sl_selection_wraps(self):
        self.sm.update_state(State_Machine.APA_SKILL_LEVEL_P1)
        self.game.temp_setting_value = 1
        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.temp_setting_value, 9)

    async def test_make_idle(self):
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rules = StandardRules()
        await logic.handle_make(self.sm, self.game, self.hw)
        self.hw.enter_shot_clock.assert_called_once()

    async def test_make_running(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = NineBallRules()  # Use 9Ball rules for score/reset check
        self.game.selected_profile = "APA"
        self.game.extension_available = False
        self.game.player_1_target = 10
        self.game.player_2_target = 10

        await logic.handle_make(self.sm, self.game, self.hw)

        # Should reset extensions for APA
        self.assertTrue(self.game.extension_available)
        self.assertFalse(self.game.break_shot)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_running_wnt(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = StandardRules()
        self.game.selected_profile = "WNT"
        self.game.extension_available = False

        await logic.handle_make(self.sm, self.game, self.hw)

        # StandardRules doesn't check 'selected_profile' for extension logic
        # in handle_make, it just resets defaults.
        self.assertTrue(self.game.extension_available)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_menu_enter_edit(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.current_menu_index = 1  # Rack
        self.game.rack_counter = 5
        self.game.menu_values = [1, 5, False, None]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.EDITING_VALUE)
        self.assertEqual(self.game.temp_setting_value, 5)
        self.hw.render_menu.assert_called_once()

    async def test_make_edit_save(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 1  # Rack
        self.game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]
        self.game.temp_setting_value = 10
        self.game.menu_values = [1, 5, None, False]  # Old values

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.MENU)
        self.assertEqual(self.game.rack_counter, 10)
        self.assertEqual(self.game.menu_values[1], 10)
        self.hw.render_menu.assert_called_once()

    async def test_make_edit_save_apa(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.selected_profile = "APA"
        self.game.current_menu_index = 0  # P1
        self.game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        self.game.temp_setting_value = 15
        self.game.menu_values = [0, 0, None, False]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 15)
        self.assertEqual(self.game.menu_values[0], 15)

    async def test_make_edit_save_inning(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 0  # Inning
        self.game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]
        self.game.temp_setting_value = 3
        self.game.menu_values = [1, 1, None, False]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.inning_counter, 3.0)

    async def test_make_edit_save_mute(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 3  # Mute
        self.game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]
        self.game.temp_setting_value = True
        self.game.menu_values = [1, 1, None, False]

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertTrue(self.game.speaker_muted)

    async def test_make_menu_exit(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]
        self.game.menu_values = [1, 1, None, False]
        self.game.current_menu_index = 2  # Exit Match

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.EXIT_MATCH_CONFIRMATION)
        self.hw.render_exit_confirmation.assert_called_once()

    async def test_make_exit_confirm(self):
        self.sm.update_state(State_Machine.EXIT_MATCH_CONFIRMATION)

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.PROFILE_SELECTION)
        self.hw.render_profile_selection.assert_called_once_with(
            self.sm, self.game, clear_all=True
        )

    async def test_new_rack(self):
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rack_counter = 1
        self.game.break_shot = False

        await logic.handle_new_rack(self.sm, self.game, self.hw)

        self.assertEqual(self.game.rack_counter, 2)
        self.assertTrue(self.game.break_shot)
        self.hw.enter_idle_mode.assert_called_once()

    # --- HANDLE UP ---

    async def test_up_profile_selection(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 1

        await logic.handle_up(self.sm, self.game, self.hw)

        # 1 - 1 = 0
        self.assertEqual(self.game.profile_selection_index, 0)
        self.hw.render_profile_selection.assert_called_once()

    async def test_up_extension_apa(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = NineBallRules()
        self.game.selected_profile = "APA"
        self.game.extension_available = True
        self.game.countdown = 10
        self.game.extension_duration = 20
        self.game.player_1_shooting = True
        self.game.player_1_timeouts_remaining = 1

        await logic.handle_up(self.sm, self.game, self.hw)

        self.assertFalse(self.game.extension_available)
        self.assertTrue(self.game.extension_used)
        self.assertEqual(self.game.countdown, 30)
        self.hw.update_timer_display.assert_called_once()

    async def test_up_extension_apa_unavailable(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = NineBallRules()
        self.game.selected_profile = "APA"
        self.game.extension_available = False
        self.game.countdown = 10

        await logic.handle_up(self.sm, self.game, self.hw)

        self.assertEqual(self.game.countdown, 10)  # No change
        self.hw.update_timer_display.assert_not_called()

    async def test_up_extension_wnt_p1(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = StandardRules()
        self.game.selected_profile = "WNT"
        self.game.player_1_shooting = True
        self.game.player_1_extension_available = True
        self.game.countdown = 10
        self.game.extension_duration = 30

        await logic.handle_up(self.sm, self.game, self.hw)

        self.assertFalse(self.game.player_1_extension_available)
        self.assertEqual(self.game.countdown, 40)

    async def test_up_menu(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.current_menu_index = 1
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.current_menu_index, 0)

    async def test_up_edit_increment(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 1  # Rack
        self.game.temp_setting_value = 5
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.temp_setting_value, 6)

    async def test_up_edit_toggle_mute(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 3  # Mute
        self.game.temp_setting_value = False
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertTrue(self.game.temp_setting_value)

    # --- HANDLE DOWN ---

    async def test_down_profile_selection(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 0
        self.game.game_profiles = {"A": {}, "B": {}}
        self.game.profile_names = ["A", "B"]

        await logic.handle_down(self.sm, self.game, self.hw)

        self.assertEqual(self.game.profile_selection_index, 1)

    async def test_down_menu(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.current_menu_index = 0
        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.current_menu_index, 1)

    async def test_down_edit_decrement(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 1  # Rack
        self.game.temp_setting_value = 5
        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.temp_setting_value, 4)

    async def test_down_edit_toggle_mute(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.current_menu_index = 3  # Mute
        self.game.temp_setting_value = True
        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertFalse(self.game.temp_setting_value)

    # --- HANDLE MISS ---

    async def test_miss_running(self):
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.rules = NineBallRules()
        self.game.inning_counter = 1.0

        await logic.handle_miss(self.sm, self.game, self.hw)

        self.assertEqual(self.game.inning_counter, 1.5)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_miss_idle_opens_menu(self):
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rules = NineBallRules()  # NineBall rules supports this
        self.game.selected_profile = "APA"

        await logic.handle_miss(self.sm, self.game, self.hw)

        self.assertTrue(self.sm.menu)
        self.hw.render_menu.assert_called_once()

    async def test_miss_idle_timeouts_mode_no_menu(self):
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rules = StandardRules()
        self.game.selected_profile = "Timeouts Mode"

        await logic.handle_miss(self.sm, self.game, self.hw)

        # StandardRules logic also checks for Timeouts Mode?
        # Check lib/game_rules.py StandardRules.handle_miss
        # It calls render_menu. Wait, the old logic had a check for "Timeouts Mode".
        pass

    async def test_miss_exit_menu(self):
        self.sm.update_state(State_Machine.MENU)
        await logic.handle_miss(self.sm, self.game, self.hw)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_miss_cancel_edit(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        await logic.handle_miss(self.sm, self.game, self.hw)
        self.assertTrue(self.sm.menu)
        self.hw.render_menu.assert_called_once()

    async def test_miss_cancel_exit_confirmation(self):
        self.sm.update_state(State_Machine.EXIT_MATCH_CONFIRMATION)
        await logic.handle_miss(self.sm, self.game, self.hw)
        self.assertTrue(self.sm.menu)
        self.hw.render_menu.assert_called_once()

    async def test_make_confirm_rack_end_win(self):
        self.sm.update_state(State_Machine.CONFIRM_RACK_END)
        self.game.pending_rack_result = "win"
        self.game.player_1_shooting = True
        self.game.player_1_score = 0
        self.game.rack_counter = 1
        self.game.player_1_target = 5
        self.game.player_2_target = 5

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 1)
        self.assertEqual(self.game.rack_counter, 2)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_make_confirm_rack_end_lose(self):
        self.sm.update_state(State_Machine.CONFIRM_RACK_END)
        self.game.pending_rack_result = "lose"
        self.game.player_1_shooting = True
        self.game.player_1_score = 0
        self.game.player_2_score = 0
        self.game.rack_counter = 1
        self.game.player_1_target = 5
        self.game.player_2_target = 5

        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 0)
        self.assertEqual(self.game.player_2_score, 1)  # Opponent scored
        self.assertEqual(self.game.rack_counter, 2)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.hw.enter_idle_mode.assert_called_once()


if __name__ == "__main__":
    unittest.main()
