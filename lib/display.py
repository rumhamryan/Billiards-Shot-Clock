from lib.hardware_config import DISPLAY_REGIONS
from lib.models import State_Machine

# Low Level Helpers


def display_text(oled, state_machine, payload, x, y, font_size, send_payload=True):
    """Displays a text string on the OLED screen."""
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        x = 0
        font_size = 2

    oled.text_scaled(str(payload), x, y, font_size)

    if payload == "Timeouts Mode" and state_machine.profile_selection:
        oled.text_scaled("Mode", 32, 48, 2)

    if send_payload:
        oled.show()


def display_shape(oled, payload, x, y, width, height, send_payload=True):
    """Draws a shape on the OLED display."""
    if payload == "line":
        oled.line(x, y, width, height, oled.white)
    elif payload == "rect":
        oled.rect(x, y, width, height, oled.white, True)

    if send_payload:
        oled.show()


def display_clear(oled, *regions, send_payload=True):
    """Clears specified sections of the OLED display."""
    for region in regions:
        if region in DISPLAY_REGIONS:
            x, y, width, height = DISPLAY_REGIONS[region]
            oled.rect(x, y, width, height, oled.black, True)

    if send_payload:
        oled.show()


def process_timer_duration(duration):
    """Formats duration as a string with leading zeros."""
    return f"{duration:02d}"


# High Level Logic Rendering


async def enter_idle_mode(state_machine, game, oled):
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    display_clear(oled, "everything")

    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(
            oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8, False
        )
        display_text(oled, state_machine, "Timeouts Mode", 12, 57, 1)
    else:
        game.speaker_5_count = 4
        if game.selected_profile == "APA":
            score_1, target_1 = game.player_1_score, game.player_1_target
            shift = 0
            if score_1 < 10:
                shift = 7
            display_text(oled, state_machine, f"{score_1}", 0, 57, 1, False)
            display_text(oled, state_machine, "/", 15 - shift, 57, 1, False)
            display_text(oled, state_machine, f"{target_1}", 23 - shift, 57, 1, False)

            # display_text(oled, state_machine, "Score", 44, 57, 1, False)

            score_2, target_2 = game.player_2_score, game.player_2_target
            if score_2 < 10:
                shift = 7
            display_text(oled, state_machine, f"{score_2}", 89 + shift, 57, 1, False)
            display_text(oled, state_machine, "/", 104, 57, 1, False)
            display_text(oled, state_machine, f"{target_2}", 112, 57, 1, False)

            # Draw underline for shooting player
            if game.inning_counter % 1 == 0:
                display_text(oled, state_machine, "<", 34, 57, 1, False)
            else:
                display_text(oled, state_machine, ">", 87, 57, 1, False)

        else:
            racks, innings = game.rack_counter, int(game.inning_counter)
            display_text(oled, state_machine, f"Rack:{racks}", 0, 57, 1, False)
            display_text(oled, state_machine, f"Inning:{innings}", 57, 57, 1, False)

        if game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(
            oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8
        )


async def enter_shot_clock(state_machine, game, oled):
    state_machine.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)

    # Logic from original shot_clock()
    if game.inning_counter % 1 == 0:
        game.player_1_shooting = True
        game.player_2_shooting = False
    else:
        game.player_1_shooting = False
        game.player_2_shooting = True


async def update_timer_display(state_machine, game, oled):
    display_clear(oled, "shot_clock_digit_1", "shot_clock_digit_2")
    display_text(oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8)


async def render_profile_selection(state_machine, game, oled, clear_all=False):
    region = "everything" if clear_all else "profile_selection"
    display_clear(oled, region, send_payload=False)

    profile_list = game.profile_names
    idx = game.profile_selection_index
    name = profile_list[idx]

    display_text(oled, state_machine, "Select Game:", 15, 10, 1, False)
    display_text(oled, state_machine, str(name), 25, 30, 3, True)


async def render_skill_level_selection(state_machine, game, oled, player_num):
    """Renders the skill level selection screen for a player."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, f"Player {player_num}", 20, 10, 1, False)
    display_text(oled, state_machine, "Skill Level:", 15, 25, 1, False)

    sl = game.temp_setting_value
    display_text(oled, state_machine, str(sl), 50, 40, 3, True)


async def render_victory(state_machine, game, oled, winner_num):
    """Renders the victory screen."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, "VICTORY!", 10, 10, 2, False)
    display_text(oled, state_machine, f"Player {winner_num}", 0, 35, 2, False)

    oled.show()


async def render_menu(state_machine, game, oled):
    """Renders the game menu. Handles both navigation and editing modes."""
    # 1. Clear the entire buffer but DON'T send to hardware yet
    display_clear(oled, "everything", send_payload=False)

    # 2. Draw static Header
    display_text(oled, state_machine, "Game", 0, 2, 2, False)
    display_text(oled, state_machine, "Menu", 66, 2, 2, False)
    display_shape(oled, "line", 0, 19, 128, 19, False)
    display_shape(oled, "line", 0, 20, 128, 20, False)

    # 3. Determine what values to show (Current values vs Temporary edit value)
    prev_idx = (game.current_menu_index - 1) % len(game.menu_items)
    next_idx = (game.current_menu_index + 1) % len(game.menu_items)

    val_prev = game.menu_values[prev_idx]
    val_curr = (
        game.temp_setting_value
        if state_machine.editing_value
        else game.menu_values[game.current_menu_index]
    )
    val_next = game.menu_values[next_idx]

    # Helper to format
    def fmt(name, val):
        return name if val is None else f"{name}:{val}"

    # 4. Draw the menu items
    display_text(
        oled, state_machine, fmt(game.menu_items[prev_idx], val_prev), 24, 24, 1, False
    )
    display_text(
        oled,
        state_machine,
        fmt(game.menu_items[game.current_menu_index], val_curr),
        24,
        40,
        1,
        False,
    )
    display_text(
        oled, state_machine, fmt(game.menu_items[next_idx], val_next), 24, 56, 1, False
    )

    # 5. Draw the cursor and FINAL show()
    display_shape(oled, "rect", 8, 40, 8, 8, True)


async def render_exit_confirmation(state_machine, game, oled):
    """Renders the 'Are you sure?' confirmation screen for exiting the match."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, "Are you sure?", 12, 25, 1, False)

    oled.show()
