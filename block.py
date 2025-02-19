from item import Item, IRON_INGOT, GOLD_INGOT, COAL, MELTABLE_ITEMS, FUEL_ITEMS  # Add COAL to imports
import pygame
import config as c
import pygame
import config as c
from block_loader import BlockLoader
from registry import REGISTRY

class Block:
    def __init__(self, id, name, solid, color, texture_coords, drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        self.id = id
        self.name = name
        self.solid = solid
        self.color = color
        # Convert texture_coords to tuple or use default
        self.texture_coords = tuple(texture_coords) if texture_coords is not None else (0, 0)
        self.drop_item = drop_item  # Optional item drop
        self.animation_frames = animation_frames  # List of (x, y) tuples for animation frames
        self.frame_duration = frame_duration  # Duration of each frame in milliseconds
        self.tint = tint  # Tint color to modify block appearance
        self.item_variant = None  # New: will hold the corresponding item
        self.entity_type = entity_type  # New: entity type to spawn

    # NEW: Helper method to get the block texture with tint applied if set.
    def get_texture(self, atlas):
        # Always use tuple for cache key
        cache_key = (self.id, self.texture_coords)  # texture_coords is already a tuple

        # Clear texture cache if coordinates changed
        if hasattr(self, '_last_coords') and self._last_coords != self.texture_coords:
            if hasattr(self, '_cached_base'):
                del self._cached_base
            if hasattr(self, '_cached_texture'):
                del self._cached_texture
        self._last_coords = self.texture_coords

        # Special case for AIR - return None to indicate no texture
        if self.id == 0:
            return None

        # Generate texture
        if not hasattr(self, '_cached_base'):
            block_size = c.BLOCK_SIZE
            tx, ty = self.texture_coords
            texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
            self._cached_base = atlas.subsurface(texture_rect).convert_alpha()
            #print(f"[TEXTURE] Created new texture for {self.name} at {self.texture_coords}")

        if not self.tint:
            return self._cached_base
        if not hasattr(self, "_cached_texture"):
            tinted = self._cached_base.copy()
            tinted.fill(self.tint, special_flags=pygame.BLEND_RGBA_MULT)
            self._cached_texture = tinted
        return self._cached_texture

    def create_instance(self):
        """Create a new instance of the block"""
        # Special case for AIR blocks
        if self.id == 0:
            return self  # Return the singleton AIR instance
            
        # For other blocks, create a new instance
        new_block = Block(
            id=self.id,
            name=self.name,
            solid=self.solid,
            color=self.color,
            texture_coords=self.texture_coords,
            drop_item=self.drop_item,
            animation_frames=self.animation_frames,
            frame_duration=self.frame_duration,
            tint=self.tint,
            entity_type=self.entity_type
        )
        new_block.item_variant = self.item_variant
        return new_block

    def to_dict(self):
        """Base serialization for blocks"""
        return {
            'id': self.id,
            'name': self.name,
            'solid': self.solid,
            'color': self.color,
            'texture_coords': self.texture_coords,
            'tint': self.tint,
            'entity_type': self.entity_type
        }

    def from_dict(self, data, item_registry):
        """Base deserialization for blocks"""
        self.id = data.get('id', self.id)
        self.name = data.get('name', self.name)
        self.solid = data.get('solid', self.solid)
        self.color = data.get('color', self.color)
        self.texture_coords = data.get('texture_coords', self.texture_coords)
        self.tint = data.get('tint', self.tint)
        self.entity_type = data.get('entity_type', self.entity_type)  # Fixed missing parenthesis

class StorageBlock(Block):
    def __init__(self, id, name, texture_coords, solid=True, color=(139, 69, 19), 
                 drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        super().__init__(id, name, solid, color, texture_coords, drop_item, 
                        animation_frames, frame_duration, tint, entity_type)
        self.has_inventory = True
        
        # Import and create script right away
        from scripts.blocks.storage_block import BlockScript
        self.script = BlockScript(self)
        # For backward compatibility
        self.max_slots = self.script.max_slots
        self.inventory = self.script.inventory

    def create_instance(self):
        """Create a new instance with its own inventory"""
        new_block = StorageBlock(
            id=self.id,
            name=self.name,
            texture_coords=self.texture_coords,
            solid=self.solid,
            color=self.color
        )
        # Ensure script is initialized
        from scripts.blocks.storage_block import BlockScript
        new_block.script = BlockScript(new_block)
        new_block.max_slots = new_block.script.max_slots
        new_block.inventory = new_block.script.inventory
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def to_dict(self):
        """Serialize storage state"""
        data = super().to_dict()
        if self.script:
            data.update({
                'storage_data': self.script.to_dict()
            })
        return data

    def from_dict(self, data, item_registry):
        """Deserialize storage state"""
        super().from_dict(data, item_registry)
        if self.script and 'storage_data' in data:
            self.script.from_dict(data['storage_data'], item_registry)
            self.inventory = self.script.inventory  # Update compatibility reference

class FurnaceBlock(Block):
    def __init__(self, id, name, texture_coords, solid=True, color=(100, 100, 100), 
                 drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        super().__init__(id=id, name=name, solid=solid, color=color, texture_coords=texture_coords,
                        drop_item=drop_item, animation_frames=animation_frames, 
                        frame_duration=frame_duration, tint=tint, entity_type=entity_type)
        self.has_inventory = True
        
        # Import and create script right away
        from scripts.blocks.furnace_block import BlockScript
        self.script = BlockScript(self)
        # Add these proxy properties to maintain compatibility
        self._update_proxy_slots()

    def _update_proxy_slots(self):
        """Update proxy slots from script"""
        self.input_slot = self.script.input_slot
        self.fuel_slot = self.script.fuel_slot
        self.output_slot = self.script.output_slot

    def create_instance(self):
        """Create a new instance of the furnace with its own inventory"""
        new_block = FurnaceBlock(self.id, self.name, self.texture_coords)
        # Ensure script is initialized
        from scripts.blocks.furnace_block import BlockScript
        new_block.script = BlockScript(new_block)
        # Update proxy properties
        new_block._update_proxy_slots()
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    # Delegate all methods to script
    def update(self, dt):
        if self.script:
            self.script.update(dt)
            self._update_proxy_slots()  # Keep proxy slots in sync

    def to_dict(self):
        """Serialize furnace state"""
        data = super().to_dict()
        if self.script:
            data.update({
                'furnace_data': self.script.to_dict()  # Store script data in its own key
            })
        return data

    def from_dict(self, data, item_registry):
        """Deserialize furnace state"""
        super().from_dict(data, item_registry)
        if self.script and 'furnace_data' in data:
            self.script.from_dict(data['furnace_data'], item_registry)
            self._update_proxy_slots()

class EnhancerBlock(Block):
    def __init__(self, id, name, texture_coords, solid=True, color=(100, 50, 150), 
                 drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        super().__init__(id, name, solid, color, texture_coords, drop_item, 
                        animation_frames, frame_duration, tint, entity_type)
        self.has_inventory = True
        self.can_interact = True
        
        # Import and create script right away, similar to FurnaceBlock
        from scripts.blocks.enhancer_block import BlockScript
        self.script = BlockScript(self)
        # For backward compatibility
        self.input_slot = self.script.input_slot
        self.ingredient_slot = self.script.ingredient_slot

    def create_instance(self):
        """Create a new instance with its own inventory"""
        new_block = EnhancerBlock(
            id=self.id,
            name=self.name,
            texture_coords=self.texture_coords,
            solid=self.solid,
            color=self.color
        )
        # Ensure script is initialized
        from scripts.blocks.enhancer_block import BlockScript
        new_block.script = BlockScript(new_block)
        new_block.input_slot = new_block.script.input_slot
        new_block.ingredient_slot = new_block.script.ingredient_slot
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def update_slots(self):
        """Keep backward compatibility slots in sync with script"""
        self.input_slot = self.script.input_slot
        self.ingredient_slot = self.script.ingredient_slot

    def handle_item_transfer(self, slot_name, item_data):
        """Handle item transfers to/from the enhancer block"""
        if not self.script:
            return False
            
        if slot_name not in ['input_slot', 'ingredient_slot']:
            return False
            
        slot = getattr(self.script, slot_name)
        if item_data:
            slot.update(item_data)
        else:
            slot.clear()
        self.update_slots()
        return True

    def to_dict(self):
        """Serialize enhancer state"""
        data = super().to_dict()
        if self.script:
            data.update({
                'enhancer_data': self.script.to_dict()
            })
        return data

    def from_dict(self, data, item_registry):
        """Deserialize enhancer state"""
        super().from_dict(data, item_registry)
        if self.script and 'enhancer_data' in data:
            self.script.from_dict(data['enhancer_data'], item_registry)
            # Update compatibility references
            self.input_slot = self.script.input_slot
            self.ingredient_slot = self.script.ingredient_slot

class FarmingBlock(Block):
    def __init__(self, id, name, texture_coords, solid=True, color=(139, 69, 19), 
                 drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        super().__init__(id, name, solid, color, texture_coords, drop_item, 
                        animation_frames, frame_duration, tint, entity_type)
        self.has_inventory = True
        self.can_interact = True
        
        # Import and create script right away
        from scripts.blocks.farming_block import BlockScript
        self.script = BlockScript(self)
        # For backward compatibility
        self.plantable = self.script.plantable
        self.plant = self.script.plant
        self.tilled = self.script.tilled

    def create_instance(self):
        """Create a new instance of the farming block"""
        print("[FARM DEBUG] Creating new FarmingBlock instance")
        new_block = FarmingBlock(
            self.id, 
            self.name, 
            self.texture_coords,
            solid=self.solid,
            color=self.color
        )
        # Ensure script is initialized properly
        from scripts.blocks.farming_block import BlockScript
        new_block.script = BlockScript(new_block)
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        
        print(f"[FARM DEBUG] Created block: texture={new_block.texture_coords}, tilled={new_block.script.tilled}")
        return new_block
        
    def till(self):
        """Delegate to script"""
        if self.script:
            print(f"[FARM DEBUG] Till requested on block: {self.texture_coords}")
            result = self.script.till()
            # Force texture update
            if hasattr(self, '_cached_base'):
                del self._cached_base
            print(f"[FARM DEBUG] Till result: {result}, New texture: {self.texture_coords}")
            return result
        return False

    def plant_seed(self, seed_item):
        """Delegate to script"""
        result = self.script.plant_seed(seed_item)
        self.plant = self.script.plant  # Update proxy property
        return result

    def update(self, dt):
        """Delegate to script"""
        if self.script:
            result = self.script.update(dt)
            # Update proxy properties
            self.plant = self.script.plant
            self.tilled = self.script.tilled
            return result
        return False

    def harvest(self, tool=None):
        """Delegate to script"""
        result = self.script.harvest(tool)
        self.plant = self.script.plant  # Update proxy property
        return result

    def to_dict(self):
        """Serialize farming block state"""
        data = super().to_dict()
        if self.script:
            data.update({
                'farming_data': self.script.to_dict()
            })
        return data

    def from_dict(self, data, item_registry):
        """Deserialize farming block state"""
        super().from_dict(data, item_registry)
        if self.script and 'farming_data' in data:
            self.script.from_dict(data['farming_data'], item_registry)
            # Update proxy properties
            self.plant = self.script.plant
            self.tilled = self.script.tilled
            self.plantable = self.script.plantable

# Update WOOD block creation with burn time
WOOD = Block(19, "Wood", True, (139, 69, 19), (1, 13))
WOOD.burn_time = 1000  # Add burn time before registration

# Update ensure_block_item_variants function
def ensure_block_item_variants():
    """Make sure all blocks have item variants and are registered"""
    from item import Item, ITEM_REGISTRY, FUEL_ITEMS
    for block in REGISTRY.blocks.values():
        if not hasattr(block, 'item_variant') or block.item_variant is None:
            # First check FUEL_ITEMS, then block's burn_time
            burn_time = FUEL_ITEMS.get(block.id, 0)
            if (burn_time == 0 and hasattr(block, 'burn_time')):
                burn_time = block.burn_time
            
            print(f"Creating item for {block.name}, burn_time={burn_time}")
            
            item_variant = Item(
                id=block.id,
                name=block.name,
                texture_coords=block.texture_coords,
                stack_size=64,
                is_block=True,
                burn_time=burn_time
            )
            
            # Ensure burn time is set on both item and block
            block.burn_time = burn_time
            item_variant.burn_time = burn_time
            
            item_variant.block = block
            block.item_variant = item_variant
            block.drop_item = item_variant
            
            # Register in both registries
            REGISTRY.items[str(item_variant.id)] = item_variant
            ITEM_REGISTRY[item_variant.id] = item_variant

# Create and register predefined blocks before loader initialization
AIR = Block(0, "Air", False, (0, 0, 0), None)  # Change texture_coords to None
REGISTRY.register_block(AIR)  # Register AIR block first
GRASS = Block(1, "Grass", True, (0, 255, 0), (1, 10))
DIRT = Block(2, "Dirt", True, (139, 69, 19), (8, 5))
STONE = Block(4, "Stone", True, (128, 128, 128), (19, 6))
SAND = Block(30, "Sand", True, (238, 214, 175), (18, 5))
SANDSTONE = Block(31, "Sandstone", True, (219, 211, 173), (18, 6))
SNOW_GRASS = Block(32, "Snow Grass", True, (248, 248, 248), (3, 20))
SNOW_DIRT = Block(33, "Snow Dirt", True, (225, 225, 225), (8, 5))

# Add these blocks after the existing predefined blocks but before registry
LEAVES = Block(20, "Leaves", True, (34, 139, 34), (9, 12))
LEAVESGG = Block(21, "Golden Leaves", True, (218, 165, 32), (9, 12))
SAVANNA_GRASS = Block(34, "Savanna Grass", True, (189, 188, 107), (8, 6))
SAVANNA_DIRT = Block(35, "Savanna Dirt", True, (150, 120, 60), (8, 5))
UNBREAKABLE = Block(8, "Unbreakable", True, (50, 50, 50), (4, 3))  # Add this line
WATER = Block(9, "Water", False, (64, 64, 255, 128), (3, 0), tint=(64, 64, 255, 128))  # Add water with transparency
LIGHT = Block(10, "Light", False, (255, 255, 200), (14, 9), tint=(255, 255, 200, 128))   # Add light with glow effect

# Add ore blocks
COAL_ORE = Block(16, "Coal Ore", True, (47, 44, 54), (1, 5))
IRON_ORE = Block(17, "Iron Ore", True, (136, 132, 132), (0, 12))
GOLD_ORE = Block(18, "Gold Ore", True, (204, 172, 0), (0, 10))

# Add special blocks
SPAWNER = Block(
    id=22, 
    name="Spawner", 
    solid=True, 
    color=(255, 0, 0), 
    texture_coords=(5, 5),
    entity_type="mob",
    tint=(255, 100, 100, 128)  # Add tint to make it more visible
)
STORAGE = StorageBlock(23, "Storage", (15, 1))
FURNACE = FurnaceBlock(
    id=24,
    name="Furnace", 
    texture_coords=(16, 1),
    solid=True,
    color=(100, 100, 100)
)
FARMLAND = FarmingBlock(25, "Farmland", (13, 0), True, (101, 67, 33))  # Fix this line
ENHANCER = EnhancerBlock(50, "Enhancer", (17, 1))

# Import UNBREAKABLE item
from item import UNBREAKABLE as UNBREAKABLE_ITEM

# Create unbreakable block with proper item reference
UNBREAKABLE = Block(8, "Unbreakable", True, (50, 50, 50), (4, 3))
UNBREAKABLE.item_variant = UNBREAKABLE_ITEM
UNBREAKABLE_ITEM.block = UNBREAKABLE

# Ensure it's properly registered before loader initialization
REGISTRY.register_block(UNBREAKABLE)

# Register blocks in registry
for block in [AIR, GRASS, DIRT, STONE, SAND, SANDSTONE, SNOW_GRASS, SNOW_DIRT,
              WOOD, LEAVES, LEAVESGG, SAVANNA_GRASS, SAVANNA_DIRT, UNBREAKABLE,  # Add UNBREAKABLE here
              WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE,  # Add ore blocks here
              SPAWNER, STORAGE, FURNACE, FARMLAND, ENHANCER]:  # Add special blocks here
    REGISTRY.register_block(block)

# Initialize block loader after predefined blocks are registered
BLOCK_LOADER = BlockLoader()

# Load JSON blocks
BLOCK_LOADER.load_blocks()

# Ensure all blocks have item variants
ensure_block_item_variants()

# Create backward compatibility mappings
BLOCK_TYPES = REGISTRY.blocks
BLOCK_MAP = {
    0: "AIR",
    1: "GRASS", 
    2: "DIRT",
    4: "STONE",  # Note: ID changed to 4
    8: "UNBREAKABLE",
    9: "WATER",
    10: "LIGHT",
    16: "COAL_ORE",
    17: "IRON_ORE",
    18: "GOLD_ORE",
    19: "WOOD",    # Add correct ID for WOOD
    20: "LEAVES",  # Add correct ID for LEAVES
    21: "LEAVESGG",
    22: "SPAWNER",
    23: "STORAGE",
    24: "FURNACE",
    25: "FARMLAND",
    30: "SAND",    # Update to match block definition
    31: "SANDSTONE",
    32: "SNOW_GRASS",
    33: "SNOW_DIRT",
    34: "SAVANNA_GRASS",
    35: "SAVANNA_DIRT",
    50: "ENHANCER"
}

# Update __all__ to include new blocks
__all__ = ['Block', 'StorageBlock', 'FurnaceBlock', 'EnhancerBlock', 'FarmingBlock',
           'AIR', 'GRASS', 'DIRT', 'STONE', 'SAND', 'SANDSTONE', 'SNOW_GRASS', 'SNOW_DIRT',
           'WOOD', 'LEAVES', 'LEAVESGG', 'SAVANNA_GRASS', 'SAVANNA_DIRT', 'UNBREAKABLE',  # Add UNBREAKABLE here
           'WATER', 'LIGHT', 'COAL_ORE', 'IRON_ORE', 'GOLD_ORE',  # Add ore blocks
           'SPAWNER', 'STORAGE', 'FURNACE', 'FARMLAND', 'ENHANCER',  # Add special blocks here
           'BLOCK_TYPES', 'BLOCK_LOADER', 'BLOCK_MAP']
