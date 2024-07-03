GND(38) = GND

SDA, LCD = GP0
SCL, LCD = GP1
VCC, LCD = VBUS
GND, LCD = GND

button_1 = GND, GP16 (make button)
button_2 = GND, GP17 (up button)
button_3 = GND, GP18 (down button)
button_4 = GND, GP19 (miss button)

buzzer = GND, GP20



ways to organize the code:

functions:
    wait for countdown with reset timer function (1s intervals)
    countdown
    blink for countdown completion and await reset (1s intervals)

can I use machine.idle() for a low power state (mostly to save the OLED display)?



states:

profile selection   (profiles blinks)
shot clock idle     (display profile based timer selection)
countdown           (the countdown)
countdown complete  ("00" blinks)
