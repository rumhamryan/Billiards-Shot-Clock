from machine import I2S, Pin, PWM # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore
import uasyncio as asyncio # type: ignore

# --- Constants ---
# Pin Definitions
MAKE_PIN = 16
UP_PIN = 17
DOWN_PIN = 18
MISS_PIN = 19

# Audio Settings
I2S_ID = 0
I2S_SCK = Pin(11)
I2S_WS = Pin(12)
I2S_SD = Pin(10)
I2S_RATE = 48000
I2S_BITS = 16

# OLED Regions (x, y, width, height)
DISPLAY_REGIONS = {
    "everything": (0, 0, 128, 64),
    "profile_selection": (0, 20, 128, 44),
    "inning_counter": (55, 55, 17, 9),
    "rack_counter": (113, 57, 14, 8),
    "shot_clock_full": (0, 0, 125, 56),
    "shot_clock_digit_1": (0, 0, 62, 56),
    "shot_clock_digit_2": (62, 0, 66, 56),
    "menu_selector": (8, 24, 8, 64),
    "menu_items": (24, 24, 80, 40),
    "menu_inning_counter": (80, 40, 17, 8),
    "menu_rack_counter": (64, 40, 17, 8),
    "menu_mute_bool": (64, 40, 40, 8),
}

# Set up the GPIO pins as input with pull-down resistors
make_button = Pin(MAKE_PIN, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(UP_PIN, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(DOWN_PIN, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(MISS_PIN, Pin.IN, Pin.PULL_DOWN)

# Define debounce delay in milliseconds
DEBOUNCE_DELAY = 200

# Last time the button was pressed
last_press_time = 0

def debounce_handler(pin):
    """
    Handles button debounce to prevent multiple triggers from a single press.

    Args:
        pin (machine.Pin): The pin object associated with the button press.

    Behavior:
        - Checks if the button press occurs outside the debounce window (200ms).
        - If valid, logs the button press and updates the last press time.
    """
    global last_press_time
    current_time = utime.ticks_ms()

    # Check if the current press is outside the debounce window
    if (current_time - last_press_time) > DEBOUNCE_DELAY:
        print(f"Button pressed: {pin}")
        print("")
        last_press_time = current_time

# Attach interrupt handlers to each button with the debounce handler
make_button.irq(trigger=Pin.IRQ_FALLING, handler=debounce_handler)
up_button.irq(trigger=Pin.IRQ_FALLING, handler=debounce_handler)
down_button.irq(trigger=Pin.IRQ_FALLING, handler=debounce_handler)
miss_button.irq(trigger=Pin.IRQ_FALLING, handler=debounce_handler)

class State_Machine:
    """
    Class to manage the state of the device during the game.

    Behavior:
        - Tracks and updates the current game state such as profile selection, shot clock, and game status.
    """
    PROFILE_SELECTION = "profile_selection"
    SHOT_CLOCK_IDLE = "shot_clock_idle"
    COUNTDOWN_IN_PROGRESS = "countdown_in_progress"
    COUNTDOWN_COMPLETE = "countdown_complete"
    MENU = "menu"

    def __init__(self, initial_state=PROFILE_SELECTION):
        """
        Initializes the state machine with an initial state.

        Args:
            initial_state (str): The starting state of the machine.
        """
        self.state = initial_state
        self.game_on = False

    def update_state(self, new_state):
        """
        Updates the current state of the machine.

        Args:
            new_state (str): The state to transition to.
        """
        self.state = new_state

    @property
    def profile_selection(self):
        return self.state == self.PROFILE_SELECTION

    @property
    def shot_clock_idle(self):
        return self.state == self.SHOT_CLOCK_IDLE

    @property
    def countdown_in_progress(self):
        return self.state == self.COUNTDOWN_IN_PROGRESS

    @property
    def countdown_complete(self):
        return self.state == self.COUNTDOWN_COMPLETE

    @property
    def menu(self):
        return self.state == self.MENU

class Game_Stats:
    """
    Class to track and manage game statistics and settings.

    Behavior:
        - Stores and manages various game-related statistics such as countdown timers, player status, game profiles, and speaker status.
        - Facilitates updating and retrieving game state information during play.
    """
    def __init__(self, profile_based_countdown = 0, countdown = 0, extension_duration = 0, extension_available = True, extension_used = False, player_1_shooting=True, player_1_extension_available=True, player_2_shooting=False, player_2_extension_available=True, inning_counter= 1.0, rack_counter = 1, break_shot = True, 
                 speaker_muted = False, speaker_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 20, "extension_duration": 25}, 
                                  "WNT": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45},
                                  "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}},
                 selected_profile = None, timeouts_only = False,
                 menu_items = ["Rack", "Mute", "Inning"],
                 menu_values = None,
                 current_menu_index = 0,
                 current_menu_selection = None,
                 current_menu_values = None):
        """
        Initializes the game statistics with default or provided values.

        Args:
            profile_based_countdown (int): Countdown based on the selected profile.
            countdown (int): Current countdown value.
            extension_duration (int): Duration of the extension.
            extension_available (bool): Indicates if the extension is available.
            extension_used (bool): Indicates if the extension has been used.
            player_1_shooting (bool): Indicates if player 1 is shooting.
            player_1_extension_available (bool): Indicates if player 1 has an extension available.
            player_2_shooting (bool): Indicates if player 2 is shooting.
            player_2_extension_available (bool): Indicates if player 2 has an extension available.
            inning_counter (float): Tracks the current inning.
            rack_counter (int): Tracks the current rack.
            break_shot (bool): Indicates if the current shot is a break shot.
            speaker_muted (bool): Indicates if the speaker is muted.
            speaker_5_count (int): Counter for speaker actions.
            game_profiles (dict): Dictionary of game profiles and their settings.
            selected_profile (str): The currently selected game profile.
            timeouts_only (bool): Indicates if the game is in timeouts mode.
            menu_items (list): List of menu items.
            menu_values (list): List of values corresponding to menu items.
            current_menu_index (int): Index of the current menu item.
            current_menu_selection (list): List tracking the previous, current, and next menu items.
            current_menu_values (list): List tracking the values corresponding to the previous, current, and next menu items.

        Behavior:
            - Initializes game statistics and settings based on the provided arguments.
            - Manages different aspects of game state, including player actions and countdown timers.
        """
        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.extension_available: bool = extension_available
        self.extension_used: bool = extension_used
        self.player_1_shooting: bool = player_1_shooting
        self.player_1_extension_available: bool = player_1_extension_available
        self.player_2_shooting: bool = player_2_shooting
        self.player_2_extension_available: bool = player_2_extension_available
        self.inning_counter: float = inning_counter
        self.rack_counter: int = rack_counter
        self.break_shot: bool = break_shot
        self.speaker_muted: bool = speaker_muted
        self.speaker_5_count: int = speaker_5_count
        self.game_profiles: dict = game_profiles
        self.selected_profile: str = selected_profile
        self.timeouts_only: bool = timeouts_only
        self.menu_items: list = menu_items
        self.menu_values: list = menu_values or [rack_counter, speaker_muted, int(inning_counter)]
        self.current_menu_index: int = current_menu_index
        self.current_menu_selection: list = current_menu_selection or [None, menu_items[current_menu_index], None]
        self.current_menu_values: list = current_menu_values or [None, self.menu_values[current_menu_index], None]

    def update_menu_selection(self, send_payload=True, clear_before_payload=True):
        """
        Updates the current_menu_selection list based on the current_menu_index.
        Displays the current selection along with its previous and next menu_items.

        Args:
            send_payload (bool): Whether to update the display.
            clear_before_payload (bool): Whether to clear the display before updating.

        Behavior:
            - Updates the menu selection and corresponding values.
            - Optionally updates the OLED display with the new selections.
        """
        # Set previous index, wrapping around if necessary
        prev_index = (self.current_menu_index - 1) % len(self.menu_items)

        # Set next index, wrapping around if necessary
        next_index = (self.current_menu_index + 1) % len(self.menu_items)

        # Update the current_menu_selection list
        self.current_menu_selection = [self.menu_items[prev_index], self.menu_items[self.current_menu_index], self.menu_items[next_index]]
        self.current_menu_values = [self.menu_values[prev_index], self.menu_values[self.current_menu_index], self.menu_values[next_index]]

        # Display the menu items
        if send_payload:
            if clear_before_payload:
                display_clear("menu_items")
            display_text(f"{self.current_menu_selection[0]}:{self.current_menu_values[0]}", 24, 24, 1, False)
            display_text(f"{self.current_menu_selection[1]}:{self.current_menu_values[1]}", 24, 40, 1, False)
            display_text(f"{self.current_menu_selection[2]}:{self.current_menu_values[2]}", 24, 56, 1, False)
            display_shape("rect", 8, 40, 8, 8, True)  # menu cursor

# Instantiate Classes
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()

async def wait_for_release_async(pin):
    """
    Asynchronously waits until the specified button is released.
    Allows other tasks to run while waiting.
    """
    while pin.value():
        await asyncio.sleep_ms(10)

def wait_for_release(pin):
    """
    Waits until the specified button is released.
    
    Args:
        pin (machine.Pin): The pin object associated with the button.
    """
    while pin.value():
        pass

def process_timer_duration(duration):
    """
    Processes the timer duration to ensure it is displayed with leading zeros if necessary.

    Args:
        duration (int): The duration to be processed.

    Returns:
        str: The processed duration as a string, with a leading zero if necessary.

    Behavior:
        - Converts an integer duration to a string with leading zeros for display purposes.
    """
    processed_integer = duration
    if processed_integer < 10:
        return (str(0) + str(processed_integer))
    else:
        return str(processed_integer)

def display_text(payload, x_coordinates, y_coordinates, font_size, send_payload=True):
    """
    Displays a text string on the OLED screen at specified coordinates with a given font size.

    Args:
        payload (str): The text to be displayed.
        x_coordinates (int): The x-coordinate on the screen.
        y_coordinates (int): The y-coordinate on the screen.
        font_size (int): The size of the font to be used.
        send_payload (bool, optional): If True, updates the OLED display to show the text. Defaults to True.

    Behavior:
        - Renders text on the OLED screen at the specified location with the specified font size.
        - Adjusts text positioning and font size for certain conditions, like when "Timeouts Mode" is selected.
        - If send_payload is False, withholds the `OLED.show()` command, allows stringing repeated calls together.
    """
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        x_coordinates = 0
        font_size = 2
        
    OLED.text_scaled(str(payload), x_coordinates, y_coordinates, font_size)
    
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        OLED.text_scaled("Mode", 32, 48, 2)
    
    if send_payload:
        OLED.show()

def display_shape(payload, x, y, width, height, send_payload=True):
    """
    Draws a shape on the OLED display based on the specified payload.

    Args:
        payload (str): The type of shape to draw. Options are "line" or "rect".
        x (int): The x-coordinate of the shape's starting position.
        y (int): The y-coordinate of the shape's starting position.
        width (int): The width of the shape. For "line", this represents the end x-coordinate.
        height (int): The height of the shape. For "line", this represents the end y-coordinate.
        send_payload (bool, optional): If True, updates the OLED display to show the drawn shape. Defaults to True.

    Behavior:
        - If payload is "line", a line is drawn from (x, y) to (width, height).
        - If payload is "rect", a filled rectangle is drawn at (x, y) with the specified width and height.
        - If send_payload is True, the OLED display is updated to reflect the changes.
        - If send_payload is False, withholds the `OLED.show()` command, allows stringing repeated calls together.
    """
    if payload == "line":
        OLED.line(x,y,width,height,OLED.white)
    elif payload == "rect":
        OLED.rect(x,y,width,height,OLED.white,True)

    if send_payload:
        OLED.show()

def display_clear(*regions, send_payload=True):
    """
    Clears specified sections or the entire OLED display by turning off pixels.

    Args:
        *regions (str): Variable number of region names to clear (defined in DISPLAY_REGIONS).
        send_payload (bool): If True, updates the OLED display after clearing. Defaults to True.

    Behavior:
        - Clears the specified sections of the OLED display based on the region names provided.
        - If no regions are specified, it does nothing.
        - If send_payload is True, the OLED display is updated.
    """
    for region in regions:
        if region in DISPLAY_REGIONS:
            x, y, width, height = DISPLAY_REGIONS[region]
            OLED.rect(x, y, width, height, OLED.black, True)

    if send_payload:
        OLED.show()

async def idle_mode():
    """
    Updates the display during idle mode, showing the current inning, rack, and countdown timer.
    This function also sets the game state to idle.

    Behavior:
        - Displays the inning, rack, and countdown timer on the OLED screen.
        - Adjusts the game countdown based on the game mode (timeouts or standard).
        - Updates the state machine to reflect the shot clock idle state.
    """
    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8, False)
        display_text("Timeouts Mode", 12, 57, 1)
    else:
        state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
        game.speaker_5_count = 4
        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1, False)
        display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)

        if game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8)

    state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)

async def shot_clock():
    """
    Runs the countdown timer based on the selected game profile, updating the display at each second.
    This function also handles shot clock expiration and player actions such as using an extension or ending the turn.

    Behavior:
        - Manages the countdown timer, updating the display and handling end-of-timer events.
        - Handles player actions such as making shots, using extensions, or ending turns.
        - Updates game state and manages transitions between shot clock, idle, and game over states.
    """
    state_machine.update_state(State_Machine.COUNTDOWN_IN_PROGRESS)
    countdown_checker = utime.ticks_ms()

    if game.inning_counter % 1 == 0:
        print("player_1 shooting")
        game.player_1_shooting = True
        game.player_2_shooting = False
    else:
        game.player_1_shooting = False
        game.player_2_shooting = True
        print("player_2 shooting")

    while game.countdown > -1:
        if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 1000:
            # Get the current tens and units digits
            current_tens = game.countdown // 10  # Tens digit
            current_units = game.countdown % 10  # Units digit

            # Decrement countdown
            game.countdown -= 1

            # Get the new tens and units digits after decrement
            new_tens = game.countdown // 10
            new_units = game.countdown % 10

            # Play the shot clock beep
            if game.countdown < 5 and not game.speaker_muted:
                _thread.start_new_thread(shot_clock_beep, ())

            # Clear and update the display as needed
            if current_tens != new_tens and current_units != new_units:
                display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                display_text(process_timer_duration(game.countdown), 0, 0, 8)

            elif current_tens != new_tens:  # Tens digit changed
                display_clear("shot_clock_digit_1")
                display_text(str(new_tens), 0, 0, 8)

            elif current_units != new_units:  # Units digit changed
                display_clear("shot_clock_digit_2")
                display_text(str(new_units), 60, 0, 8)

            countdown_checker = utime.ticks_ms()

            if game.countdown == 0:
                off = True
                state_machine.update_state(State_Machine.COUNTDOWN_COMPLETE)
                if game.selected_profile == "APA":
                    game.extension_available = True
                    game.extension_used = False

                flash_checker = utime.ticks_ms()
                while True:
                    if utime.ticks_diff(utime.ticks_ms(), flash_checker) > 330:
                        flash_checker = utime.ticks_ms()
                        if off:
                            display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                            off = False
                        else:
                            display_text(process_timer_duration(game.countdown), 0, 0, 8)
                            off = True

                    if make_button.value() or miss_button.value():
                        if make_button.value():
                            await wait_for_release_async(make_button)
                        if miss_button.value():
                            await wait_for_release_async(miss_button)
                            game.inning_counter +=0.5
                            
                        game.countdown = game.profile_based_countdown
                        display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                        return await idle_mode()
                    
                    await asyncio.sleep_ms(10)
        
        if make_button.value():
            await wait_for_release_async(make_button)
            game.countdown = game.profile_based_countdown
            if game.selected_profile == "APA":
                game.extension_available = True
                game.extension_used = False
            state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
            display_clear("shot_clock_digit_1", "shot_clock_digit_2")
            if game.break_shot:
                game.break_shot = False
            return await idle_mode()
        
        if up_button.value():
            await wait_for_release_async(up_button)
            if game.selected_profile == "WNT" or game.selected_profile == "BCA":
                if game.player_1_shooting and game.player_1_extension_available:
                    game.player_1_extension_available = False
                    game.countdown += game.extension_duration
                    game.speaker_5_count = 4
                    display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                    display_text(process_timer_duration(game.countdown), 0, 0, 8)
                elif game.player_2_shooting and game.player_2_extension_available:
                    game.player_2_extension_available = False
                    game.countdown += game.extension_duration
                    game.speaker_5_count = 4
                    display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                    display_text(process_timer_duration(game.countdown), 0, 0, 8)
            else:
                game.extension_used = True
                game.extension_available = False
                game.countdown += game.extension_duration
                game.speaker_5_count = 4
                display_clear("shot_clock_digit_1", "shot_clock_digit_2")
                display_text(process_timer_duration(game.countdown), 0, 0, 8)

        if miss_button.value():
            await wait_for_release_async(miss_button)
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            state_machine.update_state(State_Machine.SHOT_CLOCK_IDLE)
            display_clear("shot_clock_digit_1", "shot_clock_digit_2")
            if game.inning_counter - 0.5 != int(game.inning_counter):
                display_clear("inning_counter")
            if game.break_shot:
                game.break_shot = False
            return await idle_mode()
        
        await asyncio.sleep_ms(10)

async def select_game_profile():
    """
    Allows the user to select a game profile. Displays the list of profiles and handles user input to make a selection.

    Behavior:
        - Displays available game profiles and allows the user to cycle through them using buttons.
        - Updates the game state based on the selected profile and transitions to idle mode.
    """
    inactivity_check = utime.ticks_ms()
    countdown_checker = utime.ticks_ms()
    off = False
    list_traverser = 1 # Starting at 2 because list)self.game_profiles) returns a list in a different order than the dictionary
    profile_list = list(game.game_profiles)
    profile_list_length = len(profile_list) - 1
    display_text("Select Game:", 15, 10, 1)
    while True:
        if utime.ticks_diff(utime.ticks_ms(), inactivity_check) > 500:
            if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 500:
                countdown_checker = utime.ticks_ms()
                if off:
                    display_clear("profile_selection")
                    off = False
                else:
                    display_text(str((profile_list[list_traverser])), 25, 30, 3)
                    off = True
        else:
            display_text(str((profile_list[list_traverser])), 25, 30, 3)

        if make_button.value():
            await wait_for_release_async(make_button)
            if state_machine.profile_selection:
                # Transitioning to SHOT_CLOCK_IDLE will happen in idle_mode()
                game.countdown = game.profile_based_countdown
                display_clear("everything")
            game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
            game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
            game.selected_profile = profile_list[list_traverser]
            if game.extension_duration == 0:
                game.timeouts_only = True
            state_machine.game_on = True
            game.menu_values = [game.rack_counter, game.speaker_muted, int(game.inning_counter)]
            return await idle_mode()
        
        if up_button.value():
            await wait_for_release_async(up_button)
            if list_traverser == profile_list_length:
                list_traverser = 0
            else:
                list_traverser += 1
            display_clear("profile_selection")
            if off:
                display_text(str(profile_list[list_traverser]), 25, 30, 3)

            inactivity_check = utime.ticks_ms()

        if down_button.value():
            await wait_for_release_async(down_button)
            if list_traverser == 0:
                list_traverser = profile_list_length
            else:
                list_traverser -= 1
            display_clear("profile_selection")
            if off:
                display_text(str(profile_list[list_traverser]), 25, 30, 3)

            inactivity_check = utime.ticks_ms()
        
        await asyncio.sleep_ms(10)

async def game_menu():
    """
    Displays a new game settings menu, allowing the user to adjust various game parameters 
    such as the inning counter, rack counter, and mute status.

    Behavior:
        - Opens a menu where the user can cycle through different settings using up and down buttons.
        - Make button allows for editing item next to cursor.
        - Allows the user to increment or decrement the selected setting using up and down buttons.
        - Saves changes with the make button and reverts them with the miss button.
        - Exits the menu with the miss button.
        - Cursor will blink on the OLED display to indicate value is being edited.
    """
    if state_machine.shot_clock_idle:
        state_machine.update_state(State_Machine.MENU)
        display_clear("everything")
        off = False
        game.current_menu_index = game.menu_items.index("Rack") # Ensure current_menu_index is set to "Rack" before entering the menu
        inning_counter_before_mod = game.inning_counter
        rack_counter_before_mode = game.rack_counter
        mute_bool_before_mod = game.speaker_muted
        display_text("Game", 0,2,2, False)
        display_text("Menu", 66,2,2, False)
        display_shape("line",0,19,128,19,False) #underline "Menu"
        display_shape("line",0,20,128,20,False) #make it bold
        game.update_menu_selection(clear_before_payload=False)
        countdown_checker = utime.ticks_ms()
        while True:

            if make_button.value():
                await wait_for_release_async(make_button)
                inning_counter_before_mod = game.inning_counter
                rack_counter_before_mode = game.rack_counter
                mute_bool_before_mod = game.speaker_muted
                while True:
                    if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 500:
                        countdown_checker = utime.ticks_ms()
                        if off:
                            display_clear("menu_selector")
                            off = False
                        else:
                            display_shape("rect",8,40,8,8) #menu cursor)
                            off = True

                    if make_button.value():
                        display_shape("rect",8,40,8,8) #menu cursor)
                        await wait_for_release_async(make_button)
                        game.menu_values = [game.rack_counter, game.speaker_muted, int(game.inning_counter)]
                        break

                    if up_button.value():
                        await wait_for_release_async(up_button)
                        if game.current_menu_selection[1] == "Inning":
                            display_clear("menu_inning_counter")
                            game.inning_counter += 1
                            display_text(str(int(game.inning_counter)), 80,40,1)
                        elif game.current_menu_selection[1] == "Rack":
                            display_clear("menu_rack_counter")
                            game.rack_counter += 1
                            display_text(game.rack_counter, 64,40,1)
                        elif game.current_menu_selection[1] == "Mute":
                            display_clear("menu_mute_bool")
                            if game.speaker_muted:
                                game.speaker_muted = False
                            else:
                                game.speaker_muted = True
                            display_text(game.speaker_muted, 64,40,1)

                    if down_button.value():
                        await wait_for_release_async(down_button)
                        if game.current_menu_selection[1] == "Inning":
                            if game.inning_counter > 1:
                                display_clear("menu_inning_counter")
                                game.inning_counter -= 1
                            display_text(str(int(game.inning_counter)), 80,40,1)
                        elif game.current_menu_selection[1] == "Rack":
                            if game.rack_counter > 1:
                                display_clear("menu_rack_counter")
                                game.rack_counter -= 1
                            display_text(game.rack_counter, 64,40,1)
                        elif game.current_menu_selection[1] == "Mute":
                            display_clear("menu_mute_bool")
                            if game.speaker_muted:
                                game.speaker_muted = False
                            else:
                                game.speaker_muted = True
                            display_text(game.speaker_muted, 64,40,1)

                    if miss_button.value():
                        display_shape("rect",8,40,8,8) #menu cursor)
                        game.menu_values = [rack_counter_before_mode, mute_bool_before_mod, int(inning_counter_before_mod)]
                        await wait_for_release_async(miss_button)
                        if game.current_menu_selection[1] == "Inning":
                            if game.inning_counter != inning_counter_before_mod:
                                display_clear("menu_inning_counter")
                                game.inning_counter = inning_counter_before_mod
                                display_text(str(int(game.inning_counter)), 80,40,1)
                        elif game.current_menu_selection[1] == "Rack":
                            if game.rack_counter != rack_counter_before_mode:
                                display_clear("menu_rack_counter")
                                game.rack_counter = rack_counter_before_mode
                                display_text(game.rack_counter, 64,40,1)
                        elif game.current_menu_selection[1] == "Mute":
                            if game.speaker_muted != mute_bool_before_mod:
                                display_clear("menu_mute_bool")
                                game.speaker_muted = mute_bool_before_mod
                                display_text(game.speaker_muted, 64, 40, 1)
                        break
                    
                    await asyncio.sleep_ms(10)

            if up_button.value():
                await wait_for_release_async(up_button)
                game.current_menu_index = (game.current_menu_index - 1) % len(game.menu_items)
                game.update_menu_selection()

            if down_button.value():
                await wait_for_release_async(down_button)
                game.current_menu_index = (game.current_menu_index + 1) % len(game.menu_items)
                game.update_menu_selection()

            if miss_button.value():
                await wait_for_release_async(miss_button)
                display_clear("everything")
                if game.rack_counter != rack_counter_before_mode:
                    game.break_shot = True
                return await idle_mode()
            
            await asyncio.sleep_ms(10)

def shot_clock_beep():
    """
    Sends an audio beep signal to the MAX98357A amplifier, indicating shot clock status.

    Behavior:
        - Plays an audio beep through the MAX98357A amplifier to signal the shot clock status.
        - The beep is played from a WAV file loaded from the filesystem.
    """
    # Initialize I2S
    audio_out = I2S(
        I2S_ID,
        sck=I2S_SCK,
        ws=I2S_WS,
        sd=I2S_SD,
        mode=I2S.TX,
        bits=I2S_BITS,
        format=I2S.MONO,
        rate=I2S_RATE,
        ibuf=20000
    )
    
    # Open WAV file
    wav_file = open("beep.wav", "rb")

    # Skip WAV header (typically 44 bytes)
    wav_file.seek(80)

    # Buffer to hold audio data
    wav_buffer = bytearray(1024)

    # Play audio
    try:
        while True:
            num_read = wav_file.readinto(wav_buffer)
            if num_read == 0:
                break  # End of file
            audio_out.write(wav_buffer)
    finally:
        # Cleanup
        wav_file.close()
        audio_out.deinit()

async def main():
    """
    Main entry point for the async program.
    """
    await select_game_profile()
    while True:
        if make_button.value():
            await wait_for_release_async(make_button)
            await shot_clock()

        if up_button.value():
            await wait_for_release_async(up_button)
            await idle_mode()

        if down_button.value():
            await wait_for_release_async(down_button)
            await idle_mode()

        if miss_button.value():
            await wait_for_release_async(miss_button)
            if not game.selected_profile == "Timeouts Mode":
                await game_menu()

        await asyncio.sleep_ms(10)  # Short delay to prevent busy-waiting

# Start Program
try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    pass
finally:
    asyncio.new_event_loop()  # Reset the event loop
