import unittest
from unittest.mock import MagicMock, mock_open, patch

from lib.models import Game_Stats, State_Machine


class TestModels(unittest.TestCase):
    def test_state_machine_defaults(self):
        sm = State_Machine()
        self.assertEqual(sm.state, State_Machine.PROFILE_SELECTION)
        self.assertFalse(sm.game_on)

    def test_state_machine_transitions(self):
        sm = State_Machine()
        sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.assertTrue(sm.shot_clock_idle)
        self.assertFalse(sm.profile_selection)

        sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.assertTrue(sm.countdown_in_progress)

        sm.update_state(State_Machine.COUNTDOWN_COMPLETE)
        self.assertTrue(sm.countdown_complete)

        sm.update_state(State_Machine.MENU)
        self.assertTrue(sm.menu)

        sm.update_state(State_Machine.EDITING_VALUE)
        self.assertTrue(sm.editing_value)

        sm.update_state(State_Machine.APA_SKILL_LEVEL_P1)
        self.assertTrue(sm.apa_skill_level_p1)

        sm.update_state(State_Machine.VICTORY)
        self.assertTrue(sm.victory)

    def test_game_stats_defaults(self):
        game = Game_Stats()
        self.assertEqual(game.profile_based_countdown, 0)
        self.assertEqual(game.match_countdown, 1800)
        self.assertEqual(game.inning_counter, 1.0)
        self.assertEqual(game.game_profiles["APA"]["timer_duration"], 20)
        self.assertTrue(game.extension_available)
        self.assertEqual(game.player_1_skill_level, 0)
        self.assertEqual(game.player_1_target, 0)
        self.assertEqual(game.match_type, "9-Ball")

    def test_ultimate_pool_match_clock_initialization(self):
        """Ensure Ultimate Pool match clock defaults to 1800 seconds (30 mins)."""
        game = Game_Stats()
        game.selected_profile = "Ultimate Pool"
        self.assertEqual(game.match_countdown, 1800)

    def test_game_stats_menu_update(self):
        # Mock dependencies
        oled = "OLED_MOCK"
        sm = "SM_MOCK"
        clear_mock = MagicMock()
        text_mock = MagicMock()
        shape_mock = MagicMock()

        game = Game_Stats()
        game.menu_items = ["A", "B", "C"]
        game.menu_values = [1, 2, 3]
        game.current_menu_index = 1  # Item "B"

        # Test update with display
        game.update_menu_selection(oled, sm, clear_mock, text_mock, shape_mock)

        # Check logic: Prev=A, Curr=B, Next=C
        self.assertEqual(game.current_menu_selection, ["A", "B", "C"])
        self.assertEqual(game.current_menu_values, [1, 2, 3])

        # Verify calls
        clear_mock.assert_called_once()
        self.assertEqual(text_mock.call_count, 3)
        shape_mock.assert_called_once()

    def test_game_stats_menu_update_no_payload(self):
        # Mock dependencies
        oled = "OLED_MOCK"
        sm = "SM_MOCK"
        clear_mock = MagicMock()
        text_mock = MagicMock()
        shape_mock = MagicMock()

        game = Game_Stats()
        game.menu_items = ["A", "B", "C"]
        game.current_menu_index = 0

        # Test update WITHOUT display
        game.update_menu_selection(
            oled, sm, clear_mock, text_mock, shape_mock, send_payload=False
        )

        # Logic should update
        self.assertEqual(game.current_menu_selection, ["C", "A", "B"])
        # Calls should NOT happen
        clear_mock.assert_not_called()
        text_mock.assert_not_called()

    def test_load_rules_json_error(self):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            game = Game_Stats()
            self.assertEqual(game.rules_config, {})

    def test_add_score_p2(self):
        game = Game_Stats()
        game.menu_items = ["P1", "P2"]
        game.menu_values = [0, 0]
        game.add_score(2, 5)
        self.assertEqual(game.player_2_score, 5)
        self.assertEqual(game.menu_values[1], 5)

    def test_set_score_p2(self):
        game = Game_Stats()
        game.menu_items = ["P1", "P2"]
        game.menu_values = [0, 0]
        game.set_score(2, 10)
        self.assertEqual(game.player_2_score, 10)
        self.assertEqual(game.menu_values[1], 10)

    def test_add_score_no_menu_item(self):
        game = Game_Stats()
        game.menu_items = ["Inning"]  # No P1
        game.player_1_score = 0
        game.add_score(1, 1)
        self.assertEqual(game.player_1_score, 1)
        # Should not crash


if __name__ == "__main__":
    unittest.main()
