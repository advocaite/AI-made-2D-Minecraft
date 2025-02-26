import pygame
import config as c
from item import Item  # Ensure Item is imported
from ui_tooltip import Tooltip, get_item_tooltip
from ui_manager import UIManager

class InventoryUI:
    def __init__(self, screen, inventory, atlas):
        self.screen = screen
        self.inventory = inventory
        self.atlas = atlas
        self.slot_size = 50  # Changed from 40 to 50 to match hotbar
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
        self.selected_slot = None  # Add this line to initialize selected_slot
        self.texture_atlas = atlas  # Add this line to fix texture_atlas reference

        # Add frame tracking variables
        self._last_frame_items = {}
        self._last_frame_hotbar = {}

        self.ui_manager = UIManager(screen)
        self.inventory_batch = self.ui_manager.create_batch('inventory')
        self.hotbar_batch = self.ui_manager.create_batch('hotbar')

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

    def draw_grid(self, slots, start_pos, cols):
        slot_size = 50  # Changed from 40 to 50 to match hotbar
        padding = 5
        for i, slot in enumerate(slots):
            row = i // cols
            col = i % cols
            x = start_pos[0] + col * (slot_size + padding)
            y = start_pos[1] + row * (slot_size + padding)
            
            # Draw slot background
            pygame.draw.rect(self.screen, (50, 50, 50), (x, y, slot_size, slot_size))
            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, slot_size, slot_size), 1)
            
            # Draw item if present
            if slot and slot.get("item"):
                item = slot["item"]
                # Add safety check for texture_coords
                if hasattr(item, 'texture_coords') and item.texture_coords:
                    try:
                        tx, ty = item.texture_coords
                        # Updated scaling to match new slot size
                        texture_rect = pygame.Rect(tx * 16, ty * 16, 16, 16)
                        item_texture = self.texture_atlas.subsurface(texture_rect)
                        scaled_texture = pygame.transform.scale(item_texture, (slot_size-8, slot_size-8))
                        self.screen.blit(scaled_texture, (x+4, y+4))
                        
                        # Update quantity text position for new size
                        quantity = slot.get("quantity", 0)
                        if quantity > 1:
                            quantity_text = self.font.render(str(quantity), True, (255, 255, 255))
                            self.screen.blit(quantity_text, (x + slot_size - 20, y + slot_size - 20))
                    except (TypeError, ValueError) as e:
                        print(f"Error rendering item {item.name}: {e}")
                else:
                    print(f"Warning: Item {item.name} has no texture coordinates")
            
            # Highlight selected slot
            if self.selected_slot == i:
                pygame.draw.rect(self.screen, (255, 255, 0), (x, y, slot_size, slot_size), 2)

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
        """Draw the inventory UI with batched rendering"""
        self.ui_manager.begin_frame()
        
        # Draw background
        self.screen.fill((30, 30, 30))
        bg_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_overlay.fill((0, 0, 0, 200))
        self.screen.blit(bg_overlay, (0, 0))

        # Draw section titles
        title_color = (200, 200, 200)
        inventory_title = self.font.render("Inventory", True, title_color)
        armor_title = self.font.render("Equipment", True, title_color)
        hotbar_title = self.font.render("Hotbar", True, title_color)

        # Draw titles
        self.screen.blit(armor_title, (c.SCREEN_WIDTH//2 - armor_title.get_width()//2, 70))
        self.screen.blit(inventory_title, (c.SCREEN_WIDTH//2 - inventory_title.get_width()//2, 220))
        self.screen.blit(hotbar_title, (c.SCREEN_WIDTH//2 - hotbar_title.get_width()//2, 
                                      c.SCREEN_HEIGHT - self.slot_size - 70))

        # First pass: Draw all slot backgrounds
        # Draw armor slot backgrounds
        for i in range(len(self.inventory.armor)):
            pos = self._get_armor_pos(i)
            pygame.draw.rect(self.screen, (60, 60, 80), (*pos, self.slot_size, self.slot_size))
            pygame.draw.rect(self.screen, (120, 120, 140), (*pos, self.slot_size, self.slot_size), 1)

        # Draw inventory slot backgrounds
        for i in range(len(self.inventory.main)):
            pos = self._get_inventory_pos(i)
            pygame.draw.rect(self.screen, (50, 50, 50), (*pos, self.slot_size, self.slot_size))
            pygame.draw.rect(self.screen, (100, 100, 100), (*pos, self.slot_size, self.slot_size), 1)

        # Draw hotbar slot backgrounds
        for i in range(len(self.inventory.hotbar)):
            pos = self._get_hotbar_pos(i)
            pygame.draw.rect(self.screen, (50, 50, 50), (*pos, self.slot_size, self.slot_size))
            pygame.draw.rect(self.screen, (100, 100, 100), (*pos, self.slot_size, self.slot_size), 1)
            if i == self.inventory.selected_hotbar_index:
                pygame.draw.rect(self.screen, (255, 215, 0), 
                               (pos[0]-2, pos[1]-2, self.slot_size+4, self.slot_size+4), 2)

        # Second pass: Draw items and quantities
        # Draw armor slots
        for i, slot in enumerate(self.inventory.armor):
            if slot is None:
                slot = {"item": None, "quantity": 0}
            slot_id = f"armor_slot_{i}"
            surface = self._render_armor_slot(slot, i)
            self.ui_manager.draw_ui_element(self.inventory_batch, slot_id, surface, 
                                          self._get_armor_pos(i), True)

        # Draw inventory slots
        for i, slot in enumerate(self.inventory.main):
            if slot is None:
                slot = {"item": None, "quantity": 0}
            slot_id = f"inv_slot_{i}"
            surface = self._render_slot(slot, i)
            self.ui_manager.draw_ui_element(self.inventory_batch, slot_id, surface, 
                                          self._get_inventory_pos(i), True)

        # Draw hotbar slots
        for i, slot in enumerate(self.inventory.hotbar):
            if slot is None:
                slot = {"item": None, "quantity": 0}
            slot_id = f"hotbar_slot_{i}"
            surface = self._render_hotbar_slot(slot, i)
            self.ui_manager.draw_ui_element(self.hotbar_batch, slot_id, surface,
                                          self._get_hotbar_pos(i), True)

        # Update cached states
        self._last_frame_items = {
            i: dict(slot) if slot is not None else {"item": None, "quantity": 0} 
            for i, slot in enumerate(self.inventory.main)
        }
        for i, slot in enumerate(self.inventory.armor):
            self._last_frame_items[f"armor_{i}"] = dict(slot) if slot is not None else {"item": None, "quantity": 0}
        self._last_frame_hotbar = {
            i: dict(slot) if slot is not None else {"item": None, "quantity": 0} 
            for i, slot in enumerate(self.inventory.hotbar)
        }

        # Draw dragged item last
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            self._render_dragged_item(mx, my)

        # Draw tooltip if hovering over an item
        mouse_pos = pygame.mouse.get_pos()
        self.get_slot_at_pos(mouse_pos)  # Updates self.hovered_item
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

    def _render_slot(self, slot, index):
        """Create a surface for a single inventory slot"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Draw slot background
        pygame.draw.rect(surface, (50, 50, 50, 200), (0, 0, self.slot_size, self.slot_size))
        pygame.draw.rect(surface, (100, 100, 100, 255), (0, 0, self.slot_size, self.slot_size), 1)
        
        # Draw item if present
        if slot and slot.get("item"):
            item = slot["item"]
            if hasattr(item, 'texture_coords'):
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                surface.blit(scaled_texture, (4, 4))
                
                if slot["quantity"] > 1:
                    quantity_text = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    surface.blit(quantity_text, (self.slot_size - 20, self.slot_size - 20))
        
        return surface

    def _render_hotbar_slot(self, slot, index):
        """Create a surface for a hotbar slot"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Draw slot background
        pygame.draw.rect(surface, (50, 50, 50, 200), (0, 0, self.slot_size, self.slot_size))
        
        # Highlight selected slot
        if index == self.inventory.selected_hotbar_index:
            pygame.draw.rect(surface, (255, 215, 0), (-2, -2, self.slot_size+4, self.slot_size+4), 2)
        
        pygame.draw.rect(surface, (100, 100, 100, 255), (0, 0, self.slot_size, self.slot_size), 1)
        
        # Draw item if present
        if slot and slot.get("item"):
            item = slot["item"]
            if hasattr(item, 'texture_coords'):
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                surface.blit(scaled_texture, (4, 4))
                
                if slot["quantity"] > 1:
                    quantity_text = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    surface.blit(quantity_text, (self.slot_size - 20, self.slot_size - 20))
        
        return surface

    def _get_inventory_pos(self, index):
        """Get position for inventory slot"""
        row = index // 8
        col = index % 8
        x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding) + col * (self.slot_size + self.padding)
        y = 250 + row * (self.slot_size + self.padding)
        return (x, y)

    def _get_hotbar_pos(self, index):
        """Get position for hotbar slot"""
        x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding) + index * (self.slot_size + self.padding)
        y = c.SCREEN_HEIGHT - self.slot_size - 40
        return (x, y)

    def _render_dragged_item(self, mx, my):
        """Render dragged item at mouse position"""
        if not self.dragging_item or not self.dragging_item.get("item"):
            return
            
        item = self.dragging_item["item"]
        if hasattr(item, 'texture_coords'):
            tx, ty = item.texture_coords
            texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
            item_texture = self.atlas.subsurface(texture_rect)
            scaled_texture = pygame.transform.scale(item_texture, (self.slot_size, self.slot_size))
            self.screen.blit(scaled_texture, (mx - self.slot_size//2, my - self.slot_size//2))

    def _render_armor_slot(self, slot, index):
        """Create a surface for an armor slot"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Draw slot background with armor type indicator
        pygame.draw.rect(surface, (60, 60, 80, 200), (0, 0, self.slot_size, self.slot_size))
        
        # Add armor type indicator
        armor_types = ["Helmet", "Chestplate", "Leggings", "Boots", "Shield", "Weapon"]
        if index < len(armor_types):
            type_text = self.font.render(armor_types[index][:1], True, (200, 200, 200))
            surface.blit(type_text, (2, 2))
        
        pygame.draw.rect(surface, (120, 120, 140, 255), (0, 0, self.slot_size, self.slot_size), 1)
        
        # Draw item if present
        if slot and slot.get("item"):
            item = slot["item"]
            if hasattr(item, 'texture_coords'):
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                surface.blit(scaled_texture, (4, 4))
        
        return surface

    def _get_armor_pos(self, index):
        """Get position for armor slot"""
        x = c.SCREEN_WIDTH//2 - 1.5*(self.slot_size + self.padding)
        y = 100 + (index // 3) * (self.slot_size + self.padding)
        x += (index % 3) * (self.slot_size + self.padding)
        return (x, y)
