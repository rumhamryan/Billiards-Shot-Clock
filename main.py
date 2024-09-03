from machine import I2S, Pin, PWM # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore

# Set up the GPIO pins as input with pull-down resistors
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)

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
        - Tracks and updates various game states such as speaker muting, profile selection, shot clock, and game status.
    """
    def __init__(self, speaker_muted = False, profile_selection = True, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False, game_on = False):
        """
        Initializes the state machine with default values or provided states.

        Args:
            speaker_muted (bool): Indicates if the speaker is muted.
            profile_selection (bool): Indicates if a profile is being selected.
            shot_clock_idle (bool): Indicates if the shot clock is idle.
            countdown_in_progress (bool): Indicates if a countdown is in progress.
            countdown_complete (bool): Indicates if the countdown is complete.
            game_on (bool): Indicates if a game is ongoing.

        Behavior:
            - Initializes state variables to manage different phases of the game.
        """
        self.speaker_muted: bool = speaker_muted
        self.profile_selection: bool = profile_selection
        self.shot_clock_idle: bool = shot_clock_idle
        self.countdown_in_progress: bool = countdown_in_progress
        self.countdown_complete: bool = countdown_complete
        self.game_on: bool = game_on

    def update_state(self, profile_selection = False, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False, menu = False):
        """
        Updates the state of the machine based on the provided arguments.

        Args:
            profile_selection (bool): Set to True if profile selection state should be active.
            shot_clock_idle (bool): Set to True if shot clock idle state should be active.
            countdown_in_progress (bool): Set to True if countdown in progress state should be active.
            countdown_complete (bool): Set to True if countdown complete state should be active.

        Behavior:
            - Updates internal state variables to reflect the current game phase.
            - Transitions between different states such as profile selection, shot clock idle, countdown, and menu navigation.
        """
        if profile_selection:
            self.profile_selection = True
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = False
            self.menu = False
        elif shot_clock_idle:
            self.profile_selection = False
            self.shot_clock_idle = True
            self.countdown_in_progress = False
            self.countdown_complete = False
            self.menu = False
        elif countdown_in_progress:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = True
            self.countdown_complete = False
            self.menu = False
        elif countdown_complete:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = True
        elif menu:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = False
            self.menu = True

class Game_Stats:
    """
    Class to track and manage game statistics and settings.

    Behavior:
        - Stores and manages various game-related statistics such as countdown timers, player status, and game profiles.
        - Facilitates updating and retrieving game state information during play.
    """
    def __init__(self,profile_based_countdown = 0, countdown = 0, extension_duration = 0, extension_available = True, extension_used = False, player_1_shooting=True, player_1_extension_available=True, player_2_shooting=False, player_2_extension_available=True, inning_counter= 1.0, rack_counter = 1, break_shot = True, speaker_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 20, "extension_duration": 25}, 
                                  "WNT": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45},
                                  "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}},
                selected_profile = None, timeouts_only = False):
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
            speaker_5_count (int): Counter for speaker actions.
            game_profiles (dict): Dictionary of game profiles and their settings.
            selected_profile (str): The currently selected game profile.
            timeouts_only (bool): Indicates if the game is in timeouts mode.

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
        self.speaker_5_count: int = speaker_5_count
        self.game_profiles: dict = game_profiles
        self.selected_profile: str = selected_profile
        self.timeouts_only: bool = timeouts_only

# Instantiate Classes
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()

menu_items = ["Rack", "Mute", "Inning"]
menu_values = []
current_menu_index = 0
current_menu_selection = [None, menu_items[current_menu_index], None]  # [previous, current, next]
current_menu_values = []

def make_button_pressed():
    """
    Handles the action when the make button is pressed.

    Behavior:
        - Waits until the make button is released before proceeding.
        - This prevents any action from being taken until the button is fully released.
    """

    while make_button.value():
        pass  # Wait for button release
    # print("Make button pressed")

def up_button_pressed():
    """
    Handles the action when the up button is pressed.

    Behavior:
        - Waits until the up button is released before proceeding.
        - Ensures that the action tied to the up button occurs only once per press.
    """

    while up_button.value():
        pass  # Wait for button release
    # print("Up button pressed")

def down_button_pressed():
    """
    Handles the action when the down button is pressed.

    Behavior:
        - Waits until the down button is released before proceeding.
        - Ensures that the action tied to the down button occurs only once per press.
    """
    while down_button.value():
        pass # Wait for button release
    # print("Down button pressed")

def miss_button_pressed():
    """
    Handles the action when the miss button is pressed.

    Behavior:
        - Waits until the miss button is released before proceeding.
        - Ensures that the action tied to the miss button occurs only once per press.
    """
    while miss_button.value():
        pass  # Wait for button release
    # print("Miss button pressed")

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

def display_clear(shot_clock_digit_1=False, shot_clock_digit_2=False, profile_selection=False, inning_counter=False, rack_counter=False, menu_selector=False, menu_items=False, menu_inning_counter=False, menu_rack_counter=False, menu_mute_bool=False, everything=False, send_payload=True):
    """
    Clears sections or the entire OLED display by turning off pixels in specified areas.

    Args:
        shot_clock_digit_1 (bool): Clear the first shot clock digit section.
        shot_clock_digit_2 (bool): Clear the second shot clock digit section.
        profile_selection (bool): Clear the profile selection area.
        inning_counter (bool): Clear the inning counter area.
        rack_counter (bool): Clear the rack counter area.
        menu_selector (bool): Clear the menu selector area.
        menu_inning_counter (bool): Clear the menu inning counter area.
        menu_rack_counter (bool): Clear the menu rack counter area.
        menu_mute_bool (bool): Clear the menu mute option area.
        everything (bool): Clear the entire screen.
        send_payload (bool): If True, updates the OLED display after clearing. Defaults to True.

    Behavior:
        - Clears specified sections of the OLED display, based on the provided arguments.
        - If send_payload is False, withholds the `OLED.show()` command, allows stringing repeated calls together.
    """
    x, y, width, height = 0, 0, 0, 0
    
    if everything:
        x, y, width, height = 0, 0, 128, 64
    elif profile_selection:
        x, y, width, height = 0, 20, 128, 44
    elif inning_counter:
        x, y, width, height = 55, 55, 17, 9
    elif rack_counter:
        x, y, width, height = 113, 57, 14, 8
    elif shot_clock_digit_1 and shot_clock_digit_2:
        x, y, width, height = 0, 0, 125, 56
    elif shot_clock_digit_1:
        x, y, width, height = 0, 0, 62, 56
    elif shot_clock_digit_2:
        x, y, width, height = 62, 0, 66, 56
    elif menu_selector:
        x, y, width, height = 8, 24, 8, 64
    elif menu_items:
        x, y, width, height = 24, 24, 80, 40
    elif menu_inning_counter:
        x, y, width, height = 80, 40, 17, 8
    elif menu_rack_counter:
        x, y, width, height = 64, 40, 17, 8
    elif menu_mute_bool:
        x, y, width, height = 64, 40, 40, 8

    OLED.rect(x, y, width, height, OLED.black, True)
    if send_payload:
        OLED.show()

def idle_mode():
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
        state_machine.update_state(shot_clock_idle=True)
        game.speaker_5_count = 4
        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1, False)
        display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)

        if game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8)

    state_machine.update_state(shot_clock_idle=True)

def shot_clock():
    """
    Runs the countdown timer based on the selected game profile, updating the display at each second.
    This function also handles shot clock expiration and player actions such as using an extension or ending the turn.

    Behavior:
        - Manages the countdown timer, updating the display and handling end-of-timer events.
        - Handles player actions such as making shots, using extensions, or ending turns.
        - Updates game state and manages transitions between shot clock, idle, and game over states.
    """
    state_machine.update_state(countdown_in_progress=True)
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
        if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 700:
            # Get the current tens and units digits
            current_tens = game.countdown // 10  # Tens digit
            current_units = game.countdown % 10  # Units digit

            # Decrement countdown
            game.countdown -= 1

            # Get the new tens and units digits after decrement
            new_tens = game.countdown // 10
            new_units = game.countdown % 10

            # Play the shot clock beep
            if game.countdown < 5 and not state_machine.speaker_muted:
                _thread.start_new_thread(shot_clock_beep, ())

            # Clear and update the display as needed
            if current_tens != new_tens and current_units != new_units:
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                display_text(process_timer_duration(game.countdown), 0, 0, 8)

            elif current_tens != new_tens:  # Tens digit changed
                display_clear(shot_clock_digit_1=True)
                display_text(str(new_tens), 0, 0, 8)

            elif current_units != new_units:  # Units digit changed
                display_clear(shot_clock_digit_2=True)
                display_text(str(new_units), 60, 0, 8)

            countdown_checker = utime.ticks_ms()

            if game.countdown == 0:
                off = True
                state_machine.update_state(countdown_complete=True)
                if game.selected_profile == "APA":
                    game.extension_available = True
                    game.extension_used = False

                countdown_checker = utime.ticks_ms()
                while True:
                    if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 330:
                        countdown_checker = utime.ticks_ms()
                        if off:
                            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                            off = False
                        else:
                            display_text(process_timer_duration(game.countdown), 0, 0, 8)
                            off = True

                    if make_button.value() or miss_button.value():
                        if make_button.value():
                            make_button_pressed()
                        if miss_button.value():
                            miss_button_pressed()
                            game.inning_counter +=0.5
                            
                        game.countdown = game.profile_based_countdown
                        display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                        return idle_mode()
        
        if make_button.value():
            make_button_pressed()
            game.countdown = game.profile_based_countdown
            if game.selected_profile == "APA":
                game.extension_available = True
                game.extension_used = False
            state_machine.update_state(shot_clock_idle=True)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            countdown_check = None
            countdown_checker = None
            if game.break_shot:
                game.break_shot = False
            return idle_mode()
        
        if up_button.value():
            up_button_pressed()
            if game.selected_profile == "WNT" or game.selected_profile == "BCA":
                if game.player_1_shooting and game.player_1_extension_available:
                    game.player_1_extension_available = False
                    game.countdown += game.extension_duration
                    game.speaker_5_count = 4
                    display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                    display_text(process_timer_duration(game.countdown), 0, 0, 8)
                elif game.player_2_shooting and game.player_2_extension_available:
                    game.player_2_extension_available = False
                    game.countdown += game.extension_duration
                    game.speaker_5_count = 4
                    display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                    display_text(process_timer_duration(game.countdown), 0, 0, 8)
            else:
                game.extension_used = True
                game.extension_available = False
                game.countdown += game.extension_duration
                game.speaker_5_count = 4
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                display_text(process_timer_duration(game.countdown), 0, 0, 8)

        if miss_button.value():
            miss_button_pressed()
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            state_machine.update_state(shot_clock_idle=True)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            if game.inning_counter - 0.5 != int(game.inning_counter):
                display_clear(inning_counter=True)
            countdown_check = None
            countdown_checker = None
            if game.break_shot:
                game.break_shot = False
            return idle_mode()

def select_game_profile():
    """
    Allows the user to select a game profile. Displays the list of profiles and handles user input to make a selection.

    Behavior:
        - Displays available game profiles and allows the user to cycle through them using buttons.
        - Updates the game state based on the selected profile and transitions to idle mode.
    """
    global interrupt_registered, menu_values
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
                    display_clear(profile_selection=True)
                    off = False
                else:
                    display_text(str((profile_list[list_traverser])), 25, 30, 3)
                    off = True
        else:
            display_text(str((profile_list[list_traverser])), 25, 30, 3)

        if make_button.value():
            make_button_pressed()
            if state_machine.profile_selection:
                state_machine.profile_selection = False
                game.countdown = game.profile_based_countdown
                display_clear(everything=True)
            game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
            game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
            game.selected_profile = profile_list[list_traverser]
            if game.extension_duration == 0:
                game.timeouts_only = True
            state_machine.game_on = True
            menu_values = [game.rack_counter, state_machine.speaker_muted, int(game.inning_counter)]
            return idle_mode()
        
        if up_button.value():
            up_button_pressed()
            if list_traverser == profile_list_length:
                list_traverser = 0
            else:
                list_traverser += 1
            display_clear(profile_selection=True)
            if off:
                display_text(str(profile_list[list_traverser]), 25, 30, 3)

            inactivity_check = utime.ticks_ms()

        if down_button.value():
            down_button_pressed()
            if list_traverser == 0:
                list_traverser = profile_list_length
            else:
                list_traverser -= 1
            display_clear(profile_selection=True)
            if off:
                display_text(str(profile_list[list_traverser]), 25, 30, 3)

            inactivity_check = utime.ticks_ms()

def update_menu_selection(send_payload=True, clear_before_payload=True):
    """Updates the current_menu_selection list based on the current_menu_index.
       Displays the current selection along with its previous and next menu_items."""
    global current_menu_index, current_menu_selection, current_menu_values, menu_items, menu_values
    # Set previous index, wrapping around if necessary
    prev_index = (current_menu_index - 1) % len(menu_items)
    
    # Set next index, wrapping around if necessary
    next_index = (current_menu_index + 1) % len(menu_items)
    
    # Update the current_menu_selection list
    current_menu_selection = [menu_items[prev_index], menu_items[current_menu_index], menu_items[next_index]]
    current_menu_values = [menu_values[prev_index], menu_values[current_menu_index], menu_values[next_index]]

    # Display the menu menu_items
    if send_payload:
        if clear_before_payload:
            display_clear(menu_items=True)
        display_text(f"{current_menu_selection[0]}:{current_menu_values[0]}", 24, 24, 1, False)
        display_text(f"{current_menu_selection[1]}:{current_menu_values[1]}", 24, 40, 1, False)
        display_text(f"{current_menu_selection[2]}:{current_menu_values[2]}", 24, 56, 1, False)
        display_shape("rect", 8,40,8,8, True) #menu cursor

def new_menu():
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
    global current_menu_index, current_menu_selection, current_menu_values, menu_values
    if state_machine.shot_clock_idle:
        state_machine.update_state(menu=True)
        display_clear(everything=True)
        off = False
        current_menu_index = menu_items.index("Rack") # Ensure current_menu_index is set to "Rack" before entering the menu
        inning_counter_before_mod = game.inning_counter
        rack_counter_before_mode = game.rack_counter
        mute_bool_before_mod = state_machine.speaker_muted
        display_text("Game", 0,2,2, False)
        display_text("Menu", 66,2,2, False)
        display_shape("line",0,19,128,19,False) #underline "Menu"
        display_shape("line",0,20,128,20,False) #make it bold
        update_menu_selection(clear_before_payload=False)
        countdown_checker = utime.ticks_ms()
        while True:

            if make_button.value():
                make_button_pressed()
                inning_counter_before_mod = game.inning_counter
                rack_counter_before_mode = game.rack_counter
                mute_bool_before_mod = state_machine.speaker_muted
                while True:
                    if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 500:
                        countdown_checker = utime.ticks_ms()
                        if off:
                            display_clear(menu_selector=True)
                            off = False
                        else:
                            display_shape("rect",8,40,8,8) #menu cursor)
                            off = True

                    if make_button.value():
                        display_shape("rect",8,40,8,8) #menu cursor)
                        make_button_pressed()
                        menu_values = [game.rack_counter, state_machine.speaker_muted, int(game.inning_counter)]
                        break

                    if up_button.value():
                        up_button_pressed()
                        if current_menu_selection[1] == "Inning":
                            display_clear(menu_inning_counter=True)
                            game.inning_counter += 1
                            display_text(str(int(game.inning_counter)), 80,40,1)
                        elif current_menu_selection[1] == "Rack":
                            display_clear(menu_rack_counter=True)
                            game.rack_counter += 1
                            display_text(game.rack_counter, 64,40,1)
                        elif current_menu_selection[1] == "Mute":
                            display_clear(menu_mute_bool=True)
                            if state_machine.speaker_muted:
                                state_machine.speaker_muted = False
                            else:
                                state_machine.speaker_muted = True
                            display_text(state_machine.speaker_muted, 64,40,1)

                    if down_button.value():
                        down_button_pressed()
                        if current_menu_selection[1] == "Inning":
                            if game.inning_counter > 1:
                                display_clear(menu_inning_counter=True)
                                game.inning_counter -= 1
                            display_text(str(int(game.inning_counter)), 80,40,1)
                        elif current_menu_selection[1] == "Rack":
                            if game.rack_counter > 1:
                                display_clear(menu_rack_counter=True)
                                game.rack_counter -= 1
                            display_text(game.rack_counter, 64,40,1)
                        elif current_menu_selection[1] == "Mute":
                            display_clear(menu_mute_bool=True)
                            if state_machine.speaker_muted:
                                state_machine.speaker_muted = False
                            else:
                                state_machine.speaker_muted = True
                            display_text(state_machine.speaker_muted, 64,40,1)

                    if miss_button.value():
                        display_shape("rect",8,40,8,8) #menu cursor)
                        menu_values = [rack_counter_before_mode, mute_bool_before_mod, int(inning_counter_before_mod)]
                        miss_button_pressed()
                        if current_menu_selection[1] == "Inning":
                            if game.inning_counter != inning_counter_before_mod:
                                display_clear(menu_inning_counter=True)
                                game.inning_counter = inning_counter_before_mod
                                display_text(str(int(game.inning_counter)), 80,40,1)
                        elif current_menu_selection[1] == "Rack":
                            if game.rack_counter != rack_counter_before_mode:
                                display_clear(menu_rack_counter=True)
                                game.rack_counter = rack_counter_before_mode
                                display_text(game.rack_counter, 64,40,1)
                        elif current_menu_selection[1] == "Mute":
                            if state_machine.speaker_muted != mute_bool_before_mod:
                                display_clear(menu_mute_bool=True)
                                state_machine.speaker_muted = mute_bool_before_mod
                                display_text(state_machine.speaker_muted, 64, 40, 1)
                        break

            if up_button.value():
                up_button_pressed()
                current_menu_index = (current_menu_index - 1) % len(menu_items)
                update_menu_selection()

            if down_button.value():
                down_button_pressed()
                current_menu_index = (current_menu_index + 1) % len(menu_items)
                update_menu_selection()

            if miss_button.value():
                miss_button_pressed()
                display_clear(everything=True)
                if game.rack_counter != rack_counter_before_mode:
                    game.break_shot = True
                return idle_mode()

def menu():
    """
    Opens a menu allowing the user to edit game settings such as inning counter, rack counter, and speaker mute status.

    Behavior:
        - Provides a menu interface for the user to adjust game settings.
        - Allows cycling through options and modifying game settings, reflecting changes on the OLED display.
        - Returns to shot clock mode after settings are adjusted.
    """
    if state_machine.shot_clock_idle:
        state_machine.update_state(menu=True)
        display_clear(everything=True)
        inactivity_check = utime.ticks_ms()
        countdown_checker = utime.ticks_ms()
        off = False
        selection_list = ["inning", "rack", "mute", None]
        list_traverser = 0
        inning_counter_before_mod = game.inning_counter
        rack_counter_before_mode = game.rack_counter
        selected_variable = selection_list[list_traverser]
        # print(selected_variable)
        display_text("Menu", 24, 2, 2, False)
        display_shape("line",23,18,88,18,False) #underline "Menu"
        display_shape("line",23,19,88,19,False) #make it bold
        display_text(f"Inning:{int(game.inning_counter)}", 24, 24, 1, False)
        display_shape("rect",8,24,8,8,False) #menu selector
        display_text(f"Rack:{int(game.rack_counter)}", 24, 40, 1, False)
        if state_machine.speaker_muted:
            display_text("Mute:Yes", 24, 56, 1, True)
        else:
            display_text("Mute:No", 24, 56, 1, True)
        while True:
            if utime.ticks_diff(utime.ticks_ms(), inactivity_check) > 500:
                if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 500:
                    countdown_checker = utime.ticks_ms()
                    if off:
                        if selected_variable == "inning":
                            display_clear(menu_inning_counter=True)
                        elif selected_variable == "rack":
                            display_clear(menu_rack_counter=True)
                        elif selected_variable == "mute":
                            display_clear(menu_mute_bool=True)
                        off = False
                    else:
                        if selected_variable == "inning":
                            display_text(str(int(game.inning_counter)), 80, 24, 1)
                        elif selected_variable == "rack":
                            display_text(str(game.rack_counter), 64, 40, 1)
                        elif selected_variable == "mute":
                            if state_machine.speaker_muted:
                                display_text(str("Yes"), 64, 56, 1)
                            else:
                                display_text(str("No"), 64, 56, 1)
                        off = True
            else:
                if selected_variable == "inning":
                    display_text(str(int(game.inning_counter)), 80, 24, 1)
                elif selected_variable == "rack":
                    display_text(str(game.rack_counter), 64, 40, 1)
                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        display_text(str("Yes"), 64, 56, 1)
                    else:
                        display_text(str("No"), 64, 56, 1)

            if make_button.value():
                make_button_pressed()  
                if game.rack_counter != rack_counter_before_mode:
                    game.extension_available = True
                    game.player_1_extension_available = True
                    game.player_2_extension_available = True
                    game.break_shot = True
                display_clear(everything=True)
                idle_mode()
                return shot_clock()
            
            if up_button.value():
                up_button_pressed()
                if selected_variable == "inning":
                    game.inning_counter += 1
                    display_clear(menu_inning_counter=True)
                    if off:
                        display_text(str(int(game.inning_counter)), 80, 24, 1) 

                elif selected_variable == "rack":
                    game.rack_counter += 1
                    display_clear(menu_rack_counter=True)
                    if off:
                        display_text(str(game.rack_counter), 64, 40, 1)

                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        state_machine.speaker_muted = False
                    else:
                        state_machine.speaker_muted = True
                    display_clear(menu_mute_bool=True)
                    if off:
                        if state_machine.speaker_muted:
                            display_text(str("Yes"), 64, 56, 1)
                        else:
                            display_text(str("No"), 64, 56, 1)

                inactivity_check = utime.ticks_ms()

            if down_button.value():
                down_button_pressed()
                if selected_variable == "inning":
                    if game.inning_counter - 1 > 0:
                        game.inning_counter -= 1
                        display_clear(menu_inning_counter=True)
                        if off:
                            display_text(str(int(game.inning_counter)), 80, 24, 1)
                            
                elif selected_variable == "rack":
                    if game.rack_counter - 1 > 0:
                        game.rack_counter -= 1
                        display_clear(menu_rack_counter=True)
                        if off:
                            display_text(str(game.rack_counter), 64, 40, 1)

                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        state_machine.speaker_muted = False
                    else:
                        state_machine.speaker_muted = True
                    display_clear(menu_mute_bool=True)
                    if off:
                        if state_machine.speaker_muted:
                            display_text(str("Yes"), 64, 56, 1)
                        else:
                            display_text(str("No"), 64, 56, 1)

                inactivity_check = utime.ticks_ms()

            if miss_button.value():
                if selected_variable == "inning":
                    display_text(str(int(game.inning_counter)), 80, 24, 1)
                elif selected_variable == "rack":
                    display_text(str(game.rack_counter), 64, 40, 1)
                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        display_text(str("Yes"), 64, 56, 1)
                    else:
                        display_text(str("No"), 64, 56, 1)
                miss_button_pressed()
                list_traverser += 1
                selected_variable = selection_list[list_traverser]
                # print(selected_variable)
                if selected_variable == None:
                    if game.rack_counter != rack_counter_before_mode:
                        game.extension_available = True
                        game.player_1_extension_available = True
                        game.player_2_extension_available = True
                        game.extension_used = False
                        game.break_shot = True
                    display_clear(everything=True)
                    return idle_mode()
                else:
                    display_clear(menu_selector=True, send_payload=False)
                    if selected_variable == "inning":
                        display_shape("rect", 8,24,8,8) #menu selector
                    elif selected_variable == "rack":
                        display_shape("rect", 8,40,8,8) #menu selector
                    elif selected_variable == "mute":
                        display_shape("rect", 8,56,8,8) #menu selector

def shot_clock_beep():
    """
    Sends an audio beep signal to the MAX98357A amplifier, indicating shot clock status.

    Behavior:
        - Plays an audio beep through the MAX98357A amplifier to signal the shot clock status.
        - The beep is played from a WAV file loaded from the filesystem.
    """
    # Initialize I2S
    audio_out = I2S(
    0,
    sck=Pin(11),   # BCLK
    ws=Pin(12),    # LRC
    sd=Pin(10),     # DIN
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=48000,    # Sample rate, should match the .wav file
    ibuf=20000)     # Buffer size
    
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

# Start Program
select_game_profile()
while True:

    if make_button.value():
        make_button_pressed()
        shot_clock()

    if up_button.value():
        up_button_pressed()
        idle_mode()

    if down_button.value():
        down_button_pressed()
        idle_mode()

    if miss_button.value():
        miss_button_pressed()
        if not game.selected_profile == "Timeouts Mode":
            new_menu()

    utime.sleep_ms(10)  # Short delay to prevent busy-waiting