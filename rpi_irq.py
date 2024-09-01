from machine import Pin
import utime

p2 = Pin(16, Pin.IN, Pin.PULL_DOWN)
p2.irq(lambda pin: print("IRQ with flags:", pin.irq().flags()), Pin.IRQ_FALLING)

while True:
    utime.sleep_ms(200)