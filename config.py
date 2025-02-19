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
DAY_DURATION = 180000  # 30 minutes of day
NIGHT_DURATION = 90000  # 15 minutes of night
TOTAL_CYCLE = DAY_DURATION + NIGHT_DURATION

MASTER_VOLUME = 100   # Master volume (0-100)
MUSIC_VOLUME = 100    # Music volume (0-100)

# Spawner settings
SPAWNER_RADIUS = 300    # Increased from 200 to 300 pixels for easier testing
SPAWN_COOLDOWN = 1000   # Reduced to 1 second between spawns
MAX_MOBS_PER_SPAWNER = 3  # Keep at 3 mobs per spawner

# New: Maximum number of entities per chunk
MAX_ENTITIES_PER_CHUNK = 10

# New: Spawn interval in milliseconds
SPAWN_INTERVAL = 5000  # 5 seconds

# New: AI Configuration
ENTITY_SIGHT_RANGE = 200  # How far entities can "see" in pixels
ENTITY_IDLE_SPEED = 1     # Speed when wandering
ENTITY_CHASE_SPEED = 2    # Reduced from 3 to make chase less aggressive
ENTITY_FLEE_SPEED = 4     # Speed when fleeing
ENTITY_WANDER_TIME = 2000 # Time to wander in one direction (ms)
ENTITY_REST_TIME = 1000   # Time to rest between wandering (ms)

# Mob combat settings
ENTITY_ATTACK_DAMAGE = 5  # Damage dealt to player
ENTITY_ATTACK_COOLDOWN = 1500  # Increased to 1.5 seconds between attacks
ENTITY_ATTACK_RANGE = 30  # Pixels distance for attack to connect
ENTITY_ATTACK_DURATION = 800  # Increased to 800ms for slower attack animation
ENTITY_KNOCKBACK_FORCE = 16  # Force of knockback when hit
ENTITY_KNOCKBACK_LIFT = 8  # Upward force of knockback

# Performance settings
PLANT_UPDATE_INTERVAL = 1000  # Milliseconds between plant growth updates
MAX_VISIBLE_CHUNKS = 5        # Maximum chunks to render/update at once
TEXTURE_CACHE_SIZE = 100      # Maximum number of textures to cache
FARM_CHUNK_DISTANCE = 2       # Only update farms within this many chunks of player
