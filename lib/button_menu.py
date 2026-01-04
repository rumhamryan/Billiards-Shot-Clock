from lib.models import State_Machine

# --- Menu Button Handlers ---


async def handle_make_menu(state_machine, game, hw_module):
    """Handle MAKE button in MENU state."""
    if game.menu_items[game.current_menu_index] == "Exit Match":
        state_machine.update_state(State_Machine.EXIT_MATCH_CONFIRMATION)
        await hw_module.render_exit_confirmation(state_machine, game)
        return

    # Enter Editing Mode for the current selection
    state_machine.update_state(State_Machine.EDITING_VALUE)
    game.temp_setting_value = game.menu_values[game.current_menu_index]
    await hw_module.render_menu(state_machine, game)


async def handle_make_editing(state_machine, game, hw_module):
    """Handle MAKE button in EDITING_VALUE state."""
    game.menu_values[game.current_menu_index] = game.temp_setting_value

    # Apply changes to actual game stats
    sel = game.menu_items[game.current_menu_index]
    if sel == "P1":
        game.set_score(1, int(game.temp_setting_value))
    elif sel == "P2":
        game.set_score(2, int(game.temp_setting_value))
    elif sel == "Rack":
        game.rack_counter = int(game.temp_setting_value)
        game.menu_values[1] = game.rack_counter
    elif sel == "Mute":
        game.speaker_muted = game.temp_setting_value
        if "Mute" in game.menu_items:
            idx = game.menu_items.index("Mute")
            game.menu_values[idx] = game.speaker_muted
    elif sel == "Inning":
        game.inning_counter = float(game.temp_setting_value)
        game.menu_values[0] = int(game.inning_counter)

    state_machine.update_state(State_Machine.MENU)
    await hw_module.render_menu(state_machine, game)


async def handle_up_editing(state_machine, game, hw_module):
    """Handles UP button during value editing."""
    sel = game.menu_items[game.current_menu_index]
    if sel == "Mute":
        game.temp_setting_value = not game.temp_setting_value
    else:
        game.temp_setting_value += 1
    await hw_module.render_menu(state_machine, game)


async def handle_down_editing(state_machine, game, hw_module):
    """Handles DOWN button during value editing."""
    sel = game.menu_items[game.current_menu_index]
    if sel == "Mute":
        game.temp_setting_value = not game.temp_setting_value
    else:
        game.temp_setting_value = max(1, game.temp_setting_value - 1)
    await hw_module.render_menu(state_machine, game)
