import pygame

class ProgressBar:
    def __init__(self, x, y, width, height, max_value=100, color=(0, 255, 0), 
                 background_color=(70, 70, 70), border_color=(200, 200, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.color = color
        self.background_color = background_color
        self.border_color = border_color
        self.font = pygame.font.SysFont(None, height - 4)  # Scale font to fit height

    def draw(self, surface, current_value, label=""):
        # Draw background
        pygame.draw.rect(surface, self.background_color, self.rect)
        
        # Draw progress
        progress_width = int((current_value / self.max_value) * self.rect.width)
        progress_rect = pygame.Rect(self.rect.x, self.rect.y, progress_width, self.rect.height)
        pygame.draw.rect(surface, self.color, progress_rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        
        # Draw text
        text = f"{label}: {int(current_value)}/{self.max_value}"
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
