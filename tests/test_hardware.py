import sys
import unittest
from unittest.mock import MagicMock, patch

# MOCKS
# We must mock machine and framebuf BEFORE importing display/audio
sys.modules["machine"] = MagicMock()
sys.modules["framebuf"] = MagicMock()

# Mock FrameBuffer class specifically
sys.modules["framebuf"].FrameBuffer = MagicMock  # type: ignore

# Import libraries under test
from lib import audio, display, ui
from lib.models import Game_Stats, State_Machine


class TestDisplay(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.oled = MagicMock()

    # Low Level
    def test_display_clear(self):
        display.display_clear(self.oled, "everything")
        self.oled.rect.assert_called()  # Should draw black rect

    # High Level

    async def test_enter_idle_mode_timeouts(self):
        self.game.timeouts_only = True
        await ui.enter_idle_mode(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Timeouts Mode", 12, 56, 1)

    async def test_enter_idle_mode_game(self):
        self.game.timeouts_only = False
        self.game.selected_profile = None  # Standard mode
        self.game.countdown = 0

        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        # Standard scoreline is deprecated, so only shot clock "00" is drawn.
        # Digit 1: (0, 0, 64, 56). Center "0" (size 8, 64px). x=0, y=-4.
        self.oled.text_scaled.assert_any_call("0", 0, -4, 8)
        # Digit 2: (64, 0, 64, 56). Center "0". x=64, y=-4.
        self.oled.text_scaled.assert_any_call("0", 64, -4, 8)

    async def test_enter_idle_mode_apa(self):
        self.game.selected_profile = "APA"
        self.game.timeouts_only = False
        self.game.player_1_score = 0
        self.game.player_2_score = 0

        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        # p1_score (0, 56, 14, 8). Right. x = 6.
        self.oled.text_scaled.assert_any_call("0", 6, 56, 1)
        # p2_score (96, 56, 14, 8). Right. x = 102.
        self.oled.text_scaled.assert_any_call("0", 102, 56, 1)

    async def test_enter_idle_mode_double_digit_shift(self):
        self.game.selected_profile = "APA"
        self.game.player_1_score = 5
        self.game.player_2_score = 10

        await ui.enter_idle_mode(self.sm, self.game, self.oled)

        self.oled.text_scaled.assert_any_call("5", 6, 56, 1)
        self.oled.text_scaled.assert_any_call("10", 94, 56, 1)

    async def test_enter_idle_mode_game_no_break(self):
        self.game.timeouts_only = False
        self.game.break_shot = False
        self.game.profile_based_countdown = 20
        await ui.enter_idle_mode(self.sm, self.game, self.oled)
        self.assertEqual(self.game.countdown, 20)

    async def test_enter_shot_clock(self):
        self.game.inning_counter = 1.0
        await ui.enter_shot_clock(self.sm, self.game, self.oled)
        self.assertTrue(self.game.player_1_shooting)

    async def test_render_skill_level_selection(self):
        self.game.temp_setting_value = 5
        await ui.render_skill_level_selection(self.sm, self.game, self.oled, 1)
        self.oled.text_scaled.assert_any_call("Player 1", 32, 10, 1)
        self.oled.text_scaled.assert_any_call("Skill Level:", 16, 25, 1)
        self.oled.text_scaled.assert_any_call("5", 52, 40, 3)

    async def test_render_victory(self):
        await ui.render_victory(self.sm, self.game, self.oled, 2)
        self.oled.text_scaled.assert_any_call("VICTORY!", 0, 10, 2)
        self.oled.text_scaled.assert_any_call("Player 2", 0, 35, 2)

    async def test_render_profile_selection(self):
        self.game.game_profiles = {"A": {}}
        self.game.profile_names = ["A"]
        self.game.profile_selection_index = 0
        await ui.render_profile_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Select Game:", 16, 6, 1)
        self.oled.text_scaled.assert_any_call("A", 52, 30, 3)

    async def test_render_menu_normal(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.menu_items = ["A", "B", "C"]

        await ui.render_menu(self.sm, self.game, self.oled)

        # Should draw header lines (now rects) + cursor (rect) + clear (rect) = 4 rects
        # PLUS auto-clears for every text and rect drawn.
        # Everything + 2 headers + 2 separators + 3 lines + cursor = 12
        self.assertEqual(self.oled.rect.call_count, 12)
        self.assertEqual(self.oled.line.call_count, 0)

    async def test_render_menu_editing(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.menu_items = ["A", "B", "C"]
        self.game.current_menu_index = 1
        self.game.temp_setting_value = 99

        await ui.render_menu(self.sm, self.game, self.oled)
        self.assertTrue(self.oled.text_scaled.call_count >= 5)


class TestAudio(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data=b"HEADER" + b"\x00" * 1024,
    )
    def test_shot_clock_beep(self, mock_file):
        # Mock I2S
        with patch("lib.audio.I2S") as MockI2S, patch("lib.audio.Pin"):
            file_handle = mock_file.return_value
            file_handle.readinto.side_effect = [1024, 0]
            audio.shot_clock_beep()
            MockI2S.assert_called_once()
            mock_file.assert_called_with("beep.wav", "rb")
            file_handle.seek.assert_called_with(80)
            file_handle.readinto.assert_called()

    def test_shot_clock_beep_error_handling(self):
        # Simulate file not found
        with (
            patch("builtins.open", side_effect=OSError("File not found")),
            patch("lib.audio.I2S"),
        ):
            # Should not raise exception (suppressed)
            audio.shot_clock_beep()


if __name__ == "__main__":
    unittest.main()
