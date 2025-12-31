from machine import I2S, Pin

from lib.hardware_config import (
    I2S_BITS,
    I2S_ID,
    I2S_RATE,
    I2S_SCK_PIN,
    I2S_SD_PIN,
    I2S_WS_PIN,
)


def shot_clock_beep():
    """Plays the shot clock beep via Core 1."""

    audio_out = None
    try:
        audio_out = I2S(
            I2S_ID,
            sck=Pin(I2S_SCK_PIN),
            ws=Pin(I2S_WS_PIN),
            sd=Pin(I2S_SD_PIN),
            mode=I2S.TX,
            bits=I2S_BITS,
            format=I2S.MONO,
            rate=I2S_RATE,
            ibuf=20000,
        )

        with open("beep.wav", "rb") as wav_file:
            wav_file.seek(80)  # Skip header

            wav_buffer = bytearray(1024)

            while True:
                num_read = wav_file.readinto(wav_buffer)

                if num_read == 0:
                    break

                audio_out.write(wav_buffer)

    except Exception:
        pass  # Be silent on error (missing file, etc)

    finally:
        if audio_out:
            try:
                audio_out.deinit()
            except Exception:
                pass
