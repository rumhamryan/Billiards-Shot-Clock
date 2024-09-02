Billiards Shot Clock
This project is for a Raspberry Pi Pico device that can be used for timing all things billiards.
Peripherals are an OLED screen, 4 buttons, an audio ampmlifier with 2 speakers, and a waveshare I2C battery hat.


Peripheral PINOUT

OLED Display
SCK  = GP2 (purple)
MOSI = GP3 (grey)
RST  = GP4 (yellow)
CS   = GP5 (blue)
DC   = GP6 (green)

Buttons (PULL_DOWN)
button_1 = 3v3, GP16 (make button)
button_2 = 3v3, GP17 (up button)
button_3 = 3v3, GP18 (down button)
button_4 = 3v3, GP19 (miss button)

MAX98357A DAC + 3W Amplifier
DIN  = GP10
LRC  = GP11
BCLK = GP12
GAIN = GND
VIN  = 3v3
OUT+ = 4ohm speaker +
OUT- = 4ohm speaker -

TP4056 Li-on Charging Circuit
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
#ultimate pool format
#Need to track extensions a little better, for even and odd inning numbers so each side gets 1 extension per rack


#box improvements
#remove bottom speaker
#bring all threaded insert holes in a little bit
#securing the TP4058
    #post/dowels/guides (on either side of usb-c connector)
    #current tray works perfectly with two small dabs of hot melt, incredible adhesion
#mounting points for the MAX98357A 
    #where the old one was (bottom)
    #just clear/behind of the right button (facing the front panel)
#changing internals
    #pico might be best on the back panel
    #battery could move to the bottom of the enclosure
        #enclosure might be able to shrink to 3"x3"x3"
        #might not work because the battery orientation would be difficult to install or remove
#faceplate idea
    #tilt the OLED module up just a few degrees

