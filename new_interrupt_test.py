##################################################
# 3 minute challenge (british 8-ball)
# Average 2 things for one rack: average time between shots and make miss ratio
##################################################


from machine import Pin, PWM # type: ignore
import utime # type: ignore
    
# Configure I/Os
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)

# This interrupt handling
def interrupt_handler(Pin):
    debounce_time = utime.ticks_ms()
    if (utime.ticks_ms() - debounce_time) > 200:
        debounce_time = utime.ticks_ms()

# Configure interrupts
make_button.irq(trigger = Pin.IRQ_RISING, handler = interrupt_handler)
up_button.irq(trigger = Pin.IRQ_RISING, handler = interrupt_handler)
down_button.irq(trigger = Pin.IRQ_RISING, handler = interrupt_handler)
miss_button.irq(trigger = Pin.IRQ_RISING, handler = interrupt_handler)


# Start Program
while True:

    if make_button.value():
        while make_button.value():
            utime.sleep(.1)
        print("make button")

    if up_button.value():
        while up_button.value():
            utime.sleep(.1)
        print("up button")

    if down_button.value():
        while down_button.value():
            utime.sleep(.1)
        print("down button")

    if miss_button.value():
        while miss_button.value():
            utime.sleep(.1)
        print("miss button")

    utime.sleep(.05)