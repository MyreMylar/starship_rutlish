import os
import os.path
import csv
import pygame
from operator import attrgetter


class HighScoreEntry:

    def __init__(self, stage, fonts):
        self.stage = stage

        # noinspection PyArgumentList
        self.game_title_colour = pygame.color.Color('#FAB243')
        self.font1 = fonts[1]
        self.font2 = fonts[0]

    def display(self, entered_text):

        title_text = self.font1.render('New High Score!', True, self.game_title_colour)
        title_text_rect = title_text.get_rect(centerx=self.stage.width/2)
        title_text_rect.y = 100
        self.stage.screen.blit(title_text, title_text_rect)

        select_char_text_render = self.font2.render("Enter name: " + entered_text.upper(),
                                                    True, pygame.Color("#FFFFFF"))
        self.stage.screen.blit(select_char_text_render,
                               select_char_text_render.get_rect(x=self.stage.width*0.38, y=200))

        press_any_key_text_render = self.font2.render("Press enter to confirm", True, pygame.Color("#FFFFFF"))
        self.stage.screen.blit(press_any_key_text_render,
                               press_any_key_text_render.get_rect(centerx=self.stage.width*0.5,
                                                                  centery=(self.stage.height*0.9)))


class Character:
    def __init__(self):
        self.file_name = ""
        self.name = ""
        self.stage = 0
        self.score = 0

    def load(self, file_name):
        self.file_name = file_name
        with open(self.file_name, "r") as character_file:
            reader = csv.reader(character_file)
            for line in reader:
                self.name = line[0]
                self.stage = int(line[1])
                self.score = int(line[2])

    def save(self):
        self.file_name = "high_scores/" + self.name + ".txt"
        increment_score = 2
        while os.path.isfile(self.file_name):
            self.file_name = "high_scores/" + self.name + "_" + str(increment_score) + ".txt"
            increment_score += 1
            
        with open(self.file_name, "w", newline='') as character_file:
            writer = csv.writer(character_file)
            writer.writerow([self.name, str(self.stage), str(self.score)])
            

def reload_characters(characters):
    characters[:] = []
    for character_file in os.listdir("high_scores/"):
        full_file_name = "high_scores/" + character_file
        character_to_load = Character()
        character_to_load.load(full_file_name)
        characters.append(character_to_load)

    characters.sort(key=attrgetter('score'), reverse=True)

    return characters
