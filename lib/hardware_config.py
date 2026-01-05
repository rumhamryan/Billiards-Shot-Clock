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
    "profile_title_selection": (0, 0, 128, 20),
    "profile_selection": (0, 20, 128, 44),
    "confirmation_message": (0, 0, 128, 56),
    "profile_selection_value": (0, 30, 128, 24),
    "profile_selection_alt_value": (0, 30, 128, 16),
    "profile_selection_alt_value_2": (0, 48, 128, 16),
    "skill_level_player": (0, 10, 128, 8),
    "skill_level_label": (0, 25, 128, 8),
    "skill_level_value": (0, 40, 128, 24),
    "game_type_title": (0, 10, 128, 8),
    "game_type_value": (0, 30, 128, 16),
    "wnt_target_title": (0, 10, 128, 8),
    "wnt_target_value": (0, 30, 128, 24),
    "victory_title": (0, 10, 128, 16),
    "victory_winner": (0, 35, 128, 16),
    "p1_timeout_counter_1": (40, 58, 4, 4),
    "p1_timeout_counter_2": (48, 58, 4, 4),
    "p1_timeout_single": (44, 58, 4, 4),
    "p1_timeouts": (40, 58, 12, 4),
    "p2_timeout_counter_1": (76, 58, 4, 4),
    "p2_timeout_counter_2": (84, 58, 4, 4),
    "p2_timeout_single": (80, 58, 4, 4),
    "p2_timeouts": (77, 58, 12, 4),
    "shot_clock_full": (0, 0, 128, 56),
    "shot_clock_digit_1": (0, 0, 64, 56),
    "shot_clock_digit_2": (64, 0, 64, 56),
    "match_clock_full": (41, 56, 46, 8),
    "match_clock_full_s": (48, 56, 32, 8),
    "match_clock_digit_1": (43, 56, 8, 8),
    "match_clock_digit_2": (52, 56, 8, 8),
    "match_clock_digit_3": (68, 56, 8, 8),
    "match_clock_digit_4": (77, 56, 8, 8),
    "match_clock_digit_2_s": (48, 56, 8, 8),
    "match_clock_digit_3_s": (63, 56, 8, 8),
    "match_clock_digit_4_s": (72, 56, 8, 8),
    "match_clock_colon": (60, 56, 8, 8),
    "match_clock_colon_s": (56, 56, 8, 8),
    "timeouts_mode_title": (12, 56, 104, 8),
    "up_indicator_1": (33, 56, 8, 8),
    "up_indicator_2": (87, 56, 8, 8),
    "up_indicator_1_s": (39, 56, 8, 8),
    "up_indicator_2_s": (81, 56, 8, 8),
    "menu_selector": (8, 24, 8, 64),
    "menu_items": (24, 24, 80, 40),
    "menu_line_prev": (24, 24, 80, 8),
    "menu_line_curr": (24, 40, 80, 8),
    "menu_line_next": (24, 56, 80, 8),
    "menu_cursor": (8, 40, 8, 8),
    "menu_header_left": (0, 2, 64, 16),
    "menu_header_right": (66, 2, 64, 16),
    "menu_separator_top": (0, 19, 128, 1),
    "menu_separator_bottom": (0, 20, 128, 1),
    "menu_value_counter": (55, 40, 17, 8),
    "menu_value_bool": (64, 40, 40, 8),
    "p1_score": (0, 56, 14, 8),
    "p1_separator": (14, 56, 8, 8),
    "p1_target": (22, 56, 14, 8),
    "p2_score": (91, 56, 14, 8),
    "p2_separator": (105, 56, 8, 8),
    "p2_target": (113, 56, 14, 8),
    "up_p1_score": (0, 56, 8, 8),
    "up_p1_separator": (8, 56, 8, 8),
    "up_p1_target": (16, 56, 8, 8),
    "up_p2_score": (104, 56, 8, 8),
    "up_p2_separator": (112, 56, 8, 8),
    "up_p2_target": (120, 56, 8, 8),
    "up_shootout_current_shooter": (0, 0, 128, 20),
    "up_shootout_stop_watch": (0, 22, 128, 20),
    "up_shootout_p1_title": (0, 44, 128, 12),
    "up_shootout_p1_time": (0, 56, 128, 8),
    "shooter_indicator_1": (55, 56, 8, 8),
    "shooter_indicator_2": (65, 56, 8, 8),
    "scoreline_rack": (0, 56, 56, 8),
    "scoreline_inning": (57, 56, 64, 8),
}

# Shared Debounce Setting
DEBOUNCE_DELAY = 200
