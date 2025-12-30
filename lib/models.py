class State_Machine:
    PROFILE_SELECTION = "profile_selection"
    SHOT_CLOCK_IDLE = "shot_clock_idle"
    COUNTDOWN_IN_PROGRESS = "countdown_in_progress"
    COUNTDOWN_COMPLETE = "countdown_complete"
    MENU = "menu"
    EDITING_VALUE = "editing_value"

    def __init__(self, initial_state=PROFILE_SELECTION):
        self.state = initial_state
        self.game_on = False

    def update_state(self, new_state):
        self.state = new_state

    @property
    def profile_selection(self):
        return self.state == self.PROFILE_SELECTION

    @property
    def shot_clock_idle(self):
        return self.state == self.SHOT_CLOCK_IDLE

    @property
    def countdown_in_progress(self):
        return self.state == self.COUNTDOWN_IN_PROGRESS

    @property
    def countdown_complete(self):
        return self.state == self.COUNTDOWN_COMPLETE

    @property
    def menu(self):
        return self.state == self.MENU

    @property
    def editing_value(self):
        return self.state == self.EDITING_VALUE

class Game_Stats:
    def __init__(self, profile_based_countdown=0, countdown=0, extension_duration=0, 
                 extension_available=True, extension_used=False, player_1_shooting=True, 
                 player_1_extension_available=True, player_2_shooting=False, 
                 player_2_extension_available=True, inning_counter=1.0, rack_counter=1, 
                 break_shot=True, speaker_muted=False, speaker_5_count=4,
                 game_profiles=None, selected_profile=None, timeouts_only=False,
                 menu_items=None, menu_values=None, current_menu_index=0,
                 current_menu_selection=None, current_menu_values=None,
                 profile_selection_index=0, temp_setting_value=None):
        
        self.profile_based_countdown = profile_based_countdown
        self.countdown = countdown
        self.extension_duration = extension_duration
        self.extension_available = extension_available
        self.extension_used = extension_used
        self.player_1_shooting = player_1_shooting
        self.player_1_extension_available = player_1_extension_available
        self.player_2_shooting = player_2_shooting
        self.player_2_extension_available = player_2_extension_available
        self.inning_counter = inning_counter
        self.rack_counter = rack_counter
        self.break_shot = break_shot
        self.speaker_muted = speaker_muted
        self.speaker_5_count = speaker_5_count
        self.game_profiles = game_profiles or {
            "APA": {"timer_duration": 20, "extension_duration": 25}, 
            "WNT": {"timer_duration": 30, "extension_duration": 30}, 
            "BCA": {"timer_duration": 45, "extension_duration": 45},
            "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0}
        }
        self.selected_profile = selected_profile
        self.timeouts_only = timeouts_only
        self.menu_items = menu_items or ["Rack", "Mute", "Inning"]
        self.menu_values = menu_values or [rack_counter, speaker_muted, int(inning_counter)]
        self.current_menu_index = current_menu_index
        self.current_menu_selection = current_menu_selection or [None, self.menu_items[current_menu_index], None]
        self.current_menu_values = current_menu_values or [None, self.menu_values[current_menu_index], None]
        
        # New State Tracking Variables
        self.profile_selection_index = profile_selection_index
        self.temp_setting_value = temp_setting_value

    def update_menu_selection(self, oled, state_machine, display_clear_func, display_text_func, display_shape_func, send_payload=True, clear_before_payload=True):
        prev_index = (self.current_menu_index - 1) % len(self.menu_items)
        next_index = (self.current_menu_index + 1) % len(self.menu_items)

        self.current_menu_selection = [self.menu_items[prev_index], self.menu_items[self.current_menu_index], self.menu_items[next_index]]
        self.current_menu_values = [self.menu_values[prev_index], self.menu_values[self.current_menu_index], self.menu_values[next_index]]

        if send_payload:
            if clear_before_payload:
                display_clear_func(oled, "menu_items")
            display_text_func(oled, state_machine, f"{self.current_menu_selection[0]}:{self.current_menu_values[0]}", 24, 24, 1, False)
            display_text_func(oled, state_machine, f"{self.current_menu_selection[1]}:{self.current_menu_values[1]}", 24, 40, 1, False)
            display_text_func(oled, state_machine, f"{self.current_menu_selection[2]}:{self.current_menu_values[2]}", 24, 56, 1, False)
            display_shape_func(oled, "rect", 8, 40, 8, 8, True)
