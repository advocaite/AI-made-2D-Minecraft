import pygame

class ScrollableList:
    def __init__(self, x, y, width, height, item_height=60):
        self.rect = pygame.Rect(x, y, width, height)
        self.item_height = item_height
        self.items = []
        self.scroll_offset = 0
        self.max_scroll = 0

    def set_items(self, items):
        self.items = items
        self.scroll_offset = 0
        self.max_scroll = max(0, len(items) * self.item_height - self.rect.height)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # wheel up
                self.scroll_offset = max(0, self.scroll_offset - self.item_height)
            elif event.button == 5:  # wheel down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.item_height)

    def draw(self, surface, font, selected_index):
        # Save previous clip and set clip to scrollable area
        previous_clip = surface.get_clip()
        surface.set_clip(self.rect)
        
        # Clear background in the scroll area
        pygame.draw.rect(surface, (30, 30, 30), self.rect)
        
        offset_y = -self.scroll_offset
        for idx, item in enumerate(self.items):
            # Determine if item is a dict with image.
            if isinstance(item, dict):
                name = item.get("name", "")
                info = item.get("info", "")
                image = item.get("image", None)
            else:
                name = str(item)
                info = ""
                image = None
            color = (255, 215, 0) if idx == selected_index else (255, 255, 255)
            text_x = self.rect.x + 10
            # If an image exists, draw it and offset text.
            if image:
                # Draw image centered vertically.
                img_y = self.rect.y + offset_y + (self.item_height - image.get_height()) // 2
                surface.blit(image, (self.rect.x + 10, img_y))
                text_x += image.get_width() + 10
            # Render top line (name).
            name_surf = font.render(name, True, color)
            name_rect = name_surf.get_rect(topleft=(text_x, self.rect.y + offset_y + 5))
            # Render bottom line (info) in grey.
            info_surf = font.render(info, True, (180, 180, 180))
            info_rect = info_surf.get_rect(topleft=(
                text_x,
                self.rect.y + offset_y + self.item_height - info_surf.get_height() - 5
            ))
            # Only draw if it intersects the list’s viewport.
            if name_rect.bottom > self.rect.y and info_rect.top < self.rect.y + self.rect.height:
                surface.blit(name_surf, name_rect)
                surface.blit(info_surf, info_rect)
            offset_y += self.item_height

        # Reset clip region
        surface.set_clip(previous_clip)
        
        # Optional: Draw border around scrollable area
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)