import pygame
import config as c
from item import Item  # Ensure Item is imported

class InventoryUI:
    def __init__(self, screen, inventory, atlas):
        self.screen = screen
        self.inventory = inventory
        self.atlas = atlas
        self.slot_size = 50
        self.padding = 10
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.dragging_item = None
        self.dragging_index = None
        self.dragging_container = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def draw_grid(self, container, top_left, columns):
        x0, y0 = top_left
        for idx, slot in enumerate(container):
            col = idx % columns
            row = idx // columns
            x = x0 + col * (self.slot_size + self.padding)
            y = y0 + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            if slot and slot["item"]:
                item = slot["item"]
                tx, ty = item.texture_coords
                block_size = c.BLOCK_SIZE
                texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
                self.screen.blit(item_img, rect.topleft)
                if slot.get("quantity", 0) > 1:
                    amount_surf = self.font.render(str(slot["quantity"]), True, (255,255,255))
                    self.screen.blit(amount_surf, (rect.right - amount_surf.get_width(), rect.bottom - amount_surf.get_height()))
            if self.dragging_item and self.dragging_container == container and self.dragging_index == idx:
                # Skip drawing the item in its original slot while dragging.
                continue

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.start_drag(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.stop_drag(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.update_drag(event.pos)
            self.draw()
            pygame.display.flip()

    def start_drag(self, mouse_pos):
        for container, top_left, columns in [
            (self.inventory.hotbar, (c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding), c.SCREEN_HEIGHT - self.slot_size - 40), 9),
            (self.inventory.armor, (c.SCREEN_WIDTH//2 - 1.5*(self.slot_size + self.padding), 100), 3),
            (self.inventory.main, (c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding), 250), 8)
        ]:
            x0, y0 = top_left
            for idx, slot in enumerate(container):
                col = idx % columns
                row = idx // columns
                x = x0 + col * (self.slot_size + self.padding)
                y = y0 + row * (self.slot_size + self.padding)
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                if rect.collidepoint(mouse_pos):
                    self.dragging_item = slot
                    self.dragging_index = idx
                    self.dragging_container = container
                    self.drag_offset_x = mouse_pos[0] - x
                    self.drag_offset_y = mouse_pos[1] - y
                    self.dragging_item["x"] = x  # Initialize x position
                    self.dragging_item["y"] = y  # Initialize y position
                    container[idx] = {"item": None, "quantity": 0}
                    return

    def update_drag(self, mouse_pos):
        if self.dragging_item:
            self.dragging_item["x"] = mouse_pos[0] - self.drag_offset_x
            self.dragging_item["y"] = mouse_pos[1] - self.drag_offset_y

    def stop_drag(self, mouse_pos):
        if not self.dragging_item:
            return
        for container, top_left, columns in [
            (self.inventory.hotbar, (c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding), c.SCREEN_HEIGHT - self.slot_size - 40), 9),
            (self.inventory.armor, (c.SCREEN_WIDTH//2 - 1.5*(self.slot_size + self.padding), 100), 3),
            (self.inventory.main, (c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding), 250), 8)
        ]:
            x0, y0 = top_left
            for idx, slot in enumerate(container):
                col = idx % columns
                row = idx // columns
                x = x0 + col * (self.slot_size + self.padding)
                y = y0 + row * (self.slot_size + self.padding)
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                if rect.collidepoint(mouse_pos):
                    if container == self.inventory.armor and not getattr(self.dragging_item["item"], "is_armor", False):
                        # If trying to drop a non-armor item into an armor slot, cancel the drag.
                        self.dragging_container[self.dragging_index] = self.dragging_item
                        self.dragging_item = None
                        self.dragging_index = None
                        self.dragging_container = None
                        return
                    if container[idx]["item"]:
                        # If the items are of the same type, add to the existing stack or fill the stack and keep the rest in the original slot.
                        if self.dragging_item is not None and self.dragging_item.get("item") is not None:
                            if container[idx].get("item") is not None and container[idx]["item"].id == self.dragging_item["item"].id:
                                available_space = container[idx]["item"].stack_size - container[idx]["quantity"]
                                if available_space > 0:
                                    transfer_amount = min(available_space, self.dragging_item["quantity"])
                                    container[idx]["quantity"] += transfer_amount
                                    self.dragging_item["quantity"] -= transfer_amount
                                    if self.dragging_item["quantity"] > 0:
                                        self.dragging_container[self.dragging_index] = self.dragging_item
                                    else:
                                        self.dragging_item = None
                                        self.dragging_index = None
                                        self.dragging_container = None
                                    return
                        # Swap items if the target slot is not empty and items are different.
                        container[idx], self.dragging_container[self.dragging_index] = self.dragging_item, container[idx]
                    else:
                        # Move item to the new slot.
                        container[idx] = self.dragging_item
                    self.dragging_item = None
                    self.dragging_index = None
                    self.dragging_container = None
                    return
        # If not dropped on a valid slot, return the item to its original slot.
        self.dragging_container[self.dragging_index] = self.dragging_item
        self.dragging_item = None
        self.dragging_index = None
        self.dragging_container = None

    def draw(self):
        self.screen.fill((30, 30, 30))
        # Draw UI overlay background
        overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), flags=pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0,0))

        # Draw title text
        title = pygame.font.SysFont(None, 48).render("Inventory", True, (255, 255, 255))
        title_rect = title.get_rect(center=(c.SCREEN_WIDTH//2, 50))
        self.screen.blit(title, title_rect)

        # Draw Armor Grid (slots 10-15)
        armor_top_left = (c.SCREEN_WIDTH//2 - 1.5*(self.slot_size + self.padding), 100)
        self.draw_grid(self.inventory.armor, armor_top_left, 3)
        # Draw label for Armor
        armor_label = self.font.render("Armor", True, (255, 255, 255))
        armor_label_rect = armor_label.get_rect(center=(c.SCREEN_WIDTH//2, 100 - 20))
        self.screen.blit(armor_label, armor_label_rect)

        # Draw Main Inventory Grid (slots 16-47)
        main_top_left = (c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding), 250)
        self.draw_grid(self.inventory.main, main_top_left, 8)
        # Draw label for Main Inventory
        main_label = self.font.render("Main Inventory", True, (255, 255, 255))
        main_label_rect = main_label.get_rect(center=(c.SCREEN_WIDTH//2, 250 - 20))
        self.screen.blit(main_label, main_label_rect)

        self.draw_hotbar_ui()

        # Draw the dragging item if any.
        if self.dragging_item:
            item = self.dragging_item["item"]
            if item:
                tx, ty = item.texture_coords
                block_size = c.BLOCK_SIZE
                texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
                self.screen.blit(item_img, (self.dragging_item["x"], self.dragging_item["y"]))
                if self.dragging_item.get("quantity", 0) > 1:
                    amount_surf = self.font.render(str(self.dragging_item["quantity"]), True, (255, 255, 255))
                    self.screen.blit(amount_surf, (self.dragging_item["x"] + self.slot_size - amount_surf.get_width(), self.dragging_item["y"] + self.slot_size - amount_surf.get_height()))

    def draw_hotbar_ui(self):
        # Draw hotbar with visual effect for the selected slot.
        slot_size = 50  # Larger UI slot size
        padding = 10
        total_width = len(self.inventory.hotbar) * (slot_size + padding) - padding
        x_start = (c.SCREEN_WIDTH - total_width) // 2
        y = c.SCREEN_HEIGHT - slot_size - 40

        for i, slot in enumerate(self.inventory.hotbar):
            rect = pygame.Rect(x_start + i * (slot_size + padding), y, slot_size, slot_size)
            if i == self.inventory.selected_hotbar_index:
                # Glowing border effect for the selected slot.
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(6, 6), 4)
            pygame.draw.rect(self.screen, (50, 50, 50), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            if slot and "item" in slot and slot["item"]:
                item = slot["item"]
                tx, ty = item.texture_coords
                block_size = c.BLOCK_SIZE
                texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (slot_size, slot_size))
                self.screen.blit(item_img, rect.topleft)
                if slot.get("quantity", 0) > 1:
                    amount_surf = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    self.screen.blit(amount_surf, (rect.right - amount_surf.get_width(), rect.bottom - amount_surf.get_height()))
            if self.dragging_item and self.dragging_container == self.inventory.hotbar and self.dragging_index == i:
                # Skip drawing the item in its original slot while dragging.
                continue
