from machine import Pin
import utime

# Set up the GPIO pins as input with pull-down resistors
make_button = Pin(16, Pin.IN, Pin.PULL_DOWN)
up_button = Pin(17, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(18, Pin.IN, Pin.PULL_DOWN)
miss_button = Pin(19, Pin.IN, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)

# Define debounce delay in milliseconds
DEBOUNCE_DELAY = 200

# Last time the button was pressed
last_press_time = 0

def debounce_handler(pin):
    global last_press_time
    current_time = utime.ticks_ms()

    # Check if the current press is outside the debounce window
    if (current_time - last_press_time) > DEBOUNCE_DELAY:
        print(f"Button pressed: {pin}")
        print("")
        last_press_time = current_time

# Attach interrupt handlers to each button with the debounce handler
make_button.irq(trigger=Pin.IRQ_RISING, handler=debounce_handler)
up_button.irq(trigger=Pin.IRQ_RISING, handler=debounce_handler)
down_button.irq(trigger=Pin.IRQ_RISING, handler=debounce_handler)
miss_button.irq(trigger=Pin.IRQ_RISING, handler=debounce_handler)

# Start Program
while True:
    utime.sleep(0.05)
