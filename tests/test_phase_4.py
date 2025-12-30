import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock machine
sys.modules['machine'] = MagicMock()
sys.modules['_thread'] = MagicMock()
sys.modules['uasyncio'] = asyncio

from lib.shot_clock_models import State_Machine, Game_Stats
import lib.shot_clock_hw as hw

class TestPhase4Hardware(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.state_machine = State_Machine()
        self.game = Game_Stats()
        self.oled = MagicMock()
        
    async def test_enter_idle_mode_timeouts_only(self):
        self.game.timeouts_only = True
        self.game.profile_based_countdown = 60
        self.game.countdown = 0
        
        await hw.enter_idle_mode(self.state_machine, self.game, self.oled)
        
        self.assertEqual(self.state_machine.state, State_Machine.SHOT_CLOCK_IDLE)
        self.assertEqual(self.game.countdown, 60)
        # Verify specific text calls
        # 1. Timer
        # 2. "Timeouts Mode"
        # 3. Mode (handled inside display_text logic)
        self.assertTrue(self.oled.text_scaled.call_count >= 2)

    async def test_enter_shot_clock(self):
        self.game.inning_counter = 1.0 # Player 1
        await hw.enter_shot_clock(self.state_machine, self.game, self.oled)
        
        self.assertEqual(self.state_machine.state, State_Machine.COUNTDOWN_IN_PROGRESS)
        self.assertTrue(self.game.player_1_shooting)
        self.assertFalse(self.game.player_2_shooting)

    async def test_render_profile_selection(self):
        self.game.profile_selection_index = 0
        await hw.render_profile_selection(self.state_machine, self.game, self.oled)
        
        # Should clear profile region
        # Should display "Select Game"
        # Should display Profile Name
        self.oled.rect.assert_called()
        self.oled.text_scaled.assert_called()

if __name__ == '__main__':
    unittest.main()
