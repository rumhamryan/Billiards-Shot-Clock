import json

from lib.game_rules import EightBallRules, NineBallRules, StandardRules
from lib.models import State_Machine

# --- APA Helper Logic ---


def calculate_apa_targets(game):
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
            # Clamp SL to valid 8-Ball range (2-7)
            p1_sl_val = max(2, min(7, game.player_1_skill_level))
            p2_sl_val = max(2, min(7, game.player_2_skill_level))

            p1_sl = str(p1_sl_val)
            p2_sl = str(p2_sl_val)
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


# --- Profile Initialization ---


async def init_apa_selection(state_machine, game, hw_module):
    """Initializes the APA match setup flow."""
    state_machine.update_state(State_Machine.APA_SKILL_LEVEL_P1)
    game.temp_setting_value = 3  # Start with SL 3
    await hw_module.render_skill_level_selection(state_machine, game, 1)


async def init_wnt_selection(state_machine, game, hw_module):
    """Initializes the WNT match setup flow."""
    state_machine.update_state(State_Machine.WNT_TARGET_SELECTION)

    wnt_config = game.rules_config.get("WNT", {})
    targets = wnt_config.get("targets", [5, 7, 9, 11, 13])
    game.temp_setting_value = targets[2] if len(targets) > 2 else targets[0]

    timeouts = wnt_config.get("timeouts", 1)
    game.player_1_timeouts_per_rack = timeouts
    game.player_2_timeouts_per_rack = timeouts

    await hw_module.render_wnt_target_selection(state_machine, game)


async def init_bca_selection(state_machine, game, hw_module):
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


async def init_standard_selection(state_machine, game, hw_module, selected_name):
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


async def init_ultimate_selection(state_machine, game, hw_module):
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


# --- Setup Button Handlers ---


async def handle_make_skill_level(state_machine, game, hw_module):
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


async def handle_make_game_type_selection(state_machine, game, hw_module):
    """Handles MAKE button during APA game type selection."""
    # 0 = 8-Ball, 1 = 9-Ball
    is_9ball = game.temp_setting_value == 1
    game.match_type = "9-Ball" if is_9ball else "8-Ball"

    # Instantiate Rules
    if is_9ball:
        game.rules = NineBallRules()
    else:
        game.rules = EightBallRules()

    calculate_apa_targets(game)

    # Initialize APA stats
    game.menu_items = ["P1", "P2", "Exit Match", "Mute"]
    game.set_score(1, 0)
    game.set_score(2, 0)

    state_machine.game_on = True
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    await hw_module.enter_idle_mode(state_machine, game)


async def handle_make_wnt_target_selection(state_machine, game, hw_module):
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


async def handle_up_wnt_target_selection(state_machine, game, hw_module):
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


async def handle_down_wnt_target_selection(state_machine, game, hw_module):
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


async def handle_up_apa_skill(state_machine, game, hw_module):
    """Handles UP button during APA skill level selection."""
    game.temp_setting_value = (game.temp_setting_value % 9) + 1
    player_num = 1 if state_machine.apa_skill_level_p1 else 2
    await hw_module.render_skill_level_selection(state_machine, game, player_num)


async def handle_down_apa_skill(state_machine, game, hw_module):
    """Handles DOWN button during APA skill level selection."""
    game.temp_setting_value = game.temp_setting_value - 1
    if game.temp_setting_value < 1:
        game.temp_setting_value = 9
    player_num = 1 if state_machine.apa_skill_level_p1 else 2
    await hw_module.render_skill_level_selection(state_machine, game, player_num)


async def handle_up_apa_game_type(state_machine, game, hw_module):
    """Handles UP button during APA game type selection."""
    game.temp_setting_value = 1 - game.temp_setting_value
    await hw_module.render_game_type_selection(state_machine, game)


async def handle_down_apa_game_type(state_machine, game, hw_module):
    """Handles DOWN button during APA game type selection."""
    game.temp_setting_value = 1 - game.temp_setting_value
    await hw_module.render_game_type_selection(state_machine, game)


async def handle_miss_skill_level(state_machine, game, hw_module):
    """Handles MISS button during skill level selection."""
    # Cancel Skill Level Selection -> Back to Profile Selection
    game.profile_selection_index = 0
    state_machine.update_state(State_Machine.PROFILE_SELECTION)
    await hw_module.render_profile_selection(state_machine, game, clear_all=True)
