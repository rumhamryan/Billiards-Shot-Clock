##################################################
# Timeouts only mode
# 3 minute challenge (british 8-ball)
# Average 2 things for one rack: average time between shots and make miss ratio
##################################################



from machine import Pin, PWM # type: ignore
import I2C_LCD_driver
import utime # type: ignore
import _thread # type: ignore
mylcd = I2C_LCD_driver.lcd()

# Configure I/Os
button_1 = Pin(16, Pin.IN, Pin.PULL_DOWN)
button_2 = Pin(17, Pin.IN, Pin.PULL_DOWN)
button_3 = Pin(18, Pin.IN, Pin.PULL_DOWN)
button_4 = Pin(19, Pin.IN, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)
buzzer = PWM(Pin(20))

# This interrupt handling
def interrupt_handler(Pin):
    debounce_time = utime.ticks_ms()
    if (utime.ticks_ms() - debounce_time) > 300:
        debounce_time = utime.ticks_ms()

# Configure interrupts
button_1.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_2.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_3.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_4.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)

# Used to track the state of the device
class State_Machine:
    def __init__(self, profile_selection = True, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False):

        self.profile_selection: bool = profile_selection
        self.shot_clock_idle: bool = shot_clock_idle
        self.countdown_in_progress: bool = countdown_in_progress
        self.countdown_complete: bool = countdown_complete

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
    def __init__(self,profile_based_countdown = 0, countdown = 0, extension_duration = 0, extension_available = True, inning_counter= 1.0, buzzer_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 5, "extension_duration": 5}, 
                                  "Mosconi": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45}}):

        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.extension_available: bool = extension_available
        self.inning_counter: float = inning_counter
        self.buzzer_5_count: int = buzzer_5_count
        self.game_profiles: dict = game_profiles

state_machine = State_Machine()
game = Game_Stats()

# This will ensure single digits are padded with a leading zero
def process_timer_duration(duration):
        processed_integer = duration
        if processed_integer < 10:
            return (str(0) + str(processed_integer))
        else:
            return str(processed_integer)

# This will udpate the display with countdown based on the selected profile
def idle_mode():
    state_machine.update_state(shot_clock_idle=True)
    mylcd.lcd_display_string(str("Inning: ") + str(game.inning_counter), 1)
    if game.extension_available:
        game.countdown = game.profile_based_countdown
    else:
        game.countdown = game.profile_based_countdown + game.extension_duration
    mylcd.lcd_display_string(str("Shot Clock: ") + process_timer_duration(game.countdown), 2)

# This will run a countdown based on the selected profile
def shot_clock():
    countdown_checker = utime.time()
    state_machine.update_state(countdown_in_progress=True)
    while game.countdown > -1:
        if utime.time() - countdown_checker > 0: # udpate display once every second
            game.countdown -= 1

            if game.countdown < 5:
                _thread.start_new_thread(buzzer_toggle, ())

            mylcd.lcd_display_string(str("Shot Clock: ") + process_timer_duration(game.countdown), 2)
            countdown_checker = utime.time()

            if game.countdown == 0:
                off = True
                state_machine.update_state(countdown_complete=True)
                countdown_checker = utime.time()
                while True:
                    if utime.time() - countdown_checker > 0.1:
                        countdown_checker = utime.time()
                        if off:
                            mylcd.lcd_display_string(str("Shot Clock: ") + str("     "), 2)
                            off = False
                        else:
                            mylcd.lcd_display_string(str("Shot Clock: ") + process_timer_duration(game.countdown), 2)
                            off = True

                    if button_1.value():
                        state_machine.update_state(shot_clock_idle=True)
                        game.countdown = game.profile_based_countdown
                        while button_1.value():
                            utime.sleep(.1)
                        return
                    if button_4.value():
                        state_machine.update_state(shot_clock_idle=True)
                        game.countdown = game.profile_based_countdown
                        game.inning_counter +=0.5
                        while button_4.value():
                            utime.sleep(.1)
                        return
                
        if button_1.value():
            state_machine.update_state(shot_clock_idle=True)
            game.countdown = game.profile_based_countdown
            while button_1.value():
                utime.sleep(.1)
            return
        if button_2.value():
            if game.extension_available:
                game.countdown += game.extension_duration
                game.extension_available = False
            while button_2.value():
                utime.sleep(.1)
        if button_4.value():
            state_machine.update_state(shot_clock_idle=True)
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            while button_4.value():
                utime.sleep(.1)
            return

# This will select a game profile
def select_game_profile():
    inactivity_check = utime.time()
    countdown_checker = utime.time()
    off = False
    list_traverser = 2 # Starting at 2 because list)self.game_profiles) returns a list in a different order than the dictionary
    profile_list = list(game.game_profiles)
    profile_list_length = len(profile_list) - 1
    mylcd.lcd_display_string(str("Select Rules:"), 1)
    while True:
        if utime.time() - inactivity_check > 1.0:
            if utime.time() - countdown_checker > 0.1:
                countdown_checker = utime.time()
                if off:
                    mylcd.lcd_display_string(str("         "), 2)
                    off = False
                else:
                    mylcd.lcd_display_string(str(profile_list[list_traverser]), 2)
                    off = True
        else:
            mylcd.lcd_display_string(str(profile_list[list_traverser]), 2)

        if button_1.value():
            if state_machine.profile_selection:
                state_machine.profile_selection = False
                game.countdown = game.profile_based_countdown
                mylcd.lcd_display_string(str("               "), 1)
            game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
            game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
            while button_1.value():
                utime.sleep(.1)
            return
        if button_2.value():
            if list_traverser == profile_list_length:
                list_traverser = 0
            else:
                list_traverser += 1
            while button_2.value():
                utime.sleep(.1)
                if off:
                    mylcd.lcd_display_string(str("         "), 2)
                    mylcd.lcd_display_string(str(profile_list[list_traverser]), 2)
            inactivity_check = utime.time()
        if button_3.value():
            if list_traverser == 0:
                list_traverser = profile_list_length
            else:
                list_traverser -= 1
            while button_3.value():
                utime.sleep(.1)
            if off:
                mylcd.lcd_display_string(str("         "), 2)
                mylcd.lcd_display_string(str(profile_list[list_traverser]), 2)
            inactivity_check = utime.time()
        
def buzzer_toggle():
    if game.buzzer_5_count > 0:
        duration = 0.2
    else:
        duration = 0.8
    if game.buzzer_5_count == 0:
        buzzer.freq(750)
        game.buzzer_5_count = 4
    else:
        buzzer.freq(500)
        game.buzzer_5_count -= 1
    buzzer.duty_u16(250)
    utime.sleep(duration)
    buzzer.duty_u16(0)

select_game_profile()
while True:
    idle_mode()

    if button_1.value() or button_4.value():
        while button_1.value() or button_4.value():
            utime.sleep(.1)
        shot_clock()
        if not game.extension_available:
            game.extension_available = True

    if button_2.value():
        while button_2.value():
            utime.sleep(.1)
        if game.countdown == game.profile_based_countdown or game.countdown == game.profile_based_countdown + game.extension_duration:
            if game.extension_available:
                game.extension_available = False
            else:
                game.extension_available = True

    if button_3.value():
        while button_3.value():
            utime.sleep(.1)
        if game.inning_counter > 1.0:
            game.inning_counter -= 0.5

