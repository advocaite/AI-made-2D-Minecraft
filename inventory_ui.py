import pygame
import config as c
from item import Item  # Ensure Item is imported
from ui_tooltip import Tooltip, get_item_tooltip

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
        self.drag_origin_x = 0  # Add these two new variables
        self.drag_origin_y = 0
        self.drag_pos = {"x": 0, "y": 0}  # Add this line to store drag position
        # Add tooltip support
        self.tooltip = Tooltip(self.font)
        self.hovered_item = None

    def can_equip_in_armor_slot(self, item, slot_index):
        """Check if an item can be equipped in the given armor slot"""
        if not hasattr(item, 'type'):
            return False
            
        # Armor slot indices:
        # 0: Helmet
        # 1: Chestplate
        # 2: Leggings
        # 3: Boots
        # 4: Left Hand
        # 5: Right Hand
        
        slot_requirements = {
            0: ['helmet'],
            1: ['chestplate'],
            2: ['leggings'],
            3: ['boots'],
            4: ['shield', 'weapon', 'tool'],  # Left hand can hold shields, weapons, tools
            5: ['weapon', 'tool']  # Right hand can hold weapons and tools
        }
        
        if slot_index in slot_requirements:
            return item.type in slot_requirements[slot_index]
        return False

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
                    if slot is not None and slot.get("item") is not None:
                        self.dragging_item = dict(slot)  # Make a copy of the slot
                        self.drag_pos["x"] = mouse_pos[0] - self.slot_size//2
                        self.drag_pos["y"] = mouse_pos[1] - self.slot_size//2
                        self.dragging_index = idx
                        self.dragging_container = container
                        self.drag_offset_x = self.slot_size//2
                        self.drag_offset_y = self.slot_size//2
                        container[idx] = None  # Clear the original slot
                        return

    def update_drag(self, mouse_pos):
        if self.dragging_item:
            self.drag_pos["x"] = mouse_pos[0] - self.slot_size//2
            self.drag_pos["y"] = mouse_pos[1] - self.slot_size//2

    def stop_drag(self, pos):
        if not self.dragging_item:
            return

        target_slot = self.get_slot_at_pos(pos)
        if not target_slot:
            # Return item to original slot if dropped outside
            if self.dragging_container and self.dragging_index is not None:
                self.dragging_container[self.dragging_index] = self.dragging_item
            self.dragging_item = None
            self.dragging_container = None
            self.dragging_index = None
            return

        container, idx = self.get_container_and_index(target_slot)
        if container is None:
            return

        # Check armor slot restrictions
        if container == self.inventory.armor:
            if not self.can_equip_in_armor_slot(self.dragging_item["item"], idx):
                # Return item to original slot if it can't be equipped
                self.return_to_source()
                return

        # Get current item at target slot
        target_item = container[idx]

        # If target slot is empty, just place the item
        if target_item is None:
            container[idx] = self.dragging_item
            self.dragging_item = None
        # If target has same item type and can stack
        elif target_item["item"] and self.dragging_item["item"] and \
             target_item["item"].id == self.dragging_item["item"].id and \
             target_item["quantity"] < target_item["item"].stack_size:
            # Calculate stack space
            space_left = target_item["item"].stack_size - target_item["quantity"]
            amount_to_add = min(space_left, self.dragging_item["quantity"])
            
            # Add to existing stack
            target_item["quantity"] += amount_to_add
            self.dragging_item["quantity"] -= amount_to_add
            
            # If we have leftover items, return them to original slot
            if self.dragging_item["quantity"] > 0:
                if self.dragging_container and self.dragging_index is not None:
                    self.dragging_container[self.dragging_index] = self.dragging_item
            self.dragging_item = None
        else:
            # Simple swap: put dragged item in target slot and put target item in original slot
            container[idx] = self.dragging_item
            if self.dragging_container and self.dragging_index is not None:
                self.dragging_container[self.dragging_index] = target_item
            self.dragging_item = None

        # Reset drag state
        self.dragging_container = None
        self.dragging_index = None

    def draw(self):
        # Get current mouse position and update hovered item
        mouse_pos = pygame.mouse.get_pos()
        self.get_slot_at_pos(mouse_pos)  # This updates self.hovered_item

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
                self.screen.blit(item_img, (self.drag_pos["x"], self.drag_pos["y"]))
                if self.dragging_item.get("quantity", 0) > 1:
                    amount_surf = self.font.render(str(self.dragging_item["quantity"]), True, (255, 255, 255))
                    self.screen.blit(amount_surf, (self.drag_pos["x"] + self.slot_size - amount_surf.get_width(), self.drag_pos["y"] + self.slot_size - amount_surf.get_height()))

        # Draw tooltip last (after dragged item)
        if self.hovered_item and not self.dragging_item:
            tooltip_text = get_item_tooltip(self.hovered_item)
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

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

    def get_slot_at_pos(self, pos):
        """Convert mouse position to inventory slot information"""
        mx, my = pos
        slot_info = None
        self.hovered_item = None  # Reset hovered item

        # Check hotbar slots
        hotbar_x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding)
        hotbar_y = c.SCREEN_HEIGHT - self.slot_size - 40
        for i in range(len(self.inventory.hotbar)):
            x = hotbar_x + i * (self.slot_size + self.padding)
            y = hotbar_y
            if pygame.Rect(x, y, self.slot_size, self.slot_size).collidepoint(mx, my):
                slot_info = ("hotbar", i)
                if self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                    self.hovered_item = self.inventory.hotbar[i]["item"]
                break

        # Check armor slots
        if not slot_info:
            armor_x = c.SCREEN_WIDTH//2 - 1.5*(self.slot_size + self.padding)
            armor_y = 100
            for i in range(len(self.inventory.armor)):
                x = armor_x + (i % 3) * (self.slot_size + self.padding)
                y = armor_y + (i // 3) * (self.slot_size + self.padding)
                if pygame.Rect(x, y, self.slot_size, self.slot_size).collidepoint(mx, my):
                    slot_info = ("armor", i)
                    if self.inventory.armor[i] and self.inventory.armor[i].get("item"):
                        self.hovered_item = self.inventory.armor[i]["item"]
                    break

        # Check main inventory slots
        if not slot_info:
            main_x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding)
            main_y = 250
            for i in range(len(self.inventory.main)):
                x = main_x + (i % 8) * (self.slot_size + self.padding)
                y = main_y + (i // 8) * (self.slot_size + self.padding)
                if pygame.Rect(x, y, self.slot_size, self.slot_size).collidepoint(mx, my):
                    slot_info = ("main", i)
                    if self.inventory.main[i] and self.inventory.main[i].get("item"):
                        self.hovered_item = self.inventory.main[i]["item"]
                    break

        return slot_info

    def get_container_and_index(self, slot_info):
        """Convert slot information to container and index"""
        if not slot_info:
            return None, None
            
        container_type, idx = slot_info
        if container_type == "hotbar":
            return self.inventory.hotbar, idx
        elif container_type == "armor":
            return self.inventory.armor, idx
        elif container_type == "main":
            return self.inventory.main, idx
        return None, None

    def return_to_source(self):
        """Return dragging item to its original slot"""
        if self.dragging_item and self.dragging_container and self.dragging_index is not None:
            self.dragging_container[self.dragging_index] = self.dragging_item
            self.dragging_item = None
            self.dragging_container = None
            self.dragging_index = None
            self.drag_pos = {"x": 0, "y": 0}
