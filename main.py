from machine import Pin, PWM # type: ignore
import I2C_LCD_driver
import utime # type: ignore
import _thread # type: ignore

mylcd = I2C_LCD_driver.lcd()

#######################################
# 1. Figure out how to change exit interrupt detection for threading, also how to exit the thread
# 2. Add a buzzer:    DONE
# 3. Consider a method to skip the current countdown or reset the current countdown to default duration:    DONE
# 4. Might need to pull the blink function apart into separate smaller functions
# 5. A button (or repurpose one) that adds a 30 second extension:    DONE
#######################################


class Pico:
    def __init__(self,
                 debounce_time = 00,
                 interrupt_1 = 0, interrupt_2 = 0, interrupt_3 = 0, interrupt_4 = 0, recall_interrupt = False,
                 button_1_interrupt = False, button_2_interrupt = False, button_3_interrupt = False, button_4_interrupt = False,
                 button_1 = Pin(16, Pin.IN, Pin.PULL_UP),
                 button_2 = Pin(17, Pin.IN, Pin.PULL_UP),
                 button_3 = Pin(18, Pin.IN, Pin.PULL_UP),
                 button_4 = Pin(19, Pin.IN, Pin.PULL_UP),
                 led = Pin(25, Pin.OUT),
                 buzzer = PWM(Pin(20)),
                 buzzer_5_count = 5): 

        self.debounce_time: int = debounce_time

        self.interrupt_1: int = interrupt_1
        self.interrupt_2: int = interrupt_2
        self.interrupt_3: int = interrupt_3
        self.interrupt_4: int = interrupt_4
        self.recall_interrupt: bool = recall_interrupt

        self.button_1_interrupt: bool = button_1_interrupt
        self.button_2_interrupt: bool = button_2_interrupt
        self.button_3_interrupt: bool = button_3_interrupt
        self.button_4_interrupt: bool = button_4_interrupt

        self.button_1 = button_1
        self.button_2 = button_2
        self.button_3 = button_3
        self.button_4 = button_4
        self.led = led

        self.buzzer = buzzer
        self.buzzer_5_count = buzzer_5_count

    # This function is called each time an interrupt is issued from the "button_1" switch
    def interrupt_1_handler(self, Pin):
        if (utime.ticks_ms() - self.debounce_time) > 120:
            self.interrupt_1 = 1
            self.debounce_time = utime.ticks_ms()
            print(str("interrupt_1: ") + str(self.interrupt_1))

    def button_1_thread(self):
        while True:
            if self.button_1.value() == 1:
                self.button_1_interrupt = True
            
    # This function is called each time an interrupt is issued from the "button_2" switch
    def interrupt_2_handler(self, Pin):
        if (utime.ticks_ms() - self.debounce_time) > 120:
            self.interrupt_2 = 1
            self.debounce_time = utime.ticks_ms()
            print(str("interrupt_2: ") + str(self.interrupt_2))

    # This function is called each time an interrupt is issued from the "button_3" switch
    def interrupt_3_handler(self, Pin):
        if (utime.ticks_ms() - self.debounce_time) > 120:
            self.interrupt_3 = 1
            self.debounce_time = utime.ticks_ms()
            print(str("interrupt_3: ") + str(self.interrupt_3))

    # This function is called each time an interrupt is issued from the "button_4" switch
    def interrupt_4_handler(self, Pin):
        if (utime.ticks_ms() - self.debounce_time) > 120:
            self.interrupt_4 = 1
            self.debounce_time = utime.ticks_ms()
            print(str("interrupt_4: ") + str(self.interrupt_4))

    def buzzer_toggle(self, duration):
        if self.buzzer_5_count == 0:
            self.buzzer.freq(750)
            self.buzzer_5_count = 5
        else:
            self.buzzer.freq(500)
            self.buzzer_5_count -= 1
        self.buzzer.duty_u16(250)
        utime.sleep(duration)
        self.buzzer.duty_u16(0)

    def configure_interrupts(self, thread: bool = False):
        if thread:
            # These are the actual interrupt request to the 2040 controller
            self.button_1.irq(trigger = 0, handler = None)
            self.button_2.irq(trigger = 0, handler = None)
            self.button_3.irq(trigger = 0, handler = None)
            # _thread.start_new_thread(self.button_1_thread, ())
        else:
            # These are the actual interrupt request to the 2040 controller
            self.button_1.irq(trigger = Pin.IRQ_RISING, handler = self.interrupt_1_handler)
            self.button_2.irq(trigger = Pin.IRQ_RISING, handler = self.interrupt_2_handler)
            self.button_3.irq(trigger = Pin.IRQ_RISING, handler = self.interrupt_3_handler)
            self.button_4.irq(trigger = Pin.IRQ_RISING, handler = self.interrupt_4_handler)
            # if _thread.get_ident != 0:
            #     _thread.exit()

class Display_Stats:
    def __init__(self,
                 timer_duration_choices = [5, 30, 45, 60], selecting_timer_duration = True, user_input_timer_duration = 0,
                 current_countdown = 0, last_interrupted_countdown = "N/A", countdown_complete = True, awaiting_countdown = False,
                 inning_counter = 0.5, inning_updated = 0,
                 extension = False):
        
        self.timer_duration_choices: list = timer_duration_choices
        self.selecting_timer_duration:bool = selecting_timer_duration
        self.user_input_timer_duration: int = user_input_timer_duration
        self.current_countdown = current_countdown
        self.last_interrupted_countdown = last_interrupted_countdown
        self.countdown_complete: int = countdown_complete
        self.awaiting_countdown: bool = awaiting_countdown
        
        self.inning_counter: float = inning_counter
        self.inning_updated: float = inning_updated

        self.extension: bool = extension
        
    # This function will "blink" either the inning_c`ounter or current_countdown variables on the I2C lcd display
    def blink(self, inning = False, shot_clock = False):
        list_traverser = 0
        if inning:
            data_type = [str("Inning: "), str(self.inning_counter), 1]
        elif shot_clock:
            data_type = [str("Shot Clock: "), self.process_timer_duration(self.current_countdown), 2]
        elif self.selecting_timer_duration:
            data_type = [str("Shot Clock: "), self.process_timer_duration(self.user_input_timer_duration), 2]
            list_length = len(self.timer_duration_choices) - 1
        else:
            pass
        while True:
            if self.selecting_timer_duration:
                data_type[1] = self.process_timer_duration(self.user_input_timer_duration)
            mylcd.lcd_display_string(data_type[0] + data_type[1], data_type[2])
            utime.sleep(0.5)
            mylcd.lcd_display_string(data_type[0] + str("   "), data_type[2])
            utime.sleep(0.5)
            
            if pico.interrupt_1:
                pico.interrupt_1 = 0
                if self.selecting_timer_duration:
                    self.selecting_timer_duration = False
                    self.current_countdown = self.user_input_timer_duration
                if self.countdown_complete:
                    if self.inning_updated == 0:
                        self.update_inning_counter(True)
                        self.countdown_complete = False
                        self.awaiting_countdown = True
                break
            if pico.interrupt_2:
                pico.interrupt_2 = 0
                if self.selecting_timer_duration:
                    if list_traverser == list_length:
                        list_traverser = 0
                    else:
                        list_traverser += 1
                    self.user_input_timer_duration = self.timer_duration_choices[list_traverser]
                elif self.countdown_complete:
                    self.update_inning_counter(True)
            if pico.interrupt_3:
                pico.interrupt_3 = 0
                if self.selecting_timer_duration:
                    if list_traverser == 0:
                        list_traverser = list_length
                    else:
                        list_traverser -= 1
                    self.user_input_timer_duration = self.timer_duration_choices[list_traverser]
                elif self.countdown_complete:
                    self.update_inning_counter(False)
            if pico.interrupt_4:
                pico.interrupt_4 = 0
                
    # This is the shot clock
    def countdown(self):
        while int(self.current_countdown) > -1:
            self.countdown_complete = False
            if self.current_countdown == None:
                self.current_countdown = self.user_input_timer_duration
            mylcd.lcd_display_string(str("Inning: ") + str(self.inning_counter), 1)
            mylcd.lcd_display_string(str("Shot Clock: ") + self.process_timer_duration(self.current_countdown), 2)
            if self.current_countdown <= 4:
                pico.buzzer_toggle(.2)
                utime.sleep(.8)
            elif self.current_countdown == 0:
                pico.buzzer_toggle(.3)
            else:
                utime.sleep(1)
            self.current_countdown -= 1
            if pico.interrupt_1:
                pico.interrupt_1 = 0
                # self.blink(shot_clock = True)
                if self.extension:
                    pass
                else:
                    self.extension = True
                    self.current_countdown += 30
            if pico.interrupt_2 or pico.interrupt_3:
                pico.interrupt_2 = 0
                pico.interrupt_3 = 0
            if pico.interrupt_4:
                pico.interrupt_4 = 0
                self.last_interrupted_countdown = self.current_countdown
                self.current_countdown = self.user_input_timer_duration
                self.awaiting_countdown = True
                self.extension = False
                # self.countdown_complete = True
                self.update_inning_counter(True)
                break
            if self.current_countdown == 0:
                self.countdown_complete = True
                self.inning_updated = 0
                pico.buzzer_toggle(.5)
                self.extension = False
                self.blink(shot_clock = True)
                return True
        self.display_current_stats()
    
    # This function will update the I2C lcd display
    def display_current_stats(self):
        if not self.selecting_timer_duration:
            mylcd.lcd_display_string(str("Inning: ") + str(self.inning_counter), 1)
        if type(self.current_countdown) == int:
            if self.current_countdown == 0:
                self.current_countdown = self.user_input_timer_duration
                mylcd.lcd_display_string(str("Shot Clock: ") + self.process_timer_duration(self.user_input_timer_duration), 2)
            else:
                mylcd.lcd_display_string(str("Shot Clock: ") + self.process_timer_duration(self.current_countdown), 2)
            
    # This function will be used to process the user_input_timer_duration variable and ensure it displays properly on the I2C lcd display
    def process_timer_duration(self, duration):
        processed_integer = duration
        if processed_integer < 10:
            return (str(0) + str(processed_integer))
        else:
            return str(processed_integer)
            
    # This will be used to increment and decrement the inning_counter parameter
    def update_inning_counter(self, update: bool):
        # if not self.test:
        if update:
            self.inning_counter += 0.5
            self.inning_updated -= 0.5
        else:
            if self.inning_counter == 1.0:
                pass
            else:
                self.inning_counter -= 0.5
                self.inning_updated -= 0.5
        self.display_current_stats()

    # This will allow the user to select a duration from the timer_duration_choices list
    def user_input_timer(self):
        pico.configure_interrupts()
        self.user_input_timer_duration = self.timer_duration_choices[0]
        while True:
            mylcd.lcd_display_string(str("Select Duration"), 1)
            self.blink()
            if not self.selecting_timer_duration:
                mylcd.lcd_display_string(str("               "), 1)
                break


# Instantiate new classes
pico = Pico()
display_stats = Display_Stats()

# Start of the program
display_stats.user_input_timer()
while True:
    display_stats.display_current_stats()

    # button_1 switch cuts the shot clock short and increments the inning_counter variables
    if pico.interrupt_1:
        pico.interrupt_1 = 0
        display_stats.countdown()
        if display_stats.awaiting_countdown and display_stats.inning_updated == 0:
            display_stats.update_inning_counter(True)

    # button_2 switch decrements the inning_counter variable, but won't decrement lower than 1.0
    if pico.interrupt_2:
        pico.interrupt_2 = 0
        if display_stats.awaiting_countdown:
            display_stats.update_inning_counter(True)

    # button_3 switch increments the inning_counter variable
    if pico.interrupt_3:
        pico.interrupt_3 = 0
        if display_stats.awaiting_countdown:
            display_stats.update_inning_counter(False)
    
    # button_4 switch 
    if pico.interrupt_4:
        pico.interrupt_4 = 0
        if display_stats.extension:
            display_stats.current_countdown -= 30
            display_stats.extension = False
        else:
            display_stats.extension = True
            display_stats.current_countdown += 30