from lib import display
from lib.ui_components import render_scoreline

# Full Screen Screens/Dialogs


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
        display.TextOptions(align="center", send_payload=False),
    )
    if str(name) == "Ultimate Pool":
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value",
            "Ultimate",
            display.TextOptions(font_size=2, align="center", send_payload=False),
        )
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value_2",
            "Pool",
            display.TextOptions(font_size=2, align="center", send_payload=True),
        )
    elif str(name) == "Timeouts Mode":
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value",
            "Timeouts",
            display.TextOptions(font_size=2, align="center", send_payload=False),
        )
        display.draw_text_in_region(
            oled,
            "profile_selection_alt_value_2",
            "Mode",
            display.TextOptions(font_size=2, align="center", send_payload=True),
        )
    else:
        display.draw_text_in_region(
            oled,
            "profile_selection_value",
            str(name),
            display.TextOptions(font_size=3, align="center", send_payload=True),
        )


async def render_skill_level_selection(state_machine, game, oled, player_num):
    """Renders the skill level selection screen for a player."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "skill_level_player",
        f"Player {player_num}",
        display.TextOptions(align="center", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "skill_level_label",
        "Skill Level:",
        display.TextOptions(align="center", send_payload=False),
    )

    sl = game.temp_setting_value
    display.draw_text_in_region(
        oled,
        "skill_level_value",
        str(sl),
        display.TextOptions(font_size=3, align="center", send_payload=True),
    )


async def render_game_type_selection(state_machine, game, oled):
    """Renders the game type selection screen (8-Ball or 9-Ball)."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "game_type_title",
        "Select Game:",
        display.TextOptions(align="center", send_payload=False),
    )

    # temp_setting_value: 0 for 8-Ball, 1 for 9-Ball
    game_type = "9-Ball" if game.temp_setting_value == 1 else "8-Ball"
    display.draw_text_in_region(
        oled,
        "game_type_value",
        game_type,
        display.TextOptions(font_size=2, align="center", send_payload=True),
    )


async def render_wnt_target_selection(state_machine, game, oled):
    """Renders the WNT target selection screen."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "wnt_target_title",
        "Race to",
        display.TextOptions(align="center", send_payload=False),
    )

    target = game.temp_setting_value
    display.draw_text_in_region(
        oled,
        "wnt_target_value",
        str(target),
        display.TextOptions(font_size=3, align="center", send_payload=True),
    )


async def render_victory(state_machine, game, oled, winner_num):
    """Renders the victory screen."""
    display.display_clear(oled, "everything", send_payload=False)

    display.draw_text_in_region(
        oled,
        "victory_title",
        "VICTORY!",
        display.TextOptions(font_size=2, align="center", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "victory_winner",
        f"Player {winner_num}",
        display.TextOptions(font_size=2, align="center", send_payload=False),
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

    # Re-render scoreline at the bottom (except during shootout announcement)
    if not state_machine.shootout_announcement:
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
        display.TextOptions(font_size=2, align="left", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "menu_header_right",
        "Menu",
        display.TextOptions(font_size=2, align="left", send_payload=False),
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
        display.TextOptions(align="left", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "menu_line_curr",
        fmt(game.menu_items[game.current_menu_index], val_curr),
        display.TextOptions(align="left", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "menu_line_next",
        fmt(game.menu_items[next_idx], val_next),
        display.TextOptions(align="left", send_payload=False),
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
        display.TextOptions(align="center", send_payload=False),
    )
    oled.show()


async def render_shootout_announcement(state_machine, game, oled, visible=True):
    """Renders the '6-ball shootout' announcement."""
    if not visible:
        display.display_clear(oled, "everything")
        return

    await render_message(state_machine, game, oled, "6 Ball\nShootout", font_size=2)


async def render_shootout_stopwatch(state_machine, game, oled, current_ms):
    """Renders the shootout stopwatch and time-to-beat for P2."""
    display.display_clear(oled, "everything", send_payload=False)
    current_shooter = 1
    if state_machine.shootout_p2_wait or state_machine.shootout_p2_running:
        current_shooter = 2
    current_ms = 0 if state_machine.shootout_p2_wait else current_ms

    time_str = display.format_stopwatch(current_ms)
    # Draw stopwatch slightly higher than center
    display.draw_text_in_region(
        oled,
        "up_shootout_current_shooter",
        f"Player {current_shooter}",
        display.TextOptions(font_size=2, align="center", y_offset=-2, send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "up_shootout_stop_watch",
        time_str,
        display.TextOptions(font_size=2, align="center", send_payload=False),
    )

    # If it's P2's turn (WAIT or RUNNING), show P1's time to beat at the bottom
    if (
        state_machine.shootout_p2_wait or state_machine.shootout_p2_running
    ) and game.p1_shootout_time > 0:
        player_str = "Time to beat"
        beat_str = display.format_stopwatch(game.p1_shootout_time)
        display.draw_text_in_region(
            oled,
            "up_shootout_p1_title",
            player_str,
            display.TextOptions(font_size=1, align="center", send_payload=False),
        )
        display.draw_text_in_region(
            oled,
            "up_shootout_p1_time",
            beat_str,
            display.TextOptions(font_size=1, align="center", send_payload=False),
        )

    oled.show()
