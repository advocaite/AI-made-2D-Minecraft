import pygame
import config as c

class StorageUI:
    def __init__(self, screen, player_inventory, storage_block, texture_atlas):
        self.screen = screen
        self.player_inventory = player_inventory
        self.storage = storage_block
        self.texture_atlas = texture_atlas
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        
        # Calculate UI dimensions
        self.margin = 10
        self.slot_size = 40
        self.slot_padding = 5
        
        # Calculate storage grid
        self.storage_rows = 3
        self.storage_cols = 9
        self.storage_width = self.storage_cols * (self.slot_size + self.slot_padding)
        self.storage_height = self.storage_rows * (self.slot_size + self.slot_padding)
        
        # Position the storage grid
        self.storage_x = (c.SCREEN_WIDTH - self.storage_width) // 2
        self.storage_y = 100

        # Player inventory grid (for reference)
        self.player_inv_x = self.storage_x
        self.player_inv_y = self.storage_y + self.storage_height + 50

        self.selected_slot = None
        self.dragging_item = None
        self.drag_source = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                clicked_slot = self.get_slot_at_pos(mouse_pos)
                if clicked_slot:
                    slot_type, slot_index = clicked_slot
                    if slot_type == "storage":
                        self.dragging_item = self.storage.remove_item(slot_index)  # Use remove_item instead of direct access
                        if self.dragging_item:
                            self.drag_source = ("storage", slot_index)
                    elif slot_type == "player":
                        self.dragging_item = self.player_inventory.main[slot_index]
                        if self.dragging_item:
                            self.player_inventory.main[slot_index] = None  # Clear the slot
                            self.drag_source = ("player", slot_index)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item:  # Left click release
                mouse_pos = pygame.mouse.get_pos()
                target_slot = self.get_slot_at_pos(mouse_pos)
                
                placed = False
                if target_slot:
                    slot_type, slot_index = target_slot
                    if slot_type == "storage":
                        if self.storage.inventory[slot_index] is None:
                            self.storage.inventory[slot_index] = self.dragging_item
                            placed = True
                    elif slot_type == "player":
                        if self.player_inventory.main[slot_index] is None:
                            self.player_inventory.main[slot_index] = self.dragging_item
                            placed = True
                
                # If item wasn't placed, return to original position
                if not placed and self.drag_source:
                    source_type, source_index = self.drag_source
                    if source_type == "storage":
                        self.storage.inventory[source_index] = self.dragging_item
                    elif source_type == "player":
                        self.player_inventory.main[source_index] = self.dragging_item
                
                self.dragging_item = None
                self.drag_source = None

    def get_slot_at_pos(self, pos):
        mx, my = pos
        # Check storage slots
        for i in range(self.storage.max_slots):
            row = i // self.storage_cols
            col = i % self.storage_cols
            x = self.storage_x + col * (self.slot_size + self.slot_padding)
            y = self.storage_y + row * (self.slot_size + self.slot_padding)
            if x <= mx <= x + self.slot_size and y <= my <= y + self.slot_size:
                return ("storage", i)
        
        # Check player inventory slots
        for i in range(len(self.player_inventory.main)):
            row = i // 9
            col = i % 9
            x = self.player_inv_x + col * (self.slot_size + self.slot_padding)
            y = self.player_inv_y + row * (self.slot_size + self.slot_padding)
            if x <= mx <= x + self.slot_size and y <= my <= y + self.slot_size:
                return ("player", i)
        return None

    def draw(self):
        # Draw semi-transparent background
        overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        # Draw storage title
        title = self.font.render("Storage", True, (255, 255, 255))
        self.screen.blit(title, (self.storage_x, self.storage_y - 30))

        # Draw storage slots
        for i in range(self.storage.max_slots):
            row = i // self.storage_cols
            col = i % self.storage_cols
            x = self.storage_x + col * (self.slot_size + self.slot_padding)
            y = self.storage_y + row * (self.slot_size + self.slot_padding)
            
            # Draw slot background
            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, self.slot_size, self.slot_size))
            
            # Draw item if present
            if self.storage.inventory[i]:
                item = self.storage.inventory[i]["item"]
                quantity = self.storage.inventory[i]["quantity"]
                if item:
                    tx, ty = item.texture_coords
                    texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                    item_texture = self.texture_atlas.subsurface(texture_rect)
                    scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                    self.screen.blit(scaled_texture, (x+4, y+4))
                    if quantity > 1:
                        quantity_text = self.font.render(str(quantity), True, (255, 255, 255))
                        self.screen.blit(quantity_text, (x + self.slot_size - 20, y + self.slot_size - 20))

        # Draw player inventory
        self.player_inventory.draw_inventory(self.screen, self.texture_atlas, self.player_inv_x, self.player_inv_y)

        # Draw dragged item
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            item = self.dragging_item["item"]
            if item:
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.texture_atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                self.screen.blit(scaled_texture, (mx-self.slot_size//2, my-self.slot_size//2))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)
            
            self.draw()
            pygame.display.flip()
