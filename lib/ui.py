from lib import display
from lib.models import State_Machine

# High Level Logic Rendering


def display_timeouts(oled, state_machine, game, send_payload=True):
    """Draws the timeouts sections of the OLED display."""
    if game.selected_profile == "Ultimate Pool":
        return

    # player_1 timeouts
    display.display_clear(oled, "p1_timeouts", send_payload=False)
    if game.player_1_timeouts_remaining > 1:
        display.draw_rect_in_region(oled, "p1_timeout_counter_1", fill=True, clear=False)
        display.draw_rect_in_region(oled, "p1_timeout_counter_2", fill=True, clear=False)
    elif game.player_1_timeouts_remaining == 1:
        display.draw_rect_in_region(oled, "p1_timeout_single", fill=True, clear=False)

    # player_2 timeouts
    display.display_clear(oled, "p2_timeouts", send_payload=False)
    if game.player_2_timeouts_remaining > 1:
        display.draw_rect_in_region(oled, "p2_timeout_counter_1", fill=True, clear=False)
        display.draw_rect_in_region(oled, "p2_timeout_counter_2", fill=True, clear=False)
    elif game.player_2_timeouts_remaining == 1:
        display.draw_rect_in_region(oled, "p2_timeout_single", fill=True, clear=False)


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
    # Individual digits
    d1_new, d2_new = divmod(m_new, 10)
    d3_new, d4_new = divmod(s_new, 10)

    m_old, s_old = divmod(old_val, 60) if old_val is not None else (-1, -1)
    d1_old, d2_old = divmod(m_old, 10) if old_val is not None else (-1, -1)
    d3_old, d4_old = divmod(s_old, 10) if old_val is not None else (-1, -1)

    new_digits = [d1_new, d2_new, d3_new, d4_new]
    old_digits = [d1_old, d2_old, d3_old, d4_old]

    if new_shifted:
        suffix = "_s"
        colon_region = "match_clock_colon_s"
    else:
        suffix = ""
        colon_region = "match_clock_colon"

    if force_all:
        # If we are transitioning or forcing, clear the widest possible area
        # to remove artifacts. This is safe because
        # _render_ultimate_pool_shooter_indicators redraws indicators after.
        display.display_clear(oled, "match_clock_full", send_payload=False)
        # Manually draw colon
        display.draw_text_in_region(
            oled, colon_region, ":", align="center", send_payload=False
        )

    for i in range(4):
        # Skip the first digit (minutes tens) if we are in shifted mode (< 10 mins)
        if new_shifted and i == 0:
            continue

        if force_all or (new_digits[i] != old_digits[i]):
            region_key = f"match_clock_digit_{i+1}{suffix}"

            display.draw_text_in_region(
                oled, region_key, str(new_digits[i]), align="center", send_payload=False
            )

    game.prev_match_countdown = new_val
    if send_payload:
        oled.show()


def _render_ultimate_pool_shooter_indicators(
    oled, state_machine, game, force_match_timer
):
    """Draws shooter indicators for Ultimate Pool centered in the gaps."""
    # Render Match Timer
    render_match_timer(
        oled, state_machine, game, force_all=force_match_timer, send_payload=False
    )

    # Clear indicators. Only clear shifted ones when in shifted
    # mode to avoid timer collision.
    regions_to_clear = ["up_indicator_1", "up_indicator_2"]
    if game.match_countdown < 600:
        regions_to_clear.extend(["up_indicator_1_s", "up_indicator_2_s"])

    display.display_clear(oled, *regions_to_clear, send_payload=False)

    # Determine which regions to use based on shift
    suffix = "_s" if game.match_countdown < 600 else ""
    p1_key = f"up_indicator_1{suffix}"
    p2_key = f"up_indicator_2{suffix}"

    if game.player_1_shooting:
        display.draw_rect_in_region(oled, p1_key, fill=True, send_payload=False)
        display.draw_rect_in_region(oled, p2_key, fill=False, send_payload=False)
    else:
        display.draw_rect_in_region(oled, p1_key, fill=False, send_payload=False)
        display.draw_rect_in_region(oled, p2_key, fill=True, send_payload=False)


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
        display.draw_text_in_region(
            oled,
            "timeouts_mode_title",
            "Timeouts Mode",
            align="left",
            send_payload=False,
        )

    elif game.selected_profile in ["APA", "WNT", "BCA", "Ultimate Pool"]:
        if not suppress_scores:
            prefix = "up_" if game.selected_profile == "Ultimate Pool" else ""
            # Draw player_1 score/target_score
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_score",
                str(game.player_1_score),
                align="right",
                send_payload=False,
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_separator",
                "/",
                align="center",
                send_payload=False,
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_target",
                str(game.player_1_target),
                align="left",
                send_payload=False,
            )

            # Draw player_2 score/target_score
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_score",
                str(game.player_2_score),
                align="right",
                send_payload=False,
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_separator",
                "/",
                align="center",
                send_payload=False,
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_target",
                str(game.player_2_target),
                align="left",
                send_payload=False,
            )

        if game.selected_profile == "Ultimate Pool":
            # Don't render match timer or indicators in Menu or Exit Confirmation

            no_match_timer_states = [
                State_Machine.MENU,
                State_Machine.EDITING_VALUE,
                State_Machine.EXIT_MATCH_CONFIRMATION,
            ]

            if state_machine.state not in no_match_timer_states:
                _render_ultimate_pool_shooter_indicators(
                    oled, state_machine, game, force_match_timer
                )

        elif not suppress_scores:
            # Draw the current shooter indicator
            if game.player_1_shooting:
                display.draw_rect_in_region(
                    oled, "shooter_indicator_1", fill=True, send_payload=False
                )
                display.draw_rect_in_region(
                    oled, "shooter_indicator_2", fill=False, send_payload=False
                )
            else:
                display.draw_rect_in_region(
                    oled, "shooter_indicator_1", fill=False, send_payload=False
                )
                display.draw_rect_in_region(
                    oled, "shooter_indicator_2", fill=True, send_payload=False
                )

            # Draw timeouts indicators (Ultimate Pool handles its own indicators)
            if game.selected_profile != "Ultimate Pool":
                display_timeouts(oled, state_machine, game, False)

    if send_payload:
        oled.show()


async def enter_idle_mode(state_machine, game, oled):
    prev_state = state_machine.state
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)

    if game.selected_profile == "Ultimate Pool":
        if prev_state in [
            State_Machine.APA_GAME_TYPE_SELECTION,
            State_Machine.PROFILE_SELECTION,
        ]:
            display.display_clear(oled, "everything")
        else:
            display.display_clear(oled, "shot_clock_full")
    else:
        display.display_clear(oled, "everything")

    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        timer_str = display.process_timer_duration(game.countdown)
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_1",
            timer_str[0],
            font_size=8,
            align="center",
            send_payload=False,
        )
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_2",
            timer_str[1],
            font_size=8,
            align="center",
            send_payload=False,
        )
    else:
        game.speaker_5_count = 4

    render_scoreline(oled, state_machine, game, False)

    if game.break_shot:
        game.countdown = game.profile_based_countdown + game.extension_duration
    else:
        game.countdown = game.profile_based_countdown

    # Render Shot Clock Digits using regions
    timer_str = display.process_timer_duration(game.countdown)
    display.draw_text_in_region(
        oled,
        "shot_clock_digit_1",
        timer_str[0],
        font_size=8,
        align="center",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "shot_clock_digit_2",
        timer_str[1],
        font_size=8,
        align="center",
        send_payload=True,
    )


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
            timer_str = display.process_timer_duration(game.countdown)
            display.draw_text_in_region(
                oled,
                "shot_clock_digit_1",
                timer_str[0],
                font_size=8,
                align="center",
                send_payload=False,
            )
            display.draw_text_in_region(
                oled,
                "shot_clock_digit_2",
                timer_str[1],
                font_size=8,
                align="center",
                send_payload=False,
            )

        # Always update match timer (helper handles individual digit clearing)
        # EXCEPT in Menu or Exit Confirmation states to prevent overwriting them.
        no_match_timer_states = [
            State_Machine.MENU,
            State_Machine.EDITING_VALUE,
            State_Machine.EXIT_MATCH_CONFIRMATION,
        ]
        if state_machine.state not in no_match_timer_states:
            _render_ultimate_pool_shooter_indicators(oled, state_machine, game, False)
            oled.show()
        else:
            oled.show()
    else:
        timer_str = display.process_timer_duration(game.countdown)
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_1",
            timer_str[0],
            font_size=8,
            align="center",
            send_payload=False,
        )
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_2",
            timer_str[1],
            font_size=8,
            align="center",
            send_payload=True,
        )


async def render_profile_selection(state_machine, game, oled, clear_all=False):
    region = "everything" if clear_all else "profile_selection"
    display.display_clear(oled, region, send_payload=False)

    profile_list = game.profile_names
    idx = game.profile_selection_index
    name = profile_list[idx]

    display.draw_text_in_region(
        oled,
        "profile_title_selection",
        "Select Game:",
        align="center",
        send_payload=False,
    )
    if str(name) == "Ultimate Pool":
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value",
            "Ultimate",
            font_size=2,
            align="center",
            send_payload=False,
        )
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value_2",
            "Pool",
            font_size=2,
            align="center",
            send_payload=True,
        )
    elif str(name) == "Timeouts Mode":
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value",
            "Timeouts",
            font_size=2,
            align="center",
            send_payload=False,
        )
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value_2",
            "Mode",
            font_size=2,
            align="center",
            send_payload=True,
        )
    else:
        display.draw_text_in_region(
            oled,
            "profile_selection_value",
            str(name),
            font_size=3,
            align="center",
            send_payload=True,
        )


async def render_skill_level_selection(state_machine, game, oled, player_num):
    """Renders the skill level selection screen for a player."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "skill_level_player",
        f"Player {player_num}",
        align="center",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "skill_level_label",
        "Skill Level:",
        align="center",
        send_payload=False,
    )

    sl = game.temp_setting_value
    display.draw_text_in_region(
        oled,
        "skill_level_value",
        str(sl),
        font_size=3,
        align="center",
        send_payload=True,
    )


async def render_game_type_selection(state_machine, game, oled):
    """Renders the game type selection screen (8-Ball or 9-Ball)."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "game_type_title",
        "Select Game:",
        align="center",
        send_payload=False,
    )

    # temp_setting_value: 0 for 8-Ball, 1 for 9-Ball
    game_type = "9-Ball" if game.temp_setting_value == 1 else "8-Ball"
    display.draw_text_in_region(
        oled,
        "game_type_value",
        game_type,
        font_size=2,
        align="center",
        send_payload=True,
    )


async def render_wnt_target_selection(state_machine, game, oled):
    """Renders the WNT target selection screen."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "wnt_target_title",
        "Race to",
        align="center",
        send_payload=False,
    )

    target = game.temp_setting_value
    display.draw_text_in_region(
        oled,
        "wnt_target_value",
        str(target),
        font_size=3,
        align="center",
        send_payload=True,
    )


async def render_victory(state_machine, game, oled, winner_num):
    """Renders the victory screen."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "victory_title",
        "VICTORY!",
        font_size=2,
        align="center",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "victory_winner",
        f"Player {winner_num}",
        font_size=2,
        align="center",
        send_payload=False,
    )

    oled.show()


async def render_message(state_machine, game, oled, message, font_size=1):
    """Renders a generic message on the screen (e.g. for Confirmation)."""
    display.display_clear(oled, "everything", send_payload=False)

    rx, ry, rw, rh = display.get_region("confirmation_message")

    lines = message.split("\n")

    # Metrics
    base_w = 8
    base_h = 8
    char_width = base_w * font_size
    line_height = (base_h * font_size) + 4
    total_height = len(lines) * line_height

    # Vertical Start (centered within the confirmation_message region)
    y_pos = ry + (rh - total_height) // 2
    # Clamp to region top
    y_pos = max(y_pos, ry)

    for line in lines:
        # Horizontal Start
        text_width = len(line) * char_width
        x_pos = rx + (rw - text_width) // 2
        # Clamp to region left
        x_pos = max(x_pos, rx)

        oled.text_scaled(line, int(x_pos), int(y_pos), font_size)
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
    display.display_clear(oled, "everything", send_payload=False)

    # 2. Draw static Header
    display.draw_text_in_region(
        oled,
        "menu_header_left",
        "Game",
        font_size=2,
        align="left",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "menu_header_right",
        "Menu",
        font_size=2,
        align="left",
        send_payload=False,
    )
    display.draw_rect_in_region(oled, "menu_separator_top", fill=True, send_payload=False)
    display.draw_rect_in_region(
        oled, "menu_separator_bottom", fill=True, send_payload=False
    )

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

    # 4. Draw the menu items using dedicated regions
    display.draw_text_in_region(
        oled,
        "menu_line_prev",
        fmt(game.menu_items[prev_idx], val_prev),
        align="left",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "menu_line_curr",
        fmt(game.menu_items[game.current_menu_index], val_curr),
        align="left",
        send_payload=False,
    )
    display.draw_text_in_region(
        oled,
        "menu_line_next",
        fmt(game.menu_items[next_idx], val_next),
        align="left",
        send_payload=False,
    )

    # 5. Draw the cursor
    display.draw_rect_in_region(oled, "menu_cursor", fill=True)

    oled.show()


async def render_exit_confirmation(state_machine, game, oled):
    """Renders the 'Are you sure?' confirmation screen for exiting the match."""
    display.display_clear(oled, "everything", send_payload=False)
    display.draw_text_in_region(
        oled,
        "confirmation_message",
        "Are you sure?",
        align="center",
        send_payload=False,
    )
    oled.show()
