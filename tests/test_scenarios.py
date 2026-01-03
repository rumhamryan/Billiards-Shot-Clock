import unittest
from unittest.mock import AsyncMock, MagicMock

import lib.button_logic as logic
from lib.game_rules import EightBallRules, NineBallRules
from lib.models import Game_Stats, State_Machine


class TestScenarios(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.render_profile_selection = AsyncMock()
        self.hw.render_skill_level_selection = AsyncMock()
        self.hw.render_game_type_selection = AsyncMock()
        self.hw.render_wnt_target_selection = AsyncMock()
        self.hw.render_victory = AsyncMock()
        self.hw.render_menu = AsyncMock()
        self.hw.render_message = AsyncMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.hw.enter_shot_clock = AsyncMock()
        self.hw.update_timer_display = AsyncMock()

    # --- APA Scenarios ---

    async def test_apa_flow_full_setup(self):
        # 1. Start in Profile Selection
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 0  # APA

        # Select APA -> To SL P1
        await logic.handle_make(self.sm, self.game, self.hw)
        self.assertTrue(self.sm.apa_skill_level_p1)

        # Select P1 SL 3 -> To SL P2
        await logic.handle_make(self.sm, self.game, self.hw)
        self.assertTrue(self.sm.apa_skill_level_p2)

        # Select P2 SL 3 -> To Game Type Selection
        await logic.handle_make(self.sm, self.game, self.hw)
        self.assertTrue(self.sm.apa_game_type_selection)

        # Toggle to 8-Ball
        self.game.temp_setting_value = 0
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertTrue(self.sm.shot_clock_idle)
        self.assertEqual(self.game.match_type, "8-Ball")

    async def test_apa_9ball_happy_path_victory(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.rules_config = {
            "APA": {"9-Ball": {"targets": {"3": 2}, "timeouts": {"3": 2}}}
        }

        # Progress setup
        await logic.handle_make(self.sm, self.game, self.hw)  # To SL P1
        await logic.handle_make(self.sm, self.game, self.hw)  # To SL P2
        await logic.handle_make(self.sm, self.game, self.hw)  # To Game Type
        self.sm.update_state(State_Machine.APA_GAME_TYPE_SELECTION)
        self.game.temp_setting_value = 1  # 9-Ball
        await logic.handle_make(self.sm, self.game, self.hw)  # To IDLE

        self.assertEqual(self.game.player_1_target, 2)

        # P1 makes 2 balls
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        await logic.handle_make(self.sm, self.game, self.hw)
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 2)
        self.assertTrue(self.sm.victory)

    async def test_apa_8ball_defensive_win(self):
        self.game.selected_profile = "APA"
        self.game.match_type = "8-Ball"
        self.game.rules = EightBallRules()
        self.game.player_1_target = 2
        self.game.player_2_target = 2
        self.game.inning_counter = 1.0  # P1

        # P1 Misses
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        await logic.handle_miss(self.sm, self.game, self.hw)
        self.assertEqual(self.game.inning_counter, 1.5)  # P2 Turn

        # P2 Wins Rack
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await logic.handle_up(self.sm, self.game, self.hw)
        self.sm.update_state(State_Machine.CONFIRM_RACK_END)
        await logic.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_2_score, 1)

    async def test_apa_9ball_rack_logic(self):
        self.game.selected_profile = "APA"
        self.game.match_type = "9-Ball"
        self.game.rules = NineBallRules()
        self.game.inning_counter = 1.0
        self.game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        self.game.menu_values = [0, 0, None, False]
        self.game.break_shot = False  # Essential to allow starting new rack
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

        # UP to start rack
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.player_1_score, 1)
        self.assertTrue(self.game.break_shot)

        # DOWN to cancel
        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.player_1_score, 0)
        self.assertFalse(self.game.break_shot)

    # --- BCA Scenarios ---

    async def test_bca_flow(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 1  # BCA
        self.game.rules_config = {"BCA": {"target": 16, "timeouts": 0}}

        await logic.handle_make(self.sm, self.game, self.hw)
        self.assertEqual(self.game.selected_profile, "BCA")
        self.assertEqual(self.game.player_1_timeouts_per_rack, 0)

        # Extension check
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        await logic.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.countdown, 0)

    async def test_bca_menu_sync(self):
        self.game.selected_profile = "BCA"
        self.game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        self.game.menu_values = [0, 0, None, False]

        self.sm.update_state(State_Machine.MENU)
        self.game.current_menu_index = 0
        await logic.handle_make(self.sm, self.game, self.hw)  # Edit
        self.game.temp_setting_value = 5
        await logic.handle_make(self.sm, self.game, self.hw)  # Save

        self.assertEqual(self.game.player_1_score, 5)

    # --- WNT Scenarios ---

    async def test_wnt_no_loss_enforcement(self):
        self.game.selected_profile = "WNT"
        self.game.rules = EightBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

        await logic.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.sm.state, State_Machine.SHOT_CLOCK_IDLE)
        self.assertIsNone(self.game.pending_rack_result)

    # --- Timeouts Mode Scenarios ---

    async def test_timeouts_mode_flow(self):
        self.sm.update_state(State_Machine.PROFILE_SELECTION)
        self.game.profile_selection_index = 2  # Timeouts Mode
        await logic.handle_make(self.sm, self.game, self.hw)

        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await logic.handle_make(self.sm, self.game, self.hw)
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)

        await logic.handle_miss(self.sm, self.game, self.hw)
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.assertTrue(self.sm.shot_clock_idle)


if __name__ == "__main__":
    unittest.main()
