##################################################
# 3 minute challenge (Ultimate Pool)
# Average 2 things for one rack: average time between shots and make miss ratio
# Consider changing miss_button functionality while state_machine.shot_clock_idle to toggle/highlight game.countdown, game.inning_counter, game.rack_counter
##################################################


from machine import I2S, Pin, PWM # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore
    
# Define flags to control interrupt re-registration for each button
interrupt_registered = {
    'make': False,
    'up': False,
    'down': False,
    'miss': False
}

# Define interrupt handler functions for each button
def handle_make(pin):
    global interrupt_registered
    if not interrupt_registered['make']:
        print("Make button pressed")
        interrupt_registered['make'] = True

def handle_up(pin):
    global interrupt_registered
    if not interrupt_registered['up']:
        print("Up button pressed")
        interrupt_registered['up'] = True

def handle_down(pin):
    global interrupt_registered
    if not interrupt_registered['down']:
        print("Down button pressed")
        interrupt_registered['down'] = True

def handle_miss(pin):
    global interrupt_registered
    if not interrupt_registered['miss']:
        print("Miss button pressed")
        interrupt_registered['miss'] = True

# Set up the GPIO pins as input with pull-down resistors
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)

# Attach interrupt handlers to each button
make_button.irq(trigger=Pin.IRQ_RISING, handler=handle_make)
up_button.irq(trigger=Pin.IRQ_RISING, handler=handle_up)
down_button.irq(trigger=Pin.IRQ_RISING, handler=handle_down)
miss_button.irq(trigger=Pin.IRQ_RISING, handler=handle_miss)

# Used to track the state of the device
class State_Machine:
    def __init__(self, profile_selection = True, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False, game_on = False):

        self.profile_selection: bool = profile_selection
        self.shot_clock_idle: bool = shot_clock_idle
        self.countdown_in_progress: bool = countdown_in_progress
        self.countdown_complete: bool = countdown_complete
        self.game_on: bool = game_on

    def update_state(self, profile_selection = False, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False):
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

# Used to track the game stats
class Game_Stats:
    def __init__(self,profile_based_countdown = 0, countdown = 0, extension_duration = 0, extension_available = True, extension_used = False, inning_counter= 1.0, rack_counter = 1, break_shot = True, speaker_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 20, "extension_duration": 25}, 
                                  "WNT": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45},
                                  "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}},
                selected_profile = None, timeouts_only = False):

        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.extension_available: bool = extension_available
        self.extension_used: bool = extension_used
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

# This will ensure single digits are padded with a leading zero on the display
def process_timer_duration(duration):
        processed_integer = duration
        if processed_integer < 10:
            return (str(0) + str(processed_integer))
        else:
            return str(processed_integer)

# Sends a text string a coordinates to an OLED display  
def display_text(payload, x_coordinates, y_coordinates, font_size):
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

# Clears sections or all of the screen. Basically turning the pixels off for the coordinates
def display_clear(shot_clock_digit_1=False, shot_clock_digit_2=False, profile_selection=False, inning_counter=False, rack_counter=False, everything=False):
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
    elif everything:
        OLED.fill(OLED.black)

# This will udpate the display with countdown and extension based on the selected profile once per idle state
# Only a shot clock can reset the parameter required to send an update to the display
def idle_mode():
    if game.timeouts_only:
        game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8)
        display_text("Timeouts Mode", 12, 57, 1)
    else:
        state_machine.update_state(shot_clock_idle=True)
        game.speaker_5_count = 4
        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
        display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)
        # if game.extension_available:
        # game.countdown = game.profile_based_countdown
        # else:
        #     game.countdown = game.profile_based_countdown + game.extension_duration

        if not game.extension_available and not game.extension_used:
            game.countdown = game.profile_based_countdown + game.extension_duration
            # game.extension_used = True
        elif game.break_shot:
            game.countdown = game.profile_based_countdown + game.extension_duration
        else:
            game.countdown = game.profile_based_countdown
        display_text(process_timer_duration(game.countdown), 0, 0, 8)

    state_machine.update_state(shot_clock_idle=True)

# This will run a countdown based on the selected profile, each speaker toggle is a new thread for concurrency
def shot_clock():
    state_machine.update_state(countdown_in_progress=True)
    countdown_checker = utime.time()
    
    while game.countdown > -1:
        if utime.time() - countdown_checker > 0: # udpate display once every second
            game.countdown -= 1
            countdown_check = process_timer_duration(game.countdown)

            if game.countdown < 5:
                _thread.start_new_thread(shot_clock_beep, ())

            if process_timer_duration(game.countdown)[0] == countdown_check[0]:
                single_digit_update = True
            if int(countdown_check[1]) == 9:
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            display_clear(shot_clock_digit_2=True)
            
            if single_digit_update and int(countdown_check[1]) != 9:
                display_text(str(countdown_check[1]), 60, 0, 8)
            else:
                display_text(process_timer_duration(game.countdown), 0, 0, 8)
            countdown_checker = utime.time()

            if game.countdown == 0:
                off = True
                state_machine.update_state(countdown_complete=True)
                if game.selected_profile == "APA":
                    game.extension_available = True
                    game.extension_used = False

                countdown_checker = utime.time()
                while True:
                    if utime.time() - countdown_checker > 0.1:
                        countdown_checker = utime.time()
                        if off:
                            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                            off = False
                        else:
                            display_text(process_timer_duration(game.countdown), 0, 0, 8)
                            off = True

                    if make_button.value():
                        game.countdown = game.profile_based_countdown
                        while make_button.value():
                            utime.sleep(.1)
                        display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                        idle_mode()
                        return
                    if miss_button.value():
                        game.countdown = game.profile_based_countdown
                        game.inning_counter +=0.5
                        while miss_button.value():
                            utime.sleep(.1)
                        display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                        idle_mode()
                        return
        
        if interrupt_registered['make']:
            game.countdown = game.profile_based_countdown
            if game.selected_profile == "APA":
                game.extension_available = True
                game.extension_used = False
            utime.sleep_ms(200)  # Debounce delay
            while make_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['make'] = False  # Re-enable interrupt registration
            state_machine.update_state(shot_clock_idle=True)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            countdown_check = None
            countdown_checker = None
            if game.break_shot:
                game.break_shot = False
            idle_mode()
            return
        
        if interrupt_registered['up']:
            utime.sleep_ms(200)  # Debounce delay
            interrupt_registered['up'] = False  # Re-enable interrupt registration
            if game.extension_available and not game.extension_used:
                game.countdown += game.extension_duration
                game.extension_used = True
                game.extension_available = False
                game.speaker_5_count = 4
            while up_button.value() == 1:
                pass  # Wait for button release
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            display_text(process_timer_duration(game.countdown), 0, 0, 8)

        if interrupt_registered['miss']:
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            utime.sleep_ms(200)  # Debounce delay
            while miss_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['miss'] = False  # Re-enable interrupt registration
            state_machine.update_state(shot_clock_idle=True)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            if game.inning_counter - 0.5 != int(game.inning_counter):
                display_clear(inning_counter=True)
            countdown_check = None
            countdown_checker = None
            if game.break_shot:
                game.break_shot = False
            idle_mode()
            return

# This will select a game profile, will blink the selection after one second of inactivity
def select_game_profile():
    inactivity_check = utime.time()
    countdown_checker = utime.time()
    off = False
    list_traverser = 1 # Starting at 2 because list)self.game_profiles) returns a list in a different order than the dictionary
    profile_list = list(game.game_profiles)
    profile_list_length = len(profile_list) - 1
    display_text("Select Game:", 15, 10, 1)
    while True:
        if utime.time() - inactivity_check > 0.25:
            print("top")
            if utime.time() - countdown_checker > 0.1:
                countdown_checker = utime.time()
                if off:
                    print("offf")
                    display_clear(profile_selection=True)
                    off = False
                else:
                    print("on")
                    display_text(str((profile_list[list_traverser])), 25, 30, 3)
                    off = True
        else:
            print("bottom")
            display_text(str((profile_list[list_traverser])), 25, 30, 3)

        if interrupt_registered['make']:
            utime.sleep_ms(200)  # Debounce delay
            while make_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['make'] = False  # Re-enable interrupt registration
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
            idle_mode()
            return
        
        if interrupt_registered['up']:
            utime.sleep_ms(200)  # Debounce delay
            interrupt_registered['up'] = False  # Re-enable interrupt registration
            while up_button.value() == 1:
                pass  # Wait for button release
                utime.sleep(.1)
            if list_traverser == profile_list_length:
                list_traverser = 0
            else:
                list_traverser += 1
            while up_button.value():
                utime.sleep(.1)
            if off:
                display_clear(profile_selection=True)
                display_text(str(profile_list[list_traverser]), 25, 30, 3)
            else:
                display_clear(profile_selection=True)
            inactivity_check = utime.time()

        if interrupt_registered['down']:
            utime.sleep_ms(200)  # Debounce delay
            while miss_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['down'] = False  # Re-enable interrupt registration
            if list_traverser == 0:
                list_traverser = profile_list_length
            else:
                list_traverser -= 1
            while down_button.value():
                utime.sleep(.1)
            if off:
                display_clear(profile_selection=True)
                display_text(str(profile_list[list_traverser]), 25, 30, 3)
            else:
                display_clear(profile_selection=True)
            inactivity_check = utime.time()

# This will allow for the selection and updating of game.inning_counter and game.rack_counter
def update_counters():
    inactivity_check = utime.time()
    countdown_checker = utime.time()
    off = False
    selection_list = ["rack", "inning", None]
    list_traverser = 0
    inning_counter_before_mod = game.inning_counter
    rack_counter_before_mode = game.rack_counter
    selected_variable = selection_list[list_traverser]
    while True:
        if utime.time() - inactivity_check > 0.25:
            if utime.time() - countdown_checker > 0.25:
                countdown_checker = utime.time()
                if off:
                    if selected_variable == "inning":
                        display_clear(inning_counter=True)
                    elif selected_variable == "rack":
                        display_clear(rack_counter=True)
                    off = False
                else:
                    if selected_variable == "inning":
                        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
                    elif selected_variable == "rack":
                        display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)
                    off = True
        else:
            if selected_variable == "inning":
                display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
            elif selected_variable == "rack":
                display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)

        if interrupt_registered['make']:
            utime.sleep_ms(200)  # Debounce delay
            while make_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['make'] = False  # Re-enable interrupt registration    
            if game.rack_counter != rack_counter_before_mode:
                game.extension_available = True
                game.break_shot = True
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            idle_mode()
            shot_clock()
            return
        
        if interrupt_registered['up']:
            utime.sleep_ms(200)  # Debounce delay
            while up_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['up'] = False  # Re-enable interrupt registration
            if selected_variable == "inning":
                game.inning_counter += 1
            elif selected_variable == "rack":
                game.rack_counter += 1
            if off:
                if selected_variable == "inning":
                    display_clear(inning_counter=True)
                    display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
                elif selected_variable == "rack":
                    display_clear(rack_counter=True)
                    display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)
            else:
                if selected_variable == "inning":
                    display_clear(inning_counter=True)
                elif selected_variable == "rack":
                    display_clear(rack_counter=True)
            inactivity_check = utime.time()

        if interrupt_registered['down']:
            utime.sleep_ms(200)  # Debounce delay
            while down_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['down'] = False  # Re-enable interrupt registration
            if selected_variable == "inning":
                if game.inning_counter - 1 > 0:
                    game.inning_counter -= 1
                    if off:
                        display_clear(inning_counter=True)
                        display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
                    else:
                        display_clear(inning_counter=True)
            elif selected_variable == "rack":
                if game.rack_counter - 1 > 0:
                    game.rack_counter -= 1
                    if off:
                        display_clear(rack_counter=True)
                        display_text(f"Rack:{int(game.rack_counter)}", 72, 57, 1)
                    else:
                        display_clear(rack_counter=True)
            inactivity_check = utime.time()

        if interrupt_registered['miss']:
            utime.sleep_ms(200)  # Debounce delay
            while miss_button.value() == 1:
                pass  # Wait for button release
            interrupt_registered['miss'] = False  # Re-enable interrupt registration
            idle_mode()
            list_traverser += 1
            selected_variable = selection_list[list_traverser]
            if selected_variable == None:
                if game.rack_counter != rack_counter_before_mode:
                    game.extension_available = True
                    game.extension_used = False
                    game.break_shot = True
                    display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                    idle_mode()
                return

# This will send the wave file "beep_3_processed.wav" to the MAX98357A
def shot_clock_beep():
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
    wav_file = open("beep_3_processed.wav", "rb")

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

    if interrupt_registered['make']:
        utime.sleep_ms(200)  # Debounce delay
        while make_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['make'] = False  # Re-enable interrupt registration
        shot_clock()

    if interrupt_registered['up']:
        utime.sleep_ms(200)  # Debounce delay
        interrupt_registered['up'] = False  # Re-enable interrupt registration
        if not game.selected_profile == "Timeouts Mode":
            if game.extension_available:
                game.extension_available = False
            else:
                game.extension_available = True
            if not game.extension_used:
                display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
        while up_button.value() == 1:
            pass  # Wait for button release
            # utime.sleep(.1)
        idle_mode()

    if interrupt_registered['down']:
        utime.sleep_ms(200)  # Debounce delay
        while down_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['down'] = False  # Re-enable interrupt registration
        idle_mode()

    if interrupt_registered['miss']:
        utime.sleep_ms(200)  # Debounce delay
        while miss_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['miss'] = False  # Re-enable interrupt registration
        if not game.selected_profile == "Timeouts Mode":
            update_counters()

    utime.sleep(0.01)  # Short delay to prevent busy-waiting
