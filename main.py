##################################################
# 3 minute challenge (Ultimate Pool)
# Average 2 things for one rack: average time between shots and make miss ratio
# Consider changing miss_button functionality while state_machine.shot_clock_idle to toggle/highlight game.countdown, game.inning_counter, game.rack_counter
##################################################

from machine import I2S, Pin, PWM # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore

# Set up the GPIO pins as input with pull-down resistors
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)

debounce_time = 0
button_state = "IDLE"

def new_interrupt_handler(pin):
    """
    Interrupt handler for button presses, implementing a debouncing mechanism.

    Args:
        pin (Pin): The GPIO pin object associated with the button.
    """
    global debounce_time, button_state
    current_time = utime.ticks_ms()

    if button_state == "IDLE":
        if (current_time - debounce_time) > 50:  # Shorter initial debounce
            if pin.value() == 0:  # Button pressed
                debounce_time = current_time
                button_state = "PRESSED"

    elif button_state == "PRESSED":
        if (current_time - debounce_time) > 100:  # Longer debounce before acknowledging press
            if pin.value() == 0:
                print("Button pressed")
                debounce_time = current_time
                button_state = "RELEASED"

    elif button_state == "RELEASED":
        if pin.value() == 1:  # Wait for the button to be released
            button_state = "IDLE"

# Attach interrupt handlers to each button
make_button.irq(trigger=Pin.IRQ_RISING, handler=new_interrupt_handler)
up_button.irq(trigger=Pin.IRQ_RISING, handler=new_interrupt_handler)
down_button.irq(trigger=Pin.IRQ_RISING, handler=new_interrupt_handler)
miss_button.irq(trigger=Pin.IRQ_RISING, handler=new_interrupt_handler)

class State_Machine:
    """
    Class to manage the state of the device during the game.
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
        """
        self.speaker_muted: bool = speaker_muted
        self.profile_selection: bool = profile_selection
        self.shot_clock_idle: bool = shot_clock_idle
        self.countdown_in_progress: bool = countdown_in_progress
        self.countdown_complete: bool = countdown_complete
        self.game_on: bool = game_on

    def update_state(self, profile_selection = False, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False):
        """
        Updates the state of the machine based on the provided arguments.

        Args:
            profile_selection (bool): Set to True if profile selection state should be active.
            shot_clock_idle (bool): Set to True if shot clock idle state should be active.
            countdown_in_progress (bool): Set to True if countdown in progress state should be active.
            countdown_complete (bool): Set to True if countdown complete state should be active.
        """
        if profile_selection:
            self.profile_selection = True
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = False
        elif shot_clock_idle:
            self.profile_selection = False
            self.shot_clock_idle = True
            self.countdown_in_progress = False
            self.countdown_complete = False
        elif countdown_in_progress:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = True
            self.countdown_complete = False
        elif countdown_complete:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = True

class Game_Stats:
    """
    Class to track and manage game statistics and settings.
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

def make_button_pressed():
    """
    Handles the action when the make button is pressed.
    Waits for the button to be released before proceeding.
    """
    while make_button.value():
        pass  # Wait for button release
    print("Make button pressed")

def up_button_pressed():
    """
    Handles the action when the up button is pressed.
    Waits for the button to be released before proceeding.
    """
    while up_button.value():
        pass  # Wait for button release
    print("Up button pressed")

def down_button_pressed():
    """
    Handles the action when the down button is pressed.
    Waits for the button to be released before proceeding.
    """
    while down_button.value():
        pass # Wait for button release
    print("Down button pressed")

def miss_button_pressed():
    """
    Handles the action when the miss button is pressed.
    Waits for the button to be released before proceeding.
    """
    while miss_button.value():
        pass  # Wait for button release
    print("Miss button pressed")

def process_timer_duration(duration):
    """
    Processes the timer duration to ensure it is displayed with leading zeros if necessary.

    Args:
        duration (int): The duration to be processed.

    Returns:
        str: The processed duration as a string, with a leading zero if necessary.
    """
    processed_integer = duration
    if processed_integer < 10:
        return (str(0) + str(processed_integer))
    else:
        return str(processed_integer)

def display_text(payload, x_coordinates, y_coordinates, font_size):
    """
    Displays a text string on the OLED screen at specified coordinates with a given font size.

    Args:
        payload (str): The text to be displayed.
        x_coordinates (int): The x-coordinate on the screen.
        y_coordinates (int): The y-coordinate on the screen.
        font_size (int): The size of the font to be used.
    """
    if payload == "Mosconi":
        x_coordinates = 8
        y_coordinates = 30
        font_size = 2
    elif payload == "Timeouts Mode" and state_machine.profile_selection:
        x_coordinates = 0
        font_size = 2
        
    OLED.text_scaled(payload, x_coordinates, y_coordinates, font_size)
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        OLED.text_scaled("Mode", 32, 48, 2)
    OLED.show()

def display_clear(shot_clock_digit_1=False, shot_clock_digit_2=False, profile_selection=False, inning_counter=False, rack_counter=False, menu_selector=False,menu_inning_counter=False, menu_rack_counter=False, menu_mute_bool=False, everything=False):
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
    """
    if profile_selection:
        OLED.rect(0,20,128,44,OLED.black, True)
        OLED.show()
    elif inning_counter:
        OLED.rect(55,55,17,9,OLED.black, True)
        OLED.show()
    elif rack_counter:
        OLED.rect(113,57,14,8,OLED.black, True)
        OLED.show()
    elif shot_clock_digit_1 and shot_clock_digit_2:
        OLED.rect(0,0,125,56,OLED.black, True)
        OLED.show()
    elif shot_clock_digit_1:
        OLED.rect(0,0,62,56,OLED.black, True)
        OLED.show()
    elif shot_clock_digit_2:
        OLED.rect(62,0,66,56,OLED.black, True)
        OLED.show()
    elif menu_selector:
        OLED.rect(8,24,8,64,OLED.black, True)
        OLED.show()
    elif menu_inning_counter:
        OLED.rect(80,24,16,8,OLED.black, True)
        OLED.show()
    elif menu_rack_counter:
        OLED.rect(64,40,16,8,OLED.black, True)
        OLED.show()
    elif menu_mute_bool:
        OLED.rect(64,56,24,8,OLED.black, True)
        OLED.show()
    elif everything:
        OLED.fill(OLED.black)

def idle_mode():
    """
    Updates the display during idle mode, showing the current inning, rack, and countdown timer.
    This function also sets the game state to idle.
    """
    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8)
        display_text("Timeouts Mode", 12, 57, 1)
    else:
        state_machine.update_state(shot_clock_idle=True)
        game.speaker_5_count = 4
        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
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
    """
    state_machine.update_state(countdown_in_progress=True)
    countdown_checker = utime.ticks_ms()
    
    while game.countdown > -1:
        if utime.ticks_diff(utime.ticks_ms(), countdown_checker) > 700: # udpate display once every second (700 more or less == 1 second in this loop on battery power)
            game.countdown -= 1
            countdown_check = process_timer_duration(game.countdown)

            if game.countdown < 5 and not state_machine.speaker_muted:
                _thread.start_new_thread(shot_clock_beep, ())

            if process_timer_duration(game.countdown)[0] == countdown_check[0]:
                single_digit_update = True
            if int(countdown_check[1]) == 9:
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            else:
                display_clear(shot_clock_digit_2=True)
            
            if single_digit_update and int(countdown_check[1]) != 9:
                display_text(str(countdown_check[1]), 60, 0, 8)
            else:
                display_text(process_timer_duration(game.countdown), 0, 0, 8)
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

                    if make_button.value():
                        make_button_pressed()
                        game.countdown = game.profile_based_countdown
                        display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                        return idle_mode()
                    if miss_button.value():
                        miss_button_pressed()
                        game.countdown = game.profile_based_countdown
                        game.inning_counter +=0.5
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
            if game.inning_counter % 2 == 0:
                print("player_1 shooting")
                game.player_1_shooting = True
                game.player_2_shooting = False
            else:
                game.player_1_shooting = False
                game.player_2_shooting = True
                print("player_2 shooting")
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
    """
    global interrupt_registered
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
            return idle_mode()
        
        if up_button.value():
            up_button_pressed()
            if list_traverser == profile_list_length:
                list_traverser = 0
            else:
                list_traverser += 1
            if off:
                display_clear(profile_selection=True)
                display_text(str(profile_list[list_traverser]), 25, 30, 3)
            else:
                display_clear(profile_selection=True)
            inactivity_check = utime.ticks_ms()

        if down_button.value():
            down_button_pressed()
            if list_traverser == 0:
                list_traverser = profile_list_length
            else:
                list_traverser -= 1
            if off:
                display_clear(profile_selection=True)
                display_text(str(profile_list[list_traverser]), 25, 30, 3)
            else:
                display_clear(profile_selection=True)
            inactivity_check = utime.ticks_ms()

def idle_menu():
    """
    Opens a menu allowing the user to edit game settings such as inning counter, rack counter, and speaker mute status.
    """
    if state_machine.shot_clock_idle:
        display_clear(everything=True)
        inactivity_check = utime.ticks_ms()
        countdown_checker = utime.ticks_ms()
        off = False
        selection_list = ["inning", "rack", "mute", None]
        list_traverser = 0
        inning_counter_before_mod = game.inning_counter
        rack_counter_before_mode = game.rack_counter
        selected_variable = selection_list[list_traverser]
        print(selected_variable)
        OLED.text_scaled("Menu", 24, 2, 2)
        OLED.line(23,18,88,18,OLED.white) #underline "Menu"
        OLED.line(23,19,88,19,OLED.white) #make it bold
        OLED.text_scaled(f"Inning:{int(game.inning_counter)}", 24, 24, 1)
        OLED.rect(8,24,8,8,OLED.white, True)
        OLED.text_scaled(f"Rack:{int(game.rack_counter)}", 24, 40, 1)
        if state_machine.speaker_muted:
            OLED.text_scaled("Mute:Yes", 24, 56, 1)
        else:
            OLED.text_scaled("Mute:No", 24, 56, 1)
        OLED.show()
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
                elif selected_variable == "rack":
                    game.rack_counter += 1
                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        state_machine.speaker_muted = False
                    else:
                        state_machine.speaker_muted = True
                if off:
                    if selected_variable == "inning":
                        display_clear(menu_inning_counter=True)
                        display_text(str(int(game.inning_counter)), 80, 24, 1)
                    elif selected_variable == "rack":
                        display_clear(menu_rack_counter=True)
                        display_text(str(game.rack_counter), 64, 40, 1)
                    elif selected_variable == "mute":
                        display_clear(menu_mute_bool=True)
                        if state_machine.speaker_muted:
                            display_text(str("Yes"), 64, 56, 1)
                        else:
                            display_text(str("No"), 64, 56, 1)
                else:
                    if selected_variable == "inning":
                        display_clear(menu_inning_counter=True)
                    elif selected_variable == "rack":
                        display_clear(menu_rack_counter=True)
                    elif selected_variable == "mute":
                        display_clear(menu_mute_bool=True)
                inactivity_check = utime.ticks_ms()

            if down_button.value():
                down_button_pressed()
                if selected_variable == "inning":
                    if game.inning_counter - 1 > 0:
                        game.inning_counter -= 1
                        if off:
                            display_clear(menu_inning_counter=True)
                            display_text(str(int(game.inning_counter)), 80, 24, 1)
                        else:
                            display_clear(menu_inning_counter=True)
                elif selected_variable == "rack":
                    if game.rack_counter - 1 > 0:
                        game.rack_counter -= 1
                        if off:
                            display_clear(menu_rack_counter=True)
                            display_text(str(game.rack_counter), 64, 40, 1)
                        else:
                            display_clear(menu_rack_counter=True)
                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        state_machine.speaker_muted = False
                    else:
                        state_machine.speaker_muted = True
                    if off:
                        display_clear(menu_mute_bool=True)
                        if state_machine.speaker_muted:
                            display_text(str("Yes"), 64, 56, 1)
                        else:
                            display_text(str("No"), 64, 56, 1)
                    else:
                        display_clear(menu_mute_bool=True)
                inactivity_check = utime.ticks_ms()

            if miss_button.value():
                miss_button_pressed()
                if selected_variable == "inning":
                    display_text(str(int(game.inning_counter)), 80, 24, 1)
                elif selected_variable == "rack":
                    display_text(str(game.rack_counter), 64, 40, 1)
                elif selected_variable == "mute":
                    if state_machine.speaker_muted:
                        display_text(str("Yes"), 64, 56, 1)
                    else:
                        display_text(str("No"), 64, 56, 1)
                list_traverser += 1
                selected_variable = selection_list[list_traverser]
                print(selected_variable)
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
                    display_clear(menu_selector=True)
                    if selected_variable == "inning":
                        OLED.rect(8,24,8,8,OLED.white, True) #selector location
                    elif selected_variable == "rack":
                        OLED.rect(8,40,8,8,OLED.white, True) #selector location
                    elif selected_variable == "mute":
                        OLED.rect(8,56,8,8,OLED.white, True) #selector location
                    OLED.show()

def shot_clock_beep():
    """
    Sends an audio beep signal to the MAX98357A amplifier, indicating shot clock status.
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
            idle_menu()

    utime.sleep_ms(10)  # Short delay to prevent busy-waiting
