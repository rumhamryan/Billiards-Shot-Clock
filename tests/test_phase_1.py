import unittest
import sys
import os

# Ensure we can import from the lib directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.shot_clock_models import State_Machine, Game_Stats

class TestPhase1Models(unittest.TestCase):
    
    def test_state_machine_constants(self):
        sm = State_Machine()
        self.assertTrue(hasattr(sm, 'EDITING_VALUE'))
        self.assertEqual(sm.EDITING_VALUE, 'editing_value')
        
    def test_state_machine_properties(self):
        sm = State_Machine()
        
        sm.update_state(State_Machine.EDITING_VALUE)
        self.assertTrue(sm.editing_value)
        self.assertFalse(sm.menu)
        
        sm.update_state(State_Machine.MENU)
        self.assertTrue(sm.menu)
        self.assertFalse(sm.editing_value)

    def test_game_stats_new_fields(self):
        game = Game_Stats()
        
        # Test defaults
        self.assertEqual(game.profile_selection_index, 0)
        self.assertIsNone(game.temp_setting_value)
        self.assertEqual(game.current_menu_index, 0)
        
        # Test modification
        game.profile_selection_index = 2
        self.assertEqual(game.profile_selection_index, 2)
        
        game.temp_setting_value = "Test Value"
        self.assertEqual(game.temp_setting_value, "Test Value")

if __name__ == '__main__':
    unittest.main()
