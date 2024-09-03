##################################################
# 3 minute challenge (british 8-ball)
# Average 2 things for one rack: average time between shots and make miss ratio
##################################################


from machine import Pin, PWM # type: ignore
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
        if (current_time - debounce_time) > 5:  # Shorter initial debounce
            if pin.value() == 0:  # Button pressed
                debounce_time = current_time
                button_state = "PRESSED"

    elif button_state == "PRESSED":
        if (current_time - debounce_time) > 20:  # Longer debounce before acknowledging press
            if pin.value() == 0:
                print(f"Button pressed: {pin}")
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


# Start Program
while True:

    if make_button.value():
        while make_button.value():
            utime.sleep_ms(100)
        # print("make button")

    if up_button.value():
        while up_button.value():
            utime.sleep_ms(100)
        # print("up button")

    if down_button.value():
        while down_button.value():
            utime.sleep_ms(100)
        # print("down button")

    if miss_button.value():
        while miss_button.value():
            utime.sleep_ms(100)
        # print("miss button")

    utime.sleep(.05)