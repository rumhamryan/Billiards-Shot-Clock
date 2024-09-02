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

