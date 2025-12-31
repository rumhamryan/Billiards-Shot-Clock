import _thread

import uasyncio as asyncio
import utime

import lib.button_logic as logic

# Internal Library Imports
from lib import Pico_OLED_242, audio, display
from lib.button_interrupt import AsyncButton
from lib.hardware_config import DOWN_PIN, MAKE_PIN, MISS_PIN, UP_PIN
from lib.models import Game_Stats, State_Machine

# --- Global Initialization ---
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()
inactivity_check = utime.ticks_ms()


# --- Background Timer Task ---
async def timer_worker():  # noqa: PLR0912, PLR0915
    """
    Background task that handles the countdown timer and flashing independently.
    Replaces original timer_worker.
    """
    global inactivity_check
    last_tick = utime.ticks_ms()
    flash_checker = utime.ticks_ms()
    flash_off = False

    blink_checker = utime.ticks_ms()
    blink_off = False

    while True:
        now = utime.ticks_ms()

        # 1. Handle Countdown Logic
        if state_machine.countdown_in_progress:
            inactivity_check = now  # Reset inactivity while clock is running
            if utime.ticks_diff(now, last_tick) > 1000:
                last_tick = now

                # Track digits to selectively clear display
                curr_tens, curr_units = game.countdown // 10, game.countdown % 10
                game.countdown -= 1
                new_tens, new_units = game.countdown // 10, game.countdown % 10

                # Audio Beep
                if 0 <= game.countdown < 5 and not game.speaker_muted:
                    _thread.start_new_thread(audio.shot_clock_beep, ())

                # Display Update with selective clearing
                if game.countdown >= 0:
                    if curr_tens != new_tens and curr_units != new_units:
                        display.display_clear(
                            OLED, "shot_clock_digit_1", "shot_clock_digit_2"
                        )
                        display.display_text(
                            OLED,
                            state_machine,
                            display.process_timer_duration(game.countdown),
                            0,
                            0,
                            8,
                        )
                    elif curr_tens != new_tens:
                        display.display_clear(OLED, "shot_clock_digit_1")
                        display.display_text(OLED, state_machine, str(new_tens), 0, 0, 8)
                    elif curr_units != new_units:
                        display.display_clear(OLED, "shot_clock_digit_2")
                        display.display_text(
                            OLED, state_machine, str(new_units), 60, 0, 8
                        )

                # Zero Check
                if game.countdown == 0:
                    state_machine.update_state(State_Machine.COUNTDOWN_COMPLETE)
                    if game.selected_profile == "APA":
                        game.extension_available, game.extension_used = True, False

        # 2. Handle Flashing (Time Over)
        elif (
            state_machine.countdown_complete
            and utime.ticks_diff(now, flash_checker) > 330
        ):
            flash_checker = now
            if flash_off:
                display.display_text(
                    OLED,
                    state_machine,
                    display.process_timer_duration(game.countdown),
                    0,
                    0,
                    8,
                )
                flash_off = False
            else:
                display.display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
                flash_off = True

        # 3. Handle Other Blinking (Menu / Profile Select)
        if (
            state_machine.profile_selection
            or state_machine.menu
            or state_machine.editing_value
        ) and utime.ticks_diff(now, blink_checker) > 500:
            blink_checker = now
            blink_off = not blink_off

            if (
                state_machine.profile_selection
                and utime.ticks_diff(now, inactivity_check) > 500
            ):
                # Only blink after a short period of inactivity
                if blink_off:
                    display.display_clear(OLED, "profile_selection")
                else:
                    await display.render_profile_selection(state_machine, game, OLED)

            elif state_machine.menu:
                # Blink the cursor square
                if blink_off:
                    display.display_clear(OLED, "menu_selector")
                else:
                    display.display_shape(OLED, "rect", 8, 40, 8, 8, True)

            elif state_machine.editing_value:
                # Blink the cursor square even faster or differently?
                # Keep it simple for now
                if blink_off:
                    display.display_clear(OLED, "menu_selector")
                else:
                    display.display_shape(OLED, "rect", 8, 40, 8, 8, True)

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
    inactivity_check = utime.ticks_ms()
    await logic.handle_miss(state_machine, game, hw_wrapper)


# --- Hardware Wrapper ---
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

    async def render_profile_selection(self, sm, g):
        await display.render_profile_selection(sm, g, self.oled)

    async def render_menu(self, sm, g):
        await display.render_menu(sm, g, self.oled)


hw_wrapper = HardwareWrapper(OLED)


# --- Main Entry Point ---
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
