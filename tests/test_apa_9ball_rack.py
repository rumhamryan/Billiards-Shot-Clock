import unittest
from unittest.mock import AsyncMock, MagicMock

import lib.button_logic as logic
from lib.game_rules import NineBallRules
from lib.models import Game_Stats, State_Machine


class TestApa9BallRack(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.hw.update_timer_display = AsyncMock()

        # Setup as APA 9-Ball
        self.game.selected_profile = "APA"
        self.game.match_type = "9-Ball"
        self.game.rules = NineBallRules()
        self.game.player_1_score = 10
        self.game.player_2_score = 10
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.break_shot = False
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

    async def test_up_increments_score_apa_9ball(self):
        # Press UP to start new rack
        await logic.handle_up(self.sm, self.game, self.hw)

        # Verify rack incremented (existing behavior)
        self.assertEqual(self.game.rack_counter, 2)
        self.assertTrue(self.game.break_shot)

        # Verify score incremented (requested behavior)
        # For now this will likely fail until I implement it
        self.assertEqual(self.game.player_1_score, 11)
        self.assertEqual(self.game.player_2_score, 10)

    async def test_down_decrements_score_apa_9ball(self):
        # First start a rack
        self.game.break_shot = True
        self.game.rack_counter = 2
        self.game.player_1_score = 11

        # Press DOWN to cancel rack
        await logic.handle_down(self.sm, self.game, self.hw)

        # Verify rack decremented (existing behavior)
        self.assertEqual(self.game.rack_counter, 1)
        self.assertFalse(self.game.break_shot)

        # Verify score decremented (requested behavior)
        self.assertEqual(self.game.player_1_score, 10)

    async def test_up_increments_score_player_2_apa_9ball(self):
        self.game.inning_counter = 1.5  # Player 2 shooting

        # Press UP to start new rack
        await logic.handle_up(self.sm, self.game, self.hw)

        # Verify score incremented for player 2
        self.assertEqual(self.game.player_2_score, 11)
        self.assertEqual(self.game.player_1_score, 10)

    async def test_up_non_apa_9ball_no_score_change(self):
        self.game.selected_profile = "WNT"
        self.game.player_1_score = 0
        self.game.menu_values = [1, 1, None, False]

        # Press UP to start new rack
        await logic.handle_up(self.sm, self.game, self.hw)

        # Verify rack incremented
        self.assertEqual(self.game.rack_counter, 2)
        # Verify score NOT incremented
        self.assertEqual(self.game.player_1_score, 0)
        # Verify menu_values[1] is rack
        self.assertEqual(self.game.menu_values[1], 2)


if __name__ == "__main__":
    unittest.main()
