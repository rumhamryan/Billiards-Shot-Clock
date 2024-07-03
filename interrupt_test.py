from machine import Pin, PWM # type: ignore
import I2C_LCD_driver
import utime # type: ignore
import _thread # type: ignore

mylcd = I2C_LCD_driver.lcd()

#######################################
# 1. Figure out how to change exit interrupt detection for threading, also how to exit the thread:  DONE
# 2. Add a buzzer:    DONE
# 3. Consider a method to skip the current countdown or reset the current countdown to default duration:    DONE
# 4. Might need to pull the blink function apart into separate smaller functions:   DONE
# 5. A button (or repurpose one) that adds a 30 second extension:    DONE
# 6. Create APA or WPA 'profiles' that update the shot clock and extension values:  DONE
# 7. Can button_1 and button_2 being held together signal an automatic 60 second shot clock when the "Mosconi" profile has been selected
#     a. might consider opening a thread while awaiting_countdown to check for the button combo
#     b. should be able to use the two cores to monitor the buttons simultaneously, then exit the extra thread if only button_1 is pressed
# bug or feature?: before the first countdown, you cannot increment or decrement the inning_counter variable
# bug: the new make/miss buttons register twice during a medium and long duartion pressse, short presses only register once
#       fix: start a timer on the first press, ignore interrupts for 1 or 2 seconds, maybe like 5, it seems unlikely someone would hold a button that long
#######################################


debounce_time = 0

interrupt_1 = 0
interrupt_2 = 0
interrupt_3 = 0
interrupt_4 = 0

recall_interrupt = False

button_1_interrupt = False
interrupt_1_timer = 0
button_2_interrupt = False
interrupt_2_timer = 0
button_3_interrupt = False
interrupt_3_timer = 0
button_4_interrupt = False
interrupt_4_timer = 0

button_1 = Pin(16, Pin.IN, Pin.PULL_DOWN)
button_2 = Pin(17, Pin.IN, Pin.PULL_UP)
button_3 = Pin(18, Pin.IN, Pin.PULL_UP)
button_4 = Pin(19, Pin.IN, Pin.PULL_DOWN)

led = Pin(25, Pin.OUT)
buzzer = PWM(Pin(20))
buzzer_5_count = 4

# This function is called each time an interrupt is issued from the "button_1" switch
def interrupt_1_handler():
    global interrupt_1, debounce_time
    if (utime.ticks_ms() - debounce_time) > 200:
        interrupt_1 = 1
        debounce_time = utime.ticks_ms()

def button_1_thread():
    global button_1_interrupt
    while True:
        if button_1.value() == 1:
            button_1_interrupt = True
        
# This function is called each time an interrupt is issued from the "button_2" switch
def interrupt_2_handler():
    global interrupt_2, debounce_time
    if (utime.ticks_ms() - debounce_time) > 120:
        interrupt_2 = 1
        debounce_time = utime.ticks_ms()

# This function is called each time an interrupt is issued from the "button_3" switch
def interrupt_3_handler():
    global interrupt_3, debounce_time
    if (utime.ticks_ms() - debounce_time) > 120:
        interrupt_3 = 1
        debounce_time = utime.ticks_ms()

# This function is called each time an interrupt is issued from the "button_4" switch
def interrupt_4_handler():
    global interrupt_4, debounce_time
    if (utime.ticks_ms() - debounce_time) > 200:
        interrupt_4 = 1
        debounce_time = utime.ticks_ms()

def buzzer_toggle(duration):
    global buzzer, buzzer_5_count
    if buzzer_5_count == 0:
        buzzer.freq(750)
        buzzer_5_count = 4
    else:
        buzzer.freq(500)
        buzzer_5_count -= 1
    buzzer.duty_u16(250)
    utime.sleep(duration)
    buzzer.duty_u16(0)

def configure_interrupts(thread: bool = False):
    if thread:
        # These are the actual interrupt request to the 2040 controller
        button_1.irq(trigger = 0, handler = None)
        button_2.irq(trigger = 0, handler = None)
        button_3.irq(trigger = 0, handler = None)
        # _thread.start_new_thread(button_1_thread, ())
    else:
        # These are the actual interrupt request to the 2040 controller
        button_1.irq(trigger = Pin.IRQ_RISING, handler = interrupt_1_handler)
        button_2.irq(trigger = Pin.IRQ_RISING, handler = interrupt_2_handler)
        button_3.irq(trigger = Pin.IRQ_RISING, handler = interrupt_3_handler)
        button_4.irq(trigger = Pin.IRQ_RISING, handler = interrupt_4_handler)
        # if _thread.get_ident != 0:
        #     _thread.exit()

button_1.irq(trigger = Pin.IRQ_RISING, handler = interrupt_1_handler)
button_2.irq(trigger = Pin.IRQ_RISING, handler = interrupt_2_handler)
button_3.irq(trigger = Pin.IRQ_RISING, handler = interrupt_3_handler)
button_4.irq(trigger = Pin.IRQ_RISING, handler = interrupt_4_handler)


# Start of the program
while True:
    # button_1 switch cuts the shot clock short and increments the inning_counter variables
    if interrupt_1:
        if (utime.ticks_ms() - debounce_time) > 200:
            print("interrupt_1: 1")
            debounce_time = utime.ticks_ms()
            interrupt_1 = 0

    # button_2 switch decrements the inning_counter variable, but won't decrement lower than 1.0
    if interrupt_2:
        print("interrupt_2: 1")
        interrupt_2 = 0

    # button_3 switch increments the inning_counter variable
    if interrupt_3:
        print("interrupt_3: 1")
        interrupt_3 = 0
    
    # button_4 switch 
    if interrupt_4:
        if (utime.ticks_ms() - debounce_time) > 200:
            print("interrupt_4: 1")
            debounce_time = utime.ticks_ms()
            interrupt_4 = 0

