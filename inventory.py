import pygame
import config as c
from item import Item  # assumed item module
from block import BLOCK_MAP, AIR  # added import to get blocks

class Inventory:
    def __init__(self):
        self.hotbar = [{"item": None, "quantity": 0} for _ in range(9)]
        self.armor = [{"item": None, "quantity": 0} for _ in range(6)]
        self.main = [{"item": None, "quantity": 0} for _ in range(32)]
        self.selected_hotbar_index = 0
        # Prefill hotbar with block items (excluding AIR).
        blocks = [blk for key, blk in sorted(BLOCK_MAP.items()) if blk != AIR]
        # Limit to available hotbar slots (1-9).
        for blk in blocks[:9]:
            self.fill_empty_hotbar_slot(blk.item_variant, 64)

    def fill_empty_hotbar_slot(self, item_variant, quantity=1):
        for slot in self.hotbar:
            if slot["item"] is None:
                slot["item"] = item_variant
                slot["quantity"] = quantity
                break

    def add_item_to_hotbar(self, item_variant, quantity=1):
        self.hotbar.append({"item": item_variant, "quantity": quantity})

    def add_item(self, item, quantity=1):
        """Add an item to the inventory"""
        print(f"Debug: Adding item {item.name} with quantity {quantity}")
        
        # First try to stack with existing items
        for container in (self.hotbar, self.armor, self.main):
            for slot in container:
                if slot and slot["item"] and slot["item"].id == item.id and slot["quantity"] < item.stack_size:
                    space = item.stack_size - slot["quantity"]
                    add_amount = min(space, quantity)
                    slot["quantity"] += add_amount
                    quantity -= add_amount
                    if quantity <= 0:
                        return True

        # If we still have items to add, find empty slots
        if quantity > 0:
            # Try hotbar first
            for slot in self.hotbar:
                if not slot["item"]:  # Check the item field of the dict
                    slot["item"] = item
                    slot["quantity"] = quantity
                    return True

            # Then try main inventory
            for slot in self.main:
                if not slot["item"]:  # Check the item field of the dict
                    slot["item"] = item
                    slot["quantity"] = quantity
                    return True

        return False

    def update_quantity(self, slot, amount):
        """Update the quantity of an item in a given slot."""
        if slot and "item" in slot and slot["item"]:
            slot["quantity"] += amount
            if slot["quantity"] <= 0:
                slot["item"] = None
                slot["quantity"] = 0

    def remove_item(self, slot_id, amount=1):
        """Remove items from a given slot id (1-indexed)"""
        container, index = self.slot_id_to_slot(slot_id)
        if container[index]:
            if container[index]["quantity"] > amount:
                container[index]["quantity"] -= amount
            else:
                container[index] = None

    def slot_id_to_slot(self, slot_id):
        """Convert slot id to container and index.
           Slots 1-9: hotbar, 10-15: armor, 16-47: main."""
        if 1 <= slot_id <= 9:
            return self.hotbar, slot_id - 1
        elif 10 <= slot_id <= 15:
            return self.armor, slot_id - 10
        elif 16 <= slot_id <= 47:
            return self.main, slot_id - 16
        else:
            raise ValueError("Invalid slot id.")

    def select_hotbar_slot(self, index):
        if 0 <= index < len(self.hotbar):
            self.selected_hotbar_index = index

    def get_selected_item(self):
        if 0 <= self.selected_hotbar_index < len(self.hotbar):
            return self.hotbar[self.selected_hotbar_index]
        return None

    def get_item(self, slot_index):
        """Get item from a slot in main inventory."""
        if 0 <= slot_index < len(self.main):
            return self.main[slot_index]
        return None

    def set_item(self, slot_index, item_data):
        """Set item in a slot in main inventory."""
        if 0 <= slot_index < len(self.main):
            self.main[slot_index] = item_data
            return True
        return False

    def draw(self, surface, atlas):
        self.draw_hotbar(surface, atlas)
        # Similar drawing can be implemented for armor and main inventory as needed.

    def draw_hotbar(self, surface, atlas):
        slot_size = 40
        padding = 5
        total_width = len(self.hotbar) * (slot_size + padding) - padding
        x_start = (c.SCREEN_WIDTH - total_width) // 2
        y = c.SCREEN_HEIGHT - slot_size - 20
        for i, slot in enumerate(self.hotbar):
            rect = pygame.Rect(x_start + i * (slot_size + padding), y, slot_size, slot_size)
            if i == self.selected_hotbar_index:
                pygame.draw.rect(surface, (255, 215, 0), rect.inflate(6, 6), 4)
            pygame.draw.rect(surface, (50, 50, 50), rect)
            pygame.draw.rect(surface, (200, 200, 200), rect, 2)
            if slot and "item" in slot and slot["item"]:
                item = slot["item"]
                tx, ty = item.texture_coords
                block_size = c.BLOCK_SIZE
                texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
                item_img = atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (slot_size, slot_size))
                surface.blit(item_img, rect.topleft)
                if slot.get("quantity", 0) > 1:
                    font = pygame.font.SysFont(None, 24)
                    amount_surf = font.render(str(slot["quantity"]), True, (255, 255, 255))
                    surface.blit(amount_surf, (rect.right - amount_surf.get_width(), rect.bottom - amount_surf.get_height()))

    def draw_inventory(self, screen, texture_atlas, x, y):
        """Draw the main inventory grid (excluding hotbar)."""
        slot_size = 40
        slot_padding = 5
        rows = 4  # Standard inventory rows
        cols = 9  # Standard inventory columns
        
        # Draw main inventory slots
        for i, slot in enumerate(self.main):
            row = i // cols
            col = i % cols
            slot_x = x + col * (slot_size + slot_padding)
            slot_y = y + row * (slot_size + slot_padding)
            
            # Draw slot background
            pygame.draw.rect(screen, (100, 100, 100), (slot_x, slot_y, slot_size, slot_size))
            
            # Draw item if present
            if slot and "item" in slot and slot["item"]:
                item = slot["item"]
                quantity = slot["quantity"]
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * 16, ty * 16, 16, 16)  # Assuming 16x16 textures
                item_texture = texture_atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (slot_size-8, slot_size-8))
                screen.blit(scaled_texture, (slot_x+4, slot_y+4))
                
                # Draw quantity if more than 1
                if quantity > 1:
                    font = pygame.font.SysFont(None, 24)
                    quantity_text = font.render(str(quantity), True, (255, 255, 255))
                    screen.blit(quantity_text, (slot_x + slot_size - 20, slot_y + slot_size - 20))

    def refill_hotbar(self):
        if not self.hotbar:
            from block import BLOCK_MAP, AIR
            blocks = [blk for key, blk in sorted(BLOCK_MAP.items()) if blk != AIR]
            for blk in blocks[:9]:
                self.fill_empty_hotbar_slot(blk.item_variant, 64)
