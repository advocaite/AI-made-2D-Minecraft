SCREEN_WIDTH = 1280  # increased from 800
SCREEN_HEIGHT = 720  # increased from 600

BLOCK_SIZE = 16
CHUNK_WIDTH = 50  # blocks per chunk
WORLD_HEIGHT = 150  # vertical blocks

VIEW_DISTANCE = 2  # chunks to load left/right of current chunk

SEED = 42  # terrain seed

PLAYER_SPEED = 4
GRAVITY = 0.5
JUMP_SPEED = 10  # changed: positive jump speed constant

# New: Day and Night cycle constants in milliseconds
DAY_DURATION = 18000  # 30 minutes of day
NIGHT_DURATION = 90000  # 15 minutes of night
TOTAL_CYCLE = DAY_DURATION + NIGHT_DURATION

MASTER_VOLUME = 100   # Master volume (0-100)
MUSIC_VOLUME = 100    # Music volume (0-100)

# New: Spawner radius for spawning entities
SPAWNER_RADIUS = 100  # Radius in pixels within which entities will spawn

# New: Maximum number of entities per chunk
MAX_ENTITIES_PER_CHUNK = 10

# New: Spawn interval in milliseconds
SPAWN_INTERVAL = 5000  # 5 seconds

# New: Cooldown time between spawns in milliseconds
SPAWN_COOLDOWN = 5000  # 5 seconds
