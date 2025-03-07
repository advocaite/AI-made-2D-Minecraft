import pygame
import config as c
import os  # Add this import at the top

# Create registry dict FIRST before using it
ITEM_REGISTRY = {}

class Item:
    def __init__(self, id, name, texture_coords, stack_size=64, is_block=False, **kwargs):
        self.id = id
        self.name = name
        # Validate texture coordinates
        if texture_coords is None:
            self.texture_coords = (0, 0)  # Default texture coordinates
            print(f"Warning: No texture coordinates provided for item {name}, using default (0,0)")
        else:
            try:
                x, y = texture_coords
                self.texture_coords = (int(x), int(y))
            except (TypeError, ValueError):
                self.texture_coords = (0, 0)
                print(f"Warning: Invalid texture coordinates for item {name}, using default (0,0)")
        self.stack_size = stack_size
        self.is_block = is_block
        self.is_armor = False
        self.effective_against = kwargs.get('effective_against', [])
        self.consumable_type = kwargs.get('consumable_type', None)
        self.block = None
        self.burn_time = kwargs.get('burn_time', 0)
        self.melt_result = None
        self.hunger_restore = kwargs.get('hunger_restore', 0)
        self.thirst_restore = kwargs.get('thirst_restore', 0)
        self.health_restore = kwargs.get('health_restore', 0)
        self.tint = None  # Added this for the get_texture method
        self.type = None  # Add this line to store item type
        self.script = None  # Add script property
        self.is_seed = False  # Initialize is_seed property
        self.plant_data = None  # Initialize plant_data property

        # Add stat modifiers
        self.modifiers = {
            'damage': 0,
            'defense': 0,
            'health': 0,
            'attack_speed': 0,
            'movement_speed': 0
        }
        self.enhanced_suffix = ""  # For names like "Iron Sword of Sharpness"

        # Handle multiple scripts if defined
        if kwargs.get('scripts'):
            for script_path in kwargs['scripts']:
                self._load_script(script_path)
        # Maintain backward compatibility with single script
        elif kwargs.get('script_path'):
            self._load_script(kwargs['script_path'])

    def _load_script(self, script_path):
        """Load the item's script"""
        try:
            import importlib.util
            
            # Get absolute path to scripts directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, "scripts", "items", script_path)
            
            print(f"[ITEM] Attempting to load script from: {full_path}")
            
            if not os.path.exists(full_path):
                print(f"[ITEM] Script file not found at: {full_path}")
                return
                
            spec = importlib.util.spec_from_file_location(
                f"item_script_{self.id}", 
                full_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.script = module.ItemScript(self)
            print(f"[ITEM] Successfully loaded script for {self.name}")
            
        except Exception as e:
            print(f"[ITEM] Error loading script for {self.name}: {e}")
            import traceback
            traceback.print_exc()

    def on_hit(self, target):
        """Delegate hit behavior to script"""
        if self.script and hasattr(self.script, 'on_hit'):
            print(f"[ITEM] {self.name} delegating hit to script")
            return self.script.on_hit(target)
        print(f"[ITEM] {self.name} has no script or on_hit method")
        return False

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

# Define tool items with effective_against set:
ITEM_PICKAXE = Item(100, "Pickaxe", (0, 0), stack_size=1, effective_against=["Stone", "Dirt", "Coal Ore", "Iron Ore", "Gold Ore"])
ITEM_AXE = Item(101, "Axe", (1, 0), stack_size=1, effective_against=["Wood"])
ITEM_SHOVEL = Item(102, "Shovel", (2, 0), stack_size=1, effective_against=["Dirt"])
ITEM_SWORD = Item(103, "Sword", (3, 0), stack_size=1)

# New test items for consumables:
APPLE = Item(104, "Apple", (0, 0), stack_size=10, consumable_type="food", hunger_restore=20)
WATER_BOTTLE = Item(105, "Water Bottle", (0, 1), stack_size=10, consumable_type="drink", thirst_restore=30)

# Define meltable items and their results
IRON_INGOT = Item(200, "Iron Ingot", (20, 1), stack_size=64)
GOLD_INGOT = Item(201, "Gold Ingot", (20, 2), stack_size=64)
COAL = Item(202, "Coal", (20, 3), stack_size=64, burn_time=2000)  # Coal burns for 2 seconds

# Create registries for items that can be melted or used as fuel
MELTABLE_ITEMS = {
    17: IRON_INGOT,  # Iron Ore -> Iron Ingot
    18: GOLD_INGOT,  # Gold Ore -> Gold Ingot
    16: COAL        # Coal Ore -> Coal
}

# Update FUEL_ITEMS dictionary
FUEL_ITEMS = {
    19: 1000,     # Wood burns for 1 second (1000ms)
    202: 2000     # Coal burns for 2 seconds
}

# Create armor items with types
IRON_HELMET = Item(30, "Iron Helmet", (5, 1), stack_size=1)
IRON_HELMET.type = "helmet"

IRON_CHESTPLATE = Item(31, "Iron Chestplate", (5, 2), stack_size=1)
IRON_CHESTPLATE.type = "chestplate"

IRON_LEGGINGS = Item(32, "Iron Leggings", (5, 3), stack_size=1)
IRON_LEGGINGS.type = "leggings"

IRON_BOOTS = Item(33, "Iron Boots", (5, 4), stack_size=1)
IRON_BOOTS.type = "boots"

# Tools and weapons with types
IRON_SWORD = Item(40, "Iron Sword", (30, 3), stack_size=1, script_path="iron_sword.py")
IRON_SWORD.type = "weapon"
IRON_SWORD.modifiers = {'damage': 5, 'attack_speed': 1.0}  # Add base stats

IRON_PICKAXE = Item(41, "Iron Pickaxe", (6, 2), stack_size=1)
IRON_PICKAXE.type = "tool"

IRON_AXE = Item(42, "Iron Axe", (6, 3), stack_size=1)
IRON_AXE.type = "tool"

IRON_SHOVEL = Item(43, "Iron Shovel", (6, 4), stack_size=1)
IRON_SHOVEL.type = "tool"

# Add unbreakable item definition with proper attributes
UNBREAKABLE = Item(
    id=8,  # Must match block ID
    name="Unbreakable",
    texture_coords=(4, 3),  # Must match block texture
    stack_size=64,
    is_block=True
)

# Register items AFTER they're defined
ITEM_REGISTRY.update({
    UNBREAKABLE.id: UNBREAKABLE,
    ITEM_PICKAXE.id: ITEM_PICKAXE,
    ITEM_AXE.id: ITEM_AXE,
    APPLE.id: APPLE,
    WATER_BOTTLE.id: WATER_BOTTLE,
    IRON_INGOT.id: IRON_INGOT,
    GOLD_INGOT.id: GOLD_INGOT,
    COAL.id: COAL,
    IRON_HELMET.id: IRON_HELMET,
    IRON_CHESTPLATE.id: IRON_CHESTPLATE,
    IRON_LEGGINGS.id: IRON_LEGGINGS,
    IRON_BOOTS.id: IRON_BOOTS,
    IRON_SWORD.id: IRON_SWORD,
    IRON_PICKAXE.id: IRON_PICKAXE,
    IRON_AXE.id: IRON_AXE,
    IRON_SHOVEL.id: IRON_SHOVEL,
    ITEM_SHOVEL.id: ITEM_SHOVEL,
    ITEM_SWORD.id: ITEM_SWORD
})

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

    # Add script effects info if present
    if hasattr(item, 'script'):
        lines.append("")  # Empty line before effects
        if hasattr(item.script, 'get_tooltip_info'):
            # Let script provide its own tooltip info
            script_info = item.script.get_tooltip_info()
            lines.extend(script_info)
        else:
            # Default script effect display
            if hasattr(item.script, 'on_hit'):
                lines.append("Special Effects:")
                if item.name == "Iron Sword":  # You can make this more generic
                    lines.append("• 10% chance to cause bleeding")

    # Add other properties
    if hasattr(item, 'burn_time'):
        lines.append(f"Burn time: {item.burn_time/1000:.1f}s")
    if hasattr(item, 'stack_size'):
        lines.append(f"Stack size: {item.stack_size}")
    if hasattr(item, 'is_block') and item.is_block:
        lines.append("Placeable block")
        
    return '\n'.join(lines)

# Also register any tool items
for tool in [ITEM_PICKAXE, ITEM_AXE, ITEM_SHOVEL, ITEM_SWORD]:
    if tool.id not in ITEM_REGISTRY:
        ITEM_REGISTRY[tool.id] = tool
