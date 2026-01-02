import unittest
from unittest.mock import AsyncMock, MagicMock

from lib.game_rules import EightBallRules, NineBallRules, StandardRules
from lib.models import Game_Stats, State_Machine


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

    # --- Nine Ball Rules ---

    async def test_9ball_make_idle(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await rule.handle_make(self.sm, self.game, self.hw)
        self.hw.enter_shot_clock.assert_called_once()

    async def test_9ball_make_running_scores_and_resets(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.player_1_shooting = True
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
        self.game.player_1_shooting = True
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
        self.game.player_1_shooting = True
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
        self.game.selected_profile = "WNT"
        self.game.player_1_shooting = True
        self.game.player_1_extension_available = True
        self.game.extension_duration = 30
        self.game.countdown = 10

        await rule.handle_up(self.sm, self.game, self.hw)

        self.assertFalse(self.game.player_1_extension_available)
        self.assertEqual(self.game.countdown, 40)

    async def test_cancel_extension_logic_apa(self):
        rule = NineBallRules()
        self.sm.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
        self.game.selected_profile = "APA"
        self.game.player_1_shooting = True
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
        self.game.player_1_shooting = True
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
        self.game.player_1_shooting = True
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
