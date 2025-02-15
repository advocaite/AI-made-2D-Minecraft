import pygame
from settings import Settings

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.options = ["New Game", "Load Game", "Options", "Quit"]
        self.selected = 0
        self.settings = Settings()

    def draw(self):
        self.screen.fill((0, 0, 0))
        for idx, option in enumerate(self.options):
            color = (255, 255, 0) if idx == self.selected else (255, 255, 255)
            text = self.font.render(option, True, color)
            rect = text.get_rect(center=(self.screen.get_width()//2, 150 + idx * 50))
            self.screen.blit(text, rect)
        pygame.display.flip()

    def run(self):
        while True:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        option = self.options[self.selected]
                        if option == "Options":
                            self.run_options()
                        else:
                            return option.lower().replace(" ", "_")
            self.clock.tick(60)

    def run_options(self):
        options_menu = ["Sound Volume", "Back"]
        selected_opt = 0
        while True:
            self.screen.fill((50, 50, 50))
            for idx, item in enumerate(options_menu):
                color = (255, 255, 0) if idx == selected_opt else (255, 255, 255)
                if item == "Sound Volume":
                    vol = self.settings.options.get("sound_volume", 0.5)
                    display_text = f"{item}: {vol}"
                else:
                    display_text = item
                text = self.font.render(display_text, True, color)
                rect = text.get_rect(center=(self.screen.get_width()//2, 150 + idx * 50))
                self.screen.blit(text, rect)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_opt = (selected_opt - 1) % len(options_menu)
                    elif event.key == pygame.K_DOWN:
                        selected_opt = (selected_opt + 1) % len(options_menu)
                    elif event.key == pygame.K_LEFT and selected_opt == 0:
                        vol = max(0, self.settings.options.get("sound_volume", 0.5) - 0.1)
                        self.settings.update("sound_volume", round(vol, 1))
                    elif event.key == pygame.K_RIGHT and selected_opt == 0:
                        vol = min(1, self.settings.options.get("sound_volume", 0.5) + 0.1)
                        self.settings.update("sound_volume", round(vol, 1))
                    elif event.key == pygame.K_RETURN and options_menu[selected_opt] == "Back":
                        return
            self.clock.tick(60)
