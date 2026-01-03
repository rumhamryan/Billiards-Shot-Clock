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


def display_shape(oled, payload, x, y, width, height, fill=True, send_payload=True):
    """Draws a shape on the OLED display."""
    if payload == "line":
        oled.line(x, y, width, height, oled.white)
    elif payload == "rect":
        if not fill:
            oled.line(x, y, x + width - 1, y, oled.white)
            oled.line(x, y, x, y + height - 1, oled.white)
            oled.line(x, y + height - 1, x + width - 1, y + height - 1, oled.white)
            oled.line(x + width - 1, y, x + width - 1, y + height - 1, oled.white)
        else:
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


def display_timeouts(oled, state_machine, game, send_payload=True):
    """Draws the timeouts sections of the OLED display."""
    # player_1 timeouts
    if game.player_1_timeouts_remaining > 1:
        display_shape(oled, "rect", 38, 59, 4, 4, True, False)
        display_shape(oled, "rect", 46, 59, 4, 4, True, False)
    elif game.player_1_timeouts_remaining == 1:
        display_shape(oled, "rect", 42, 59, 4, 4, True, False)
    else:
        display_clear(oled, "timeout_counter_1", send_payload=True)

    if game.player_2_timeouts_remaining > 1:
        display_shape(oled, "rect", 80, 59, 4, 4, True, False)
        display_shape(oled, "rect", 88, 59, 4, 4, True, False)
    elif game.player_2_timeouts_remaining == 1:
        display_shape(oled, "rect", 84, 59, 4, 4, True, False)
    else:
        display_clear(oled, "timeout_counter_2", send_payload=True)


def process_timer_duration(duration):
    """Formats duration as a string with leading zeros."""
    return f"{duration:02d}"


def format_match_timer(seconds):
    """Formats seconds into MM:SS."""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def render_match_timer(oled, state_machine, game, force_all=False, send_payload=True):
    """Renders the match timer digits individually for efficiency."""
    new_val = game.match_countdown
    old_val = game.prev_match_countdown

    new_shifted = new_val < 600
    old_shifted = (old_val is not None) and (old_val < 600)

    # Force a full redraw if we crossed the 10-minute threshold or it's first render
    if (old_val is None) or (new_shifted != old_shifted):
        force_all = True

    m_new, s_new = divmod(new_val, 60)
    m_old, s_old = divmod(old_val, 60) if old_val is not None else (-1, -1)

    # Individual digits
    d1_new, d2_new = divmod(m_new, 10)
    d3_new, d4_new = divmod(s_new, 10)

    d1_old, d2_old = divmod(m_old, 10) if old_val is not None else (-1, -1)
    d3_old, d4_old = divmod(s_old, 10) if old_val is not None else (-1, -1)

    new_digits = [d1_new, d2_new, d3_new, d4_new]
    old_digits = [d1_old, d2_old, d3_old, d4_old]

    if new_shifted:
        x_positions = [39, 48, 64, 72]
        colon_x = 56
        suffix = "_s"
    else:
        x_positions = [44, 53, 69, 77]
        colon_x = 61
        suffix = ""

    if force_all:
        display_clear(oled, "match_clock_full", send_payload=False)
        display_text(oled, state_machine, ":", colon_x, 57, 1, False)

    for i in range(4):
        if force_all or (new_digits[i] != old_digits[i]):
            if not force_all:
                region = f"match_clock_digit_{i+1}{suffix}"
                display_clear(oled, region, send_payload=False)

            # Digit 1 is suppressed if 0 in shifted mode
            if i == 0 and d1_new == 0 and new_shifted:
                pass
            else:
                display_text(
                    oled, state_machine, str(new_digits[i]), x_positions[i], 57, 1, False
                )

    game.prev_match_countdown = new_val
    if send_payload:
        oled.show()


# High Level Logic Rendering


def render_scoreline(
    oled,
    state_machine,
    game,
    send_payload=True,
    suppress_scores=False,
    force_match_timer=False,
):
    """Renders the scoreline/bottom row based on the selected profile."""
    if game.timeouts_only:
        display_text(oled, state_machine, "Timeouts Mode", 12, 57, 1, False)
    elif game.selected_profile in ["APA", "WNT", "BCA", "Ultimate Pool"]:
        if not suppress_scores:
            # Draw player_1 score/target_score
            score_1, target_1 = game.player_1_score, game.player_1_target
            shift = 0
            if score_1 < 10:
                shift = 7
            display_text(oled, state_machine, f"{score_1}", 0, 57, 1, False)
            display_text(oled, state_machine, "/", 15 - shift, 57, 1, False)
            display_text(oled, state_machine, f"{target_1}", 23 - shift, 57, 1, False)

            # Draw player_2 score/target_score
            score_2, target_2 = game.player_2_score, game.player_2_target
            s2_shift = 7 if score_2 < 10 else 0
            t2_shift = 8 if target_2 < 10 else 0

            display_text(
                oled, state_machine, f"{score_2}", 89 + s2_shift + t2_shift, 57, 1, False
            )
            display_text(oled, state_machine, "/", 104 + t2_shift, 57, 1, False)
            display_text(oled, state_machine, f"{target_2}", 112 + t2_shift, 57, 1, False)

        if game.selected_profile == "Ultimate Pool":
            # Don't render match timer in Menu or Exit Confirmation
            no_match_timer_states = [
                State_Machine.MENU,
                State_Machine.EDITING_VALUE,
                State_Machine.EXIT_MATCH_CONFIRMATION,
            ]
            if state_machine.state not in no_match_timer_states:
                render_match_timer(
                    oled,
                    state_machine,
                    game,
                    force_all=force_match_timer,
                    send_payload=False,
                )
        elif not suppress_scores:
            # Draw the current shooter indicator
            if game.inning_counter % 1 == 0:
                display_shape(oled, "rect", 57, 57, 7, 7, True, False)
                display_shape(oled, "rect", 66, 57, 7, 7, False, False)
            else:
                display_shape(oled, "rect", 57, 57, 7, 7, False, False)
                display_shape(oled, "rect", 66, 57, 7, 7, True, False)

            # Draw timeouts indicators
            display_timeouts(oled, state_machine, game, False)
    else:
        racks, innings = game.rack_counter, int(game.inning_counter)
        display_text(oled, state_machine, f"Rack:{racks}", 0, 57, 1, False)
        display_text(oled, state_machine, f"Inning:{innings}", 57, 57, 1, False)

    if send_payload:
        oled.show()


async def enter_idle_mode(state_machine, game, oled):
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    display_clear(oled, "everything")

    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(
            oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8, False
        )
    else:
        game.speaker_5_count = 4

    render_scoreline(oled, state_machine, game, False)

    if game.break_shot:
        game.countdown = game.profile_based_countdown + game.extension_duration
    else:
        game.countdown = game.profile_based_countdown

    if game.selected_profile == "Ultimate Pool":
        # Full render of match timer (at y=57 via helper)
        render_match_timer(oled, state_machine, game, force_all=True, send_payload=False)
        # Render Shot Clock (Standard size/pos)
        display_text(
            oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8, True
        )
    else:
        display_text(oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8)


async def enter_shot_clock(state_machine, game, oled):
    state_machine.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)


async def update_timer_display(state_machine, game, oled):
    if game.selected_profile == "Ultimate Pool":
        # If we are in a state with an overlay message, DO NOT clear the full area
        # as it would wipe the message. Only update match timer digits.
        overlay_states = [
            State_Machine.CONFIRM_RACK_END,
            State_Machine.MENU,
            State_Machine.EDITING_VALUE,
            State_Machine.EXIT_MATCH_CONFIRMATION,
        ]

        if state_machine.state not in overlay_states:
            # Clear and update shot clock
            display_clear(oled, "shot_clock_full", send_payload=False)
            display_text(
                oled,
                state_machine,
                process_timer_duration(game.countdown),
                0,
                0,
                8,
                False,
            )

        # Always update match timer (helper handles individual digit clearing)
        render_match_timer(oled, state_machine, game, force_all=False, send_payload=True)
    else:
        display_clear(oled, "shot_clock_digit_1", "shot_clock_digit_2")
        display_text(oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8)


async def render_profile_selection(state_machine, game, oled, clear_all=False):
    region = "everything" if clear_all else "profile_selection"
    display_clear(oled, region, send_payload=False)

    profile_list = game.profile_names
    idx = game.profile_selection_index
    name = profile_list[idx]

    display_text(oled, state_machine, "Select Game:", 15, 10, 1, False)
    if str(name) == "Ultimate Pool":
        display_text(oled, state_machine, "Ultimate", 0, 30, 2, False)
        display_text(oled, state_machine, "Pool", 30, 48, 2, True)
    else:
        display_text(oled, state_machine, str(name), 25, 30, 3, True)


async def render_skill_level_selection(state_machine, game, oled, player_num):
    """Renders the skill level selection screen for a player."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, f"Player {player_num}", 20, 10, 1, False)
    display_text(oled, state_machine, "Skill Level:", 15, 25, 1, False)

    sl = game.temp_setting_value
    display_text(oled, state_machine, str(sl), 50, 40, 3, True)


async def render_game_type_selection(state_machine, game, oled):
    """Renders the game type selection screen (8-Ball or 9-Ball)."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, "Select Game:", 15, 10, 1, False)

    # temp_setting_value: 0 for 8-Ball, 1 for 9-Ball
    game_type = "9-Ball" if game.temp_setting_value == 1 else "8-Ball"
    display_text(oled, state_machine, game_type, 15, 30, 2, True)


async def render_wnt_target_selection(state_machine, game, oled):
    """Renders the WNT target selection screen."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, "Race to", 35, 10, 1, False)

    target = game.temp_setting_value
    shift = 0
    if target > 9:
        shift = 12
    display_text(oled, state_machine, str(target), 50 - shift, 30, 3, True)


async def render_victory(state_machine, game, oled, winner_num):
    """Renders the victory screen."""
    display_clear(oled, "everything", send_payload=False)

    display_text(oled, state_machine, "VICTORY!", 10, 10, 2, False)
    display_text(oled, state_machine, f"Player {winner_num}", 0, 35, 2, False)

    oled.show()


async def render_message(state_machine, game, oled, message, font_size=1):
    """Renders a generic message on the screen (e.g. for Confirmation)."""
    display_clear(oled, "everything", send_payload=False)

    lines = message.split("\n")

    # Metrics
    base_w = 8
    base_h = 8
    char_width = base_w * font_size
    line_height = (base_h * font_size) + 4
    total_height = len(lines) * line_height

    # Vertical Start
    y_pos = (64 - total_height) // 2
    # Clamp to top if message is huge
    y_pos = max(y_pos, 0)

    for line in lines:
        # Horizontal Start
        text_width = len(line) * char_width
        x_pos = (128 - text_width) // 2
        # Clamp to left
        x_pos = max(x_pos, 0)

        display_text(oled, state_machine, line, int(x_pos), int(y_pos), font_size, False)
        y_pos += line_height

    # Re-render scoreline at the bottom, suppressing scores and forcing match timer redraw
    render_scoreline(
        oled,
        state_machine,
        game,
        False,
        suppress_scores=True,
        force_match_timer=True,
    )

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
