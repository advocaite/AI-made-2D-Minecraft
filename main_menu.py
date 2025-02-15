import pygame

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.options = ["Start Game", "Quit"]
        self.selected = 0

    def run(self):
        option_rects = []
        while True:
            self.screen.fill((0, 0, 0))
            option_rects.clear()
            for idx, option in enumerate(self.options):
                color = (255, 255, 0) if idx == self.selected else (255, 255, 255)
                text = self.font.render(option, True, color)
                rect = text.get_rect(center=(self.screen.get_width()//2, 200 + idx * 60))
                self.screen.blit(text, rect)
                option_rects.append(rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                    for idx, rect in enumerate(option_rects):
                        if rect.collidepoint(mouse_pos):
                            self.selected = idx
                            break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if option_rects[self.selected].collidepoint(mouse_pos):
                        return self.options[self.selected].lower().replace(" ", "_")
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.selected].lower().replace(" ", "_")
            self.clock.tick(60)
