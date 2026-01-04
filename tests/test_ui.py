import unittest
from unittest.mock import MagicMock

from lib import display, ui
from lib.models import Game_Stats, State_Machine


class TestDisplayUnits(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.oled = MagicMock()
        # Mock some oled constants if they exist
        self.oled.white = 1
        self.oled.black = 0

    def test_render_scoreline_apa_alignment(self):
        self.game.selected_profile = "APA"
        self.game.player_1_score = 10
        self.game.player_1_target = 38
        self.game.player_2_score = 5
        self.game.player_2_target = 14
        self.game.inning_counter = 1.0  # P1 turn

        ui.render_scoreline(self.oled, self.sm, self.game, send_payload=True)

        # Standard P1 score 10 (region 0, 14). Right align -> 1 + 14 - 16 = -1.
        self.oled.text_scaled.assert_any_call("10", -1, 56, 1)
        # Standard P1 sep (region 14, 8). Center align -> 15 + (8-8)//2 = 15.
        self.oled.text_scaled.assert_any_call("/", 15, 56, 1)
        # Standard P1 target 38 (region 22, 14). Left align -> 23.
        self.oled.text_scaled.assert_any_call("38", 23, 56, 1)

        # Standard P2 score 5 (region 91, 14). Right align -> 91 + 14 - 8 = 97.
        self.oled.text_scaled.assert_any_call("5", 97, 56, 1)
        # Standard P2 sep (region 105, 8). Center -> 105.
        self.oled.text_scaled.assert_any_call("/", 105, 56, 1)
        # Standard P2 target 14 (region 113, 14). Left align -> 113.
        self.oled.text_scaled.assert_any_call("14", 113, 56, 1)

    def test_render_scoreline_ultimate_pool_alignment(self):
        self.game.selected_profile = "Ultimate Pool"
        self.game.player_1_score = 10
        self.game.player_1_target = 38
        self.game.player_2_score = 5
        self.game.player_2_target = 14

        ui.render_scoreline(self.oled, self.sm, self.game)

        # UP P1 score 10 (region 0, 8). Right align -> 8-16 = -8.
        self.oled.text_scaled.assert_any_call("10", -8, 56, 1)
        # UP P1 sep (region 8, 8). Center -> 8.
        self.oled.text_scaled.assert_any_call("/", 8, 56, 1)
        # UP P1 target 38 (region 16, 8). Left -> 16.
        self.oled.text_scaled.assert_any_call("38", 16, 56, 1)

        # UP P2 score 5 (region 104, 8). Right align -> 104 + 8 - 8 = 104.
        self.oled.text_scaled.assert_any_call("5", 104, 56, 1)
        # UP P2 sep (region 112, 8). Center -> 112.
        self.oled.text_scaled.assert_any_call("/", 112, 56, 1)
        # UP P2 target 14 (region 120, 8). Left align -> 120.
        self.oled.text_scaled.assert_any_call("14", 120, 56, 1)

    def test_render_scoreline_p2_single_digit_target_shift(self):
        self.game.selected_profile = "APA"
        self.game.player_1_score = 0
        self.game.player_1_target = 0
        self.game.player_2_score = 10
        self.game.player_2_target = 5  # Single digit

        ui.render_scoreline(self.oled, self.sm, self.game)

        # P1 score 0 (region 0, 14). Left align -> 0.
        self.oled.text_scaled.assert_any_call("0", 0, 56, 1)
        # P1 sep (14). shift=6. x = 14-6 = 8.
        self.oled.text_scaled.assert_any_call("/", 8, 56, 1)
        # P1 target 0 (22). shift=6. x = 22-6 = 16.
        self.oled.text_scaled.assert_any_call("0", 16, 56, 1)

        # P2 score 10 (region 91, 14). Right align -> 91 + 14 - 16 = 89.
        self.oled.text_scaled.assert_any_call("10", 89, 56, 1)
        # P2 sep (105).
        self.oled.text_scaled.assert_any_call("/", 105, 56, 1)
        # P2 target 5 (region 113, 14). Left align -> 113.
        self.oled.text_scaled.assert_any_call("5", 113, 56, 1)

    def test_render_scoreline_ultimate_pool_indicators(self):
        self.game.selected_profile = "Ultimate Pool"
        self.game.match_countdown = 1800  # Not shifted
        self.game.player_1_score = 2
        self.game.player_1_target = 5
        self.game.player_2_score = 3
        self.game.player_2_target = 5
        self.game.inning_counter = 1.0  # P1 turn

        ui.render_scoreline(self.oled, self.sm, self.game)

        # Verify clearing of standard regions
        self.oled.rect.assert_any_call(33, 56, 8, 8, self.oled.black, True)
        self.oled.rect.assert_any_call(87, 56, 8, 8, self.oled.black, True)

        # Verify shifted regions were NOT cleared (to avoid collision)
        calls = self.oled.rect.call_args_list
        self.assertFalse(any(c.args == (39, 56, 8, 8, 0, True) for c in calls))
        self.assertFalse(any(c.args == (81, 56, 8, 8, 0, True) for c in calls))

        # Verify P1 indicator (filled) at fixed x=33 (from region 8x8)
        self.oled.rect.assert_any_call(33, 56, 8, 8, self.oled.white, True)

    def test_render_scoreline_ultimate_pool_indicators_shifted(self):
        self.game.selected_profile = "Ultimate Pool"
        self.game.match_countdown = 500  # Shifted
        self.game.player_1_score = 2
        self.game.player_1_target = 5
        self.game.player_2_score = 3
        self.game.player_2_target = 5
        self.game.inning_counter = 1.0  # P1 turn

        ui.render_scoreline(self.oled, self.sm, self.game)

        # Verify clearing of BOTH sets of potential regions
        self.oled.rect.assert_any_call(33, 56, 8, 8, self.oled.black, True)
        self.oled.rect.assert_any_call(87, 56, 8, 8, self.oled.black, True)
        self.oled.rect.assert_any_call(39, 56, 8, 8, self.oled.black, True)
        self.oled.rect.assert_any_call(81, 56, 8, 8, self.oled.black, True)

        # Verify P1 indicator (filled) at shifted x=39
        self.oled.rect.assert_any_call(39, 56, 8, 8, self.oled.white, True)

    def test_display_timeouts_logic(self):
        # 2 timeouts
        self.game.player_1_timeouts_remaining = 2
        self.game.player_2_timeouts_remaining = 2
        ui.display_timeouts(self.oled, self.sm, self.game)
        # Should draw 4 rects
        # P1 region starts at 40.
        self.oled.rect.assert_any_call(40, 58, 4, 4, self.oled.white, True)
        self.oled.rect.assert_any_call(48, 58, 4, 4, self.oled.white, True)
        # P2 region starts at 76.
        self.oled.rect.assert_any_call(76, 58, 4, 4, self.oled.white, True)
        self.oled.rect.assert_any_call(84, 58, 4, 4, self.oled.white, True)

        self.oled.reset_mock()
        # 1 timeout
        self.game.player_1_timeouts_remaining = 1
        self.game.player_2_timeouts_remaining = 1
        ui.display_timeouts(self.oled, self.sm, self.game)
        # P1: 40+4 = 44. P2: 76+4 = 80.
        self.oled.rect.assert_any_call(44, 58, 4, 4, self.oled.white, True)
        self.oled.rect.assert_any_call(80, 58, 4, 4, self.oled.white, True)

    async def test_render_message_centering(self):
        message = "Test\nMessage"
        await ui.render_message(self.sm, self.game, self.oled, message, font_size=1)

        # line 1: Test. x = 0 + (128 - 32)//2 = 48. y = 16.
        # line 2: Message. text_w=56. x = 0 + (128 - 56)//2 = 36. y = 16+12=28.
        self.oled.text_scaled.assert_any_call("Test", 48, 16, 1)
        self.oled.text_scaled.assert_any_call("Message", 36, 28, 1)

    def test_render_scoreline_p2_turn(self):
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.5  # P2 turn
        ui.render_scoreline(self.oled, self.sm, self.game)
        # Verify P2 indicator. Region shooter_indicator_2 (65, 56, 8, 8). Fill=True.
        self.oled.rect.assert_any_call(65, 56, 8, 8, self.oled.white, True)

    async def test_render_screens_async(self):
        # Cover render_skill_level_selection
        self.game.temp_setting_value = 5
        await ui.render_skill_level_selection(self.sm, self.game, self.oled, 1)
        self.oled.text_scaled.assert_any_call("5", 52, 40, 3)

        # Cover render_game_type_selection (8-ball)
        self.game.temp_setting_value = 0
        await ui.render_game_type_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("8-Ball", 16, 30, 2)

        # Cover render_game_type_selection (9-ball)
        self.game.temp_setting_value = 1
        await ui.render_game_type_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("9-Ball", 16, 30, 2)

        # Cover enter_shot_clock
        await ui.enter_shot_clock(self.sm, self.game, self.oled)
        self.assertEqual(self.sm.state, State_Machine.COUNTDOWN_IN_PROGRESS)

    async def test_render_exit_confirmation(self):
        await ui.render_exit_confirmation(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Are you sure?", 12, 24, 1)

    def test_format_match_timer(self):
        self.assertEqual(display.format_match_timer(1800), "30:00")
        self.assertEqual(display.format_match_timer(600), "10:00")
        self.assertEqual(display.format_match_timer(577), "9:37")
        self.assertEqual(display.format_match_timer(0), "0:00")

    def test_render_match_timer_optimization(self):
        self.game.match_countdown = 1799  # 29:59
        self.game.prev_match_countdown = 1800  # 30:00

        # Should clear and redraw all 4 digits
        ui.render_match_timer(self.oled, self.sm, self.game)
        self.assertEqual(self.oled.rect.call_count, 4)

        self.oled.reset_mock()
        self.game.prev_match_countdown = 1799
        self.game.match_countdown = 1798  # 29:58
        # Only last digit changes
        ui.render_match_timer(self.oled, self.sm, self.game)
        self.assertEqual(self.oled.rect.call_count, 1)
        # Digit 4 region (77).
        self.oled.text_scaled.assert_called_once_with("8", 77, 56, 1)

    def test_render_match_timer_leading_zero_suppression(self):
        self.game.match_countdown = 540  # 09:00
        self.game.prev_match_countdown = None  # Force all

        ui.render_match_timer(self.oled, self.sm, self.game, force_all=True)
        # Should NOT call text_scaled for digit 1 (index 0) at x=39
        # (which is digit 1s region)
        x_positions = [call.args[1] for call in self.oled.text_scaled.call_args_list]
        self.assertNotIn(43, x_positions)
        # Should call for others
        self.assertIn(48, x_positions)  # 9
        self.assertIn(56, x_positions)  # : (colon is hardcoded 56 in shifted)
        self.assertIn(63, x_positions)  # 0
        self.assertIn(72, x_positions)  # 0

    async def test_render_profile_selection_ultimate_pool(self):
        self.game.profile_selection_index = 3  # Assuming Ultimate Pool index
        self.game.profile_names = ["APA", "BCA", "Timeouts Mode", "Ultimate Pool", "WNT"]
        await ui.render_profile_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Ultimate", 0, 30, 2)
        self.oled.text_scaled.assert_any_call("Pool", 32, 48, 2)

    async def test_render_wnt_target_selection(self):
        self.game.temp_setting_value = 11
        await ui.render_wnt_target_selection(self.sm, self.game, self.oled)
        # Verify shift logic: target > 9 -> shift = 12. 50 - 12 = 38
        self.oled.text_scaled.assert_any_call("11", 40, 30, 3)

    def test_render_match_timer_clears_digit_1_below_10_mins(self):
        # 1. Start at 10:00 (Digit 1 is '1')
        self.game.match_countdown = 600
        self.game.prev_match_countdown = 601
        ui.render_match_timer(self.oled, self.sm, self.game)

        # 2. Transition to 09:59
        self.oled.reset_mock()
        self.game.match_countdown = 599  # 09:59
        ui.render_match_timer(self.oled, self.sm, self.game)

        # Verify full area was cleared. "match_clock_full" region is (41, 56, 46, 8)
        self.oled.rect.assert_any_call(41, 56, 46, 8, self.oled.black, True)

        # Verify NO digit was drawn at x=43
        x_positions = [call.args[1] for call in self.oled.text_scaled.call_args_list]
        self.assertNotIn(43, x_positions)

    async def test_ultimate_pool_menu_exit_timer_redraw(self):
        """Regression test for bug where exiting menu didn't redraw match timer."""
        from unittest.mock import patch

        self.game.selected_profile = "Ultimate Pool"
        self.sm.update_state(State_Machine.MENU)

        # Mock render_ultimate_pool_shooter_indicators where it is DEFINED,
        # so that when ui_gameplay calls render_scoreline (from components),
        # it uses our mock.
        with patch(
            "lib.ui_components.render_ultimate_pool_shooter_indicators"
        ) as mock_render:
            await ui.enter_idle_mode(self.sm, self.game, self.oled)

            # verify that state changed
            self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)

            # Verify render_ultimate_pool_shooter_indicators was called
            # with force_match_timer=True It's called inside
            # render_scoreline which is called by enter_idle_mode.
            mock_render.assert_called_with(self.oled, self.sm, self.game, True)


if __name__ == "__main__":
    unittest.main()
