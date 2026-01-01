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
from lib import audio, display
from lib.models import Game_Stats, State_Machine


class TestDisplay(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.oled = MagicMock()

    # Low Level
    def test_display_text(self):
        display.display_text(self.oled, self.sm, "Test", 0, 0, 1)
        self.oled.text_scaled.assert_called_with("Test", 0, 0, 1)
        self.oled.show.assert_called_once()

    def test_display_text_timeouts_mode(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        display.display_text(self.oled, self.sm, "Timeouts Mode", 10, 10, 1)

        # Should override x=0, size=2
        self.oled.text_scaled.assert_any_call("Timeouts Mode", 0, 10, 2)
        # Should draw "Mode"
        self.oled.text_scaled.assert_any_call("Mode", 32, 48, 2)

    def test_display_shape(self):
        display.display_shape(self.oled, "rect", 0, 0, 10, 10)
        self.oled.rect.assert_called_once()

        display.display_shape(self.oled, "line", 0, 0, 10, 10)
        self.oled.line.assert_called_once()

    def test_display_shape_rect_no_fill(self):
        # Reset mock to clear previous calls
        self.oled.line.reset_mock()
        display.display_shape(self.oled, "rect", 10, 20, 30, 40, fill=False)
        # Should call line 4 times
        self.assertEqual(self.oled.line.call_count, 4)
        # Check specific calls
        # Top line: (x, y, x+w-1, y) -> (10, 20, 39, 20)
        self.oled.line.assert_any_call(10, 20, 39, 20, self.oled.white)
        # Bottom line: (x, y+h-1, x+w-1, y+h-1) -> (10, 59, 39, 59)
        self.oled.line.assert_any_call(10, 59, 39, 59, self.oled.white)
        # Left line: (x, y, x, y+h-1) -> (10, 20, 10, 59)
        self.oled.line.assert_any_call(10, 20, 10, 59, self.oled.white)
        # Right line: (x+w-1, y, x+w-1, y+h-1) -> (39, 20, 39, 59)
        self.oled.line.assert_any_call(39, 20, 39, 59, self.oled.white)

    def test_display_clear(self):
        display.display_clear(self.oled, "everything")
        self.oled.rect.assert_called()  # Should draw black rect

    def test_display_clear_invalid(self):
        display.display_clear(self.oled, "invalid_region")
        # Should not call rect
        self.oled.rect.assert_not_called()

    def test_display_shape_invalid(self):
        display.display_shape(self.oled, "circle", 0, 0, 10, 10)
        self.oled.rect.assert_not_called()
        self.oled.line.assert_not_called()

    # High Level

    async def test_enter_idle_mode_timeouts(self):
        self.game.timeouts_only = True
        await display.enter_idle_mode(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Timeouts Mode", 12, 57, 1)

        async def test_enter_idle_mode_game(self):
            self.game.timeouts_only = False

            self.game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]

            await display.enter_idle_mode(self.sm, self.game, self.oled)

            self.oled.text_scaled.assert_any_call("1 --- Score --- ", 0, 57, 1)

            self.oled.text_scaled.assert_any_call("1", 104, 57, 1)

        async def test_enter_idle_mode_apa(self):
            self.game.selected_profile = "APA"

            self.game.timeouts_only = False

            self.game.menu_items = ["P1", "P2", "Exit Match", "Mute"]

            self.game.player_1_score = 0

            self.game.player_2_score = 0

            await display.enter_idle_mode(self.sm, self.game, self.oled)

            self.oled.text_scaled.assert_any_call("0 --- Score --- ", 0, 57, 1)

            self.oled.text_scaled.assert_any_call("0", 104, 57, 1)

        async def test_enter_idle_mode_double_digit_shift(self):
            self.game.selected_profile = "APA"

            self.game.player_1_score = 5

            self.game.player_2_score = 10

            await display.enter_idle_mode(self.sm, self.game, self.oled)

            self.oled.text_scaled.assert_any_call("5 --- Score --- ", 0, 57, 1)

            self.oled.text_scaled.assert_any_call("10", 102, 57, 1)

    async def test_enter_idle_mode_game_no_break(self):
        self.game.timeouts_only = False
        self.game.break_shot = False
        self.game.profile_based_countdown = 20
        await display.enter_idle_mode(self.sm, self.game, self.oled)
        self.assertEqual(self.game.countdown, 20)

    async def test_enter_shot_clock(self):
        self.game.inning_counter = 1.0
        await display.enter_shot_clock(self.sm, self.game, self.oled)
        self.assertTrue(self.game.player_1_shooting)

    async def test_render_skill_level_selection(self):
        self.game.temp_setting_value = 5
        await display.render_skill_level_selection(self.sm, self.game, self.oled, 1)
        self.oled.text_scaled.assert_any_call("Player 1", 20, 10, 1)
        self.oled.text_scaled.assert_any_call("Skill Level:", 15, 25, 1)
        self.oled.text_scaled.assert_any_call("5", 50, 40, 3)

    async def test_render_victory(self):
        await display.render_victory(self.sm, self.game, self.oled, 2)
        self.oled.text_scaled.assert_any_call("VICTORY!", 10, 10, 2)
        self.oled.text_scaled.assert_any_call("Player 2", 0, 35, 2)

    async def test_render_profile_selection(self):
        self.game.game_profiles = {"A": {}}
        self.game.profile_names = ["A"]
        self.game.profile_selection_index = 0
        await display.render_profile_selection(self.sm, self.game, self.oled)
        self.oled.text_scaled.assert_any_call("Select Game:", 15, 10, 1)
        self.oled.text_scaled.assert_any_call("A", 25, 30, 3)

    async def test_render_menu_normal(self):
        self.sm.update_state(State_Machine.MENU)
        self.game.menu_items = ["A", "B", "C"]

        await display.render_menu(self.sm, self.game, self.oled)

        # Should draw header lines
        self.assertEqual(self.oled.line.call_count, 2)
        # Should draw cursor
        self.oled.rect.assert_called()

    async def test_render_menu_editing(self):
        self.sm.update_state(State_Machine.EDITING_VALUE)
        self.game.menu_items = ["A", "B", "C"]
        self.game.current_menu_index = 1
        self.game.temp_setting_value = 99

        await display.render_menu(self.sm, self.game, self.oled)
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
