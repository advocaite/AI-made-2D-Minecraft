class Item:
    def __init__(self, id, name, texture_coords, stack_size=64, is_block=False, is_armor=False, consumable_type=None, hunger_restore=0, thirst_restore=0, health_restore=0, effective_against=None):
        self.id = id
        self.name = name
        self.texture_coords = texture_coords  # (x, y) in the texture atlas
        self.stack_size = stack_size
        self.is_block = is_block
        self.is_armor = is_armor
        self.consumable_type = consumable_type  # e.g., "food", "drink", "potion"
        self.hunger_restore = hunger_restore
        self.thirst_restore = thirst_restore
        self.health_restore = health_restore
        # Ensure we always have a list copy.
        self.effective_against = list(effective_against) if effective_against is not None else []

    def consume(self, character):
        # Apply consumable effects to the character.
        if self.consumable_type == "food":
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
