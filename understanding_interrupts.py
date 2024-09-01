from machine import Pin
import time

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

# Main loop
while True:
    if interrupt_registered['make']:
        time.sleep_ms(150)  # Debounce delay
        while make_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['make'] = False  # Re-enable interrupt registration

    if interrupt_registered['up']:
        time.sleep_ms(150)  # Debounce delay
        while up_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['up'] = False  # Re-enable interrupt registration

    if interrupt_registered['down']:
        time.sleep_ms(150)  # Debounce delay
        while down_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['down'] = False  # Re-enable interrupt registration

    if interrupt_registered['miss']:
        time.sleep_ms(150)  # Debounce delay
        while miss_button.value() == 1:
            pass  # Wait for button release
        interrupt_registered['miss'] = False  # Re-enable interrupt registration

    time.sleep(0.01)  # Short delay to prevent busy-waiting
