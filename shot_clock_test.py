from machine import I2S, Pin, PWM # type: ignore
import lib.Pico_OLED_242 as Pico_OLED_242 # type: ignore
import _thread # type: ignore
import utime # type: ignore

file_name = "beep_3_processed.wav"
is_playing = False  # Flag to indicate if the sound is currently playing

class State_Machine:
    def __init__(self, profile_selection = True, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False, game_on = False):

        self.profile_selection: bool = profile_selection
        self.shot_clock_idle: bool = shot_clock_idle
        self.countdown_in_progress: bool = countdown_in_progress
        self.countdown_complete: bool = countdown_complete
        self.game_on: bool = game_on

    def update_state(self, profile_selection = False, shot_clock_idle = False, countdown_in_progress = False, countdown_complete = False):
        if profile_selection:
            self.profile_selection = True
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = False
        elif shot_clock_idle:
            self.profile_selection = False
            self.shot_clock_idle = True
            self.countdown_in_progress = False
            self.countdown_complete = False
        elif countdown_in_progress:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = True
            self.countdown_complete = False
        elif countdown_complete:
            self.profile_selection = False
            self.shot_clock_idle = False
            self.countdown_in_progress = False
            self.countdown_complete = True

# Used to track the game stats
class Game_Stats:
    def __init__(self,profile_based_countdown = 7, countdown = 7, extension_duration = 0, extension_available = True, extension_used = False, inning_counter= 1.0, rack_counter = 1, break_shot = True, speaker_5_count = 4,
                 game_profiles = {"APA": {"timer_duration": 20, "extension_duration": 25}, 
                                  "WNT": {"timer_duration": 30, "extension_duration": 30}, 
                                  "BCA": {"timer_duration": 45, "extension_duration": 45},
                                  "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}},
                selected_profile = None, timeouts_only = False):

        self.profile_based_countdown: int = profile_based_countdown
        self.countdown: int = countdown
        self.extension_duration: int = extension_duration
        self.extension_available: bool = extension_available
        self.extension_used: bool = extension_used
        self.inning_counter: float = inning_counter
        self.rack_counter: int = rack_counter
        self.break_shot: bool = break_shot
        self.speaker_5_count: int = speaker_5_count
        self.game_profiles: dict = game_profiles
        self.selected_profile: str = selected_profile
        self.timeouts_only: bool = timeouts_only

# Instantiate Classes
state_machine = State_Machine()
game = Game_Stats()
OLED = Pico_OLED_242.OLED_2inch42()

def shot_clock():
    state_machine.update_state(countdown_in_progress=True)
    countdown_checker = utime.time()
    
    while game.countdown > 0:
        if utime.time() - countdown_checker > 0: # udpate display once every second
            game.countdown -= 1
            countdown_check = game.countdown

            if game.countdown < 5:
                _thread.start_new_thread(shot_clock_beep, ())
            
            print(game.countdown)
            countdown_checker = utime.time()

            if game.countdown == 0:
                off = True
                state_machine.update_state(countdown_complete=True)

                countdown_checker = utime.time()

def shot_clock_beep():
    global is_playing
    if is_playing:
        return  # Skip if a beep is already playing
    
    is_playing = True  # Set the flag to indicate playback has started

    # Initialize I2S
    audio_out = I2S(
        0,
        sck=Pin(11),   # BCLK
        ws=Pin(12),    # LRC
        sd=Pin(10),     # DIN
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=48000,    # Sample rate, should match the .wav file
        ibuf=20000     # Buffer size
    )
    # Open WAV file
    wav_file = open(file_name, "rb")

    # Skip WAV header (typically 44 bytes)
    wav_file.seek(80)

    # Buffer to hold audio data
    wav_buffer = bytearray(1024)

    # Play audio
    try:
        while True:
            num_read = wav_file.readinto(wav_buffer)
            if num_read == 0:
                break  # End of file
            audio_out.write(wav_buffer)
    finally:
        # Cleanup
        wav_file.close()
        audio_out.deinit()
        is_playing = False  # Reset the flag after playback completes

shot_clock()