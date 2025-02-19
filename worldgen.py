from noise import pnoise1, pnoise2
import random
import block as b  # Keep the original import style
from tree_generator import generate_tree
from biomes import BiomeManager
from dungeon_generator import DungeonGenerator

# Add chunk caching
chunk_cache = {}
MAX_CACHED_CHUNKS = 50

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
        19: b.WOOD,
        20: b.LEAVES
    }
    return mapping.get(code, b.AIR)

def generate_chunk(chunk_index, chunk_width, height, seed=0):
    """Generate a chunk with biome-based terrain and caching"""
    # Check cache first
    cache_key = (chunk_index, seed)
    if cache_key in chunk_cache:
        return [row[:] for row in chunk_cache[cache_key]]  # Return deep copy

    biome_manager = BiomeManager(seed)
    chunk = [[0 for _ in range(chunk_width)] for _ in range(height)]
    surface_heights = [None] * chunk_width

    # Generate base terrain heights
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        
        # Get biome and its height modifier
        biome = biome_manager.get_biome(global_x)
        height_mod = biome.height_mod
        
        # Generate base terrain height
        noise_val = pnoise1((global_x + seed) / 50.0, octaves=4)
        base_height = int((noise_val + 1) / 2 * (height // 3)) + (height // 3)
        
        # Apply biome height modification
        terrain_height = int(base_height + (height_mod * 10))
        terrain_height = max(height//4, min(height-3, terrain_height))  # Clamp height
        surface_heights[local_x] = terrain_height
        
        # Place biome-specific blocks
        chunk[terrain_height][local_x] = biome.surface_block
        
        # Underground layers
        dirt_depth = random.randint(3, 5)
        for y in range(terrain_height + 1, min(terrain_height + dirt_depth, height - 1)):
            chunk[y][local_x] = biome.subsurface_block
            
        # Stone layer remains the same
        for y in range(terrain_height + dirt_depth, height - 1):
            chunk[y][local_x] = b.STONE  # Changed from b.STONE
            
        # Bottom bedrock
        chunk[height - 1][local_x] = b.UNBREAKABLE  # Changed from b.UNBREAKABLE

    # --- Wormy Cave Generation ---
    # Lower cave_scale and reduced octaves yield longer, winding tunnels.
    cave_scale = 20.0
    cave_threshold = 0.3  # Higher threshold carves more stone into caves
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height - 1):
            if chunk[y][local_x] == b.STONE:  # Only carve in stone areas
                noise_val = pnoise2(global_x / cave_scale, y / cave_scale,
                                     octaves=2, base=seed)
                if noise_val > cave_threshold:
                    chunk[y][local_x] = b.AIR  # Changed from b.AIR

    # --- Water in Caves ---
    # Water will only spawn in air blocks below the grass surface.
    water_cave_chance = 0.07
    for local_x in range(chunk_width):
        surface = surface_heights[local_x]
        # Only start placing water below the grass surface.
        for y in range(surface + 1, height):
            if chunk[y][local_x] == b.AIR and random.random() < water_cave_chance:
                group_length = random.randint(3, 5)
                for i in range(group_length):
                    if local_x + i < chunk_width and chunk[y][local_x + i] == b.AIR:
                        chunk[y][local_x + i] = b.WATER

    # --- Dungeon Generation Last ---
    if random.random() < 0.1:  # 10% chance per chunk
        print(f"\nDEBUG: Generating dungeon in chunk {chunk_index}")
        dungeon_y = random.randint(height // 3, height - 25)
        dungeon = DungeonGenerator(min_rooms=4, max_rooms=8)
        
        # Generate dungeon and apply modifications
        modified_chunks = dungeon.generate(chunk, -chunk_width, dungeon_y, chunk_index)
        
        # Apply modifications to current chunk, ensuring water is replaced
        if chunk_index in modified_chunks:
            for y in range(len(chunk)):
                for x in range(len(chunk[0])):
                    # If dungeon block is not air, replace any existing block (including water)
                    if modified_chunks[chunk_index][y][x] != b.AIR:
                        chunk[y][x] = modified_chunks[chunk_index][y][x]
                    # If dungeon block is air and current block is water, replace with air
                    elif modified_chunks[chunk_index][y][x] == b.AIR and chunk[y][x] == b.WATER:
                        chunk[y][x] = b.AIR
            print(f"DEBUG: Applied dungeon modifications to chunk {chunk_index}")

    # --- Ore Generation Passes ---

    # Gold Pass: Increase gold occurrence by using a lower threshold.
    gold_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == b.STONE:  # Only replace stone
                ore_noise = pnoise2(global_x * gold_scale, y * gold_scale,
                                     octaves=3, base=seed + 100)
                if ore_noise > 0.2:  # Lower threshold for more gold
                    chunk[y][local_x] = b.GOLD_ORE  # gold

    # Iron Pass: Increase iron occurrence.
    iron_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == b.STONE:  # Only replace stone
                ore_noise = pnoise2(global_x * iron_scale, y * iron_scale,
                                     octaves=3, base=seed + 200)
                if ore_noise > 0.25:  # Adjust threshold for more iron
                    chunk[y][local_x] = b.IRON_ORE  # iron

    # Coal Pass: Only fill remaining stone with coal.
    coal_scale = 0.05
    for local_x in range(chunk_width):
        global_x = chunk_index * chunk_width + local_x
        for y in range(height):
            if chunk[y][local_x] == b.STONE:  # Only replace stone
                ore_noise = pnoise2(global_x * coal_scale, y * coal_scale,
                                     octaves=3, base=seed + 300)
                if ore_noise > 0.30:
                    chunk[y][local_x] = b.COAL_ORE  # coal

    # Modified tree generation to use biome-specific settings
    for local_x in range(chunk_width):
        terrain_height = surface_heights[local_x]
        if terrain_height is not None:
            biome = biome_manager.get_biome(chunk_index * chunk_width + local_x)
            if random.random() < biome.tree_chance:
                if biome.tree_type == "normal":
                    generate_tree(chunk, local_x, terrain_height)
                elif biome.tree_type == "acacia":
                    generate_acacia_tree(chunk, local_x, terrain_height)

    # Convert to Block objects
    for y in range(height):
        for x in range(chunk_width):
            if isinstance(chunk[y][x], int):
                chunk[y][x] = int_to_block(chunk[y][x])

    # Cache the chunk before returning
    if len(chunk_cache) >= MAX_CACHED_CHUNKS:
        chunk_cache.pop(next(iter(chunk_cache)))
    chunk_cache[cache_key] = [row[:] for row in chunk]  # Store deep copy

    return chunk

def generate_acacia_tree(chunk, x, y):
    """Generate an acacia tree (wider canopy, different leaves)"""
    # Tree height and canopy settings
    trunk_height = random.randint(4, 6)
    canopy_width = random.randint(5, 7)
    canopy_height = 2

    # Generate trunk
    for dy in range(trunk_height):
        if y - dy >= 0 and y - dy < len(chunk):
            chunk[y - dy][x] = b.WOOD

    # Generate Y-shaped split at top
    split_height = trunk_height - 2
    if y - split_height >= 0:
        # Left branch
        chunk[y - split_height][x - 1] = b.WOOD
        # Right branch
        chunk[y - split_height][x + 1] = b.WOOD

    # Generate wide, flat canopy at top
    canopy_y = y - trunk_height
    for dy in range(canopy_height):
        for dx in range(-canopy_width//2, canopy_width//2 + 1):
            if (0 <= x + dx < len(chunk[0]) and 
                canopy_y - dy >= 0 and 
                canopy_y - dy < len(chunk)):
                # Add some randomness to canopy edges
                if dx in (-canopy_width//2, canopy_width//2):
                    if random.random() < 0.5:
                        chunk[canopy_y - dy][x + dx] = b.LEAVESGG
                else:
                    chunk[canopy_y - dy][x + dx] = b.LEAVESGG

def clear_chunk_cache():
    """Clear the chunk cache when needed"""
    chunk_cache.clear()
