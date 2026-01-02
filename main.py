import _thread

import uasyncio as asyncio
import utime

import lib.button_logic as logic

# Internal Library Imports
from lib import Pico_OLED_242, audio, display
from lib.button_interrupt import AsyncButton
from lib.hardware_config import DOWN_PIN, MAKE_PIN, MISS_PIN, UP_PIN
from lib.models import Game_Stats, State_Machine

# Global Initialization
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()
inactivity_check = utime.ticks_ms()


# Background Timer Helpers


def _update_clock_display(curr_val, new_val):
    """Handles the selective clearing and updating of the countdown digits."""
    if new_val < 0:
        return

    curr_tens, curr_units = curr_val // 10, curr_val % 10
    new_tens, new_units = new_val // 10, new_val % 10
    if curr_tens != new_tens and curr_units != new_units:
        display.display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
        display.display_text(
            OLED, state_machine, display.process_timer_duration(new_val), 0, 0, 8
        )
    elif curr_tens != new_tens:
        display.display_clear(OLED, "shot_clock_digit_1")
        display.display_text(OLED, state_machine, str(new_tens), 0, 0, 8)
    elif curr_units != new_units:
        display.display_clear(OLED, "shot_clock_digit_2")
        display.display_text(OLED, state_machine, str(new_units), 60, 0, 8)


def _handle_countdown_tick():
    """Logic executed every 1 second during active countdown."""
    global inactivity_check
    inactivity_check = utime.ticks_ms()
    old_val = game.countdown
    game.countdown -= 1
    new_val = game.countdown
    # Audio trigger

    if 0 <= new_val < 5 and not game.speaker_muted:
        _thread.start_new_thread(audio.shot_clock_beep, ())

    _update_clock_display(old_val, new_val)

    if new_val == 0:
        state_machine.update_state(State_Machine.COUNTDOWN_COMPLETE)
        if game.selected_profile == "APA":
            game.extension_available, game.extension_used = True, False


def _handle_expired_flash(flash_off):
    """Toggle the '00' display when time has expired."""
    if flash_off:
        display.display_text(
            OLED, state_machine, display.process_timer_duration(game.countdown), 0, 0, 8
        )
    else:
        display.display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
    return not flash_off


async def _handle_ui_blink(blink_off):
    """Manages blinking for menu cursor and profile selection."""
    if (
        state_machine.profile_selection
        and utime.ticks_diff(utime.ticks_ms(), inactivity_check) > 500
    ):
        if blink_off:
            display.display_clear(OLED, "profile_selection")

        else:
            await display.render_profile_selection(state_machine, game, OLED)

    elif state_machine.menu or state_machine.editing_value:
        if blink_off:
            display.display_clear(OLED, "menu_selector")

        else:
            display.display_shape(OLED, "rect", 8, 40, 8, 8, True)

    elif state_machine.victory:
        if blink_off:
            display.display_clear(OLED, "everything")
        else:
            # We don't easily know who won here, but render_victory was called.
            # We can just re-render or assume the winner is stored.
            # For simplicity, let's just not clear it if we want it to blink.
            # Actually, render_victory is async, we can call it if we store winner.
            # Let's just store the winner in Game_Stats for blinking.
            winner = 1 if game.player_1_score >= game.player_1_target else 2
            await display.render_victory(state_machine, game, OLED, winner)

    return not blink_off


# Background Timer Task
async def timer_worker():
    """
    Main heartbeat loop. Dispatches to helpers based on timing and state.
    """
    last_tick = utime.ticks_ms()
    flash_checker = utime.ticks_ms()
    blink_checker = utime.ticks_ms()
    flash_off = False
    blink_off = False

    while True:
        now = utime.ticks_ms()
        # 1. Ticking Countdown
        if (
            state_machine.countdown_in_progress
            and utime.ticks_diff(now, last_tick) > 1000
        ):
            last_tick = now
            _handle_countdown_tick()

        # 2. Expired Flashing
        elif (
            state_machine.countdown_complete
            and utime.ticks_diff(now, flash_checker) > 330
        ):
            flash_checker = now
            flash_off = _handle_expired_flash(flash_off)

        # 3. UI Blinking
        if (
            state_machine.profile_selection
            or state_machine.menu
            or state_machine.editing_value
            or state_machine.victory
        ) and utime.ticks_diff(now, blink_checker) > 500:
            blink_checker = now
            blink_off = await _handle_ui_blink(blink_off)

        await asyncio.sleep_ms(50)


# --- Button Handlers (Bridge) ---
# We need to update inactivity_check on any button press


async def on_make():
    global inactivity_check
    inactivity_check = utime.ticks_ms()
    await logic.handle_make(state_machine, game, hw_wrapper)


async def on_up():
    global inactivity_check
    inactivity_check = utime.ticks_ms()
    await logic.handle_up(state_machine, game, hw_wrapper)


async def on_down():
    global inactivity_check
    inactivity_check = utime.ticks_ms()
    await logic.handle_down(state_machine, game, hw_wrapper)


async def on_miss():
    global inactivity_check
    if not state_machine.profile_selection:
        inactivity_check = utime.ticks_ms()
    await logic.handle_miss(state_machine, game, hw_wrapper)


# Hardware Wrapper
# Logic module expects an object with methods like enter_idle_mode.
# We create a simple wrapper or just pass the module if signature matches.
# The logic module calls: hw_module.enter_idle_mode(state_machine, game)
# Our hw module functions are: enter_idle_mode(state_machine, game, oled)
# We need a partial binding or a wrapper class.


class HardwareWrapper:
    def __init__(self, oled):
        self.oled = oled

    async def enter_idle_mode(self, sm, g):
        await display.enter_idle_mode(sm, g, self.oled)

    async def enter_shot_clock(self, sm, g):
        await display.enter_shot_clock(sm, g, self.oled)

    async def update_timer_display(self, sm, g):
        await display.update_timer_display(sm, g, self.oled)

    async def render_profile_selection(self, sm, g, clear_all=False):
        await display.render_profile_selection(sm, g, self.oled, clear_all=clear_all)

    async def render_menu(self, sm, g):
        await display.render_menu(sm, g, self.oled)

    async def render_exit_confirmation(self, sm, g):
        await display.render_exit_confirmation(sm, g, self.oled)

    async def render_skill_level_selection(self, sm, g, player_num):
        await display.render_skill_level_selection(sm, g, self.oled, player_num)

    async def render_game_type_selection(self, sm, g):
        await display.render_game_type_selection(sm, g, self.oled)

    async def render_victory(self, sm, g, winner_num):
        await display.render_victory(sm, g, self.oled, winner_num)

    async def render_message(self, sm, g, message, font_size=1):
        await display.render_message(sm, g, self.oled, message, font_size)


hw_wrapper = HardwareWrapper(OLED)


# Main Entry Point
async def main():
    # 1. Initialize Inputs
    AsyncButton(MAKE_PIN, on_make)
    AsyncButton(UP_PIN, on_up)
    AsyncButton(DOWN_PIN, on_down)
    AsyncButton(MISS_PIN, on_miss)

    # 2. Start Background Timer
    asyncio.create_task(timer_worker())

    # 3. Initial Display
    state_machine.update_state(State_Machine.PROFILE_SELECTION)
    await display.render_profile_selection(state_machine, game, OLED)

    # 4. The Infinite Wait
    while True:
        await asyncio.sleep(1)


# Start Program
try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    pass
finally:
    # Reset/Cleanup if needed
    asyncio.new_event_loop()
