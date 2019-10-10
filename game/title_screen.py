import pygame
from game.high_scores import reload_characters


# ------------------------------------------------------------------------
# Title Menu class
# ------------------------------------------------------------------------
class TitleScreen(object):

    def __init__(self, stage, fonts):
        self.stage = stage
        self.show_high_score_table = False
        # noinspection PyArgumentList
        self.game_title_colour = pygame.color.Color('#FAB243')
        self.fonts = fonts

        self.high_scores = []
        self.high_scores = reload_characters(self.high_scores)

        self.title_text = self.fonts[2].render(self.stage.game_title, True, self.game_title_colour)
        self.title_text_rect = self.title_text.get_rect(centerx=self.stage.width / 2)
        self.title_text_rect.y = self.stage.height / 2 - self.title_text_rect.height

        self.keys_text = self.fonts[0].render('Arrow keys for steering and thrust, space bar to fire guns,'
                                              ' shift to fire a missile, Esc to quit (or use a 360 game-pad!)',
                                              True, (255, 255, 255))
        self.keys_text_rect = self.keys_text.get_rect(centerx=self.stage.width / 2)
        self.keys_text_rect.y = self.stage.height / 2 - self.keys_text_rect.height / 2

        self.highscore_text = self.fonts[0].render('Press \'H\' for high scores!', True, (255, 255, 255))
        self.highscore_text_rect = self.highscore_text.get_rect(centerx=self.stage.width / 2)
        self.highscore_text_rect.y = self.stage.height / 2 + self.highscore_text_rect.height

        self.instruction_text = self.fonts[1].render('Press Enter To Play', True, (255, 255, 255))
        self.instruction_text_rect = self.instruction_text.get_rect(centerx=self.stage.width / 2)
        self.instruction_text_rect.y = self.stage.height / 2 + self.instruction_text_rect.height

        self.high_scores_title_text = self.fonts[1].render('High Scores', True, self.game_title_colour)
        self.high_scores_title_text_rect = self.high_scores_title_text.get_rect(centerx=self.stage.width / 2)
        self.high_scores_title_text_rect.y = 40

        self.press_any_key_text_render = self.fonts[0].render("Press any key to return to title screen",
                                                              True, pygame.Color("#FFFFFF"))

    # displays the text in the title menu that displays when you start the game
    # and after each time you lose all your lives
    def display_title_menu_text(self):
        if not self.show_high_score_table:

            self.stage.screen.blit(self.title_text, self.title_text_rect)
            self.stage.screen.blit(self.keys_text, self.keys_text_rect)
            self.stage.screen.blit(self.highscore_text, self.highscore_text_rect)
            self.stage.screen.blit(self.instruction_text, self.instruction_text_rect)

        elif self.show_high_score_table:

            self.stage.screen.blit(self.high_scores_title_text, self.high_scores_title_text_rect)

            character_number = 0
            while character_number < 10 and character_number < len(self.high_scores):
                character = self.high_scores[character_number]
                char_str = str(character_number + 1) + ". " + character.name.upper()
                level_str = " - Stage: " + str(character.stage) + " - {:,}".format(character.score)
                final_char_str = char_str + level_str
                select_char_text_render = self.fonts[0].render(final_char_str, True, pygame.Color("#FFFFFF"))
                self.stage.screen.blit(select_char_text_render,
                                       select_char_text_render.get_rect(x=self.stage.width * 0.4,
                                                                        y=120 + (40 * character_number)))
                character_number += 1

            self.stage.screen.blit(self.press_any_key_text_render,
                                   self.press_any_key_text_render.get_rect(centerx=self.stage.width * 0.5,
                                                                           centery=(self.stage.height * 0.9)))
