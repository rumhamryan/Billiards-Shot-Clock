from lib.models import State_Machine


async def handle_make(state_machine, game, hw_module):
    """Logic for the MAKE button based on current state."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        # Confirm Profile
        profile_list = list(game.game_profiles)
        selected_name = profile_list[game.profile_selection_index]
        profile = game.game_profiles[selected_name]

        game.selected_profile = selected_name
        game.profile_based_countdown = profile["timer_duration"]
        game.extension_duration = profile["extension_duration"]
        game.timeouts_only = game.extension_duration == 0
        state_machine.game_on = True

        # Initial Menu Values
        game.menu_values = [
            game.rack_counter,
            game.speaker_muted,
            int(game.inning_counter),
        ]

        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.SHOT_CLOCK_IDLE:
        # Start Clock
        await hw_module.enter_shot_clock(state_machine, game)

    elif state in [
        State_Machine.COUNTDOWN_IN_PROGRESS,
        State_Machine.COUNTDOWN_COMPLETE,
    ]:
        # Shot Made - Reset to Idle
        game.countdown = game.profile_based_countdown
        if game.selected_profile == "APA":
            game.extension_available, game.extension_used = True, False
        game.break_shot = False
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.MENU:
        # Enter Editing Mode for the current selection
        state_machine.update_state(State_Machine.EDITING_VALUE)
        game.temp_setting_value = game.menu_values[game.current_menu_index]
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        # Save Value and return to Menu
        game.menu_values[game.current_menu_index] = game.temp_setting_value

        # Apply changes to actual game stats
        sel = game.menu_items[game.current_menu_index]
        if sel == "Rack":
            game.rack_counter = game.temp_setting_value
        elif sel == "Mute":
            game.speaker_muted = game.temp_setting_value
        elif sel == "Inning":
            game.inning_counter = float(game.temp_setting_value)

        state_machine.update_state(State_Machine.MENU)
        await hw_module.render_menu(state_machine, game)


async def handle_up(state_machine, game, hw_module):  # noqa: PLR0912
    """Logic for the UP button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        game.profile_selection_index = (game.profile_selection_index - 1) % len(
            game.game_profiles
        )
        await hw_module.render_profile_selection(state_machine, game)

    elif state == State_Machine.COUNTDOWN_IN_PROGRESS:
        # Use Extension
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
            game.game_profiles
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
        game.break_shot = False
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.SHOT_CLOCK_IDLE:
        # Open Menu
        if game.selected_profile != "Timeouts Mode":
            state_machine.update_state(State_Machine.MENU)
            await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.MENU:
        # Exit Menu
        await hw_module.enter_idle_mode(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        # Cancel editing
        state_machine.update_state(State_Machine.MENU)
        await hw_module.render_menu(state_machine, game)
