from noise import pnoise1, pnoise2
import random
import block as b  # import block definitions

def int_to_block(code):
    """Convert an integer code to the corresponding Block object."""
    mapping = {
        0: b.AIR,
        1: b.GRASS,
        2: b.DIRT,
        4: b.STONE,
        8: b.UNBREAKABLE,
        9: b.WATER,
        10: b.LIGHT,
        16: b.COAL_ORE,
        17: b.IRON_ORE,
        18: b.GOLD_ORE,
        19: b.WOOD
    }
    return mapping.get(code, b.AIR)

def generate_chunk(chunk_index, chunk_width, height, seed=0):
    """
    Generate a chunk with:
      - Uniform terrain,
      - Wormy caves,
      - Water that only spawns underground,
      - And ore generation in three separate passes for gold, iron, and coal.
    """
    random.seed(seed + chunk_index)
    chunk = [[0 for _ in range(chunk_width)] for _ in range(height)]
    tree_chance = 0.1  # Chance for tree generation per column
    surface_heights = [None] * chunk_width

    # --- Terrain Generation ---
    flat_scale = 50.0  # Larger scale for a smoother, uniform landscape
    octaves = 4
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        noise_val = pnoise1((global_x + seed) / flat_scale, octaves=octaves)
        # Terrain height is in the middle third of the world:
        terrain_height = int((noise_val + 1) / 2 * (height // 3)) + (height // 3)
        if terrain_height >= height - 2:
            terrain_height = height - 3
        surface_heights[local_x] = terrain_height

        # Top layer: grass (code 1)
        chunk[terrain_height][local_x] = 1
        # Dirt layer: 3-5 blocks (code 2)
        dirt_depth = random.randint(3, 5)
        for y in range(terrain_height + 1, min(terrain_height + dirt_depth, height - 1)):
            chunk[y][local_x] = 2
        # Stone: fill until the bottom (code 4)
        for y in range(terrain_height + dirt_depth, height - 1):
            chunk[y][local_x] = 4
        # Bottom row: unbreakable block (code 8)
        chunk[height - 1][local_x] = 8

    # --- Wormy Cave Generation ---
    # Lower cave_scale and reduced octaves yield longer, winding tunnels.
    cave_scale = 20.0
    cave_threshold = 0.3  # Higher threshold carves more stone into caves
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height - 1):
            if chunk[y][local_x] == 4:  # Only carve in stone areas
                noise_val = pnoise2(global_x / cave_scale, y / cave_scale,
                                     octaves=2, base=seed)
                if noise_val > cave_threshold:
                    chunk[y][local_x] = 0

    # --- Water in Caves ---
    # Water will only spawn in air blocks below the grass surface.
    water_cave_chance = 0.07
    for local_x in range(chunk_width):
        surface = surface_heights[local_x]
        # Only start placing water below the grass surface.
        for y in range(surface + 1, height):
            if chunk[y][local_x] == 0 and random.random() < water_cave_chance:
                group_length = random.randint(3, 5)
                for i in range(group_length):
                    if local_x + i < chunk_width and chunk[y][local_x + i] == 0:
                        chunk[y][local_x + i] = 9

    # --- Ore Generation Passes ---

    # Gold Pass: Increase gold occurrence by using a lower threshold.
    gold_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == 4:  # Only replace stone
                ore_noise = pnoise2(global_x * gold_scale, y * gold_scale,
                                     octaves=3, base=seed + 100)
                if ore_noise > 0.2:  # Lower threshold for more gold
                    chunk[y][local_x] = 18  # gold

    # Iron Pass: Increase iron occurrence.
    iron_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == 4:  # Only replace stone
                ore_noise = pnoise2(global_x * iron_scale, y * iron_scale,
                                     octaves=3, base=seed + 200)
                if ore_noise > 0.25:  # Adjust threshold for more iron
                    chunk[y][local_x] = 17  # iron

    # Coal Pass: Only fill remaining stone with coal.
    coal_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == 4:  # Only replace stone
                ore_noise = pnoise2(global_x * coal_scale, y * coal_scale,
                                     octaves=3, base=seed + 300)
                if ore_noise > 0.30:
                    chunk[y][local_x] = 16  # coal

    # --- Tree Generation ---
    for local_x in range(chunk_width):
        terrain_height = surface_heights[local_x]
        if terrain_height is not None and chunk[terrain_height][local_x] == 1:
            if random.random() < tree_chance:
                tree_height = random.randint(3, 5)
                can_place = True
                for h in range(1, tree_height + 1):
                    if terrain_height - h < 0 or chunk[terrain_height - h][local_x] != 0:
                        can_place = False
                        break
                if can_place:
                    for h in range(1, tree_height + 1):
                        chunk[terrain_height - h][local_x] = 19  # wood

    # --- Convert to Block Objects ---
    for y in range(height):
        for x in range(chunk_width):
            chunk[y][x] = int_to_block(chunk[y][x])
    return chunk
