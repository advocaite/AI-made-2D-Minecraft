from item import Item  # added import

class Block:
    def __init__(self, id, name, solid, color, texture_coords, drop_item=None, animation_frames=None, frame_duration=0):
        self.id = id
        self.name = name
        self.solid = solid
        self.color = color
        self.texture_coords = texture_coords  # (x, y) in the texture atlas
        self.drop_item = drop_item  # Optional item drop
        self.animation_frames = animation_frames  # List of (x, y) tuples for animation frames
        self.frame_duration = frame_duration  # Duration of each frame in milliseconds
        self.item_variant = None  # New: will hold the corresponding item

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

# NEW: Create item variants for each block except AIR.
for block in (GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE, WOOD):
    # Create an Item with a high stack size (e.g., 64) and assign a reference to its block.
    item_variant = Item(block.id, block.name, block.texture_coords, stack_size=64, is_block=True)
    item_variant.block = block  # reference back to the block
    block.item_variant = item_variant

# Assign drop_item after item_variant is set.
GRASS.drop_item = GRASS.item_variant
DIRT.drop_item = DIRT.item_variant
STONE.drop_item = STONE.item_variant
COAL_ORE.drop_item = COAL_ORE.item_variant
IRON_ORE.drop_item = IRON_ORE.item_variant
GOLD_ORE.drop_item = GOLD_ORE.item_variant
WOOD.drop_item = WOOD.item_variant
WATER.drop_item = WATER.item_variant

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
    19: WOOD
}
