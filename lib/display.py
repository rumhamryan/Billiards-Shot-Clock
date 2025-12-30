import uasyncio as asyncio
from lib.hardware_config import DISPLAY_REGIONS
from lib.models import State_Machine

# --- Low Level Helpers ---

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

# --- High Level Logic Rendering ---

async def enter_idle_mode(state_machine, game, oled):
    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
    display_clear(oled, "everything")
    
    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8, False)
        display_text(oled, state_machine, "Timeouts Mode", 12, 57, 1)
    else:
        game.speaker_5_count = 4
        display_text(oled, state_machine, f"Inning:{int(game.inning_counter)}", 0, 57, 1, False)
        display_text(oled, state_machine, f"Rack:{int(game.rack_counter)}", 72, 57, 1)

        if game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(oled, state_machine, process_timer_duration(game.countdown), 0, 0, 8)

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

async def render_profile_selection(state_machine, game, oled):
    display_clear(oled, "profile_selection")
    
    profile_list = list(game.game_profiles)
    idx = game.profile_selection_index
    name = profile_list[idx]
    
    display_text(oled, state_machine, "Select Game:", 15, 10, 1, False)
    display_text(oled, state_machine, str(name), 25, 30, 3)

async def render_menu(state_machine, game, oled):
    display_clear(oled, "everything")
    
    # Header
    display_text(oled, state_machine, "Game", 0, 2, 2, False)
    display_text(oled, state_machine, "Menu", 66, 2, 2, False)
    display_shape(oled, "line", 0, 19, 128, 19, False)
    display_shape(oled, "line", 0, 20, 128, 20, False)
    
    # Using existing helper to draw list
    game.update_menu_selection(
        oled, state_machine, display_clear, display_text, display_shape, 
        send_payload=True, clear_before_payload=False
    )
    
    # Cursor Logic
    if state_machine.editing_value:
        # Show a solid indicator or highlight when editing
        display_shape(oled, "rect", 8, 40, 8, 8, True)
        # Clear the value area of the middle item and draw the temp value
        display_clear(oled, "menu_items", send_payload=False) # Clear items area
        # Re-draw with the temp value for the selected item
        prev_idx = (game.current_menu_index - 1) % len(game.menu_items)
        next_idx = (game.current_menu_index + 1) % len(game.menu_items)
        
        display_text(oled, state_machine, f"{game.menu_items[prev_idx]}:{game.menu_values[prev_idx]}", 24, 24, 1, False)
        display_text(oled, state_machine, f"{game.menu_items[game.current_menu_index]}:{game.temp_setting_value}", 24, 40, 1, False)
        display_text(oled, state_machine, f"{game.menu_items[next_idx]}:{game.menu_values[next_idx]}", 24, 56, 1, True)
    else:
        # Normal cursor
        display_shape(oled, "rect", 8, 40, 8, 8, True)
