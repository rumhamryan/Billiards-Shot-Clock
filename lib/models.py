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
    def __init__(self):
        self.profile_based_countdown = 0
        self.countdown = 0
        self.extension_duration = 0
        self.extension_available = True
        self.extension_used = False
        self.player_1_shooting = True
        self.player_1_extension_available = True
        self.player_2_shooting = False
        self.player_2_extension_available = True
        self.inning_counter = 1.0
        self.rack_counter = 1
        self.break_shot = True
        self.speaker_muted = False
        self.speaker_5_count = 4
        self.game_profiles = {
            "APA": {"timer_duration": 20, "extension_duration": 25},
            "WNT": {"timer_duration": 30, "extension_duration": 30},
            "BCA": {"timer_duration": 45, "extension_duration": 45},
            "Timeouts Mode": {"timer_duration": 60, "extension_duration": 0},
        }
        self.selected_profile = None
        self.timeouts_only = False
        self.menu_items = ["Rack", "Mute", "Inning"]
        self.menu_values = [
            self.rack_counter,
            self.speaker_muted,
            int(self.inning_counter),
        ]
        self.current_menu_index = 0
        self.current_menu_selection = [
            None,
            self.menu_items[self.current_menu_index],
            None,
        ]
        self.current_menu_values = [
            None,
            self.menu_values[self.current_menu_index],
            None,
        ]

        # New State Tracking Variables
        self.profile_selection_index = 0
        self.temp_setting_value = None

    def update_menu_selection(
        self,
        oled,
        state_machine,
        display_clear_func,
        display_text_func,
        display_shape_func,
        send_payload=True,
        clear_before_payload=True,
    ):
        prev_index = (self.current_menu_index - 1) % len(self.menu_items)
        next_index = (self.current_menu_index + 1) % len(self.menu_items)

        self.current_menu_selection = [
            self.menu_items[prev_index],
            self.menu_items[self.current_menu_index],
            self.menu_items[next_index],
        ]
        self.current_menu_values = [
            self.menu_values[prev_index],
            self.menu_values[self.current_menu_index],
            self.menu_values[next_index],
        ]

        if send_payload:
            if clear_before_payload:
                display_clear_func(oled, "menu_items")
            display_text_func(
                oled,
                state_machine,
                f"{self.current_menu_selection[0]}:{self.current_menu_values[0]}",
                24,
                24,
                1,
                False,
            )
            display_text_func(
                oled,
                state_machine,
                f"{self.current_menu_selection[1]}:{self.current_menu_values[1]}",
                24,
                40,
                1,
                False,
            )
            display_text_func(
                oled,
                state_machine,
                f"{self.current_menu_selection[2]}:{self.current_menu_values[2]}",
                24,
                56,
                1,
                False,
            )
            display_shape_func(oled, "rect", 8, 40, 8, 8, True)
