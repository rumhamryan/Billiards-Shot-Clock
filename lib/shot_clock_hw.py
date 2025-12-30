from machine import I2S, Pin # type: ignore
import _thread # type: ignore
from lib.shot_clock_config import (
    I2S_ID, I2S_SCK_PIN, I2S_WS_PIN, I2S_SD_PIN, 
    I2S_RATE, I2S_BITS, DISPLAY_REGIONS
)

def display_text(oled, state_machine, payload, x, y, font_size, send_payload=True):
    """
    Displays a text string on the OLED screen.
    """
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        x = 0
        font_size = 2
        
    oled.text_scaled(str(payload), x, y, font_size)
    
    if payload == "Timeouts Mode" and state_machine.profile_selection:
        oled.text_scaled("Mode", 32, 48, 2)
    
    if send_payload:
        oled.show()

def display_shape(oled, payload, x, y, width, height, send_payload=True):
    """
    Draws a shape on the OLED display.
    """
    if payload == "line":
        oled.line(x, y, width, height, oled.white)
    elif payload == "rect":
        oled.rect(x, y, width, height, oled.white, True)

    if send_payload:
        oled.show()

def display_clear(oled, *regions, send_payload=True):
    """
    Clears specified sections of the OLED display.
    """
    for region in regions:
        if region in DISPLAY_REGIONS:
            x, y, width, height = DISPLAY_REGIONS[region]
            oled.rect(x, y, width, height, oled.black, True)

    if send_payload:
        oled.show()

def process_timer_duration(duration):
    """
    Formats duration as a string with leading zeros.
    """
    return f"{duration:02d}"

def shot_clock_beep():
    """
    Plays the shot clock beep via Core 1.
    """
    audio_out = I2S(
        I2S_ID,
        sck=Pin(I2S_SCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.TX,
        bits=I2S_BITS,
        format=I2S.MONO,
        rate=I2S_RATE,
        ibuf=20000
    )
    
    try:
        with open("beep.wav", "rb") as wav_file:
            wav_file.seek(80) # Skip header
            wav_buffer = bytearray(1024)
            while True:
                num_read = wav_file.readinto(wav_buffer)
                if num_read == 0:
                    break
                audio_out.write(wav_buffer)
    finally:
        audio_out.deinit()
