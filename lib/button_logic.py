from lib.models import State_Machine


async def _handle_make_profile_selection(state_machine, game, hw_module):
    """Handle MAKE button in PROFILE_SELECTION state."""
    profile_list = game.profile_names
    selected_name = profile_list[game.profile_selection_index]
    profile = game.game_profiles[selected_name]

    game.selected_profile = selected_name
    game.profile_based_countdown = profile["timer_duration"]
    game.extension_duration = profile["extension_duration"]
    game.timeouts_only = game.extension_duration == 0
    state_machine.game_on = True

    # Update menu items and initial stats based on profile
    if selected_name == "APA":
        game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        game.player_1_score = 0
        game.player_2_score = 0
        game.menu_values = [
            game.player_1_score,
            game.player_2_score,
            None,
            game.speaker_muted,
        ]
    else:
        game.menu_items = ["Inning", "Rack", "Exit Match", "Mute"]
        game.inning_counter = 1.0
        game.rack_counter = 1
        game.menu_values = [
            int(game.inning_counter),
            game.rack_counter,
            None,
            game.speaker_muted,
        ]

    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_make_countdown(state_machine, game, hw_module):
    """Handle MAKE button in countdown-related states."""
    if game.selected_profile == "APA":
        if game.player_1_shooting:
            game.player_1_score += 1
        else:
            game.player_2_score += 1
        # Update menu values to reflect new scores
        game.menu_values[0] = game.player_1_score
        game.menu_values[1] = game.player_2_score
        game.extension_available, game.extension_used = True, False

    game.countdown = game.profile_based_countdown
    game.break_shot = False
    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_make_menu(state_machine, game, hw_module):
    """Handle MAKE button in MENU state."""
    if game.menu_items[game.current_menu_index] == "Exit Match":
        state_machine.update_state(State_Machine.EXIT_MATCH_CONFIRMATION)
        await hw_module.render_exit_confirmation(state_machine, game)
        return

    # Enter Editing Mode for the current selection
    state_machine.update_state(State_Machine.EDITING_VALUE)
    game.temp_setting_value = game.menu_values[game.current_menu_index]
    await hw_module.render_menu(state_machine, game)


async def _handle_make_editing(state_machine, game, hw_module):
    """Handle MAKE button in EDITING_VALUE state."""
    game.menu_values[game.current_menu_index] = game.temp_setting_value

    # Apply changes to actual game stats
    sel = game.menu_items[game.current_menu_index]
    if sel == "P1":
        game.player_1_score = int(game.temp_setting_value)
        game.menu_values[0] = game.player_1_score
    elif sel == "P2":
        game.player_2_score = int(game.temp_setting_value)
        game.menu_values[1] = game.player_2_score
    elif sel == "Rack":
        game.rack_counter = int(game.temp_setting_value)
        game.menu_values[1] = game.rack_counter
    elif sel == "Mute":
        game.speaker_muted = game.temp_setting_value
        game.menu_values[3] = game.speaker_muted
    elif sel == "Inning":
        game.inning_counter = float(game.temp_setting_value)
        game.menu_values[0] = int(game.inning_counter)

    state_machine.update_state(State_Machine.MENU)
    await hw_module.render_menu(state_machine, game)


async def _handle_make_exit_confirmation(state_machine, game, hw_module):
    """Handle MAKE button in EXIT_MATCH_CONFIRMATION state."""
    game.profile_selection_index = 0
    state_machine.update_state(State_Machine.PROFILE_SELECTION)
    await hw_module.render_profile_selection(state_machine, game, clear_all=True)


async def handle_make(state_machine, game, hw_module):
    """Logic for the MAKE button based on current state."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_make_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.SHOT_CLOCK_IDLE:
        await hw_module.enter_shot_clock(state_machine, game)

    elif state in [
        State_Machine.COUNTDOWN_IN_PROGRESS,
        State_Machine.COUNTDOWN_COMPLETE,
    ]:
        await _handle_make_countdown(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        await _handle_make_menu(state_machine, game, hw_module)

    elif state == State_Machine.EDITING_VALUE:
        await _handle_make_editing(state_machine, game, hw_module)

    elif state == State_Machine.EXIT_MATCH_CONFIRMATION:
        await _handle_make_exit_confirmation(state_machine, game, hw_module)


def _process_extension(game):
    """Internal helper to calculate if an extension can be applied and apply it."""
    p1_can = game.player_1_shooting and game.player_1_extension_available
    p2_can = game.player_2_shooting and game.player_2_extension_available

    can_extend = False
    if game.selected_profile in ["WNT", "BCA"] and (p1_can or p2_can):
        if game.player_1_shooting:
            game.player_1_extension_available = False
        else:
            game.player_2_extension_available = False
        can_extend = True
    elif game.selected_profile == "APA" and game.extension_available:
        game.extension_available, game.extension_used = False, True
        can_extend = True

    if can_extend:
        game.countdown += game.extension_duration
    return can_extend


async def handle_up(state_machine, game, hw_module):
    """Logic for the UP button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        game.profile_selection_index = (game.profile_selection_index - 1) % len(
            game.profile_names
        )
        await hw_module.render_profile_selection(state_machine, game)

    elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
        if _process_extension(game):
            await hw_module.update_timer_display(state_machine, game)

    elif state == State_Machine.MENU:
        game.current_menu_index = (game.current_menu_index - 1) % len(game.menu_items)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        # Increment value
        sel = game.menu_items[game.current_menu_index]
        if sel == "Mute":
            game.temp_setting_value = not game.temp_setting_value
        else:
            game.temp_setting_value += 1
        await hw_module.render_menu(state_machine, game)


async def handle_down(state_machine, game, hw_module):
    """Logic for the DOWN button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        game.profile_selection_index = (game.profile_selection_index + 1) % len(
            game.profile_names
        )
        await hw_module.render_profile_selection(state_machine, game)

    elif state == State_Machine.MENU:
        game.current_menu_index = (game.current_menu_index + 1) % len(game.menu_items)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        # Decrement value
        sel = game.menu_items[game.current_menu_index]
        if sel == "Mute":
            game.temp_setting_value = not game.temp_setting_value
        else:
            game.temp_setting_value = max(1, game.temp_setting_value - 1)
        await hw_module.render_menu(state_machine, game)


async def handle_miss(state_machine, game, hw_module):
    """Logic for the MISS button."""
    state = state_machine.state

    if state in [State_Machine.COUNTDOWN_IN_PROGRESS, State_Machine.COUNTDOWN_COMPLETE]:
        # Turn over
        game.countdown = game.profile_based_countdown
        game.inning_counter += 0.5
        # Update menu values if applicable (though we are going back to IDLE)
        if game.selected_profile == "APA":
            game.menu_values[0] = game.player_1_score
            game.menu_values[1] = game.player_2_score
        else:
            game.menu_values[0] = int(game.inning_counter)
            game.menu_values[1] = game.rack_counter

        game.break_shot = False
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.SHOT_CLOCK_IDLE:
        # Open Menu
        if game.selected_profile != "Timeouts Mode":
            game.current_menu_index = 0
            state_machine.update_state(State_Machine.MENU)
            await hw_module.render_menu(state_machine, game)

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
