from lib import button_menu as menu
from lib import button_setup as setup
from lib.models import State_Machine


async def _handle_make_profile_selection(state_machine, game, hw_module):
    """Handle MAKE button in PROFILE_SELECTION state."""
    profile_list = game.profile_names
    selected_name = profile_list[game.profile_selection_index]
    profile = game.game_profiles[selected_name]

    game.selected_profile = selected_name
    game.profile_based_countdown = profile["timer_duration"]
    game.extension_duration = profile["extension_duration"]
    game.timeouts_only = selected_name == "Timeouts Mode"

    if selected_name == "APA":
        await setup.init_apa_selection(state_machine, game, hw_module)
    elif selected_name == "WNT":
        await setup.init_wnt_selection(state_machine, game, hw_module)
    elif selected_name == "BCA":
        await setup.init_bca_selection(state_machine, game, hw_module)
    elif selected_name == "Ultimate Pool":
        await setup.init_ultimate_selection(state_machine, game, hw_module)
    else:
        await setup.init_standard_selection(state_machine, game, hw_module, selected_name)


async def _handle_make_exit_confirmation(state_machine, game, hw_module):
    """Handle MAKE button in EXIT_MATCH_CONFIRMATION state."""
    game.reset()
    state_machine.reset()
    await hw_module.render_profile_selection(state_machine, game, clear_all=True)


async def _handle_make_confirm_rack_end(state_machine, game, hw_module):
    """Handle MAKE in CONFIRM_RACK_END state (Confirming Win/Loss)."""
    if not game.pending_rack_result:
        # Should not happen, but safe fallback
        state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await hw_module.enter_idle_mode(state_machine, game)
        return

    # Apply Score
    if game.pending_rack_result == "win":
        if game.player_1_shooting:
            game.add_score(1, 1)
        else:
            game.add_score(2, 1)
    elif game.pending_rack_result == "lose":
        # Opponent wins
        if game.player_1_shooting:
            game.add_score(2, 1)
        else:
            game.add_score(1, 1)
        # Switch shooter as current shooter lost the rack
        game.inning_counter += 0.5

    # Update Rack
    game.rack_counter += 1

    # Reset Timeouts (APA/WNT/BCA/Ultimate Pool)
    if game.selected_profile in ["APA", "WNT", "BCA", "Ultimate Pool"]:
        game.reset_rack_stats()

    if game.selected_profile == "Ultimate Pool":
        game.match_timer_running = False

    # Clear pending
    game.pending_rack_result = None

    # Check for Match Victory
    if (game.player_1_score >= game.player_1_target) or (
        game.player_2_score >= game.player_2_target
    ):
        game.winner = 1 if game.player_1_score >= game.player_1_target else 2
        state_machine.update_state(State_Machine.VICTORY)
        await hw_module.render_victory(state_machine, game, game.winner)
        return

    # Return to Idle
    game.break_shot = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_make_shootout(state_machine, game, hw_module):
    """Handle MAKE button during Ultimate Pool shootout."""
    import uasyncio as asyncio
    import utime

    state = state_machine.state

    if state == State_Machine.SHOOTOUT_ANNOUNCEMENT:
        state_machine.update_state(State_Machine.SHOOTOUT_P1_WAIT)
        await hw_module.render_shootout_stopwatch(state_machine, game, 0)

    elif state == State_Machine.SHOOTOUT_P1_WAIT:
        game.shootout_start_tick = utime.ticks_ms()
        state_machine.update_state(State_Machine.SHOOTOUT_P1_RUNNING)

    elif state == State_Machine.SHOOTOUT_P1_RUNNING:
        game.p1_shootout_time = utime.ticks_diff(
            utime.ticks_ms(), game.shootout_start_tick
        )
        state_machine.update_state(State_Machine.SHOOTOUT_P2_WAIT)
        await hw_module.render_shootout_stopwatch(state_machine, game, 0)

    elif state == State_Machine.SHOOTOUT_P2_WAIT:
        game.shootout_start_tick = utime.ticks_ms()
        state_machine.update_state(State_Machine.SHOOTOUT_P2_RUNNING)

    elif state == State_Machine.SHOOTOUT_P2_RUNNING:
        game.p2_shootout_time = utime.ticks_diff(
            utime.ticks_ms(), game.shootout_start_tick
        )
        # Render final time immediately to freeze display
        await hw_module.render_shootout_stopwatch(
            state_machine, game, game.p2_shootout_time
        )

        # 2 second pause after shootout finishes
        await asyncio.sleep(2)

        # Determine winner
        game.winner = 1 if game.p1_shootout_time < game.p2_shootout_time else 2
        state_machine.update_state(State_Machine.VICTORY)
        await hw_module.render_victory(state_machine, game, game.winner)


async def handle_make(state_machine, game, hw_module):
    """Logic for the MAKE button based on current state."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_make_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.CONFIRM_RACK_END:
        await _handle_make_confirm_rack_end(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        await menu.handle_make_menu(state_machine, game, hw_module)

    elif state == State_Machine.EDITING_VALUE:
        await menu.handle_make_editing(state_machine, game, hw_module)

    elif state == State_Machine.EXIT_MATCH_CONFIRMATION:
        await _handle_make_exit_confirmation(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await setup.handle_make_skill_level(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await setup.handle_make_game_type_selection(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await setup.handle_make_wnt_target_selection(state_machine, game, hw_module)

    elif state == State_Machine.VICTORY:
        # After victory, return to profile selection
        game.reset()
        state_machine.reset()
        await hw_module.render_profile_selection(state_machine, game, clear_all=True)

    elif state in [
        State_Machine.SHOOTOUT_ANNOUNCEMENT,
        State_Machine.SHOOTOUT_P1_WAIT,
        State_Machine.SHOOTOUT_P1_RUNNING,
        State_Machine.SHOOTOUT_P2_WAIT,
        State_Machine.SHOOTOUT_P2_RUNNING,
    ]:
        await _handle_make_shootout(state_machine, game, hw_module)

    # Delegate Game States to Rules
    elif (
        state
        in [
            State_Machine.SHOT_CLOCK_IDLE,
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]
        and game.rules
    ):
        if (
            state == State_Machine.SHOT_CLOCK_IDLE
            and game.selected_profile == "Ultimate Pool"
        ):
            game.match_timer_running = True
        await game.rules.handle_make(state_machine, game, hw_module)


async def handle_new_rack(state_machine, game, hw_module):
    """Logic for starting a new rack (Make + Miss pressed together)."""
    if state_machine.profile_selection or state_machine.victory:
        return

    # Only allow in game states
    if not (
        state_machine.shot_clock_idle
        or state_machine.countdown_in_progress
        or state_machine.countdown_complete
    ):
        return

    game.rack_counter += 1

    # Update menu values for non-APA/WNT/BCA/Ultimate Pool
    standard_profiles = ["APA", "WNT", "BCA", "Ultimate Pool"]
    if game.selected_profile not in standard_profiles:
        game.menu_values[1] = game.rack_counter
        game.break_shot = True
    else:
        # Reset APA/WNT/BCA/Ultimate Pool timeouts for new rack
        game.reset_rack_stats()

    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_up_profile_selection(state_machine, game, hw_module):
    """Handles UP button during profile selection."""
    game.profile_selection_index = (game.profile_selection_index - 1) % len(
        game.profile_names
    )
    await hw_module.render_profile_selection(state_machine, game)


async def handle_up(state_machine, game, hw_module):
    """Logic for the UP button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_up_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        game.current_menu_index = (game.current_menu_index - 1) % len(game.menu_items)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        await menu.handle_up_editing(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await setup.handle_up_apa_skill(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await setup.handle_up_apa_game_type(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await setup.handle_up_wnt_target_selection(state_machine, game, hw_module)

    # Delegate Game States to Rules
    elif (
        state
        in [
            State_Machine.SHOT_CLOCK_IDLE,
            State_Machine.COUNTDOWN_IN_PROGRESS,
        ]
        and game.rules
    ):
        await game.rules.handle_up(state_machine, game, hw_module)


async def _handle_down_profile_selection(state_machine, game, hw_module):
    """Handles DOWN button during profile selection."""
    game.profile_selection_index = (game.profile_selection_index + 1) % len(
        game.profile_names
    )
    await hw_module.render_profile_selection(state_machine, game)


async def handle_down(state_machine, game, hw_module):
    """Logic for the DOWN button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_down_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        game.current_menu_index = (game.current_menu_index + 1) % len(game.menu_items)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        await menu.handle_down_editing(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await setup.handle_down_apa_skill(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await setup.handle_down_apa_game_type(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await setup.handle_down_wnt_target_selection(state_machine, game, hw_module)

    # Delegate Game States to Rules
    elif (
        state
        in [
            State_Machine.SHOT_CLOCK_IDLE,
            State_Machine.COUNTDOWN_IN_PROGRESS,
        ]
        and game.rules
    ):
        await game.rules.handle_down(state_machine, game, hw_module)


async def handle_miss(state_machine, game, hw_module):
    """Logic for the MISS button."""
    state = state_machine.state

    if state == State_Machine.CONFIRM_RACK_END:
        # Cancel Confirmation
        game.pending_rack_result = None
        state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.MENU:
        # Exit Menu
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        # Cancel Edit
        state_machine.update_state(State_Machine.MENU)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EXIT_MATCH_CONFIRMATION:
        # Cancel Exit
        state_machine.update_state(State_Machine.MENU)
        await hw_module.render_menu(state_machine, game)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await setup.handle_miss_skill_level(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        # Go back to P2 Skill Level Selection
        state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P2)
        game.temp_setting_value = game.player_2_skill_level
        await hw_module.render_skill_level_selection(state_machine, game, 2)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        # Go back to Profile Selection
        state_machine.update_state(State_Machine.PROFILE_SELECTION)
        game.profile_selection_index = game.profile_names.index("WNT")
        await hw_module.render_profile_selection(state_machine, game, clear_all=True)

    # Delegate Game States to Rules
    elif (
        state
        in [
            State_Machine.SHOT_CLOCK_IDLE,
            State_Machine.COUNTDOWN_IN_PROGRESS,
            State_Machine.COUNTDOWN_COMPLETE,
        ]
        and game.rules
    ):
        await game.rules.handle_miss(state_machine, game, hw_module)


# --- Test/Legacy Aliases ---
_calculate_apa_targets = setup.calculate_apa_targets
_init_apa_selection = setup.init_apa_selection
_init_wnt_selection = setup.init_wnt_selection
_init_bca_selection = setup.init_bca_selection
_init_standard_selection = setup.init_standard_selection
_init_ultimate_selection = setup.init_ultimate_selection
_handle_make_wnt_target_selection = setup.handle_make_wnt_target_selection
