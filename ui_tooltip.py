import pygame
from item import IRON_SWORD  # Add this import

class Tooltip:
    def __init__(self, font, padding=5, bg_color=(40, 40, 40, 230), text_color=(255, 255, 255)):
        self.font = font
        self.padding = padding
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, screen, text, pos):
        if not text:
            return

        # Split text into lines and render each line
        lines = text.split('\n')
        text_surfaces = [self.font.render(line, True, self.text_color) for line in lines]
        
        # Calculate tooltip dimensions
        max_width = max(surface.get_width() for surface in text_surfaces)
        total_height = sum(surface.get_height() for surface in text_surfaces)
        
        # Create tooltip surface
        tooltip_width = max_width + (self.padding * 2)
        tooltip_height = total_height + (self.padding * 2)
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_surface.fill(self.bg_color)

        # Position tooltip to avoid going off screen
        x, y = pos
        if x + tooltip_width > screen.get_width():
            x = screen.get_width() - tooltip_width
        if y + tooltip_height > screen.get_height():
            y = y - tooltip_height - 5  # Move above cursor

        # Draw text lines
        current_y = self.padding
        for surface in text_surfaces:
            tooltip_surface.blit(surface, (self.padding, current_y))
            current_y += surface.get_height()

        screen.blit(tooltip_surface, (x, y))

def get_item_tooltip(item):
    if not item:
        return None

    lines = [
        f"{item.name}",
        f"ID: {item.id}"
    ]

    # Add stats if they exist
    if hasattr(item, "modifiers") and item.modifiers:
        lines.append("")  # Empty line for spacing
        stats = []
        for stat, value in item.modifiers.items():
            if value != 0:
                stats.append(f"{stat.replace('_', ' ').title()}: +{value}")
        lines.extend(stats)

    # Add script effects info if present
    if hasattr(item, 'script') and item.script:
        lines.append("")  # Empty line before effects
        if hasattr(item.script, 'get_tooltip_info'):
            # Let script provide its own tooltip info
            script_info = item.script.get_tooltip_info()
            lines.extend(script_info)
        elif hasattr(item.script, 'on_hit'):  # Fallback for scripts without tooltip info
            lines.append("Special Effects:")
            # Check type by name instead of instance
            if item.name == "Iron Sword":
                lines.append("• 10% chance to cause bleeding")
                lines.append("• Bleeding deals 1 damage/second")
                lines.append("• Effect lasts 5 seconds")

    # Add other properties
    if hasattr(item, 'burn_time') and item.burn_time:
        lines.append(f"Burn time: {item.burn_time/1000:.1f}s")
    if hasattr(item, 'stack_size'):
        lines.append(f"Stack size: {item.stack_size}")
    if hasattr(item, 'is_block') and item.is_block:
        lines.append("Placeable block")

    return '\n'.join(lines)
