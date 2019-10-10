import pygame


class SoundManager(object):
   
    def __init__(self):
        self.sounds = {}
        pygame.mixer.init()

        # self.sounds["fire"] = pygame.mixer.Sound("data/FIRE.WAV")
        # self.sounds["explode_1"] = pygame.mixer.Sound("data/EXPLODE1.WAV")
        # self.sounds["explode_2"] = pygame.mixer.Sound("data/EXPLODE2.WAV")
        # self.sounds["explode_3"] = pygame.mixer.Sound("data/EXPLODE3.WAV")
        # self.sounds["l_saucer"] = pygame.mixer.Sound("data/LSAUCER.WAV")
        # self.sounds["s_saucer"] = pygame.mixer.Sound("data/SSAUCER.WAV")
        # self.sounds["thrust"] = pygame.mixer.Sound("data/THRUST.WAV")
        # self.sounds["s_fire"] = pygame.mixer.Sound("data/SFIRE.WAV")
        # self.sounds["extra_life"] = pygame.mixer.Sound("data/LIFE.WAV")
        # self.sounds["missile"] = pygame.mixer.Sound("data/MISSILE.WAV")

    def play_sound(self, sound_name):
        pass
        # channel = self.sounds[sound_name].play()

    def play_sound_continuous(self, sound_name):
        pass
        # channel = self.sounds[sound_name].play(-1)
    
    def stop_sound(self, sound_name):
        pass
        # channel = self.sounds[sound_name].stop()
