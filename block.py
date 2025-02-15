from item import Item  # added import
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

# NEW: Automatically create item variants and assign drop_item for each block except AIR.
for blk in (GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE, WOOD, LEAVES, LEAVESGG, SPAWNER):
    item_variant = Item(blk.id, blk.name, blk.texture_coords, stack_size=64, is_block=True)
    item_variant.block = blk  # reference back to the block
    blk.item_variant = item_variant
    blk.drop_item = item_variant

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
    22: SPAWNER  # NEW: Spawner block added
}
