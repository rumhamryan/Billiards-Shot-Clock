Billiards Shot Clock
This project is for a Raspberry Pi Pico device that can be used for timing all things billiards.
Peripherals are an OLED screen, 4 buttons, a buzzer and a waveshare I2C battery hat.


Peripheral PINOUT

OLED Display
SCK  =  2
MOSI =  3
RST  =  4
CS   =  5
DC   =  6

Buttons (PULL_DOWN)
button_1 = GND, GP16 (make button)
button_2 = GND, GP17 (up button)
button_3 = GND, GP18 (down button)
button_4 = GND, GP19 (miss button)

Buzzer
buzzer = GND, GP20


Use Cases:
- APA
- BCA
- Mosconi
- Timeouts Only
- One Rack stats (pending)
