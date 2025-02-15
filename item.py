import pygame
import config as c

class Item:
    def __init__(self, id, name, texture_coords, stack_size=1, is_block=False, is_armor=False, tint=None, effective_against=None, consumable_type=None, hunger_restore=0, thirst_restore=0, health_restore=0):
        self.id = id
        self.name = name
        self.texture_coords = texture_coords
        self.stack_size = stack_size
        self.is_block = is_block
        self.is_armor = is_armor  # NEW: Add is_armor attribute
        self.tint = tint  # Tint color to modify item appearance
        self.effective_against = effective_against  # List of block names this item is effective against
        self.consumable_type = consumable_type  # Type of consumable (e.g., "food", "drink", "potion")
        self.hunger_restore = hunger_restore  # Amount of hunger restored
        self.thirst_restore = thirst_restore  # Amount of thirst restored
        self.health_restore = health_restore  # Amount of health restored

    def get_texture(self, atlas):
        block_size = c.BLOCK_SIZE
        tx, ty = self.texture_coords
        texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
        image = atlas.subsurface(texture_rect).convert_alpha()
        # Apply tint if set (ensuring transparency).
        if self.tint:
            tinted = image.copy()
            tinted.fill(self.tint, special_flags=pygame.BLEND_RGBA_MULT)
            image = tinted
        return image

    def consume(self, character):
        # Apply consumable effects to the character.
        if self.consumable_type == "food":
            character.hunger = min(100, character.hunger + self.hunger_restore)
            print(f"{self.name} consumed: hunger increased by {self.hunger_restore}")
        elif self.consumable_type == "drink":
            character.thirst = min(100, character.thirst + self.thirst_restore)
            print(f"{self.name} consumed: thirst increased by {self.thirst_restore}")
        elif self.consumable_type == "potion":
            character.health = min(100, character.health + self.health_restore)
            print(f"{self.name} consumed: health increased by {self.health_restore}")
        else:
            print(f"{self.name} is not consumable")
        # Return True if consumed successfully, False otherwise.
        return self.consumable_type is not None

# Define tool items with effective_against set:
ITEM_PICKAXE = Item(100, "Pickaxe", (0, 0), stack_size=1, effective_against=["Stone", "Dirt", "Coal Ore", "Iron Ore", "Gold Ore"])
ITEM_AXE = Item(101, "Axe", (1, 0), stack_size=1, effective_against=["Wood"])
ITEM_SHOVEL = Item(102, "Shovel", (2, 0), stack_size=1, effective_against=["Dirt"])
ITEM_SWORD = Item(103, "Sword", (3, 0), stack_size=1)

# New test items for consumables:
APPLE = Item(103, "Apple", (0, 0), stack_size=10, consumable_type="food", hunger_restore=20)
WATER_BOTTLE = Item(104, "Water Bottle", (0, 1), stack_size=10, consumable_type="drink", thirst_restore=30)

# ...add additional item types or subclasses as needed...
