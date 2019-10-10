import pygame
import os


class Stage:
    
    # Set up the PyGame surface
    def __init__(self, caption, dimensions=None):
        self.game_title = caption
        pygame.init()

        os.environ['SDL_VIDEO_CENTERED'] = '1'
        
        # If no screen size is provided pick the first available mode        
        if dimensions is None:
            dimensions = pygame.display.list_modes()[0]

        pygame.mouse.set_visible(False)
        pygame.display.set_caption(self.game_title)
        self.screen = pygame.display.set_mode(dimensions)

        self.width = dimensions[0]
        self.height = dimensions[1]

        self.star_field_image = pygame.image.load("data/star_field.png").convert()

        self.current_player_ship = None
        self.current_player_ship_stats = None

    def get_ship(self):
        return self.current_player_ship

    def get_ship_stats(self):
        return self.current_player_ship_stats
