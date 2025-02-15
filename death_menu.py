import pygame

class DeathMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.SysFont(None, 72)  # Larger font for death message
        self.button_font = pygame.font.SysFont(None, 48)  # Smaller font for buttons
        
        # Create buttons
        button_width = 200
        button_height = 50
        spacing = 20
        start_x = (screen_width - (button_width * 2 + spacing)) // 2
        button_y = screen_height // 2

        self.try_again_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        self.quit_rect = pygame.Rect(start_x + button_width + spacing, button_y, button_width, button_height)

        # Update button text
        self.buttons = {
            "try_again": {
                "rect": self.try_again_rect,
                "text": "Try Again",
                "colors": {"normal": (0, 200, 0), "hover": (0, 255, 0)}
            },
            "main_menu": {  # Changed from "quit"
                "rect": self.quit_rect,
                "text": "Main Menu",  # Changed text
                "colors": {"normal": (200, 0, 0), "hover": (255, 0, 0)}
            }
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.try_again_rect.collidepoint(mouse_pos):
                return "try_again"
            elif self.quit_rect.collidepoint(mouse_pos):
                return "main_menu"  # Changed from "quit"
        return None

    def draw(self, screen):
        # Draw semi-transparent dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)  # Slightly transparent
        screen.blit(overlay, (0, 0))

        # Draw death message
        death_text = self.font.render("YOU DIED!", True, (255, 0, 0))
        text_rect = death_text.get_rect(center=(self.screen_width // 2, self.screen_height // 3))
        screen.blit(death_text, text_rect)

        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button_id, button in self.buttons.items():
            color = button["colors"]["hover"] if button["rect"].collidepoint(mouse_pos) else button["colors"]["normal"]
            pygame.draw.rect(screen, color, button["rect"])
            text = self.button_font.render(button["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=button["rect"].center)
            screen.blit(text, text_rect)
