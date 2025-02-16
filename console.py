import pygame
from command_manager import CommandManager

class Console:
    def __init__(self, font, screen_width, screen_height, player, inventory, mobs):
        self.active = False
        self.input_text = ""
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.manager = CommandManager()
        self.player = player
        self.inventory = inventory
        self.mobs = mobs  # Add mobs to the constructor
        self.output_lines = []
        self.commands = {
            'setday': self.set_day,
            'setnight': self.set_night,
            'setweather': self.set_weather,
            'set3': self.set_3,
            'spawn_entity': self.spawn_entity,  # Added spawn_entity command mapping.
        }
        self.callbacks = {
            'setday': None,
            'setnight': None,
            'setweather': None,
            'set3': None,
        }
        self.history = []
        self.history_index = -1
        self.selection_start = None
        self.selection_end = None
        self.cursor_position = 0  # Initialize cursor position

        # Initialize the scrap system
        pygame.scrap.init()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKQUOTE or event.unicode == "~":  # toggle console with ~ key
                self.active = not self.active
                self.player.paused = self.active  # Pause character movement when console is active
            elif self.active:
                if event.key == pygame.K_RETURN:
                    self.history.append(self.input_text)
                    self.history_index = len(self.history)
                    self.manager.execute_command(self.input_text, self.player, self.inventory, self.mobs)  # Pass mobs to CommandManager
                    self.execute_command(self.input_text)
                    self.input_text = ""
                    self.selection_start = None
                    self.selection_end = None
                    self.cursor_position = 0
                elif event.key == pygame.K_BACKSPACE:
                    if self.selection_start is not None and self.selection_end is not None:
                        start = min(self.selection_start, self.selection_end)
                        end = max(self.selection_start, self.selection_end)
                        self.input_text = self.input_text[:start] + self.input_text[end:]
                        self.cursor_position = start
                        self.selection_start = None
                        self.selection_end = None
                    elif self.cursor_position > 0:
                        self.input_text = self.input_text[:self.cursor_position - 1] + self.input_text[self.cursor_position:]
                        self.cursor_position -= 1
                elif event.key == pygame.K_UP:
                    if self.history:
                        self.history_index = max(0, self.history_index - 1)
                        self.input_text = self.history[self.history_index]
                        self.cursor_position = len(self.input_text)
                elif event.key == pygame.K_DOWN:
                    if self.history:
                        self.history_index = min(len(self.history) - 1, self.history_index + 1)
                        self.input_text = self.history[self.history_index]
                        self.cursor_position = len(self.input_text)
                elif event.key == pygame.K_ESCAPE:
                    self.active = False  # exit console on ESC key press
                    self.player.paused = self.active  # Resume character movement when console is inactive
                elif event.key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # Handle CTRL+A for selecting all text
                    self.selection_start = 0
                    self.selection_end = len(self.input_text)
                    self.cursor_position = len(self.input_text)
                elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # Handle CTRL+V for pasting clipboard content
                    clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if clipboard_text:
                        self.input_text = self.input_text[:self.cursor_position] + clipboard_text.decode("utf-8") + self.input_text[self.cursor_position:]
                        self.cursor_position += len(clipboard_text.decode("utf-8"))
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # Handle CTRL+C for copying selected text
                    if self.selection_start is not None and self.selection_end is not None:
                        start = min(self.selection_start, self.selection_end)
                        end = max(self.selection_start, self.selection_end)
                        selected_text = self.input_text[start:end]
                        pygame.scrap.put(pygame.SCRAP_TEXT, selected_text.encode("utf-8"))
                elif event.key == pygame.K_x and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # Handle CTRL+X for cutting selected text
                    if self.selection_start is not None and self.selection_end is not None:
                        start = min(self.selection_start, self.selection_end)
                        end = max(self.selection_start, self.selection_end)
                        selected_text = self.input_text[start:end]
                        pygame.scrap.put(pygame.SCRAP_TEXT, selected_text.encode("utf-8"))
                        self.input_text = self.input_text[:start] + self.input_text[end:]
                        self.cursor_position = start
                        self.selection_start = None
                        self.selection_end = None
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    # Ignore CTRL key presses to prevent deselection
                    pass
                elif event.key == pygame.K_LEFT and self.cursor_position > 0:
                    self.cursor_position -= 1
                elif event.key == pygame.K_RIGHT and self.cursor_position < len(self.input_text):
                    self.cursor_position += 1
                elif event.key == pygame.K_HOME:
                    self.cursor_position = 0
                elif event.key == pygame.K_END:
                    self.cursor_position = len(self.input_text)
                else:
                    # Filter out unsupported unicode characters and handle None case
                    try:
                        char = event.unicode.encode("ascii", "ignore").decode("ascii")
                        if char:  # Only update if char is not empty
                            self.input_text = self.input_text[:self.cursor_position] + char + self.input_text[self.cursor_position:]
                            self.cursor_position += len(char)
                            self.selection_start = None
                            self.selection_end = None
                    except (AttributeError, UnicodeEncodeError):
                        pass  # Ignore characters that can't be encoded
        elif event.type == pygame.MOUSEBUTTONDOWN and self.active:
            if event.button == 1:  # Left mouse button
                self.selection_start = self.get_char_index_at_pos(event.pos)
                self.selection_end = self.selection_start
                self.cursor_position = self.selection_start
        elif event.type == pygame.MOUSEMOTION and self.active:
            if event.buttons[0]:  # Left mouse button held down
                self.selection_end = self.get_char_index_at_pos(event.pos)

    def get_char_index_at_pos(self, pos):
        x, y = pos
        rect_height = 40
        rect = pygame.Rect(0, self.screen_height - rect_height, self.screen_width, rect_height)
        if not rect.collidepoint(x, y):
            return None
        text_x = x - rect.x - 5
        for i, char in enumerate(self.input_text):
            char_width = self.font.size(char)[0]
            if text_x < char_width:
                return i
            text_x -= char_width
        return len(self.input_text)

    def execute_command(self, command_line):
        parts = command_line.strip().split()
        if not parts:
            return
        # Combine "set weather" into "setweather" if applicable.
        if len(parts) >= 2 and parts[0].lower() == "set" and parts[1].lower() == "weather":
            cmd = "setweather"
            args = parts[2:]
        # NEW: Combine "spawn entity" into "spawn_entity" if applicable.
        elif len(parts) >= 2 and parts[0].lower() == "spawn" and parts[1].lower() == "entity":
            cmd = "spawn_entity"
            args = parts[2:]
        else:
            cmd = parts[0].lower()
            args = parts[1:]
        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            self.output_lines.append("Unknown command: " + cmd)

    def set_day(self, args):
        self.output_lines.append("Time set to day")
        print("Console Command: Time set to day")
        if self.callbacks.get('setday'):
            self.callbacks['setday']()

    def set_night(self, args):
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

    def spawn_entity(self, args):
        # This command has already been executed via CommandManager.
        self.output_lines.append("Spawn entity command executed.")
        print("Console Command: spawn_entity executed")

    def draw(self, screen):
        if not self.active:
            return
        rect_height = 40
        rect = pygame.Rect(0, self.screen_height - rect_height, self.screen_width, rect_height)
        overlay = pygame.Surface((rect.width, rect.height), flags=pygame.SRCALPHA)
        overlay.fill((50, 50, 50, 200))
        screen.blit(overlay, rect.topleft)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        blink = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        # Filter out null characters from input text
        safe_input_text = self.input_text.replace('\x00', '')
        text_surface = self.font.render(safe_input_text[:self.cursor_position] + blink + safe_input_text[self.cursor_position:], True, (255, 255, 255))
        screen.blit(text_surface, (rect.x + 5, rect.y + 5))
        if self.selection_start is not None and self.selection_end is not None:
            start = min(self.selection_start, self.selection_end)
            end = max(self.selection_start, self.selection_end)
            selected_text = safe_input_text[start:end]
            pre_text = safe_input_text[:start]
            post_text = safe_input_text[end:]
            pre_surface = self.font.render(pre_text, True, (255, 255, 255))
            selected_surface = self.font.render(selected_text, True, (0, 0, 0), (255, 255, 255))
            post_surface = self.font.render(post_text, True, (255, 255, 255))
            screen.blit(pre_surface, (rect.x + 5, rect.y + 5))
            screen.blit(selected_surface, (rect.x + 5 + pre_surface.get_width(), rect.y + 5))
            screen.blit(post_surface, (rect.x + 5 + pre_surface.get_width() + selected_surface.get_width(), rect.y + 5))
