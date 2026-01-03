import json

from lib.game_rules import EightBallRules, NineBallRules, StandardRules
from lib.models import State_Machine


def _calculate_apa_targets(game):
    """Calculates player targets and timeouts based on skill levels and rules_config."""
    match_rules = game.rules_config.get("APA", {}).get(game.match_type, {})

    if not match_rules:
        # Fallback defaults if config missing
        game.player_1_target = 14
        game.player_2_target = 14
        game.player_1_timeouts_per_rack = 1
        game.player_1_timeouts_remaining = 1
        game.player_2_timeouts_per_rack = 1
        game.player_2_timeouts_remaining = 1
        return

    # Targets
    try:
        if game.match_type == "9-Ball":
            game.player_1_target = match_rules["targets"][str(game.player_1_skill_level)]
            game.player_2_target = match_rules["targets"][str(game.player_2_skill_level)]
        elif game.match_type == "8-Ball":
            p1_sl = str(game.player_1_skill_level)
            p2_sl = str(game.player_2_skill_level)
            race = match_rules["race_grid"][p1_sl][p2_sl]
            game.player_1_target = race[0]
            game.player_2_target = race[1]
    except KeyError:
        game.player_1_target = 14
        game.player_2_target = 14

    # Timeouts
    timeout_rules = match_rules.get("timeouts", {"3": 2, "4": 1})

    # Player 1
    if game.player_1_skill_level <= 3:
        game.player_1_timeouts_per_rack = timeout_rules["3"]
    else:
        game.player_1_timeouts_per_rack = timeout_rules["4"]
    game.player_1_timeouts_remaining = game.player_1_timeouts_per_rack

    # Player 2
    if game.player_2_skill_level <= 3:
        game.player_2_timeouts_per_rack = timeout_rules["3"]
    else:
        game.player_2_timeouts_per_rack = timeout_rules["4"]
    game.player_2_timeouts_remaining = game.player_2_timeouts_per_rack


async def _init_apa_selection(state_machine, game, hw_module):
    """Initializes the APA match setup flow."""
    state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P1)
    game.temp_setting_value = 3  # Start with SL 3
    await hw_module.render_skill_level_selection(state_machine, game, 1)


async def _init_wnt_selection(state_machine, game, hw_module):
    """Initializes the WNT match setup flow."""
    state_machine.update_state(State_Machine.WNT_TARGET_SELECTION)

    wnt_config = game.rules_config.get("WNT", {})
    targets = wnt_config.get("targets", [5, 7, 9, 11, 13])
    game.temp_setting_value = targets[2] if len(targets) > 2 else targets[0]

    timeouts = wnt_config.get("timeouts", 1)
    game.player_1_timeouts_per_rack = timeouts
    game.player_2_timeouts_per_rack = timeouts

    await hw_module.render_wnt_target_selection(state_machine, game)


async def _init_bca_selection(state_machine, game, hw_module):
    """Initializes the BCA match setup flow."""
    bca_config = game.rules_config.get("BCA", {})
    game.player_1_target = bca_config.get("target", 16)
    game.player_2_target = bca_config.get("target", 16)
    game.player_1_timeouts_per_rack = bca_config.get("timeouts", 0)
    game.player_2_timeouts_per_rack = bca_config.get("timeouts", 0)

    game.reset_rack_stats()
    game.set_score(1, 0)
    game.set_score(2, 0)

    game.rules = EightBallRules()
    game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
    game.menu_values = [
        game.player_1_score,
        game.player_2_score,
        None,
        game.speaker_muted,
    ]
    state_machine.game_on = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def _init_standard_selection(state_machine, game, hw_module, selected_name):
    """Initializes standard/timeouts-only match setup."""
    game.rules = StandardRules()
    state_machine.game_on = True
    if selected_name == "Timeouts Mode":
        game.menu_items = ["Exit Match", "Mute"]
        game.menu_values = [None, game.speaker_muted]
    else:
        # Fallback for any other standard profiles
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
        await _init_apa_selection(state_machine, game, hw_module)
    elif selected_name == "WNT":
        await _init_wnt_selection(state_machine, game, hw_module)
    elif selected_name == "BCA":
        await _init_bca_selection(state_machine, game, hw_module)
    elif selected_name == "Ultimate Pool":
        await _init_ultimate_selection(state_machine, game, hw_module)
    else:
        await _init_standard_selection(state_machine, game, hw_module, selected_name)


async def _init_ultimate_selection(state_machine, game, hw_module):
    """Initializes the Ultimate Pool match setup flow."""
    up_config = game.rules_config.get("Ultimate Pool", {})
    game.player_1_target = up_config.get("target", 5)
    game.player_2_target = up_config.get("target", 5)

    timeouts = up_config.get("timeouts", 1)
    game.player_1_timeouts_per_rack = timeouts
    game.player_2_timeouts_per_rack = timeouts

    game.reset_rack_stats()
    game.set_score(1, 0)
    game.set_score(2, 0)

    game.rules = EightBallRules()
    game.menu_items = ["P1", "P2", "Exit Match", "Mute"]

    state_machine.game_on = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_make_skill_level(state_machine, game, hw_module):
    """Handles MAKE button during skill level selection."""
    if state_machine.apa_skill_level_p1:
        game.player_1_skill_level = game.temp_setting_value
        state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P2)
        game.temp_setting_value = 3  # Start with SL 3
        await hw_module.render_skill_level_selection(state_machine, game, 2)
        return

    elif state_machine.apa_skill_level_p2:
        game.player_2_skill_level = game.temp_setting_value

    # Transition to Game Type Selection
    state_machine.update_state(State_Machine.APA_GAME_TYPE_SELECTION)
    game.temp_setting_value = 1  # Default to 9-Ball (0=8-Ball, 1=9-Ball)
    await hw_module.render_game_type_selection(state_machine, game)


async def _handle_make_game_type_selection(state_machine, game, hw_module):
    """Handles MAKE button during APA game type selection."""
    # 0 = 8-Ball, 1 = 9-Ball
    is_9ball = game.temp_setting_value == 1
    game.match_type = "9-Ball" if is_9ball else "8-Ball"

    # Instantiate Rules
    if is_9ball:
        game.rules = NineBallRules()
    else:
        game.rules = EightBallRules()

    _calculate_apa_targets(game)

    # Initialize APA stats
    game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
    game.set_score(1, 0)
    game.set_score(2, 0)

    state_machine.game_on = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def _handle_make_wnt_target_selection(state_machine, game, hw_module):
    """Handles MAKE button during WNT target selection."""
    game.player_1_target = game.temp_setting_value
    game.player_2_target = game.temp_setting_value

    # WNT uses Games Won scoring similar to 8-Ball
    game.rules = EightBallRules()

    # Timeouts from rules_config
    wnt_config = game.rules_config.get("WNT", {})
    timeouts = wnt_config.get("timeouts", 1)
    game.player_1_timeouts_per_rack = timeouts
    game.player_2_timeouts_per_rack = timeouts

    game.reset_rack_stats()
    game.set_score(1, 0)
    game.set_score(2, 0)

    # Menu setup
    game.menu_items = ["P1", "P2", "Exit Match", "Mute"]

    state_machine.game_on = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
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
        winner = 1 if game.player_1_score >= game.player_1_target else 2
        state_machine.update_state(State_Machine.VICTORY)
        await hw_module.render_victory(state_machine, game, winner)
        return

    # Return to Idle
    game.break_shot = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def handle_make(state_machine, game, hw_module):
    """Logic for the MAKE button based on current state."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_make_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.CONFIRM_RACK_END:
        await _handle_make_confirm_rack_end(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        await _handle_make_menu(state_machine, game, hw_module)

    elif state == State_Machine.EDITING_VALUE:
        await _handle_make_editing(state_machine, game, hw_module)

    elif state == State_Machine.EXIT_MATCH_CONFIRMATION:
        await _handle_make_exit_confirmation(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await _handle_make_skill_level(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await _handle_make_game_type_selection(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await _handle_make_wnt_target_selection(state_machine, game, hw_module)

    elif state == State_Machine.VICTORY:
        # After victory, return to profile selection
        game.reset()
        state_machine.reset()
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


async def _handle_up_wnt_target_selection(state_machine, game, hw_module):
    """Handles UP button during WNT target selection."""
    try:
        with open("lib/rules.json") as f:
            rules = json.load(f)
        targets = rules.get("WNT", {}).get("targets", [5, 7, 9, 11, 13])
        try:
            idx = targets.index(game.temp_setting_value)
            game.temp_setting_value = targets[(idx + 1) % len(targets)]
        except ValueError:
            game.temp_setting_value = targets[0]
    except (OSError, KeyError):
        game.temp_setting_value = (game.temp_setting_value % 20) + 1

    await hw_module.render_wnt_target_selection(state_machine, game)


async def _handle_down_wnt_target_selection(state_machine, game, hw_module):
    """Handles DOWN button during WNT target selection."""
    try:
        with open("lib/rules.json") as f:
            rules = json.load(f)
        targets = rules.get("WNT", {}).get("targets", [5, 7, 9, 11, 13])
        try:
            idx = targets.index(game.temp_setting_value)
            game.temp_setting_value = targets[(idx - 1) % len(targets)]
        except ValueError:
            game.temp_setting_value = targets[-1]
    except (OSError, KeyError):
        game.temp_setting_value = max(1, game.temp_setting_value - 1)

    await hw_module.render_wnt_target_selection(state_machine, game)


async def _handle_up_editing(state_machine, game, hw_module):
    """Handles UP button during value editing."""
    sel = game.menu_items[game.current_menu_index]
    if sel == "Mute":
        game.temp_setting_value = not game.temp_setting_value
    else:
        game.temp_setting_value += 1
    await hw_module.render_menu(state_machine, game)


async def _handle_up_apa_skill(state_machine, game, hw_module):
    """Handles UP button during APA skill level selection."""
    game.temp_setting_value = (game.temp_setting_value % 9) + 1
    player_num = 1 if state_machine.apa_skill_level_p1 else 2
    await hw_module.render_skill_level_selection(state_machine, game, player_num)


async def _handle_up_apa_game_type(state_machine, game, hw_module):
    """Handles UP button during APA game type selection."""
    game.temp_setting_value = 1 - game.temp_setting_value
    await hw_module.render_game_type_selection(state_machine, game)


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
        await _handle_up_editing(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await _handle_up_apa_skill(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await _handle_up_apa_game_type(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await _handle_up_wnt_target_selection(state_machine, game, hw_module)

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


async def _handle_down_apa_game_type(state_machine, game, hw_module):
    """Handles DOWN button during APA game type selection."""
    game.temp_setting_value = 1 - game.temp_setting_value
    await hw_module.render_game_type_selection(state_machine, game)


async def _handle_down_profile_selection(state_machine, game, hw_module):
    """Handles DOWN button during profile selection."""
    game.profile_selection_index = (game.profile_selection_index + 1) % len(
        game.profile_names
    )
    await hw_module.render_profile_selection(state_machine, game)


async def _handle_down_editing(state_machine, game, hw_module):
    """Handles DOWN button during value editing."""
    sel = game.menu_items[game.current_menu_index]
    if sel == "Mute":
        game.temp_setting_value = not game.temp_setting_value
    else:
        game.temp_setting_value = max(1, game.temp_setting_value - 1)
    await hw_module.render_menu(state_machine, game)


async def _handle_down_apa_skill(state_machine, game, hw_module):
    """Handles DOWN button during APA skill level selection."""
    game.temp_setting_value = game.temp_setting_value - 1
    if game.temp_setting_value < 1:
        game.temp_setting_value = 9
    player_num = 1 if state_machine.apa_skill_level_p1 else 2
    await hw_module.render_skill_level_selection(state_machine, game, player_num)


async def handle_down(state_machine, game, hw_module):
    """Logic for the DOWN button."""
    state = state_machine.state

    if state == State_Machine.PROFILE_SELECTION:
        await _handle_down_profile_selection(state_machine, game, hw_module)

    elif state == State_Machine.MENU:
        game.current_menu_index = (game.current_menu_index + 1) % len(game.menu_items)
        await hw_module.render_menu(state_machine, game)

    elif state == State_Machine.EDITING_VALUE:
        await _handle_down_editing(state_machine, game, hw_module)

    elif state in [State_Machine.APA_SKILL_LEVEL_P1, State_Machine.APA_SKILL_LEVEL_P2]:
        await _handle_down_apa_skill(state_machine, game, hw_module)

    elif state == State_Machine.APA_GAME_TYPE_SELECTION:
        await _handle_down_apa_game_type(state_machine, game, hw_module)

    elif state == State_Machine.WNT_TARGET_SELECTION:
        await _handle_down_wnt_target_selection(state_machine, game, hw_module)

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


async def _handle_miss_skill_level(state_machine, game, hw_module):
    """Handles MISS button during skill level selection."""
    # Cancel Skill Level Selection -> Back to Profile Selection
    game.profile_selection_index = 0
    state_machine.update_state(State_Machine.PROFILE_SELECTION)
    await hw_module.render_profile_selection(state_machine, game, clear_all=True)


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
        await _handle_miss_skill_level(state_machine, game, hw_module)

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
