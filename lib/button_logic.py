import json

from lib.models import State_Machine


def _calculate_apa_targets(game):
    """Calculates player targets based on skill levels and rules.json."""
    try:
        with open("lib/rules.json") as f:
            rules = json.load(f)

        if game.match_type == "9-Ball":
            game.player_1_target = rules["9-Ball"]["targets"][
                str(game.player_1_skill_level)
            ]
            game.player_2_target = rules["9-Ball"]["targets"][
                str(game.player_2_skill_level)
            ]
        elif game.match_type == "8-Ball":
            race = rules["8-Ball"]["race_grid"][str(game.player_1_skill_level)][
                str(game.player_2_skill_level)
            ]
            game.player_1_target = race[0]
            game.player_2_target = race[1]
    except (OSError, KeyError):
        # Fallback defaults if file missing or invalid SL
        game.player_1_target = 14
        game.player_2_target = 14


async def _handle_make_profile_selection(state_machine, game, hw_module):
    """Handle MAKE button in PROFILE_SELECTION state."""
    profile_list = game.profile_names
    selected_name = profile_list[game.profile_selection_index]
    profile = game.game_profiles[selected_name]

    game.selected_profile = selected_name
    game.profile_based_countdown = profile["timer_duration"]
    game.extension_duration = profile["extension_duration"]
    game.timeouts_only = game.extension_duration == 0

    if selected_name == "APA":
        state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P1)
        game.temp_setting_value = 3  # Start with SL 3
        await hw_module.render_skill_level_selection(state_machine, game, 1)
        return

    state_machine.game_on = True
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


async def _handle_make_skill_level(state_machine, game, hw_module):
    """Handles MAKE button during skill level selection."""
    if state_machine.apa_skill_level_p1:
        game.player_1_skill_level = game.temp_setting_value
        state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P2)
        game.temp_setting_value = 3  # Start with SL 3
        await hw_module.render_skill_level_selection(state_machine, game, 2)
    elif state_machine.apa_skill_level_p2:
        game.player_2_skill_level = game.temp_setting_value
        _calculate_apa_targets(game)

        # Initialize APA stats
        game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
        game.player_1_score = 0
        game.player_2_score = 0
        game.menu_values = [
            game.player_1_score,
            game.player_2_score,
            None,
            game.speaker_muted,
        ]
        state_machine.game_on = True
        state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
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

        # Check for victory
        if (game.player_1_score >= game.player_1_target) or (
            game.player_2_score >= game.player_2_target
        ):
            winner = 1 if game.player_1_score >= game.player_1_target else 2
            state_machine.update_state(State_Machine.VICTORY)
            await hw_module.render_victory(state_machine, game, winner)
            return

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

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await _handle_make_skill_level(state_machine, game, hw_module)

    elif state == State_Machine.VICTORY:
        # After victory, return to profile selection
        game.profile_selection_index = 0
        state_machine.update_state(State_Machine.PROFILE_SELECTION)
        await hw_module.render_profile_selection(state_machine, game, clear_all=True)


async def handle_new_rack(state_machine, game, hw_module):
    """Logic for starting a new rack (Make + Miss pressed together)."""
    if state_machine.profile_selection or state_machine.victory:
        return

    game.rack_counter += 1
    game.break_shot = True

    # Update menu values for non-APA
    if game.selected_profile != "APA":
        game.menu_values[1] = game.rack_counter

    await hw_module.enter_idle_mode(state_machine, game)


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

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        # Skill levels 1-9 wrapping
        game.temp_setting_value = (game.temp_setting_value % 9) + 1
        player_num = 1 if state == State_Machine.APA_SKILL_LEVEL_P1 else 2
        await hw_module.render_skill_level_selection(state_machine, game, player_num)


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

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        # Skill levels 1-9 wrapping (down)
        game.temp_setting_value = game.temp_setting_value - 1
        if game.temp_setting_value < 1:
            game.temp_setting_value = 9
        player_num = 1 if state == State_Machine.APA_SKILL_LEVEL_P1 else 2
        await hw_module.render_skill_level_selection(state_machine, game, player_num)


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

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        # Cancel Skill Level Selection -> Back to Profile Selection
        game.profile_selection_index = 0
        state_machine.update_state(State_Machine.PROFILE_SELECTION)
        await hw_module.render_profile_selection(state_machine, game, clear_all=True)
