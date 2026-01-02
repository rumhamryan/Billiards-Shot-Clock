from lib.models import State_Machine


class GameRules:
    def __init__(self):
        pass

    async def handle_make(self, state_machine, game, hw_module):
        """Handle MAKE button press."""
        pass

    async def handle_miss(self, state_machine, game, hw_module):
        """Handle MISS button press."""
        pass

    async def handle_up(self, state_machine, game, hw_module):
        """Handle UP button press."""
        pass

    async def handle_down(self, state_machine, game, hw_module):
        """Handle DOWN button press."""
        pass

    def _process_extension(self, game):
        """Helper to calculate and apply extension."""
        p1_can = game.player_1_shooting and game.player_1_extension_available
        p2_can = game.player_2_shooting and game.player_2_extension_available

        can_extend = False
        if game.selected_profile in ["WNT", "BCA"] and (p1_can or p2_can):
            if game.player_1_shooting:
                game.player_1_extension_available = False
            else:
                game.player_2_extension_available = False
            game.extension_used = True
            can_extend = True
        elif game.selected_profile == "APA" and game.extension_available:
            # Check if current player has timeouts remaining
            has_timeout = False
            if game.player_1_shooting:
                if game.player_1_timeouts_remaining > 0:
                    has_timeout = True
                    game.player_1_timeouts_remaining -= 1
            elif game.player_2_timeouts_remaining > 0:
                has_timeout = True
                game.player_2_timeouts_remaining -= 1

            if has_timeout:
                game.extension_available, game.extension_used = False, True
                can_extend = True

        if can_extend:
            game.countdown += game.extension_duration
        return can_extend

    def _cancel_extension(self, game):
        """Helper to cancel a previously applied extension."""
        # Must have an active extension to cancel
        if not game.extension_used:
            return False

        # Must be at or above the threshold to allow cancellation
        # We use an explicit integer comparison to avoid any ambiguity
        current_timer = int(game.countdown)
        if current_timer < 30:
            return False

        # Subtract the extension duration, ensuring we don't drop below zero
        game.countdown = max(0, current_timer - game.extension_duration)

        # Reset extension flags
        game.extension_used = False
        game.extension_available = True

        # Refund the extension resource
        if game.selected_profile in ["WNT", "BCA"]:
            if game.player_1_shooting:
                game.player_1_extension_available = True
            else:
                game.player_2_extension_available = True
        elif game.selected_profile == "APA":
            if game.player_1_shooting:
                game.player_1_timeouts_remaining += 1
            else:
                game.player_2_timeouts_remaining += 1

        return True

    async def _check_win_condition(self, state_machine, game, hw_module):
        if (game.player_1_score >= game.player_1_target) or (
            game.player_2_score >= game.player_2_target
        ):
            winner = 1 if game.player_1_score >= game.player_1_target else 2
            state_machine.update_state(State_Machine.VICTORY)
            await hw_module.render_victory(state_machine, game, winner)
            return True
        return False


class NineBallRules(GameRules):
    async def handle_make(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            await hw_module.enter_shot_clock(state_machine, game)
        elif state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # Score
            if game.player_1_shooting:
                game.player_1_score += 1
            else:
                game.player_2_score += 1

            # Update menu values
            game.menu_values[0] = game.player_1_score
            game.menu_values[1] = game.player_2_score
            game.extension_available, game.extension_used = True, False

            # Check Win
            if await self._check_win_condition(state_machine, game, hw_module):
                return

            # Reset Timer
            game.countdown = game.profile_based_countdown
            game.break_shot = False
            await hw_module.enter_idle_mode(state_machine, game)

    async def handle_miss(self, state_machine, game, hw_module):
        state = state_machine.state
        if state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # End Turn
            game.countdown = game.profile_based_countdown
            game.inning_counter += 0.5
            game.menu_values[0] = game.player_1_score
            game.menu_values[1] = game.player_2_score
            game.extension_available, game.extension_used = True, False
            game.break_shot = False
            await hw_module.enter_idle_mode(state_machine, game)
        elif state == State_Machine.SHOT_CLOCK_IDLE:
            # Open Menu
            game.current_menu_index = 0
            state_machine.update_state(State_Machine.MENU)
            await hw_module.render_menu(state_machine, game)

    async def handle_up(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            # Exit early if already a new rack
            if game.break_shot:
                return
            # Immediate New Rack
            game.rack_counter += 1
            game.break_shot = True

            # APA 9-Ball Score Increment
            if game.selected_profile == "APA":
                if game.inning_counter % 1 == 0:
                    game.player_1_score += 1
                else:
                    game.player_2_score += 1
                # Update Menu Values (Scores for APA 9-Ball)
                game.menu_values[0] = game.player_1_score
                game.menu_values[1] = game.player_2_score
            else:
                # Update Menu Values (Rack for non-APA)
                game.menu_values[1] = game.rack_counter

            # Reset APA Timeouts
            game.player_1_timeouts_remaining = game.player_1_timeouts_per_rack
            game.player_2_timeouts_remaining = game.player_2_timeouts_per_rack

            await hw_module.enter_idle_mode(state_machine, game)

        elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
            if self._process_extension(game):
                await hw_module.update_timer_display(state_machine, game)

    async def handle_down(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            # Exit early if not a new rack
            if not game.break_shot:
                return
            # Cancel/Undo New Rack
            game.rack_counter = max(1, game.rack_counter - 1)
            game.break_shot = False

            # APA 9-Ball Score Decrement
            if game.selected_profile == "APA":
                if game.inning_counter % 1 == 0:
                    game.player_1_score = max(0, game.player_1_score - 1)
                else:
                    game.player_2_score = max(0, game.player_2_score - 1)
                # Update Menu Values
                game.menu_values[0] = game.player_1_score
                game.menu_values[1] = game.player_2_score
            else:
                # Update Menu Values
                game.menu_values[1] = game.rack_counter

            await hw_module.enter_idle_mode(state_machine, game)
        elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
            if self._cancel_extension(game):
                await hw_module.update_timer_display(state_machine, game)


class EightBallRules(GameRules):
    async def handle_make(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            await hw_module.enter_shot_clock(state_machine, game)
        elif state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # 8-Ball Make just resets timer (no score increment per ball usually)
            # But "Score" in APA 8-ball is "Games Won".
            # In-game makes don't add to score.

            game.extension_available, game.extension_used = True, False

            # Reset Timer
            game.countdown = game.profile_based_countdown
            game.break_shot = False
            await hw_module.enter_idle_mode(state_machine, game)

    async def handle_miss(self, state_machine, game, hw_module):
        state = state_machine.state
        if state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # End Turn
            game.countdown = game.profile_based_countdown
            game.inning_counter += 0.5
            game.extension_available, game.extension_used = True, False
            game.break_shot = False
            await hw_module.enter_idle_mode(state_machine, game)
        elif state == State_Machine.SHOT_CLOCK_IDLE:
            # Open Menu
            game.current_menu_index = 0
            state_machine.update_state(State_Machine.MENU)
            await hw_module.render_menu(state_machine, game)

    async def handle_up(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            # Trigger WIN RACK Confirmation
            game.pending_rack_result = "win"
            state_machine.update_state(State_Machine.CONFIRM_RACK_END)
            await hw_module.render_message(state_machine, game, "Confirm Win?")
        elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
            if self._process_extension(game):
                await hw_module.update_timer_display(state_machine, game)

    async def handle_down(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            # Trigger LOSE RACK Confirmation
            game.pending_rack_result = "lose"
            state_machine.update_state(State_Machine.CONFIRM_RACK_END)
            await hw_module.render_message(state_machine, game, "Confirm Loss?")
        elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
            if self._cancel_extension(game):
                await hw_module.update_timer_display(state_machine, game)


class StandardRules(GameRules):
    # BCA, WNT, Timeouts Mode
    async def handle_make(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.SHOT_CLOCK_IDLE:
            await hw_module.enter_shot_clock(state_machine, game)
        elif state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # Standard Make just resets timer
            game.extension_available, game.extension_used = True, False
            game.countdown = game.profile_based_countdown
            game.break_shot = False
            await hw_module.enter_idle_mode(state_machine, game)

    async def handle_miss(self, state_machine, game, hw_module):
        state = state_machine.state
        if state in [
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]:
            # End Turn
            game.countdown = game.profile_based_countdown
            game.inning_counter += 0.5
            game.extension_available, game.extension_used = True, False
            game.break_shot = False
            # Update menu (inning/rack)
            game.menu_values[0] = int(game.inning_counter)
            await hw_module.enter_idle_mode(state_machine, game)
        elif state == State_Machine.SHOT_CLOCK_IDLE:
            game.current_menu_index = 0
            state_machine.update_state(State_Machine.MENU)
            await hw_module.render_menu(state_machine, game)

    async def handle_up(self, state_machine, game, hw_module):
        if state_machine.countdown_in_progress and self._process_extension(game):
            await hw_module.update_timer_display(state_machine, game)

    async def handle_down(self, state_machine, game, hw_module):
        state = state_machine.state
        if state == State_Machine.COUNTDOWN_IN_PROGRESS and self._cancel_extension(game):
            await hw_module.update_timer_display(state_machine, game)
