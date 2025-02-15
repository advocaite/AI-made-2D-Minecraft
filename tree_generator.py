import random
import block
from block import WOOD, LEAVES, LEAVESGG

def generate_tree(world, base_x, base_y, min_height=4, max_height=7):
    # Determine tree height.
    height = random.randint(min_height, max_height)
    # Place trunk blocks using code 19 for WOOD.
    for i in range(height):
        world[base_y - i][base_x] = WOOD.id  # use WOOD id for trunk
    top_y = base_y - height
    # Improved canopy generation: generate a roughly round canopy with some randomness.
    canopy_radius = random.randint(2, 3)
    # NEW: Define available leaves variant ids and choose one for the whole tree.
    available_leaves_ids = [LEAVES.id, LEAVESGG.id]
    leaf_variant = random.choice(available_leaves_ids)
    for y_offset in range(-canopy_radius, canopy_radius + 1):
        for x_offset in range(-canopy_radius, canopy_radius + 1):
            # Using Manhattan distance for a diamond shape canopy.
            if abs(x_offset) + abs(y_offset) <= canopy_radius:
                # Add slight randomness to avoid a perfect shape.
                if random.random() > 0.2:
                    x = base_x + x_offset
                    y = top_y + y_offset
                    if 0 <= y < len(world) and 0 <= x < len(world[0]):
                        # Use the selected leaf variant for the whole canopy.
                        world[y][x] = leaf_variant
