import pygame
import config as c

class Item:
    def __init__(self, id, name, texture_coords, stack_size=64, is_block=False, burn_time=0):
        self.id = id
        self.name = name
        self.texture_coords = texture_coords
        self.stack_size = stack_size
        self.is_block = is_block
        self.burn_time = burn_time
        self.type = None  # weapon, tool, armor, consumable, etc.
        self.modifiers = {}
        self.enhanced_suffix = ""
        self.is_armor = False
        self.consumable_type = None  # food, drink, etc.
        self.effective_against = []  # List of block names this tool is effective against
        self.is_seed = False
        self.plant_data = None
        self.melt_result = None

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

    def apply_enhancement(self, modifiers, suffix):
        """Apply enhancement modifiers to the item"""
        for stat, value in modifiers.items():
            if stat in self.modifiers:
                self.modifiers[stat] += value
        self.enhanced_suffix = suffix
        self.name = f"{self.name} {suffix}"

    def get_stats_display(self):
        """Get formatted string of item stats for tooltip"""
        stats = []
        for stat, value in self.modifiers.items():
            if value != 0:
                stats.append(f"{stat.replace('_', ' ').title()}: +{value}")
        return "\n".join(stats)

# Define item IDs in clear ranges:
# 1-99: Basic blocks (defined in block.py)
# 100-199: Consumables
# 200-299: Materials
# 300-399: Armor
# 400-499: Tools and Weapons

# Consumables (100-199)
APPLE = Item(100, "Apple", (5, 0), stack_size=16)
APPLE.consumable_type = "food"
APPLE.healing = 20
APPLE.hunger_restore = 30

WATER_BOTTLE = Item(101, "Water Bottle", (6, 0), stack_size=16)
WATER_BOTTLE.consumable_type = "drink"
WATER_BOTTLE.thirst_restore = 40

# Create WHEAT_SEED first without plant_data
WHEAT_SEED = Item(150, "Wheat Seed", (20, 0), stack_size=64)
WHEAT_SEED.is_seed = True

# Base drops for growth stages (using the already created WHEAT_SEED)
WHEAT_DROPS = [
    [(WHEAT_SEED, 1)],  # Stage 0 drops
    [(WHEAT_SEED, 1)],  # Stage 1 drops
    [(WHEAT_SEED, 2)],  # Stage 2 drops
    [(WHEAT_SEED, 3)]   # Stage 3 drops (fully grown)
]

# Now assign plant_data using the predefined drops
WHEAT_SEED.plant_data = {
    'growth_stages': [0, 1, 2, 3],
    'growth_time': 5000,
    'texture_coords': [(21, 0), (21, 1), (21, 2), (21, 3)],
    'drops': WHEAT_DROPS
}

# Materials (200-299)
IRON_INGOT = Item(200, "Iron Ingot", (7, 0))
GOLD_INGOT = Item(201, "Gold Ingot", (8, 0))
COAL = Item(202, "Coal", (9, 0), burn_time=2000)

# Armor (300-399)
IRON_HELMET = Item(300, "Iron Helmet", (10, 0), stack_size=1)
IRON_HELMET.is_armor = True
IRON_HELMET.type = "armor"
IRON_HELMET.modifiers = {"defense": 5, "health": 10}

IRON_CHESTPLATE = Item(301, "Iron Chestplate", (11, 0), stack_size=1)
IRON_CHESTPLATE.is_armor = True
IRON_CHESTPLATE.type = "armor"
IRON_CHESTPLATE.modifiers = {"defense": 8, "health": 20}

IRON_LEGGINGS = Item(302, "Iron Leggings", (12, 0), stack_size=1)
IRON_LEGGINGS.is_armor = True
IRON_LEGGINGS.type = "armor"
IRON_LEGGINGS.modifiers = {"defense": 6, "health": 15}

IRON_BOOTS = Item(303, "Iron Boots", (13, 0), stack_size=1)
IRON_BOOTS.is_armor = True
IRON_BOOTS.type = "armor"
IRON_BOOTS.modifiers = {"defense": 4, "health": 5, "movement_speed": 0.2}

# Tools and Weapons (400-499)
IRON_SWORD = Item(400, "Iron Sword", (14, 0), stack_size=1)
IRON_SWORD.type = "weapon"
IRON_SWORD.modifiers = {"damage": 10, "attack_speed": 1.0}

IRON_PICKAXE = Item(401, "Iron Pickaxe", (15, 0), stack_size=1)
IRON_PICKAXE.type = "tool"
IRON_PICKAXE.effective_against = ["Stone", "Coal Ore", "Iron Ore", "Gold Ore"]
IRON_PICKAXE.modifiers = {"damage": 5}

IRON_AXE = Item(402, "Iron Axe", (16, 0), stack_size=1)
IRON_AXE.type = "tool"
IRON_AXE.effective_against = ["Wood"]
IRON_AXE.modifiers = {"damage": 8}

IRON_SHOVEL = Item(403, "Iron Shovel", (17, 0), stack_size=1)
IRON_SHOVEL.type = "tool"
IRON_SHOVEL.effective_against = ["Dirt", "Grass"]
IRON_SHOVEL.modifiers = {"damage": 4}

IRON_HOE = Item(404, "Iron Hoe", (18, 0), stack_size=1)
IRON_HOE.type = "hoe"  # Change from "tool" to "hoe"
IRON_HOE.effective_against = ["Crops", "Farmland"]

# Special registries for meltable and fuel items
MELTABLE_ITEMS = {}  # Will be populated in block.py for ore->ingot recipes
FUEL_ITEMS = {}      # Will be populated in block.py for items with burn_time

# Update tooltip function to show modifiers
def get_item_tooltip(item):
    if not item:
        return None

    lines = [
        f"{item.name}",
        f"ID: {item.id}"
    ]

    # Add stats if they exist
    stats = item.get_stats_display()
    if stats:
        lines.append("")  # Empty line for spacing
        lines.extend(stats.split("\n"))

    # Add other properties
    if hasattr(item, 'burn_time'):
        lines.append(f"Burn time: {item.burn_time/1000:.1f}s")
    if hasattr(item, 'stack_size'):
        lines.append(f"Stack size: {item.stack_size}")
    if hasattr(item, 'is_block') and item.is_block:
        lines.append("Placeable block")
        
    return '\n'.join(lines)

# Global item registry - all items must be registered here
ITEM_REGISTRY = {
    # Consumables
    100: APPLE,
    101: WATER_BOTTLE,
    150: WHEAT_SEED,  # Add wheat seed
    # Materials
    200: IRON_INGOT,
    201: GOLD_INGOT,
    202: COAL,
    # Armor
    300: IRON_HELMET,
    301: IRON_CHESTPLATE,
    302: IRON_LEGGINGS,
    303: IRON_BOOTS,
    # Tools and Weapons
    400: IRON_SWORD,
    401: IRON_PICKAXE,
    402: IRON_AXE,
    403: IRON_SHOVEL,
    404: IRON_HOE,
}

# Verify no duplicate IDs exist
if len(set(ITEM_REGISTRY.keys())) != len(ITEM_REGISTRY):
    raise ValueError("Duplicate item IDs detected in ITEM_REGISTRY!")

print("Item registry initialized with", len(ITEM_REGISTRY), "items")
for item_id, item in sorted(ITEM_REGISTRY.items()):
    print(f"Registered item {item.name} with ID {item_id}")
