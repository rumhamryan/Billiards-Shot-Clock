from lib import display
from lib.models import State_Machine

# Reusable UI Elements


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
            oled,
            colon_region,
            ":",
            display.TextOptions(align="center", send_payload=False),
        )

    for i in range(4):
        # Skip the first digit (minutes tens) if we are in shifted mode (< 10 mins)
        if new_shifted and i == 0:
            continue

        if force_all or (new_digits[i] != old_digits[i]):
            region_key = f"match_clock_digit_{i + 1}{suffix}"

            display.draw_text_in_region(
                oled,
                region_key,
                str(new_digits[i]),
                display.TextOptions(align="center", send_payload=False),
            )

    game.prev_match_countdown = new_val
    if send_payload:
        oled.show()


def render_ultimate_pool_shooter_indicators(oled, state_machine, game, force_match_timer):
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
            display.TextOptions(align="left", send_payload=False),
        )

    elif game.selected_profile in ["APA", "WNT", "BCA", "Ultimate Pool"]:
        if not suppress_scores:
            prefix = "up_" if game.selected_profile == "Ultimate Pool" else ""
            p1_x_offset = 1 if (game.player_1_score > 9 and prefix == "") else 0

            # Alignment Logic
            is_apa_8ball = (
                game.selected_profile == "APA"
                and getattr(game, "match_type", "") == "8-Ball"
            )

            alignment = "left" if prefix == "" and game.player_1_score < 10 else "right"

            shift = 6 if (prefix == "" and alignment == "left") else 0

            is_wnt_single_digit = (
                game.selected_profile == "WNT" and game.player_2_target < 10
            )
            p2_x_offset = 8 if (is_apa_8ball or is_wnt_single_digit) else 0

            # Draw player_1 score/target_score
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_score",
                str(game.player_1_score),
                display.TextOptions(
                    align=alignment, send_payload=False, x_offset=p1_x_offset
                ),
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_separator",
                "/",
                display.TextOptions(
                    align="center",
                    send_payload=False,
                    x_offset=p1_x_offset - shift,
                ),
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p1_target",
                str(game.player_1_target),
                display.TextOptions(
                    align="left",
                    send_payload=False,
                    x_offset=p1_x_offset - shift,
                ),
            )

            # Draw player_2 score/target_score
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_score",
                str(game.player_2_score),
                display.TextOptions(
                    align="right", send_payload=False, x_offset=p2_x_offset
                ),
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_separator",
                "/",
                display.TextOptions(
                    align="center", send_payload=False, x_offset=p2_x_offset
                ),
            )
            display.draw_text_in_region(
                oled,
                f"{prefix}p2_target",
                str(game.player_2_target),
                display.TextOptions(
                    align="left", send_payload=False, x_offset=p2_x_offset
                ),
            )

        if game.selected_profile == "Ultimate Pool":
            # Don't render match timer or indicators in Menu or Exit Confirmation

            no_match_timer_states = [
                State_Machine.MENU,
                State_Machine.EDITING_VALUE,
                State_Machine.EXIT_MATCH_CONFIRMATION,
            ]

            if state_machine.state not in no_match_timer_states:
                render_ultimate_pool_shooter_indicators(
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
