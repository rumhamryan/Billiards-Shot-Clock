##################################################
# 3 minute challenge (british 8-ball)
# Average 2 things for one rack: average time between shots and make miss ratio
# Fix the extension logic
##################################################


from machine import Pin, PWM # type: ignore
import Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore
    
# Configure I/Os
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)
speaker = PWM(Pin(20))

# This interrupt handling
def interrupt_handler(Pin):
    debounce_time = utime.ticks_ms()
    if (utime.ticks_ms() - debounce_time) > 300:
        debounce_time = utime.ticks_ms()

# Configure interrupts
make_button.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
up_button.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
down_button.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
miss_button.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)

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
    def __init__(self,profile_based_countdown = 0, countdown = 0, extension_duration = 0, extension_available = True, inning_counter= 1.0, speaker_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 20, "extension_duration": 25}, 
                                  "Mosconi": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45},
                                  "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}},
                timeouts_only = False):

        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.extension_available: bool = extension_available
        self.inning_counter: float = inning_counter
        self.speaker_5_count: int = speaker_5_count
        self.game_profiles: dict = game_profiles
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
        OLED.rect(113,55,15,9,OLED.black, True)
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
    if state_machine.shot_clock_idle:
        pass
    else:
        if game.timeouts_only:
            game.countdown = game.profile_based_countdown
            display_text(process_timer_duration(game.countdown), 0, 0, 8)
            display_text("Timeouts Mode", 12, 57, 1)
        else:
            state_machine.update_state(shot_clock_idle=True)
            game.speaker_5_count = 4
            display_text(f"Inning:{int(game.inning_counter)}", 0, 57, 1)
            if game.extension_available:
                game.countdown = game.profile_based_countdown
            else:
                game.countdown = game.profile_based_countdown + game.extension_duration
            display_text(process_timer_duration(game.countdown), 0, 0, 8)

        state_machine.update_state(shot_clock_idle=True)

# This will run a countdown based on the selected profile, each speaker toggle is a new thread for concurrency
def shot_clock():
    countdown_checker = utime.time()
    state_machine.update_state(countdown_in_progress=True)
    while game.countdown > -1:
        if utime.time() - countdown_checker > 0: # udpate display once every second
            game.countdown -= 1
            countdown_check = process_timer_duration(game.countdown)

            if game.countdown < 5:
                _thread.start_new_thread(speaker_toggle, ())

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
                        return
                    if miss_button.value():
                        game.countdown = game.profile_based_countdown
                        game.inning_counter +=0.5
                        while miss_button.value():
                            utime.sleep(.1)
                        display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
                        return
                
        if make_button.value():
            game.countdown = game.profile_based_countdown
            while make_button.value():
                utime.sleep(.1)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            return
        if up_button.value():
            if game.extension_available:
                game.countdown += game.extension_duration
                game.extension_available = False
                game.speaker_5_count = 4
            while up_button.value():
                utime.sleep(.1)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
        if miss_button.value():
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            while miss_button.value():
                utime.sleep(.1)
            display_clear(shot_clock_digit_1=True, shot_clock_digit_2=True)
            if game.inning_counter - 0.5 != int(game.inning_counter):
                display_clear(inning_counter=True)
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
        if utime.time() - inactivity_check > 1.0:
            if utime.time() - countdown_checker > 0.1:
                countdown_checker = utime.time()
                if off:
                    display_clear(profile_selection=True)
                    off = False
                else:
                    display_text(str((profile_list[list_traverser])), 25, 30, 3)
                    off = True
        else:
            display_text(str((profile_list[list_traverser])), 25, 30, 3)

        if make_button.value():
            if state_machine.profile_selection:
                state_machine.profile_selection = False
                game.countdown = game.profile_based_countdown
                display_clear(everything=True)
            game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
            game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
            if game.extension_duration == 0:
                game.timeouts_only = True
            while make_button.value():
                utime.sleep(.1)
            state_machine.game_on = True
            return
        if up_button.value():
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
        if down_button.value():
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

# Toggle the speaker, longer duration and higher pitch for final toggle
def speaker_toggle():
    if game.speaker_5_count > 0:
        duration = 0.2
    else:
        duration = 0.8
    if game.speaker_5_count == 0:
        speaker.freq(750)
        game.speaker_5_count = 4
    else:
        speaker.freq(500)
        game.speaker_5_count -= 1
    speaker.duty_u16(10000) # value makes the speakers loud without clipping, so there's room to go higher
    utime.sleep(duration)
    speaker.duty_u16(0)


# Start Program
select_game_profile()
while True:
    idle_mode()

    if make_button.value() or miss_button.value():
        if not game.extension_available:
            game.extension_available = True
        while make_button.value() or miss_button.value():
            utime.sleep(.1)
        shot_clock()

    if up_button.value():
        if state_machine.shot_clock_idle:
            if game.extension_available:
                game.extension_available = False
            else:
                game.extension_available = True
        while up_button.value():
            utime.sleep(.1)

    if down_button.value():
        if game.inning_counter > 1.0:
            game.inning_counter -= 0.5
        while down_button.value():
            utime.sleep(.1)
