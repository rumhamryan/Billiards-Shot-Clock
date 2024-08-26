Billiards Shot Clock
This project is for a Raspberry Pi Pico device that can be used for timing all things billiards.
Peripherals are an OLED screen, 4 buttons, an audio ampmlifier with 2 speakers, and a waveshare I2C battery hat.


Peripheral PINOUT

OLED Display
SCK  =  2 (purple)
MOSI =  3 (grey)
RST  =  4 (yellow)
CS   =  5 (blue)
DC   =  6 (green)

Buttons (PULL_DOWN)
button_1 = GND, GP16 (make button)
button_2 = GND, GP17 (up button)
button_3 = GND, GP18 (down button)
button_4 = GND, GP19 (miss button)

Audio Ammplifier Circuit
buzzer = GND, GP20
power+ = VSYS
power- = GND

4056 Li-on Charging Circuit
OUT+ = ON/OFF Switch > VSYS
OUT- = GND


Use Cases:
- APA
- BCA
- WNT
- Timeouts Only
- Ultimate Pool (pending)
- One Rack stats (pending)



#Things to add to my firmware release.
#in the framebuf.c file
#-add 'text_scaled' function
#- add the const for 'text_scaled' obj
#- update "STATIC" macro to lowercase

#Compiling my own firmware
deps = 'build-essentials', 'gcc', 'libffi-dev', 'pkg-config'
#0. checkout the version you want to compile
#1. cd to project root
#2. 'make -C mpy-cross'
#3. cd to rp2 folder within the project, /ports/rp2
#4. 'make submodules'
#5. 'make clean'
#6. 'make'

#Things to work on later
#using audio files instead of generating tones using MAX98357A
#ultimate pool format
#Need to track extensions a little better, for even and odd inning numbers so each side gets 1 extension per rack
