from machine import Pin, PWM # type: ignore
import I2C_LCD_driver
import utime # type: ignore
import _thread # type: ignore

mylcd = I2C_LCD_driver.lcd()

button_1 = Pin(16, Pin.IN, Pin.PULL_DOWN)
button_2 = Pin(17, Pin.IN, Pin.PULL_UP)
button_3 = Pin(18, Pin.IN, Pin.PULL_UP)
button_4 = Pin(19, Pin.IN, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)
buzzer = PWM(Pin(20))

# This function is called each time an interrupt is issued from the "button_1" switch
def interrupt_handler(Pin):
    debounce_time = utime.ticks_ms()
    if (utime.ticks_ms() - debounce_time) > 300:
        debounce_time = utime.ticks_ms()

button_1.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_2.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_3.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)
button_4.irq(trigger = Pin.IRQ_FALLING, handler = interrupt_handler)


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

class Game_Stats:
    def __init__(self,profile_based_countdown = 0, countdown = 0, extension_duration = 0, inning_counter= 1.0,
                 game_profiles = {"APA": {"timer_duration": 5, "extension_duration": 5}, 
                                  "Mosconi": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45}}):

        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.inning_counter: float = inning_counter
        self.game_profiles: dict = game_profiles

state_machine = State_Machine()
game = Game_Stats()

def process_timer_duration(duration):
        processed_integer = duration
        if processed_integer < 10:
            return (str(0) + str(processed_integer))
        else:
            return str(processed_integer)

def idle_mode():
    state_machine.update_state(shot_clock_idle=True)
    mylcd.lcd_display_string(str("Inning: ") + str(game.inning_counter), 1)
    if game.countdown == 0:
        game.countdown = game.profile_based_countdown
        mylcd.lcd_display_string(str("Shot Clock: ") + process_timer_duration(game.profile_based_countdown), 2)
    else:
        mylcd.lcd_display_string(str("Shot Clock: ") + process_timer_duration(game.countdown), 2)

def shot_clock():
    countdown_checker = utime.time()
    state_machine.update_state(countdown_in_progress=True)
    while game.countdown > -1:
        if utime.time() - countdown_checker > 0: # udpate display once every second
            game.countdown -= 1
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
                        while button_1.value():
                            utime.sleep(.1)
                        state_machine.update_state(shot_clock_idle=True)
                        game.countdown = game.profile_based_countdown
                        return
                    if button_4.value():
                        while button_4.value():
                            utime.sleep(.1)
                        state_machine.update_state(shot_clock_idle=True)
                        game.countdown = game.profile_based_countdown
                        game.inning_counter +=0.5
                        return
                
        if button_1.value():
            while button_1.value():
                utime.sleep(.1)
            state_machine.update_state(shot_clock_idle=True)
            game.countdown = game.profile_based_countdown
            return
        if button_4.value():
            while button_4.value():
                utime.sleep(.1)
            state_machine.update_state(shot_clock_idle=True)
            game.countdown = game.profile_based_countdown
            game.inning_counter +=0.5
            return

# This will select a game profile
def select_game_profile():
    countdown_checker = utime.time()
    off = False
    list_traverser = 2 # Starting at 2 because list)self.game_profiles) returns a list in a different order than the dictionary
    mylcd.lcd_display_string(str("Select Rules:"), 1)
    while True:
        if utime.time() - countdown_checker > 0.1:
            countdown_checker = utime.time()
            profile_list = list(game.game_profiles)
            profile_list_length = len(profile_list) - 1
            if off:
                mylcd.lcd_display_string(str("         "), 2)
                off = False
            else:
                mylcd.lcd_display_string(str(profile_list[list_traverser]), 2)
                off = True
            
            if button_1.value():
                while button_1.value():
                    utime.sleep(.1)
                if state_machine.profile_selection:
                    state_machine.profile_selection = False
                    game.countdown = game.profile_based_countdown
                    mylcd.lcd_display_string(str("               "), 1)
                game.profile_based_countdown = game.game_profiles[profile_list[list_traverser]]["timer_duration"]
                game.extension_duration = game.game_profiles[profile_list[list_traverser]]["extension_duration"]
                return
            # if button_2.value():
            #     while button_2.value():
            #         utime.sleep(.1)
            #     if list_traverser == profile_list_length:
            #         list_traverser = 0
            #     else:
            #         list_traverser += 1
            # if button_3.value():
            #     while button_3.value():
            #         utime.sleep(.1)
            #     if list_traverser == 0:
            #         list_traverser = profile_list_length
            #     else:
            #         list_traverser -= 1

select_game_profile()
while True:
    idle_mode()
    if button_1.value() or button_4.value():
        while button_1.value() or button_4.value():
            utime.sleep(.1)
        shot_clock()
        if state_machine.countdown_complete:
            pass # blink function
        elif state_machine.shot_clock_idle:
            idle_mode()

