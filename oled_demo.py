from machine import Pin, SPI
import time
import lib.Pico_OLED_242 as Pico_OLED_242
led = Pin(25, Pin.OUT)

OLED = Pico_OLED_242.OLED_2inch42()

# OLED.fill(0x0000) 
# OLED.show()
# OLED.rect(0,0,127,63,OLED.white)
# OLED.rect(10,6,20,20,OLED.white)
# time.sleep(0.5)
# OLED.show()
# OLED.fill_rect(40,6,20,20,OLED.white)
# time.sleep(0.5)
# OLED.show()
# OLED.rect(70,6,20,20,OLED.white)
# time.sleep(0.5)
# OLED.show()
# OLED.fill_rect(100,6,20,20,OLED.white)
# time.sleep(0.5)
# OLED.show()

# time.sleep(1)

# OLED.fill(0x0000)
# OLED.line(0,0,5,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,20,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,35,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,65,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,95,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,125,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,125,63,OLED.white)
# OLED.show()
# time.sleep(0.1)
# OLED.line(0,0,125,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(0,0,125,63,OLED.white)
# OLED.show()
# time.sleep(0.01)

# OLED.line(127,1,125,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,110,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,95,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,65,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,35,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,1,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,1,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,1,63,OLED.white)
# OLED.show()
# time.sleep(0.01)
# OLED.line(127,1,1,1,OLED.white)
# OLED.show()
# time.sleep(1)



countdown = 10
text_x_axis = 0
text_y_axis = 0
text_size = 8

# def clear_digit_1():
#     OLED.rect(0,0,62,56,OLED.black, True)
#     OLED.show()

# def clear_digit_2():
#     OLED.rect(62,0,66,56,OLED.black, True)
#     OLED.show()

# def clear_both_digits():
#     OLED.rect(0,0,125,56,OLED.black, True)
#     OLED.show()

# for i in range(10, -1, -1):
#     led.toggle()
#     if countdown == 9:
#         clear_both_digits()
#     clear_digit_2()
#     print(countdown)
#     # OLED.text_scaled("Inning Count:", text_x_axis, 57, 1)
#     OLED.text("Inning:1", 0, 57)
#     OLED.text("Rack:1", 75, 57)
#     OLED.show()
#     if countdown < 10:
#         OLED.text_scaled(str(0) + str(countdown), 0, text_y_axis, text_size)
#     else:
#         OLED.text_scaled(str(countdown), 0, text_y_axis, text_size)
#     # OLED.text("128 x 64 Pixels",0,2,OLED.white)
#     # OLED.text("Pico-OLED-2.42",0,12,OLED.white)
#     # OLED.text("SSD1309",0,22,OLED.white)
#     # OLED.text("Waveshare",0,32,OLED.white)
#     OLED.show()
#     time.sleep(1)
#     countdown -= 1

# OLED.text_scaled(str(countdown), 0, 0, 8)
# OLED.text_scaled(str(1), 0, 0, 8)
# OLED.text_scaled("Menu", 24, 2, 2)
# OLED.line(23,18,88,18,OLED.white)
# OLED.line(23,19,88,19,OLED.white)
# OLED.text_scaled("Inning:99", 24, 24, 1)
# OLED.rect(80,24,16,8,OLED.black, True) #counter location
# OLED.rect(8,24,8,8,OLED.white, True) #selector location
# OLED.text_scaled("Rack:99", 24, 40, 1)
# OLED.rect(64,40,16,8,OLED.black, True) #counter location
# OLED.rect(8,40,8,8,OLED.white, True) #selector location
# OLED.text_scaled("Mute:Yes", 24, 56, 1)
# OLED.rect(64,56,24,8,OLED.black, True) #counter location
# OLED.rect(8,56,8,8,OLED.white, True) #selector location
# OLED.rect(8,24,8,64,OLED.black, True) #clear selector locations
# OLED.show()
# time.sleep(10)

OLED.fill(OLED.black)
OLED.show()
# OLED.fill(0x0000) 
# time.sleep(1)
# OLED.fill(0xffff)