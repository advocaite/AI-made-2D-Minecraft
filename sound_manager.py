import pygame
import config as c

class SoundManager:
    def __init__(self):
        # Clamp volumes and compute effective volumes
        master_vol = max(0, min(c.MASTER_VOLUME, 100)) / 100
        music_vol = max(0, min(c.MUSIC_VOLUME, 100)) / 100
        self.effective_music_volume = master_vol * music_vol
        self.effective_sound_volume = master_vol  # using master volume for sound effects
        
        # Load and play background music
        pygame.mixer.music.load("sounds/ObservingTheStar.ogg")  # update filename as needed
        pygame.mixer.music.set_volume(self.effective_music_volume)
        pygame.mixer.music.play(-1)  # loop indefinitely
        
        # Load jump sound
        self.jump_sound = pygame.mixer.Sound("sounds/jump.mp3")  # update filename as needed
        self.jump_sound.set_volume(self.effective_sound_volume)

    def play_jump(self):
        self.jump_sound.play()
