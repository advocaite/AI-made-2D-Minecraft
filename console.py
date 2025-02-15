import pygame
from command_manager import CommandManager

class Console:
    def __init__(self, font, screen_width, screen_height, player, inventory):
        self.active = False
        self.input_text = ""
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = CommandManager()
        self.player = player
        self.inventory = inventory
        self.output_lines = []
        # Add new commands for time, weather control and set3 change
        self.commands = {
            'setday': self.set_day,
            'setnight': self.set_night,
            'setweather': self.set_weather,
            'set3': self.set_3,
        }
        # New: Dictionary for callbacks; users can assign functions later.
        self.callbacks = {
            'setday': None,
            'setnight': None,
            'setweather': None,
            'set3': None,
        }
        # NEW: Command history and pointer.
        self.history = []
        self.history_index = -1

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKQUOTE or event.unicode == "~":  # toggle console with ~ key
                self.active = not self.active
            elif self.active:
                if event.key == pygame.K_RETURN:
                    self.history.append(self.input_text)
                    self.history_index = len(self.history)
                    self.manager.execute_command(self.input_text, self.player, self.inventory)
                    self.execute_command(self.input_text)
                    self.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_UP:
                    if self.history:
                        self.history_index = max(0, self.history_index - 1)
                        self.input_text = self.history[self.history_index]
                elif event.key == pygame.K_DOWN:
                    if self.history:
                        self.history_index = min(len(self.history) - 1, self.history_index + 1)
                        self.input_text = self.history[self.history_index]
                else:
                    # Filter out unsupported unicode characters.
                    char = event.unicode.encode("ascii", "ignore").decode("ascii")
                    self.input_text += char

    def execute_command(self, command_line):
        parts = command_line.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            self.output_lines.append("Unknown command: " + cmd)

    def set_day(self, args):
        # Set world time to day (e.g. start of day)
        self.output_lines.append("Time set to day")
        print("Console Command: Time set to day")
        # New: If a callback is assigned for setday, execute it.
        if self.callbacks.get('setday'):
            self.callbacks['setday']()

    def set_night(self, args):
        # Set world time to night (e.g. start of night)
        self.output_lines.append("Time set to night")
        print("Console Command: Time set to night")
        if self.callbacks.get('setnight'):
            self.callbacks['setnight']()

    def set_weather(self, args):
        if args:
            weather = args[0].lower()
            self.output_lines.append(f"Weather set to: {weather}")
            print("Console Command: Weather set to:", weather)
            if self.callbacks.get('setweather'):
                self.callbacks['setweather'](weather)
        else:
            self.output_lines.append("Usage: setweather <weather_type>")
            print("Console Command: Usage: setweather <weather_type>")

    def set_3(self, args):
        self.output_lines.append("Set3 executed")
        print("Console Command: Set3 executed")
        if self.callbacks.get('set3'):
            self.callbacks['set3']()

    def draw(self, screen):
        if not self.active:
            return
        rect_height = 40
        rect = pygame.Rect(0, self.screen_height - rect_height, self.screen_width, rect_height)
        overlay = pygame.Surface((rect.width, rect.height), flags=pygame.SRCALPHA)
        overlay.fill((50, 50, 50, 200))
        screen.blit(overlay, rect.topleft)
        # Draw a white border around the text box
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        # NEW: Append a blinking cursor at end of input.
        blink = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        text_surface = self.font.render(self.input_text + blink, True, (255, 255, 255))
        screen.blit(text_surface, (rect.x + 5, rect.y + 5))
