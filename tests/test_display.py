import unittest
from unittest.mock import MagicMock

from lib import display
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

        display.render_scoreline(self.oled, self.sm, self.game, send_payload=True)

        # P1 score 10 starts at x=0
        self.oled.text_scaled.assert_any_call("10", 0, 57, 1)

    def test_display_timeouts_logic(self):
        # 2 timeouts
        self.game.player_1_timeouts_remaining = 2
        self.game.player_2_timeouts_remaining = 2
        display.display_timeouts(self.oled, self.sm, self.game)
        # Should draw 4 rects
        self.assertEqual(self.oled.rect.call_count, 4)

        self.oled.reset_mock()
        # 1 timeout
        self.game.player_1_timeouts_remaining = 1
        self.game.player_2_timeouts_remaining = 1
        display.display_timeouts(self.oled, self.sm, self.game)
        self.assertEqual(self.oled.rect.call_count, 2)

    async def test_render_message_centering(self):
        message = "Test\nMessage"
        await display.render_message(self.sm, self.game, self.oled, message, font_size=1)

        self.oled.text_scaled.assert_any_call("Test", 48, 20, 1)
        self.oled.text_scaled.assert_any_call("Message", 36, 32, 1)

    def test_render_scoreline_p2_turn(self):
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.5  # P2 turn
        display.render_scoreline(self.oled, self.sm, self.game)
        # Verify P2 indicator (rect at 66, 57 is True)
        self.oled.rect.assert_any_call(66, 57, 7, 7, self.oled.white, True)

    async def test_render_screens_async(self):
        # Cover render_skill_level_selection
        self.game.temp_setting_value = 5
        await display.render_skill_level_selection(self.sm, self.game, self.oled, 1)
        self.oled.text_scaled.assert_any_call("5", 50, 40, 3)

        # Cover render_game_type_selection (8-ball)
        self.game.temp_setting_value = 0
        await display.render_game_type_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("8-Ball", 15, 30, 2)

        # Cover render_game_type_selection (9-ball)
        self.game.temp_setting_value = 1
        await display.render_game_type_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("9-Ball", 15, 30, 2)

        # Cover enter_shot_clock
        await display.enter_shot_clock(self.sm, self.game, self.oled)
        self.assertEqual(self.sm.state, State_Machine.COUNTDOWN_IN_PROGRESS)

    async def test_render_exit_confirmation(self):
        await display.render_exit_confirmation(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Are you sure?", 12, 25, 1)

    def test_render_scoreline_standard(self):
        # Timeouts Mode uses the standard Rack/Inning rendering in current logic?
        # Wait, render_scoreline:
        # if game.timeouts_only: display "Timeouts Mode"
        # else: ...

        self.game.timeouts_only = False
        self.game.selected_profile = "OTHER"  # Trigger else branch
        self.game.rack_counter = 3
        self.game.inning_counter = 2.0
        display.render_scoreline(self.oled, self.sm, self.game)
        self.oled.text_scaled.assert_any_call("Rack:3", 0, 57, 1)
        self.oled.text_scaled.assert_any_call("Inning:2", 57, 57, 1)

    def test_format_match_timer(self):
        self.assertEqual(display.format_match_timer(1800), "30:00")
        self.assertEqual(display.format_match_timer(600), "10:00")
        self.assertEqual(display.format_match_timer(577), "9:37")
        self.assertEqual(display.format_match_timer(0), "0:00")

    def test_render_match_timer_optimization(self):
        self.game.match_countdown = 1799  # 29:59
        self.game.prev_match_countdown = 1800  # 30:00

        # Should clear and redraw all 4 digits
        display.render_match_timer(self.oled, self.sm, self.game)
        self.assertEqual(self.oled.rect.call_count, 4)

        self.oled.reset_mock()
        self.game.prev_match_countdown = 1799
        self.game.match_countdown = 1798  # 29:58
        # Only last digit changes
        display.render_match_timer(self.oled, self.sm, self.game)
        self.assertEqual(self.oled.rect.call_count, 1)
        self.oled.text_scaled.assert_called_once_with("8", 77, 57, 1)

    def test_render_match_timer_leading_zero_suppression(self):
        self.game.match_countdown = 540  # 09:00
        self.game.prev_match_countdown = None  # Force all

        display.render_match_timer(self.oled, self.sm, self.game, force_all=True)
        # Should NOT call text_scaled for digit 1 (index 0) at x=39
        # call_args_list contains all calls. Check if any call has x=39
        x_positions = [call.args[1] for call in self.oled.text_scaled.call_args_list]
        self.assertNotIn(39, x_positions)
        # Should call for others (shifted positions)
        self.assertIn(48, x_positions)  # 9
        self.assertIn(56, x_positions)  # :
        self.assertIn(64, x_positions)  # 0
        self.assertIn(72, x_positions)  # 0

    async def test_render_profile_selection_ultimate_pool(self):
        self.game.profile_selection_index = 3  # Assuming Ultimate Pool index
        self.game.profile_names = ["APA", "BCA", "Timeouts Mode", "Ultimate Pool", "WNT"]
        await display.render_profile_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Ultimate", 0, 30, 2)
        self.oled.text_scaled.assert_any_call("Pool", 30, 48, 2)

    async def test_render_wnt_target_selection(self):
        self.game.temp_setting_value = 11
        await display.render_wnt_target_selection(self.sm, self.game, self.oled)
        # Verify shift logic: target > 9 -> shift = 12. 50 - 12 = 38
        self.oled.text_scaled.assert_any_call("11", 38, 30, 3)

    def test_render_match_timer_clears_digit_1_below_10_mins(self):
        # 1. Start at 10:00 (Digit 1 is '1')
        self.game.match_countdown = 600
        self.game.prev_match_countdown = 601
        display.render_match_timer(self.oled, self.sm, self.game)

        # 2. Transition to 09:59
        self.oled.reset_mock()
        self.game.match_countdown = 599  # 09:59
        display.render_match_timer(self.oled, self.sm, self.game)

        # Verify full area was cleared on threshold crossing
        # DISPLAY_REGIONS["match_clock_full"] is (39, 57, 46, 8)
        self.oled.rect.assert_any_call(39, 57, 46, 8, self.oled.black, True)

        # Verify NO digit was drawn at x=39 (leading zero suppression)
        x_positions = [call.args[1] for call in self.oled.text_scaled.call_args_list]
        self.assertNotIn(39, x_positions)


if __name__ == "__main__":
    unittest.main()
