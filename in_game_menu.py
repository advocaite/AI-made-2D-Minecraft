import pygame
import sys
from config import SCREEN_WIDTH, SCREEN_HEIGHT  # import screen dimensions

class InGameMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        # New option added in the list.
        self.options = ["Return to Game", "Toggle Screen Mode", "Quit Game"]
        self.selected = 0

    def run(self):
        # Capture the current game screen before showing the menu.
        background = self.screen.copy()
        while True:
            # Blit the captured background.
            self.screen.blit(background, (0, 0))
            # Draw translucent overlay.
            overlay = pygame.Surface(self.screen.get_size(), flags=pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # 50% transparent black
            self.screen.blit(overlay, (0, 0))
            option_rects = []
            for idx, option in enumerate(self.options):
                color = (255, 255, 0) if idx == self.selected else (255, 255, 255)
                text = self.font.render(option, True, color)
                rect = text.get_rect(center=(self.screen.get_width()//2, 200 + idx * 60))
                self.screen.blit(text, rect)
                option_rects.append(rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    for idx, rect in enumerate(option_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected = idx
                            break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    selected_option = self.options[self.selected]
                    if selected_option == "Toggle Screen Mode":
                        self.toggle_screen_mode()
                        background = self.screen.copy()
                    else:
                        return selected_option
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        selected_option = self.options[self.selected]
                        if selected_option == "Toggle Screen Mode":
                            self.toggle_screen_mode()
                            background = self.screen.copy()
                        else:
                            return selected_option
                    elif event.key == pygame.K_ESCAPE:
                        return "Return to Game"
            self.clock.tick(60)

    def toggle_screen_mode(self):
        # Toggle between fullscreen and windowed mode.
        current_flags = self.screen.get_flags()
        if current_flags & pygame.FULLSCREEN:
            # Switch to windowed mode.
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            # Switch to fullscreen.
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
