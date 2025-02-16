import pygame
import config as c
from ui_tooltip import Tooltip, get_item_tooltip

class StorageUI:
    def __init__(self, screen, player_inventory, storage_block, atlas):
        self.screen = screen
        self.player_inventory = player_inventory
        self.storage = storage_block
        self.atlas = atlas
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.dragging_item = None
        self.drag_source = None
        self.tooltip = Tooltip(self.font)
        self.hovered_item = None

        # Calculate UI dimensions
        self.slot_size = 50
        self.padding = 10
        screen_center_x = c.SCREEN_WIDTH // 2
        screen_center_y = c.SCREEN_HEIGHT // 2

        # Layout calculations
        total_height = (
            3 * (self.slot_size + self.padding) +  # Storage rows
            4 * (self.slot_size + self.padding) +  # Main inventory rows
            self.slot_size                         # Hotbar row
        )

        # Storage section at top
        self.storage_start_x = screen_center_x - (9 * (self.slot_size + self.padding)) // 2
        self.storage_start_y = 50  # Fixed distance from top

        # Main inventory in middle
        self.inventory_start_x = screen_center_x - (8 * (self.slot_size + self.padding)) // 2
        self.inventory_start_y = self.storage_start_y + 3 * (self.slot_size + self.padding) + 50

        # Hotbar at bottom
        self.hotbar_start_x = screen_center_x - (9 * (self.slot_size + self.padding)) // 2
        self.hotbar_start_y = self.inventory_start_y + 4 * (self.slot_size + self.padding) + 20

        # Labels
        self.storage_label = self.font.render("Storage", True, (255, 255, 255))
        self.inventory_label = self.font.render("Inventory", True, (255, 255, 255))
        self.hotbar_label = self.font.render("Hotbar", True, (255, 255, 255))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            clicked_slot = self.get_slot_at_pos(mouse_pos)
            
            if clicked_slot:
                slot_type, slot_index = clicked_slot
                source_item = None

                # Handle picking up items
                if slot_type == "storage":
                    if self.storage.inventory[slot_index] and self.storage.inventory[slot_index].get("item"):
                        source_item = dict(self.storage.inventory[slot_index])
                        self.storage.inventory[slot_index] = {"item": None, "quantity": 0}
                elif slot_type == "inventory":
                    if self.player_inventory.main[slot_index] and self.player_inventory.main[slot_index].get("item"):
                        source_item = dict(self.player_inventory.main[slot_index])
                        self.player_inventory.main[slot_index] = {"item": None, "quantity": 0}
                elif slot_type == "hotbar":
                    if self.player_inventory.hotbar[slot_index] and self.player_inventory.hotbar[slot_index].get("item"):
                        source_item = dict(self.player_inventory.hotbar[slot_index])
                        self.player_inventory.hotbar[slot_index] = {"item": None, "quantity": 0}

                if source_item and source_item.get("item"):
                    self.dragging_item = source_item
                    self.drag_source = (slot_type, slot_index)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_item and self.dragging_item.get("item"):
                mouse_pos = pygame.mouse.get_pos()
                target_slot = self.get_slot_at_pos(mouse_pos)
                
                if not target_slot:
                    self.return_to_source()
                else:
                    slot_type, slot_index = target_slot
                    target_item = self.get_slot_contents(slot_type, slot_index)

                    if not target_item or not target_item.get("item"):
                        # Place in empty slot
                        self.place_item(slot_type, slot_index, dict(self.dragging_item))
                        self.dragging_item = None
                    else:
                        # Handle stacking or swapping
                        if target_item.get("item") and self.dragging_item.get("item") and \
                           target_item["item"].id == self.dragging_item["item"].id:
                            total = target_item["quantity"] + self.dragging_item["quantity"]
                            max_stack = target_item["item"].stack_size
                            if total <= max_stack:
                                target_item["quantity"] = total
                                self.dragging_item = None
                            else:
                                target_item["quantity"] = max_stack
                                self.dragging_item["quantity"] = total - max_stack
                                self.return_to_source()
                        else:
                            # Swap items
                            temp = dict(target_item)
                            self.place_item(slot_type, slot_index, dict(self.dragging_item))
                            self.dragging_item = temp

                if self.dragging_item:
                    self.return_to_source()
                self.dragging_item = None
                self.drag_source = None

    def get_slot_contents(self, slot_type, index):
        """Get contents of a slot with proper initialization"""
        content = None
        if slot_type == "storage":
            content = self.storage.inventory[index]
        elif slot_type == "inventory":
            content = self.player_inventory.main[index]
        elif slot_type == "hotbar":
            content = self.player_inventory.hotbar[index]
        
        # Initialize empty slots with proper structure
        if not content:
            content = {"item": None, "quantity": 0}
        return content

    def place_item(self, slot_type, index, item):
        """Place item with proper structure"""
        item_copy = dict(item) if item else {"item": None, "quantity": 0}
        if slot_type == "storage":
            self.storage.inventory[index] = item_copy
        elif slot_type == "inventory":
            self.player_inventory.main[index] = item_copy
        elif slot_type == "hotbar":
            self.player_inventory.hotbar[index] = item_copy

    def return_to_source(self):
        if self.drag_source:
            source_type, index = self.drag_source
            self.place_item(source_type, index, self.dragging_item)

    def get_slot_at_pos(self, pos):
        mx, my = pos
        slot_info = None
        self.hovered_item = None  # Reset hovered item

        # Check storage slots (3 rows x 9 columns)
        for i in range(27):
            row = i // 9
            col = i % 9
            x = self.storage_start_x + col * (self.slot_size + self.padding)
            y = self.storage_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            if rect.collidepoint(mx, my):
                slot_info = ("storage", i)
                if self.storage.inventory[i] and self.storage.inventory[i].get("item"):
                    self.hovered_item = self.storage.inventory[i]["item"]
                break

        # Check main inventory slots (4 rows x 8 columns)
        if not slot_info:
            for i in range(32):
                row = i // 8
                col = i % 8
                x = self.inventory_start_x + col * (self.slot_size + self.padding)
                y = self.inventory_start_y + row * (self.slot_size + self.padding)
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                if rect.collidepoint(mx, my):
                    slot_info = ("inventory", i)
                    if self.player_inventory.main[i] and self.player_inventory.main[i].get("item"):
                        self.hovered_item = self.player_inventory.main[i]["item"]
                    break

        # Check hotbar slots
        if not slot_info:
            for i in range(9):
                x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                if rect.collidepoint(mx, my):
                    slot_info = ("hotbar", i)
                    if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                        self.hovered_item = self.player_inventory.hotbar[i]["item"]
                    break

        return slot_info

    def draw(self):
        # Get current mouse position and update hovered item
        mouse_pos = pygame.mouse.get_pos()
        self.get_slot_at_pos(mouse_pos)  # This updates self.hovered_item

        # Create single translucent background
        bg_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_overlay.fill((0, 0, 0, 160))  # Reduced opacity (160 instead of 180))
        self.screen.blit(bg_overlay, (0, 0))

        # Draw slots with semi-transparent backgrounds
        slot_bg = (70, 70, 70, 200)
        slot_border = (200, 200, 200, 255)

        # Draw section labels
        self.screen.blit(self.storage_label, (self.storage_start_x, self.storage_start_y - 25))
        self.screen.blit(self.inventory_label, (self.inventory_start_x, self.inventory_start_y - 25))
        self.screen.blit(self.hotbar_label, (self.hotbar_start_x, self.hotbar_start_y - 25))

        # Draw storage slots
        for i in range(27):
            row = i // 9
            col = i % 9
            x = self.storage_start_x + col * (self.slot_size + self.padding)
            y = self.storage_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            
            slot = self.storage.inventory[i]
            if slot and slot.get("item"):
                self.draw_item(slot, rect)

        # Draw main inventory
        for i in range(32):
            row = i // 8
            col = i % 8
            x = self.inventory_start_x + col * (self.slot_size + self.padding)
            y = self.inventory_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            
            if i < len(self.player_inventory.main):
                slot = self.player_inventory.main[i]
                if slot and slot.get("item"):
                    self.draw_item(slot, rect)

        # Draw hotbar
        for i in range(9):
            x = self.hotbar_start_x + i * (self.slot_size + self.padding)
            rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            
            if i == self.player_inventory.selected_hotbar_index:
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(6, 6), 3)
            
            slot = self.player_inventory.hotbar[i]
            if slot and slot.get("item"):
                self.draw_item(slot, rect)

        # Draw dragged item
        if self.dragging_item and self.dragging_item.get("item"):
            mx, my = pygame.mouse.get_pos()
            item = self.dragging_item["item"]
            tx, ty = item.texture_coords
            texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
            item_img = self.atlas.subsurface(texture_rect)
            item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
            self.screen.blit(item_img, (mx - self.slot_size//2, my - self.slot_size//2))

        # Draw tooltip last (after dragged item)
        if self.hovered_item and not self.dragging_item:
            tooltip_text = get_item_tooltip(self.hovered_item)
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

    def draw_item(self, slot, rect):
        item = slot["item"]
        tx, ty = item.texture_coords
        texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
        item_img = self.atlas.subsurface(texture_rect)
        item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
        self.screen.blit(item_img, rect.topleft)
        if slot["quantity"] > 1:
            quantity = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
            self.screen.blit(quantity, (rect.right - quantity.get_width() - 5, rect.bottom - quantity.get_height() - 5))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
