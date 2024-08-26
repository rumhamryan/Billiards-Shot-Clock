from machine import Pin,SPI,I2C
import framebuf
import utime

# Pin definition
SCK  =  2
MOSI =  3
RST  =  4
CS   =  5
DC   =  6

Device_SPI = 1
Device_I2C = 0

if(Device_SPI == 1):
    Device = Device_SPI
else :
    Device = Device_I2C

class OLED_2inch42(framebuf.FrameBuffer):
    def __init__(self):
        self.width  =  128
        self.height =  64
        self.white  =  0xffff
        self.black  =  0x0000
        
        self.cs  =  Pin(CS ,Pin.OUT)
        self.rst =  Pin(RST,Pin.OUT)
        self.dc  =  Pin(DC ,Pin.OUT)
        
        if(Device == Device_SPI):
            self.cs(1)
            self.spi = SPI(0)
            self.spi = SPI(0,1000_000)
            self.spi = SPI(0,10000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
            self.dc(1)     
        else :
            self.dc(0)
            self.cs(0)
            self.i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=1000000)
            self.temp = bytearray(2)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()
        
    def write_cmd(self, cmd):
        if(Device == Device_SPI):
            self.cs(1)
            self.dc(0)
            self.cs(0)
            self.spi.write(bytearray([cmd]))
            self.cs(1)
        else :
            self.temp[0] = 0x00 # Co=1, D/C#=0
            self.temp[1] = cmd
            self.i2c.writeto(0x3c, self.temp)

    def write_data(self, buf):
        if(Device == Device_SPI):
            self.cs(1)
            self.dc(1)
            self.cs(0)
            self.spi.write(bytearray([buf]))
            self.cs(1)
        else :
            self.temp[0] = 0x40 # Co=1, D/C#=0
            self.temp[1] = buf
            self.i2c.writeto(0x3c, self.temp)

    def init_display(self):
        """Initialize display"""  
        self.rst(1)
        utime.sleep(0.001)
        self.rst(0)
        utime.sleep(0.01)
        self.rst(1)
        
        self.write_cmd(0xAE)# Turn off the display

        self.write_cmd(0x00)# Set low column address
        self.write_cmd(0x10)# Set high column address
    
        self.write_cmd(0x20)# Set memory addressing mode
        self.write_cmd(0x00)# Horizontal addressing mode
        
        self.write_cmd(0xC8)# Set COM scan direction
        self.write_cmd(0xA6)# Set normal/inverse display
        
        self.write_cmd(0xA8)# Set multiplex ratio
        self.write_cmd(0x3F)# Set ratio to 63
        
        self.write_cmd(0xD3)# Set display offset
        self.write_cmd(0x00)# Offset value is 0
    
        self.write_cmd(0xD5)# Set display clock divide ratio/oscillator frequency
        self.write_cmd(0x80)# Default divide ratio
    
        self.write_cmd(0xD9)# Set pre-charge period
        self.write_cmd(0x22)# Default value
    
        self.write_cmd(0xDA)# Set COM pin configuration
        self.write_cmd(0x12)# Default configuration
    
        self.write_cmd(0xDB)# Set VCOMH
        self.write_cmd(0x40)# Default value
        
        self.write_cmd(0xA1)# Set segment remap
        self.write_cmd(0xAF)# Turn on the display

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def show(self):
        for page in range(0,8):
            self.write_cmd(0xb0 + page)
            self.write_cmd(0x04)
            self.write_cmd(0x00)
            if(Device == Device_SPI):
                self.dc(1)
            for num in range(0,128):
                self.write_data(self.buffer[page*128+num])
        
