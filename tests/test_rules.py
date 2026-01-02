import json
import unittest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import lib.button_logic as logic
from lib.game_rules import EightBallRules, GameRules, NineBallRules, StandardRules
from lib.models import Game_Stats, State_Machine


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

    def test_calculate_apa_targets_invalid_sl_fallback(self):
        self.game.match_type = "9-Ball"
        self.game.player_1_skill_level = 99  # Invalid

        mock_rules = {"APA": {"9-Ball": {"targets": {"3": 25}, "timeouts": {"3": 2}}}}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_rules))):
            logic._calculate_apa_targets(self.game)

        self.assertEqual(self.game.player_1_target, 14)  # Fallback


class TestRules(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sm = State_Machine()
        self.game = Game_Stats()
        self.hw = MagicMock()
        self.hw.enter_idle_mode = AsyncMock()
        self.hw.enter_shot_clock = AsyncMock()
        self.hw.render_menu = AsyncMock()
        self.hw.render_message = AsyncMock()
        self.hw.update_timer_display = AsyncMock()
        self.hw.render_victory = AsyncMock()

    def test_base_rules_pass_methods(self):
        # Cover the empty base class methods
        base = GameRules()
        import asyncio

        async def run_passes():
            await base.handle_make(None, None, None)
            await base.handle_miss(None, None, None)
            await base.handle_up(None, None, None)
            await base.handle_down(None, None, None)

        asyncio.run(run_passes())

    async def test_cancel_extension_logic_threshold_exact(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.0
        self.game.extension_duration = 25
        self.game.extension_used = True
        self.game.countdown = 30  # Boundary

        self.assertTrue(rule._cancel_extension(self.game))
        self.assertEqual(self.game.countdown, 5)  # 30 - 25

    async def test_cancel_extension_logic_threshold_fail(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.0
        self.game.extension_duration = 25
        self.game.extension_used = True
        self.game.countdown = 29  # Below boundary

        self.assertFalse(rule._cancel_extension(self.game))
        self.assertEqual(self.game.countdown, 29)

    # --- Nine Ball Rules ---

    async def test_9ball_make_idle(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await rule.handle_make(self.sm, self.game, self.hw)
        self.hw.enter_shot_clock.assert_called_once()

    async def test_9ball_make_running_scores_and_resets(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_score = 0
        self.game.profile_based_countdown = 20
        self.game.player_1_target = 10
        self.game.player_2_target = 10

        await rule.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 1)
        self.assertEqual(self.game.countdown, 20)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_9ball_make_victory(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_score = 9
        self.game.player_1_target = 10

        await rule.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 10)
        self.assertEqual(self.sm.state, State_Machine.VICTORY)
        self.hw.render_victory.assert_called_once()

    async def test_9ball_miss_running(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.inning_counter = 1.0

        await rule.handle_miss(self.sm, self.game, self.hw)

        self.assertEqual(self.game.inning_counter, 1.5)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_9ball_up_idle_starts_new_rack(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rack_counter = 1

        await rule.handle_up(self.sm, self.game, self.hw)

        if not self.game.break_shot:
            self.assertEqual(self.game.rack_counter, 2)
            self.assertTrue(self.game.break_shot)
            self.hw.enter_idle_mode.assert_called_once()
        else:
            self.assertEqual(self.game.rack_counter, 1)

    async def test_9ball_down_idle_cancels_new_rack(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        self.game.rack_counter = 2

        await rule.handle_down(self.sm, self.game, self.hw)

        self.assertEqual(self.game.rack_counter, 1)
        self.hw.enter_idle_mode.assert_called_once()

    # --- Eight Ball Rules ---

    async def test_8ball_make_running_resets_timer_only(self):
        rule = EightBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.player_1_score = 0
        self.game.player_1_target = 5
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.profile_based_countdown = 20

        await rule.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_score, 0)  # No score change on regular make
        self.assertEqual(self.game.countdown, 20)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_8ball_up_idle_triggers_confirmation(self):
        rule = EightBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

        await rule.handle_up(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.CONFIRM_RACK_END)
        self.assertEqual(self.game.pending_rack_result, "win")
        self.hw.render_message.assert_called_with(self.sm, self.game, "Confirm Win?")

    async def test_8ball_down_idle_triggers_confirmation(self):
        rule = EightBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)

        await rule.handle_down(self.sm, self.game, self.hw)

        self.assertEqual(self.sm.state, State_Machine.CONFIRM_RACK_END)
        self.assertEqual(self.game.pending_rack_result, "lose")
        self.hw.render_message.assert_called_with(self.sm, self.game, "Confirm Loss?")

    # --- Standard Rules ---

    async def test_standard_make_running(self):
        rule = StandardRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.profile_based_countdown = 30

        await rule.handle_make(self.sm, self.game, self.hw)

        self.assertEqual(self.game.countdown, 30)
        self.hw.enter_idle_mode.assert_called_once()

    async def test_extension_logic(self):
        # Test base class logic via StandardRules
        rule = StandardRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "BCA"
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_timeouts_remaining = 1
        self.game.extension_duration = 30
        self.game.countdown = 10

        await rule.handle_up(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_timeouts_remaining, 0)
        self.assertEqual(self.game.countdown, 40)

    async def test_extension_logic_wnt(self):
        rule = StandardRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "WNT"
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_timeouts_remaining = 1
        self.game.extension_available = True
        self.game.extension_duration = 30
        self.game.countdown = 10

        await rule.handle_up(self.sm, self.game, self.hw)

        self.assertEqual(self.game.player_1_timeouts_remaining, 0)
        self.assertEqual(self.game.countdown, 40)

    async def test_cancel_extension_logic_apa(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_timeouts_remaining = 1
        self.game.extension_duration = 25
        self.game.countdown = 20  # Exactly at threshold
        self.game.extension_available = True

        # Apply extension
        await rule.handle_up(self.sm, self.game, self.hw)
        self.assertEqual(self.game.countdown, 45)
        self.assertEqual(self.game.player_1_timeouts_remaining, 0)
        self.assertTrue(self.game.extension_used)

        # Cancel extension (should work since 45 >= 20)
        await rule.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.countdown, 20)
        self.assertEqual(self.game.player_1_timeouts_remaining, 1)
        self.assertFalse(self.game.extension_used)

    async def test_cancel_extension_logic_threshold(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.extension_used = True
        self.game.extension_duration = 25

        # Test at 3`0 (should work)
        self.game.countdown = 30
        self.assertTrue(rule._cancel_extension(self.game))

        # Reset and test at 19 (should NOT work)
        self.game.extension_used = True
        self.game.countdown = 19
        self.assertFalse(rule._cancel_extension(self.game))

    async def test_cancel_extension_logic_below_20(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.inning_counter = 1.0  # Player 1 shooting
        self.game.player_1_timeouts_remaining = 1
        self.game.extension_duration = 25
        self.game.countdown = 10
        self.game.extension_available = True

        # Apply extension -> countdown becomes 35
        await rule.handle_up(self.sm, self.game, self.hw)

        # Manually set countdown below 20
        self.game.countdown = 15

        # Cancel extension (should NOT work since 15 < 20)
        await rule.handle_down(self.sm, self.game, self.hw)
        self.assertEqual(self.game.countdown, 15)
        self.assertEqual(self.game.player_1_timeouts_remaining, 0)
        self.assertTrue(self.game.extension_used)
