# Pin Definitions
MAKE_PIN = 16
UP_PIN = 17
DOWN_PIN = 18
MISS_PIN = 19

# OLED Pins
OLED_SCK_PIN = 2
OLED_MOSI_PIN = 3
OLED_RST_PIN = 4
OLED_CS_PIN = 5
OLED_DC_PIN = 6

# Audio Settings
I2S_ID = 0
I2S_SCK_PIN = 11
I2S_WS_PIN = 12
I2S_SD_PIN = 10
I2S_RATE = 48000
I2S_BITS = 16

# OLED Regions (x, y, width, height)
DISPLAY_REGIONS = {
    "everything": (0, 0, 128, 64),
    "profile_selection": (0, 20, 128, 44),
    "inning_counter": (55, 55, 17, 9),
    "rack_counter": (113, 57, 14, 8),
    "timeout_counter_1": (38, 59, 4, 4),
    "timeout_counter_2": (80, 59, 4, 4),
    "shot_clock_full": (0, 0, 125, 56),
    "shot_clock_digit_1": (0, 0, 62, 56),
    "shot_clock_digit_2": (62, 0, 66, 56),
    "match_clock_full": (39, 57, 46, 8),
    "match_clock_digit_1": (44, 57, 8, 8),
    "match_clock_digit_2": (53, 57, 8, 8),
    "match_clock_digit_3": (69, 57, 8, 8),
    "match_clock_digit_4": (77, 57, 8, 8),
    "match_clock_digit_1_s": (39, 57, 8, 8),
    "match_clock_digit_2_s": (48, 57, 8, 8),
    "match_clock_digit_3_s": (64, 57, 8, 8),
    "match_clock_digit_4_s": (72, 57, 8, 8),
    "menu_selector": (8, 24, 8, 64),
    "menu_items": (24, 24, 80, 40),
    "menu_inning_counter": (80, 40, 17, 8),
    "menu_rack_counter": (64, 40, 17, 8),
    "menu_mute_bool": (64, 40, 40, 8),
}

# Shared Debounce Setting
DEBOUNCE_DELAY = 200
