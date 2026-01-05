from lib import display
from lib.models import State_Machine
from lib.ui_components import render_scoreline, render_ultimate_pool_shooter_indicators

# Gameplay Transitions and Dynamic Updates


async def enter_idle_mode(state_machine, game, oled):
    prev_state = state_machine.state
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)

    if game.selected_profile == "Ultimate Pool":
        if prev_state in [
            State_Machine.APA_GAME_TYPE_SELECTION,
            State_Machine.PROFILE_SELECTION,
            State_Machine.MENU,
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
            display.TextOptions(font_size=8, align="center", send_payload=False),
        )
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_2",
            timer_str[1],
            display.TextOptions(font_size=8, align="center", send_payload=False),
        )
    else:
        game.speaker_5_count = 4

    render_scoreline(
        oled, state_machine, game, send_payload=False, force_match_timer=True
    )

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
        display.TextOptions(font_size=8, align="center", send_payload=False),
    )
    display.draw_text_in_region(
        oled,
        "shot_clock_digit_2",
        timer_str[1],
        display.TextOptions(font_size=8, align="center", send_payload=True),
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
            State_Machine.SHOOTOUT_ANNOUNCEMENT,
            State_Machine.SHOOTOUT_P1_WAIT,
            State_Machine.SHOOTOUT_P1_RUNNING,
            State_Machine.SHOOTOUT_P2_WAIT,
            State_Machine.SHOOTOUT_P2_RUNNING,
        ]

        if state_machine.state not in overlay_states:
            # Clear and update shot clock
            timer_str = display.process_timer_duration(game.countdown)
            display.draw_text_in_region(
                oled,
                "shot_clock_digit_1",
                timer_str[0],
                display.TextOptions(font_size=8, align="center", send_payload=False),
            )
            display.draw_text_in_region(
                oled,
                "shot_clock_digit_2",
                timer_str[1],
                display.TextOptions(font_size=8, align="center", send_payload=False),
            )

        # Always update match timer (helper handles individual digit clearing)
        # EXCEPT in Menu or Exit Confirmation states to prevent overwriting them.
        no_match_timer_states = [
            State_Machine.MENU,
            State_Machine.EDITING_VALUE,
            State_Machine.EXIT_MATCH_CONFIRMATION,
            State_Machine.SHOOTOUT_ANNOUNCEMENT,
            State_Machine.SHOOTOUT_P1_WAIT,
            State_Machine.SHOOTOUT_P1_RUNNING,
            State_Machine.SHOOTOUT_P2_WAIT,
            State_Machine.SHOOTOUT_P2_RUNNING,
        ]
        if state_machine.state not in no_match_timer_states:
            render_ultimate_pool_shooter_indicators(oled, state_machine, game, False)
            oled.show()
        else:
            oled.show()
    else:
        timer_str = display.process_timer_duration(game.countdown)
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_1",
            timer_str[0],
            display.TextOptions(font_size=8, align="center", send_payload=False),
        )
        display.draw_text_in_region(
            oled,
            "shot_clock_digit_2",
            timer_str[1],
            display.TextOptions(font_size=8, align="center", send_payload=True),
        )
