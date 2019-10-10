import pygame
from pygame.locals import *


class Struct(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        self.__dict__.update(**kwargs)


class InputManager(object):
   
    def __init__(self):
        self.shouldSaveNewHighScore = False
        self.high_score_key_pressed = False
        self.current_string = ""
        pygame.joystick.init()

        # Initialize a joystick object: grabs the first joystick
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            temp_joystick = pygame.joystick.Joystick(0)
            # TODO: can we use this name usefully for default button configs sony/microsoft?
            # joystick_name = temp_joystick.get_name().upper()
            # print(joystick_name)
            self.joystick = temp_joystick
            self.joystick.init()

        self.button_a = {'key': 0, 'value': 0}
        self.button_b = {'key': 1, 'value': 0}
        self.button_x = {'key': 2, 'value': 0}
        self.button_y = {'key': 3, 'value': 0}
        self.button_left_bumper = {'key': 4, 'value': 0}
        self.button_right_bumper = {'key': 5, 'value': 0}
        self.button_back = {'key': 6, 'value': 0}
        self.button_start = {'key': 7, 'value': 0}
        self.button_left_stick = {'key': 8, 'value': 0}
        self.button_right_stick = {'key': 9, 'value': 0}
        self.x_box_button = {'key': 10, 'value': 0}
        self.controller_buttons = [
            self.button_a, self.button_b, self.button_x, self.button_y,
            self.button_left_bumper, self.button_right_bumper,
            self.button_back, self.button_start]

        self.controller_buttons.append(self.button_left_stick)
        self.controller_buttons.append(self.button_right_stick)

        self.axes = []
        if self.joystick is not None:
            num_axes = self.joystick.get_numaxes()
            for axis in range(num_axes):
                self.axes.append(0.0)

        self.axis_map = {'left_stick_x': 0,
                         'left_stick_y': 1,
                         'left_trigger': 2,
                         'right_stick_x': 3,
                         'right_stick_y': 4,
                         'right_trigger': 5}

    def get_mapped_axis_value(self, name):
        return self.axes[self.axis_map[name]]

    @staticmethod
    def stick_center_snap(value, snap=0.2):
        # Feeble attempt to compensate for calibration and loose stick.
        if value >= snap or value <= -snap:
            return value
        else:
            return 0.0

    def reset_axes(self):
        if self.joystick is not None:
            for index in range(0, len(self.axes)):
                if abs(self.axes[index]) > 0.0:
                    self.axes[index] = self.stick_center_snap(self.joystick.get_axis(index))

    # -----------------------------------------------------
    # Listen for, process and store input events
    # -----------------------------------------------------
    def check_for_game_state_input_events(self, events, input_game_state):
        # self.reset_axes()
        output_game_state = input_game_state

        for event in events: 
            if event.type == QUIT: 
                output_game_state = 'quit'
            elif event.type == JOYAXISMOTION:
                # TODO: don't really want to centre snap for trigger axes
                self.axes[event.axis] = self.stick_center_snap(event.value)

            elif event.type == JOYBUTTONDOWN:
                # print("Button pressed: " + str(event.button))
                self.controller_buttons[event.button]['value'] = 1
                if input_game_state == 'title_screen':
                    output_game_state = 'start_playing'
            elif event.type == JOYBUTTONUP:
                self.controller_buttons[event.button]['value'] = 0
            elif event.type == KEYDOWN:                
                if event.key == K_ESCAPE:
                    output_game_state = 'quit'

                if input_game_state == 'new_high_score':
                    if event.key == K_BACKSPACE:
                        self.current_string = self.current_string[0:-1]
                    elif event.key == K_RETURN:
                        self.shouldSaveNewHighScore = True
                        output_game_state = 'title_screen'
                    elif len(self.current_string) < 3:
                        if event.key == K_MINUS:
                            self.current_string += "_"
                        elif 97 <= event.key <= 122:
                            self.current_string += chr(event.key)
 
                if input_game_state == 'title_screen':
                    # Start a new game
                    if self.high_score_key_pressed:
                        self.high_score_key_pressed = False
                    else:
                        if event.key == K_h:
                            self.high_score_key_pressed = True
                        if event.key == K_RETURN:                                                
                            output_game_state = 'start_playing'

                if event.key == K_f:
                    pygame.display.toggle_fullscreen()
        
        return output_game_state
