import json
import unittest
from unittest.mock import mock_open, patch

import lib.button_logic as logic
from lib.models import Game_Stats


class TestApaRules(unittest.TestCase):
    def setUp(self):
        self.game = Game_Stats()

    def test_calculate_apa_targets_9ball(self):
        self.game.match_type = "9-Ball"
        self.game.player_1_skill_level = 5
        self.game.player_2_skill_level = 3

        mock_rules = {
            "APA": {
                "9-Ball": {"targets": {"3": 25, "5": 38}, "timeouts": {"3": 2, "4": 1}}
            }
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            logic._calculate_apa_targets(self.game)

        self.assertEqual(self.game.player_1_target, 38)
        self.assertEqual(self.game.player_2_target, 25)
        self.assertEqual(self.game.player_1_timeouts_per_rack, 1)
        self.assertEqual(self.game.player_2_timeouts_per_rack, 2)

    def test_calculate_apa_targets_8ball(self):
        self.game.match_type = "8-Ball"
        self.game.player_1_skill_level = 5
        self.game.player_2_skill_level = 3

        mock_rules = {
            "APA": {
                "8-Ball": {
                    "race_grid": {"5": {"3": [4, 2]}},
                    "timeouts": {"3": 2, "4": 1},
                }
            }
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            logic._calculate_apa_targets(self.game)

        self.assertEqual(self.game.player_1_target, 4)
        self.assertEqual(self.game.player_2_target, 2)
        self.assertEqual(self.game.player_1_timeouts_per_rack, 1)
        self.assertEqual(self.game.player_2_timeouts_per_rack, 2)


if __name__ == "__main__":
    unittest.main()
