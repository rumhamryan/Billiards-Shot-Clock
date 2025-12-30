from machine import Pin # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore
import uasyncio as asyncio # type: ignore

# Internal Library Imports
from lib.shot_clock_config import (
    MAKE_PIN, UP_PIN, DOWN_PIN, MISS_PIN, DEBOUNCE_DELAY
)
from lib.shot_clock_models import State_Machine, Game_Stats
from lib.shot_clock_hw import (
    display_text, display_shape, display_clear, 
    process_timer_duration, shot_clock_beep
)

# --- Hardware Setup ---
make_button = Pin(MAKE_PIN, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(UP_PIN, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(DOWN_PIN, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(MISS_PIN, Pin.IN, Pin.PULL_DOWN)

# --- State Initialization ---
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()

# --- Background Tasks ---
async def timer_worker():
    """
    Background task that handles the countdown timer and flashing independently.
    """
    countdown_checker = utime.ticks_ms()
    flash_checker = utime.ticks_ms()
    flash_off = False

    while True:
        # Only run if the shot clock is active
        if state_machine.countdown_in_progress:
            if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 1000:
                current_tens, current_units = game.countdown // 10, game.countdown % 10
                game.countdown -= 1
                new_tens, new_units = game.countdown // 10, game.countdown % 10

                if game.countdown < 5 and not game.speaker_muted and game.countdown >= 0:
                    _thread.start_new_thread(shot_clock_beep, ())

                if game.countdown >= 0:
                    if current_tens != new_tens and current_units != new_units:
                        display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
                        display_text(OLED, state_machine, process_timer_duration(game.countdown), 0, 0, 8)
                    elif current_tens != new_tens:
                        display_clear(OLED, "shot_clock_digit_1")
                        display_text(OLED, state_machine, str(new_tens), 0, 0, 8)
                    elif current_units != new_units:
                        display_clear(OLED, "shot_clock_digit_2")
                        display_text(OLED, state_machine, str(new_units), 60, 0, 8)

                if game.countdown == 0:
                    state_machine.update_state(State_Machine.COUNTDOWN_COMPLETE)
                    if game.selected_profile == "APA":
                        game.extension_available, game.extension_used = True, False
                
                countdown_checker = utime.ticks_ms()

        # Handle flashing when countdown is complete
        elif state_machine.countdown_complete:
            if utime.ticks_diff(utime.ticks_ms(), flash_checker) > 330:
                flash_checker = utime.ticks_ms()
                if flash_off:
                    display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
                    flash_off = False
                else:
                    display_text(OLED, state_machine, process_timer_duration(game.countdown), 0, 0, 8)
                    flash_off = True

        await asyncio.sleep_ms(10)

# --- Helpers ---
last_press_time = 0

def debounce_handler(pin):
    global last_press_time
    current_time = utime.ticks_ms()
    if (current_time - last_press_time) > DEBOUNCE_DELAY:
        print(f"Button pressed: {pin}")
        last_press_time = current_time

# Interrupts
for btn in [make_button, up_button, down_button, miss_button]:
    btn.irq(trigger=Pin.IRQ_FALLING, handler=debounce_handler)

async def wait_for_release_async(pin):
    while pin.value():
        await asyncio.sleep_ms(10)

# --- Game Functions ---
async def idle_mode():
    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(OLED, state_machine, process_timer_duration(game.countdown), 0, 0, 8, False)
        display_text(OLED, state_machine, "Timeouts Mode", 12, 57, 1)
    else:
        state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
        game.speaker_5_count = 4
        display_text(OLED, state_machine, f"Inning:{int(game.inning_counter)}", 0, 57, 1, False)
        display_text(OLED, state_machine, f"Rack:{int(game.rack_counter)}", 72, 57, 1)

        if game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(OLED, state_machine, process_timer_duration(game.countdown), 0, 0, 8)

    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)

async def shot_clock():
    """
    Main controller for the shot clock phase. 
    State is managed here, but the timer is handled by timer_worker.
    """
    state_machine.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)

    if game.inning_counter % 1 == 0:
        game.player_1_shooting = True
        game.player_2_shooting = False
    else:
        game.player_1_shooting = False
        game.player_2_shooting = True

    while state_machine.countdown_in_progress or state_machine.countdown_complete:
        if make_button.value():
            await wait_for_release_async(make_button)
            game.countdown = game.profile_based_countdown
            if game.selected_profile == "APA":
                game.extension_available, game.extension_used = True, False
            display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
            game.break_shot = False
            return await idle_mode()
        
        if up_button.value() and state_machine.countdown_in_progress:
            await wait_for_release_async(up_button)
            p1_can = game.player_1_shooting and game.player_1_extension_available
            p2_can = game.player_2_shooting and game.player_2_extension_available
            
            if (game.selected_profile in ["WNT", "BCA"]) and (p1_can or p2_can):
                if game.player_1_shooting: game.player_1_extension_available = False
                else: game.player_2_extension_available = False
                game.countdown += game.extension_duration
            elif game.selected_profile not in ["WNT", "BCA"]:
                game.extension_used, game.extension_available = True, False
                game.countdown += game.extension_duration
            
            display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
            display_text(OLED, state_machine, process_timer_duration(game.countdown), 0, 0, 8)

        if miss_button.value():
            await wait_for_release_async(miss_button)
            game.countdown = game.profile_based_countdown
            game.inning_counter += 0.5
            display_clear(OLED, "shot_clock_digit_1", "shot_clock_digit_2")
            if game.inning_counter - 0.5 != int(game.inning_counter):
                display_clear(OLED, "inning_counter")
            game.break_shot = False
            return await idle_mode()
        
        await asyncio.sleep_ms(10)

async def select_game_profile():
    inactivity_check = utime.ticks_ms()
    countdown_checker = utime.ticks_ms()
    off = False
    list_traverser = 1
    profile_list = list(game.game_profiles)
    profile_list_length = len(profile_list) - 1
    display_text(OLED, state_machine, "Select Game:", 15, 10, 1)
    
    while True:
        if utime.ticks_diff(utime.ticks_ms(), inactivity_check) > 500:
            if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 500:
                countdown_checker = utime.ticks_ms()
                if off:
                    display_clear(OLED, "profile_selection")
                    off = False
                else:
                    display_text(OLED, state_machine, str(profile_list[list_traverser]), 25, 30, 3)
                    off = True
        else:
            display_text(OLED, state_machine, str(profile_list[list_traverser]), 25, 30, 3)

        if make_button.value():
            await wait_for_release_async(make_button)
            display_clear(OLED, "everything")
            game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
            game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
            game.selected_profile = profile_list[list_traverser]
            game.timeouts_only = (game.extension_duration == 0)
            state_machine.game_on = True
            game.menu_values = [game.rack_counter, game.speaker_muted, int(game.inning_counter)]
            return await idle_mode()
        
        if up_button.value() or down_button.value():
            btn = up_button if up_button.value() else down_button
            await wait_for_release_async(btn)
            step = 1 if btn == up_button else -1
            list_traverser = (list_traverser + step) % (profile_list_length + 1)
            display_clear(OLED, "profile_selection")
            inactivity_check = utime.ticks_ms()
        
        await asyncio.sleep_ms(10)

async def game_menu():
    if not state_machine.shot_clock_idle: return
    state_machine.update_state(State_Machine.MENU)
    display_clear(OLED, "everything")
    
    game.current_menu_index = game.menu_items.index("Rack")
    inning_before, rack_before, mute_before = game.inning_counter, game.rack_counter, game.speaker_muted
    
    display_text(OLED, state_machine, "Game", 0, 2, 2, False)
    display_text(OLED, state_machine, "Menu", 66, 2, 2, False)
    display_shape(OLED, "line", 0, 19, 128, 19, False)
    display_shape(OLED, "line", 0, 20, 128, 20, False)
    game.update_menu_selection(OLED, state_machine, display_clear, display_text, display_shape, clear_before_payload=False)
    
    cursor_checker = utime.ticks_ms()
    off = False
    
    while True:
        if make_button.value():
            await wait_for_release_async(make_button)
            sub_inning, sub_rack, sub_mute = game.inning_counter, game.rack_counter, game.speaker_muted
            while True:
                if utime.ticks_diff(utime.ticks_ms(), cursor_checker) > 500:
                    cursor_checker = utime.ticks_ms()
                    if off: display_clear(OLED, "menu_selector"); off = False
                    else: display_shape(OLED, "rect", 8, 40, 8, 8); off = True

                if make_button.value():
                    await wait_for_release_async(make_button)
                    game.menu_values = [game.rack_counter, game.speaker_muted, int(game.inning_counter)]
                    break

                if up_button.value() or down_button.value():
                    btn = up_button if up_button.value() else down_button
                    await wait_for_release_async(btn)
                    step = 1 if btn == up_button else -1
                    sel = game.current_menu_selection[1]
                    if sel == "Inning":
                        display_clear(OLED, "menu_inning_counter")
                        game.inning_counter = max(1, game.inning_counter + step)
                        display_text(OLED, state_machine, str(int(game.inning_counter)), 80, 40, 1)
                    elif sel == "Rack":
                        display_clear(OLED, "menu_rack_counter")
                        game.rack_counter = max(1, game.rack_counter + step)
                        display_text(OLED, state_machine, str(game.rack_counter), 64, 40, 1)
                    elif sel == "Mute":
                        display_clear(OLED, "menu_mute_bool")
                        game.speaker_muted = not game.speaker_muted
                        display_text(OLED, state_machine, str(game.speaker_muted), 64, 40, 1)

                if miss_button.value():
                    await wait_for_release_async(miss_button)
                    game.inning_counter, game.rack_counter, game.speaker_muted = sub_inning, sub_rack, sub_mute
                    game.update_menu_selection(OLED, state_machine, display_clear, display_text, display_shape)
                    break
                await asyncio.sleep_ms(10)

        if up_button.value() or down_button.value():
            btn = up_button if up_button.value() else down_button
            await wait_for_release_async(btn)
            step = 1 if btn == down_button else -1
            game.current_menu_index = (game.current_menu_index + step) % len(game.menu_items)
            game.update_menu_selection(OLED, state_machine, display_clear, display_text, display_shape)

        if miss_button.value():
            await wait_for_release_async(miss_button)
            display_clear(OLED, "everything")
            if game.rack_counter != rack_before: game.break_shot = True
            return await idle_mode()
        
        await asyncio.sleep_ms(10)

async def main():
    asyncio.create_task(timer_worker()) # Start background timer
    await select_game_profile()
    while True:
        if make_button.value():
            await wait_for_release_async(make_button); await shot_clock()
        if up_button.value() or down_button.value():
            await wait_for_release_async(up_button if up_button.value() else down_button); await idle_mode()
        if miss_button.value():
            await wait_for_release_async(miss_button)
            if not game.selected_profile == "Timeouts Mode": await game_menu()
        await asyncio.sleep_ms(10)

# Start Program
try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    pass
finally:
    asyncio.new_event_loop()