from item import Item, IRON_INGOT, GOLD_INGOT, MELTABLE_ITEMS, FUEL_ITEMS  # Add to imports at top
import pygame
import config as c

class Block:
    def __init__(self, id, name, solid, color, texture_coords, drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        self.id = id
        self.name = name
        self.solid = solid
        self.color = color
        self.texture_coords = texture_coords  # (x, y) in the texture atlas
        self.drop_item = drop_item  # Optional item drop
        self.animation_frames = animation_frames  # List of (x, y) tuples for animation frames
        self.frame_duration = frame_duration  # Duration of each frame in milliseconds
        self.tint = tint  # Tint color to modify block appearance
        self.item_variant = None  # New: will hold the corresponding item
        self.entity_type = entity_type  # New: entity type to spawn

    # NEW: Helper method to get the block texture with tint applied if set.
    def get_texture(self, atlas):
        # Cache the base image extracted from the atlas.
        if not hasattr(self, "_cached_base"):
            block_size = c.BLOCK_SIZE
            tx, ty = self.texture_coords
            texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
            self._cached_base = atlas.subsurface(texture_rect).convert_alpha()
        # If no tint is set, use the base texture.
        if not self.tint:
            return self._cached_base
        # If tinted image not yet computed, compute and cache it.
        if not hasattr(self, "_cached_texture"):
            tinted = self._cached_base.copy()
            tinted.fill(self.tint, special_flags=pygame.BLEND_RGBA_MULT)
            self._cached_texture = tinted
        return self._cached_texture

class StorageBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (139, 69, 19), texture_coords)
        self.has_inventory = True
        self.max_slots = 27
        self.inventory = [None] * self.max_slots  # Initialize inventory here

    def create_instance(self):
        new_block = StorageBlock(self.id, self.name, self.texture_coords)
        new_block.inventory = [None] * self.max_slots
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def to_dict(self):
        """Serialize block data for saving"""
        return {
            'id': self.id,
            'name': self.name,
            'inventory': [
                {'item_id': slot['item'].id, 'quantity': slot['quantity']} 
                if slot and slot.get('item') else None 
                for slot in self.inventory
            ]
        }

    def from_dict(self, data, item_registry):
        """Deserialize block data when loading"""
        self.inventory = []
        for slot_data in data['inventory']:
            if slot_data is None:
                self.inventory.append(None)
            else:
                item = item_registry.get(slot_data['item_id'])
                if item:
                    self.inventory.append({
                        'item': item,
                        'quantity': slot_data['quantity']
                    })
                else:
                    self.inventory.append(None)

class FurnaceBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (100, 100, 100), texture_coords)
        self.has_inventory = True
        self.fuel_slot = None
        self.input_slot = None
        self.output_slot = None
        self.is_burning = False
        self.burn_time_remaining = 0
        self.melt_progress = 0

    def create_instance(self):
        """Create a new instance of the furnace with its own inventory"""
        new_block = FurnaceBlock(self.id, self.name, self.texture_coords)
        # Initialize slots
        new_block.fuel_slot = None
        new_block.input_slot = None
        new_block.output_slot = None
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def can_accept_fuel(self, item):
        return item and hasattr(item, 'burn_time') and item.burn_time > 0

    def can_melt(self, item):
        return item and hasattr(item, 'melt_result')

    def update(self, dt):
        # Reset burning state if no input or fuel is present
        if not self.input_slot or not self.fuel_slot:
            self.is_burning = False
            self.melt_progress = 0
            self.burn_time_remaining = 0
            return

        # Check if we should start burning
        if not self.is_burning:
            if (self.fuel_slot.get("item") and self.input_slot.get("item")):
                fuel_item = self.fuel_slot["item"]
                input_item = self.input_slot["item"]
                
                if self.can_accept_fuel(fuel_item) and self.can_melt(input_item):
                    # Check if output slot allows for melting
                    can_output = False
                    melt_result = input_item.melt_result
                    
                    if not self.output_slot or self.output_slot.get("item") is None:
                        can_output = True
                    elif (self.output_slot["item"].id == melt_result.id and 
                          self.output_slot["quantity"] < self.output_slot["item"].stack_size):
                        can_output = True
                    
                    if can_output:
                        self.is_burning = True
                        self.burn_time_remaining = fuel_item.burn_time
                        self.fuel_slot["quantity"] -= 1
                        if self.fuel_slot["quantity"] <= 0:
                            self.fuel_slot = {"item": None, "quantity": 0}

        # Process melting if burning
        if self.is_burning and self.input_slot.get("item"):
            self.burn_time_remaining -= dt
            self.melt_progress += dt

            if self.melt_progress >= 1000:  # 1 second to melt
                input_item = self.input_slot["item"]
                melt_result = input_item.melt_result
                
                # Create or update output slot
                if not self.output_slot or self.output_slot.get("item") is None:
                    self.output_slot = {"item": melt_result, "quantity": 1}
                elif self.output_slot["quantity"] < self.output_slot["item"].stack_size:
                    self.output_slot["quantity"] += 1

                # Update input slot
                self.input_slot["quantity"] -= 1
                if self.input_slot["quantity"] <= 0:
                    self.input_slot = {"item": None, "quantity": 0}

                self.melt_progress = 0

            # Check if burning should stop
            if self.burn_time_remaining <= 0:
                self.is_burning = False
                self.melt_progress = 0

    def to_dict(self):
        """Serialize furnace data for saving"""
        return {
            'id': self.id,
            'name': self.name,
            'fuel_slot': self._slot_to_dict(self.fuel_slot),
            'input_slot': self._slot_to_dict(self.input_slot),
            'output_slot': self._slot_to_dict(self.output_slot),
            'is_burning': self.is_burning,
            'burn_time_remaining': self.burn_time_remaining,
            'melt_progress': self.melt_progress
        }

    def _slot_to_dict(self, slot):
        if slot and slot.get('item'):
            return {
                'item_id': slot['item'].id,
                'quantity': slot['quantity']
            }
        return None

    def from_dict(self, data, item_registry):
        """Deserialize furnace data when loading"""
        self.is_burning = data['is_burning']
        self.burn_time_remaining = data['burn_time_remaining']
        self.melt_progress = data['melt_progress']

        self.fuel_slot = self._dict_to_slot(data['fuel_slot'], item_registry)
        self.input_slot = self._dict_to_slot(data['input_slot'], item_registry)
        self.output_slot = self._dict_to_slot(data['output_slot'], item_registry)

    def _dict_to_slot(self, slot_data, item_registry):
        if slot_data:
            item = item_registry.get(slot_data['item_id'])
            if item:
                return {
                    'item': item,
                    'quantity': slot_data['quantity']
                }
        return None

# Define standard blocks
AIR = Block(0, "Air", False, (255, 255, 255), (0, 0))
GRASS = Block(1, "Grass", True, (34, 139, 34), (1, 10))
DIRT = Block(2, "Dirt", True, (139, 69, 19), (8, 5))
STONE = Block(4, "Stone", True, (105, 105, 105), (19, 6))
UNBREAKABLE = Block(8, "Unbreakable", True, (70, 70, 70), (4, 3))
WATER = Block(9, "Water", False, (0, 191, 255), (3, 0), animation_frames=[(3, 1), (3, 0),(2, 1), (2, 0)], frame_duration=200)
# New Light block for emitting light
LIGHT = Block(10, "Light", True, (255, 255, 200), (14, 9))
COAL_ORE = Block(16, "Coal Ore", True, (0, 0, 0), (1, 5))
IRON_ORE = Block(17, "Iron Ore", True, (220, 220, 220), (0, 12))
GOLD_ORE = Block(18, "Gold Ore", True, (255, 215, 0), (0, 10))
WOOD = Block(19, "Wood", True, (255, 215, 0), (1, 13))

# NEW: Define animated Leaves block with tint.
LEAVES = Block(
    20,
    "Leaves",
    True,
    (34, 139, 34),
    (9, 12),
    animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
    frame_duration=300,
    tint=(34, 139, 34)  # Tint color applied to leaves
)
LEAVESGG = Block(
    21,
    "Leavesgg",
    True,
    (85, 170, 47),
    (9, 12),
    animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
    frame_duration=300,
    tint=(85, 170, 47)  # Tint color applied to leaves
)

# Define the new Spawner block with entity type
SPAWNER = Block(22, "Spawner", True, (255, 0, 0), (5, 5), entity_type="mob")

# Add new STORAGE block
STORAGE = StorageBlock(23, "Storage", (15, 1))  # Adjust texture coordinates as needed

# Add new FURNACE block
FURNACE = FurnaceBlock(24, "Furnace", (16, 1))  # Adjust texture coordinates as needed

# NEW: Automatically create item variants and assign drop_item for each block except AIR.
for blk in (GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE, WOOD, LEAVES, LEAVESGG, SPAWNER, STORAGE, FURNACE):
    item_variant = Item(blk.id, blk.name, blk.texture_coords, stack_size=64, is_block=True)
    item_variant.block = blk  # reference back to the block
    blk.item_variant = item_variant
    blk.drop_item = item_variant

# Set burn times and melt results here instead of in item.py
WOOD.item_variant.burn_time = 1000  # Wood burns for 1 second
IRON_ORE.item_variant.melt_result = IRON_INGOT
GOLD_ORE.item_variant.melt_result = GOLD_INGOT

# Create coal item first
COAL_ITEM = Item(25, "Coal", (20, 7), stack_size=64, burn_time=2000)

# Update the MELTABLE_ITEMS registry
MELTABLE_ITEMS.update({
    IRON_ORE.id: IRON_INGOT,
    GOLD_ORE.id: GOLD_INGOT,
    COAL_ORE.id: COAL_ITEM  # Add coal ore melting to coal item
})

FUEL_ITEMS.update({
    WOOD.id: 1000,    # Wood burns for 1 second
    COAL_ITEM.id: 2000  # Coal burns for 2 seconds
})

# Add melt result for coal ore
COAL_ORE.item_variant.melt_result = COAL_ITEM

# Ensure SPAWNER_ITEM is defined
SPAWNER_ITEM = SPAWNER.item_variant

# NEW: Mapping from integer block codes to Block objects
BLOCK_MAP = {
    0: AIR,
    1: GRASS,
    2: DIRT,
    4: STONE,
    8: UNBREAKABLE,
    9: WATER,
    10: LIGHT,
    16: COAL_ORE,
    17: IRON_ORE,
    18: GOLD_ORE,
    19: WOOD,
    20: LEAVES,  # NEW: Leaves block added
    21: LEAVESGG,  # NEW: Leaves block added
    22: SPAWNER,  # NEW: Spawner block added
    23: STORAGE,  # NEW: Storage block added
    24: FURNACE  # NEW: Furnace block added
}
