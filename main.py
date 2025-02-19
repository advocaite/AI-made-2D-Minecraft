import pygame
import math
from worldgen import generate_chunk
import random  # ensure random is imported at the top if not already
import config as c # ensure config is imported at the top if not already a
import block as b  # new import for Block definitions
from sound_manager import SoundManager  # new import
from character import Character  # new import
from save_manager import SaveManager
import inventory
import inventory_ui
from item import Item, IRON_PICKAXE, IRON_SWORD, IRON_AXE, APPLE, WATER_BOTTLE  # Fixed item names
from world_item import WorldItem  # new import for WorldItem class
from crafting_ui import CraftingUI  # new import
from action_mode_controller import ActionModeController  # new import
from console import Console  # new import
from parallax_background import ParallaxBackground  # new import for parallax backgrounds
from mob import Mob  # new import for Mob class
from death_menu import DeathMenu  # new import
from storage_ui import StorageUI  # new import
from furnace_ui import FurnaceUI  # new import
from enhancer_ui import EnhancerUI  # Add this import
from ui.progress_bar import ProgressBar  # Add this import

class World:
    def __init__(self):
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)
        print(f"Entity added to world: {entity}")

    def update(self, dt, world_info):
        for entity in self.entities:
            entity.update(dt, world_info)
            print(f"[DEBUG] Updated entity: {entity}")

    def draw(self, surface, cam_offset_x, cam_offset_y):
        for entity in self.entities:
            entity.draw(surface, cam_offset_x, cam_offset_y)
            print(f"[DEBUG] Drew entity: {entity}")

def create_light_mask(radius):
    mask = pygame.Surface((radius*2, radius*2), flags=pygame.SRCALPHA)
    for ix in range(radius*2):
        for iy in range(radius*2):
            dx = ix - radius
            dy = iy - radius
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < radius:
                alpha = int(255 * (1 - distance / radius))
                mask.set_at((ix, iy), (0, 0, 0, alpha))
    return mask

# Precompute the light mask once (radius = 100)
global_light_mask = create_light_mask(100)

def main():
    pygame.init()
    pygame.mixer.init()
    sound_manager = SoundManager()
    # Use the terrain seed from config
    save_manager = SaveManager(seed=c.SEED)
    # Compute effective volume (clamped between 0 and 100)
    master_vol = max(0, min(c.MASTER_VOLUME, 100)) / 100
    music_vol = max(0, min(c.MUSIC_VOLUME, 100)) / 100
    effective_volume = master_vol * music_vol
    # Load and play background music
    pygame.mixer.music.load("sounds/ObservingTheStar.ogg")  # change filename as needed
    pygame.mixer.music.set_volume(effective_volume)
    pygame.mixer.music.play(-1)  # loop indefinitely
    # Use config dimensions and create a fullscreen window.
    screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
    pygame.display.set_caption("Reriara Clone - Terraria-like Game")
    clock = pygame.time.Clock()
    
    block_size = c.BLOCK_SIZE
    chunk_width = c.CHUNK_WIDTH  # blocks per chunk
    world_height = c.WORLD_HEIGHT  # vertical blocks
    seed = c.SEED  # terrain seed
    view_distance = c.PLAYER_SPEED  # chunks left/right to load

    # Physics constants
    GRAVITY = c.GRAVITY
    JUMP_SPEED = c.JUMP_SPEED
    player_vy = 0

    # Use a dict to store chunks by index
    world_chunks = {}
    # New: dictionary to record water flow directions:
    # Keys: (ci, x, y), Value: -1 (flow left) or 1 (flow right)
    water_flow = {}
    
    # Basic player entity
    player = Character(100, 100)
    player_speed = 4
    camera_offset = 0
    action_mode = False  # default: movement mode

    # New flags to allow one placement or break per click:
    placed_water = False
    broken_block = False

    # Load and convert texture atlas with proper alpha
    texture_atlas = pygame.image.load("texture_atlas.png").convert_alpha()
    texture_atlas = texture_atlas.convert_alpha()  # Second convert to ensure proper alpha
    
    # Create inventory instance and link to player
    player_inventory = inventory.Inventory()
    player_inventory.set_player(player)
    player.inventory = player_inventory  # Make sure player has reference to inventory
    
    # Create ActionModeController instance.
    action_mode_controller = ActionModeController(texture_atlas, player_inventory)

    # Instantiate parallax background BEFORE creating console.
    parallax = ParallaxBackground(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
    parallax.set_weather("rain")
    
    # Create the world instance and assign it to the player
    world = World()
    player.world = world

    # Define the mobs list before creating the Console instance
    mobs = [Mob(200, 100)]

    # Create the Console instance
    console = Console(pygame.font.SysFont(None, 24), c.SCREEN_WIDTH, c.SCREEN_HEIGHT, player, player_inventory, mobs)
    # NEW: Connect console callbacks using the already created parallax instance.
    console.callbacks['setweather'] = parallax.set_weather
    console.callbacks['setday'] = lambda: world_time.__setitem__(0, 0)
    console.callbacks['setnight'] = lambda: world_time.__setitem__(0, c.DAY_DURATION)

    # Track time for animations
    animation_time = 0
    # New: world_time for day-night cycle (ms)
    world_time = [0]  # world_time[0] holds the current time in ms
    
    update_frame_count = 0  # new counter for throttling certain updates
    
    # List to store world items
    world_items = []

    # Set initial weather type (e.g., "rain", "snow", "storm", or "clear")
    parallax.set_weather("rain")  # Change weather type as desired
    # Add lightning cooldown timer (in milliseconds)
    lightning_cooldown = 5000  # initial delay before first lightning

    # NEW: Connect console setweather callback to parallax's set_weather method.
    console.callbacks['setweather'] = parallax.set_weather

    # NEW: Dictionary to track the last spawn time for each spawner block
    last_spawn_time = {}

    death_menu = None

    health_bar = ProgressBar(10, c.SCREEN_HEIGHT - 90, 200, 20, color=(255, 50, 50))
    hunger_bar = ProgressBar(10, c.SCREEN_HEIGHT - 60, 200, 20, color=(139, 69, 19))
    thirst_bar = ProgressBar(10, c.SCREEN_HEIGHT - 30, 200, 20, color=(0, 191, 255))

    # NEW: Track spawned mobs per spawner
    spawner_mobs = {}  # Key: (chunk_index, x, y), Value: list of spawned mobs

    # Add debug for spawner state tracking 
    spawner_debug = {
        'last_check': 0,
        'active_spawners': set()
    }

    # Add optimization variables
    update_counter = 0
    FARM_UPDATE_INTERVAL = 10  # Update farms every 10 frames
    chunk_updates = {}  # Track which chunks need updates

    # Add these performance optimization variables
    texture_cache = {}
    visible_chunks = {}
    MAX_TEXTURE_CACHE = 1000
    CHUNK_UPDATE_INTERVAL = 5
    frame_counter = 0

    def update_visible_chunks():
        """Calculate which chunks are actually visible on screen"""
        left_edge = cam_offset_x // (block_size * chunk_width)
        right_edge = (cam_offset_x + c.SCREEN_WIDTH) // (block_size * chunk_width) + 1
        return {i: True for i in range(left_edge, right_edge + 1)}

    while True:
        dt = clock.tick(60)  # milliseconds since last frame
        # Reset placement flags when mouse buttons are released:
        mouse_buttons = pygame.mouse.get_pressed()
        if not mouse_buttons[0] and not mouse_buttons[2]:
            placed_water = False
            broken_block = False
        animation_time += dt
        world_time[0] = (world_time[0] + dt) % c.TOTAL_CYCLE
        update_frame_count += 1

        # Compute ambient brightness (1 = full day, lower value when night)
        if world_time[0] < c.DAY_DURATION:
            # Daytime: full brightness with short dawn/dusk transitions (10% of day duration)
            if world_time[0] < 0.1 * c.DAY_DURATION:
                brightness = 0.2 + (world_time[0] / (0.1 * c.DAY_DURATION)) * 0.8
            elif world_time[0] > 0.9 * c.DAY_DURATION:
                brightness = 0.2 + ((c.DAY_DURATION - world_time[0]) / (0.1 * c.DAY_DURATION)) * 0.8
            else:
                brightness = 1.0
        else:
            # Nighttime: darker overall with brief transitions at start and end
            night_time = world_time[0] - c.DAY_DURATION
            if night_time < 0.1 * c.NIGHT_DURATION:
                brightness = 0.2 + (night_time / (0.1 * c.NIGHT_DURATION)) * 0.3
            elif night_time > 0.9 * c.NIGHT_DURATION:
                brightness = 0.2 + ((c.NIGHT_DURATION - night_time) / (0.1 * c.NIGHT_DURATION)) * 0.3
            else:
                brightness = 0.2

        # Event handling
        for event in pygame.event.get():
            # Handle death menu events first if active
            if death_menu and not player.is_alive:
                action = death_menu.handle_event(event)
                if action == "try_again":
                    # Reset player
                    player = Character(100, 100)
                    player.world = world
                    player.inventory = player_inventory
                    death_menu = None
                    continue
                elif action == "main_menu":  # Changed from "quit"
                    pygame.mixer.music.stop()  # Stop music before returning
                    return "launcher"  # Return to launcher instead of quitting

            # Pass all events to the console
            console.handle_event(event)
            # If console is active, bypass further game input handling
            if console.active:
                continue

            if event.type == pygame.QUIT:
                pygame.quit()
                return
            # Modified MOUSEBUTTONDOWN handling for movement mode attacks:
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not action_mode:
                    if event.button in (1, 3):
                        selected = player_inventory.get_selected_item()
                        if selected:
                            item_obj = selected.get("item")
                            # NEW: Safeguard check to prevent NoneType access during consumable check.
                            if item_obj is not None and event.button == 3 and item_obj.consumable_type is not None:
                                consumed = item_obj.consume(player)
                                if consumed:
                                    player_inventory.update_quantity(selected, -1)
                                    print(f"Consumed {item_obj.name}")
                                continue
                            # Existing logic if not a consumable.
                            if item_obj is not None:
                                if item_obj.is_block:
                                    print("Cannot attack with a block item.")
                                elif item_obj.is_armor:
                                    print("Armor selected. Using as shield.")
                                else:
                                    if item_obj.name == "Sword":
                                        player.start_attack()
                                    elif item_obj.name == "Axe":
                                        mx, my = event.pos
                                        world_x = int((mx + cam_offset_x) // block_size)
                                        world_y = int((my + cam_offset_y) // block_size)
                                        chunk_index = world_x // chunk_width
                                        local_x = world_x % chunk_width
                                        if chunk_index in world_chunks and 0 <= world_y < world_height:
                                            target_block = world_chunks[chunk_index][world_y][local_x]
                                            effective_list = item_obj.effective_against if item_obj.effective_against else ["Wood"]
                                            print(f"Debug: Axe effective_against: {effective_list}")
                                            print(f"Debug: Target block: {target_block.name}")
                                            if target_block == b.UNBREAKABLE:
                                                print("Cannot break unbreakable block")
                                                continue
                                            if target_block.name.lower() in [t.lower() for t in effective_list]:
                                                print("Axe hit", target_block.name, "-> breaking block.")
                                                world_chunks[chunk_index][world_y][local_x] = b.AIR
                                                if target_block.drop_item:
                                                    player_inventory.add_item(target_block.drop_item, 1)
                                                    print(f"Added {target_block.drop_item.name} to inventory.")
                                            else:
                                                print("Axe swung but", target_block.name, "is not in effective list.")
                                        player.start_attack()
                                    # NEW: Branch for Pickaxe to break stone.
                                    elif item_obj.name == "Pickaxe":
                                        mx, my = event.pos
                                        world_x = int((mx + cam_offset_x) // block_size)
                                        world_y = int((my + cam_offset_y) // block_size)
                                        chunk_index = world_x // chunk_width
                                        local_x = world_x % chunk_width
                                        if chunk_index in world_chunks and 0 <= world_y < world_height:
                                            target_block = world_chunks[chunk_index][world_y][local_x]
                                            # Use fallback effective list if empty.
                                            effective_list = item_obj.effective_against if item_obj.effective_against else ["Stone", "Dirt", "Coal Ore", "Iron Ore", "Gold Ore"]
                                            print(f"Debug: Pickaxe effective_against: {effective_list}")
                                            print(f"Debug: Target block: {target_block.name}")
                                            if target_block == b.UNBREAKABLE:
                                                print("Cannot break unbreakable block")
                                                continue
                                            if target_block.name.lower() in [t.lower() for t in effective_list]:
                                                print("Pickaxe hit", target_block.name, "-> breaking block.")
                                                world_chunks[chunk_index][world_y][local_x] = b.AIR
                                                if target_block.drop_item:
                                                    player_inventory.add_item(target_block.drop_item, 1)
                                                    print(f"Added {target_block.drop_item.name} to inventory.")
                                            else:
                                                print("Pickaxe swung but", target_block.name, "is not in effective list.")
                                        player.start_attack()
                                    else:
                                        player.start_attack()
                        else:
                            # No selected item; default attack.
                            player.start_attack()
                else:
                    # In action mode, delegate handling to ActionModeController.
                    action_mode_controller.handle_mouse_event(event, world_chunks, player, cam_offset_x, cam_offset_y, block_size, chunk_width, world_height)
                if event.button == 3 and not action_mode:  # Right click in movement mode
                    # Get block at mouse position
                    mouse_x, mouse_y = event.pos
                    world_x = int((mouse_x + cam_offset_x) // block_size)
                    world_y = int((mouse_y + cam_offset_y) // block_size)
                    chunk_index = world_x // chunk_width
                    local_x = world_x % chunk_width
                    
                    if chunk_index in world_chunks and 0 <= world_y < world_height:
                        block = world_chunks[chunk_index][world_y][local_x]
                        selected = player_inventory.get_selected_item()
                        
                        # Check if block is FarmingBlock and player has hoe selected
                        if isinstance(block, b.FarmingBlock) and selected and selected.get("item"):
                            item = selected["item"]
                            print(f"[FARM DEBUG] Right click with {item.name}")
                            print(f"[FARM DEBUG] Block state - Tilled: {block.script.tilled}, Has plant: {block.script.plant}")
                            
                            # Check for hoe
                            is_hoe = (item.type == "hoe" or 
                                     getattr(item, 'category', '') == "hoe" or 
                                     item.name.lower().endswith('hoe'))
                            
                            if is_hoe and not block.script.tilled:
                                block.till()
                                print(f"[FARM DEBUG] Tilled soil at ({world_x}, {world_y})")
                                continue
                            
                            # Handle seed planting
                            if hasattr(item, 'is_seed') and item.is_seed and block.script.tilled:
                                if block.script.plant_seed(item):
                                    print(f"[FARM DEBUG] Successfully planted {item.name}")
                                    player_inventory.update_quantity(selected, -1)
                                    continue
                            
                            # Handle harvesting fully grown plants
                            if block.script.plant and block.script.plant.is_fully_grown():
                                print(f"[FARM DEBUG] Harvesting fully grown plant")
                                drops = block.script.harvest()
                                if drops:
                                    for item, quantity in drops:
                                        player_inventory.add_item(item, quantity)
                                    print(f"[FARM DEBUG] Added harvest to inventory")
                                continue

                        # Handle other block interactions...
                        if isinstance(block, b.StorageBlock):
                            # Open storage UI
                            storage_ui = StorageUI(screen, player_inventory, block, texture_atlas)
                            storage_ui.run()
                        elif isinstance(block, b.FurnaceBlock):
                            furnace_ui = FurnaceUI(screen, player_inventory, block, texture_atlas)
                            furnace_ui.run()
                        elif isinstance(block, b.EnhancerBlock):  # Add this section
                            enhancer_ui = EnhancerUI(screen, player_inventory, texture_atlas)
                            enhancer_ui.run()
            if event.type == pygame.KEYDOWN:
                # New: Press "n" to cycle weather for testing instead of "w"
                if event.key == pygame.K_n:
                    if parallax.weather == "rain":
                        parallax.set_weather("storm")
                    elif parallax.weather == "storm":
                        parallax.set_weather("snow")
                    elif parallax.weather == "snow":
                        parallax.set_weather("clear")
                    else:
                        parallax.set_weather("rain")
                    print("Weather set to:", parallax.weather)
                if event.key == pygame.K_m:
                    action_mode = not action_mode
                    print("Action mode:", action_mode)
                elif event.key == pygame.K_ESCAPE:
                    from in_game_menu import InGameMenu
                    ingame_menu = InGameMenu(screen)
                    selection = ingame_menu.run()
                    if selection == "Quit Game":
                        pygame.quit()
                        return
                if event.key == pygame.K_SPACE:
                    center_x = int((player.rect.x + player.rect.width/2) // block_size)
                    center_y = int((player.rect.y + player.rect.height/2) // block_size)
                    ci_center, lx_center = center_x // chunk_width, center_x % chunk_width
                    if ci_center in world_chunks and world_chunks[ci_center][center_y][lx_center] == b.WATER:
                        # Water jump: half the jump height
                        player_vy = -JUMP_SPEED * 0.5
                        sound_manager.play_jump()  # play jump sound
                    else:
                        # Normal jump: only allow if grounded.
                        if player_vy == 0:
                            player_vy = -JUMP_SPEED
                            sound_manager.play_jump()  # play jump sound
                if event.key == pygame.K_o:
                    # Save current state (world + player)
                    print("Saving game state...")
                    save_manager.save_all(world_chunks, player, player_inventory)
                    print("Game state saved.")
                if event.key == pygame.K_p:
                    # Load saved world and player data
                    loaded_world, loaded_player = save_manager.load_all(b.BLOCK_MAP)
                    if loaded_world:
                        world_chunks.clear()
                        world_chunks.update(loaded_world)
                    if loaded_player:
                        pdata = loaded_player.get("player", {})
                        player.rect.x = pdata.get("x", player.rect.x)
                        player.rect.y = pdata.get("y", player.rect.y)
                        player.health = pdata.get("health", player.health)
                        player.hunger = pdata.get("hunger", player.hunger)
                        player.thirst = pdata.get("thirst", player.thirst)
                        inv = loaded_player.get("inventory", {})
                        
                        # Carefully update inventory slots
                        if "hotbar" in inv:
                            player_inventory.hotbar = inv["hotbar"]
                            # Ensure valid slots
                            for i, slot in enumerate(player_inventory.hotbar):
                                if not isinstance(slot, dict) or "item" not in slot:
                                    player_inventory.hotbar[i] = {"item": None, "quantity": 0}
                                elif slot and slot["item"] and isinstance(slot["item"], b.Block):
                                    player_inventory.hotbar[i]["item"] = slot["item"].item_variant
                        
                        if "armor" in inv:
                            player_inventory.armor = inv["armor"]
                        if "main" in inv:
                            player_inventory.main = inv["main"]
                        if "selected_hotbar_index" in inv:
                            player_inventory.selected_hotbar_index = inv["selected_hotbar_index"]

                        # Only refill if hotbar is completely empty
                        if not any(slot and slot.get("item") for slot in player_inventory.hotbar):
                            player_inventory.refill_hotbar()
                if event.key == pygame.K_i:
                    # Open full inventory UI when 'i' is pressed.
                    inv_ui = inventory_ui.InventoryUI(screen, player_inventory, texture_atlas)
                    inv_ui.run()
                if event.key == pygame.K_q:  # open Crafting UI when "q" is pressed
                    crafting_ui = CraftingUI(screen, player_inventory, texture_atlas)
                    crafting_ui.run()
                # Update hotbar selection on number key press.
                if pygame.K_1 <= event.key <= pygame.K_9:
                    slot_index = event.key - pygame.K_1
                    player_inventory.select_hotbar_slot(slot_index)
        
        # Check for death and create menu
        if player.death_triggered:
            death_menu = DeathMenu(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
            player.death_triggered = False

        # Update horizontal movement and animations (pass dt to update)
        if not action_mode:
            keys = pygame.key.get_pressed()
            player.update(keys, dt, player_inventory)
        
        # Separate collision resolution into horizontal and vertical passes:

        # Horizontal collision resolution:
        new_rect = player.rect.copy()
        for ty in range(new_rect.top // block_size, new_rect.bottom // block_size + 1):
            for tx in range(new_rect.left // block_size, new_rect.right // block_size + 1):
                ci = tx // chunk_width
                lx = tx % chunk_width
                if ci in world_chunks and ty < world_height and world_chunks[ci][ty][lx] not in (b.AIR, b.WATER):
                    block_rect = pygame.Rect(ci * chunk_width * block_size + lx * block_size,
                                              ty * block_size, block_size, block_size)
                    if new_rect.colliderect(block_rect):
                        if player.rect.x < block_rect.x:
                            new_rect.right = block_rect.left
                        else:
                            new_rect.left = block_rect.right
        player.rect.x = new_rect.x

        # Vertical collision resolution:
        new_rect = player.rect.copy()
        for ty in range(new_rect.top // block_size, new_rect.bottom // block_size + 1):
            for tx in range(new_rect.left // block_size, new_rect.right // block_size + 1):
                ci = tx // chunk_width
                lx = tx % chunk_width
                if ci in world_chunks and ty < world_height and world_chunks[ci][ty][lx] not in (b.AIR, b.WATER):
                    block_rect = pygame.Rect(ci * chunk_width * block_size + lx * block_size,
                                              ty * block_size, block_size, block_size)
                    if new_rect.colliderect(block_rect):
                        if player_vy > 0:
                            new_rect.bottom = block_rect.top
                            player_vy = 0
                        elif player_vy < 0:
                            new_rect.top = block_rect.bottom
                            player_vy = 0
        player.rect.y = new_rect.y

        # Remove duplicate vertical movement update:
        # Commented out because vertical collision resolution already adjusted player's y position.
        # player.rect.y += player_vy
        
        # Calculate current chunk index based on player.rect.x
        current_chunk = player.rect.x // (chunk_width * block_size)
        
        # Load new chunks within view_distance and unload out-of-range chunks
        for ci in range(current_chunk - view_distance, current_chunk + view_distance + 1):
            if ci not in world_chunks:
                world_chunks[ci] = generate_chunk(ci, chunk_width, world_height, seed)
        for ci in list(world_chunks.keys()):
            if ci < current_chunk - view_distance or ci > current_chunk + view_distance:
                del world_chunks[ci]
        
        # Update camera offset to follow player in all directions.
        cam_offset_x = player.rect.x - (c.SCREEN_WIDTH // 2)  # updated dynamic centering
        cam_offset_y = player.rect.y - (c.SCREEN_HEIGHT // 2)  # updated dynamic centering
        
        # 1. Background Layer
        screen.fill((135, 206, 235))
        parallax.draw(screen, cam_offset_x, dt)

        # Decrement lightning cooldown and trigger lightning when timer expires.
        lightning_cooldown -= dt
        if lightning_cooldown <= 0:
            parallax.trigger_lightning()
            # Reset cooldown for next lightning event (random interval between 5-10 seconds)
            lightning_cooldown = random.randint(5000, 10000)

        # In action mode, process mouse input for block breaking/placing (simple mapping)
        if action_mode:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = int((mouse_x + cam_offset_x) // block_size)
            world_y = int((mouse_y + cam_offset_y) // block_size)
            chunk_index = world_x // chunk_width
            local_x = world_x % chunk_width
            local_y = world_y % world_height
            if chunk_index in world_chunks and 0 <= world_y < world_height:
                block_screen_x = chunk_index * chunk_width * block_size - cam_offset_x + local_x * block_size
                block_rect = pygame.Rect(block_screen_x, world_y * block_size - cam_offset_y, block_size, block_size)
                # Draw semi-transparent highlight over the block under mouse
                highlight = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
                highlight.fill((255, 255, 255, 100))
                screen.blit(highlight, block_rect.topleft)
                # Process mouse clicks: 
                mouse_buttons = pygame.mouse.get_pressed()
                # Left click: break block (one per click)
                if mouse_buttons[0] and not broken_block:
                    # Get original block and do all checks first
                    original_block = world_chunks[chunk_index][world_y][local_x]
                    can_break = False

                    print(f"\n[BLOCK BREAK DEBUG] Attempting to break block:")
                    print(f"Block type: {original_block.__class__.__name__}")
                    print(f"Block ID: {original_block.id}")
                    print(f"Block name: {original_block.name}")
                    print(f"Is AIR?: {original_block == b.AIR}")
                    print(f"Is UNBREAKABLE?: {original_block == b.UNBREAKABLE or original_block.id == b.UNBREAKABLE.id}")

                    # Check if block is unbreakable first
                    if (original_block == b.AIR or 
                        original_block == b.UNBREAKABLE or 
                        original_block.id == b.UNBREAKABLE.id or 
                        original_block.name == "Unbreakable"):
                        print("[BLOCK BREAK DEBUG] Cannot break AIR or UNBREAKABLE block")
                        broken_block = True
                        continue

                    # Check tool effectiveness
                    selected = player_inventory.get_selected_item()
                    if selected and hasattr(selected["item"], "effective_against") and selected["item"].effective_against:
                        tool = selected["item"]
                        if original_block.name in tool.effective_against:
                            print(f"Tool {tool.name} can break {original_block.name}")
                            can_break = True
                    else:
                        # Can break without tools if not unbreakable or air
                        can_break = True

                    # Only if we can break the block, do the actual breaking
                    if can_break:
                        if hasattr(original_block, 'item_variant') and original_block.item_variant and original_block.item_variant.name != "Unbreakable" or original_block.name != "Air":
                            # Add item to inventory first
                            player_inventory.add_item(original_block.item_variant, 1)
                            print(f"Breaking block: {original_block.name}")
                            # Only after everything is confirmed OK, set to AIR
                            world_chunks[chunk_index][world_y][local_x] = b.AIR
                            broken_block = True

                # Right click: process placement in action mode
                if mouse_buttons[2] and not placed_water:  # Right click
                    selected = player_inventory.get_selected_item()
                    if selected and selected.get("item"):
                        item_obj = selected["item"]
                        print(f"Selected item: {item_obj.name} (is_block: {item_obj.is_block})")
                        
                        if item_obj.is_block and hasattr(item_obj, "block"):
                            block_to_place = item_obj.block
                            if isinstance(block_to_place, (b.StorageBlock, b.FurnaceBlock, b.EnhancerBlock)):
                                block_to_place = block_to_place.create_instance()
                            
                            print(f"Attempting to place block: {block_to_place.name}")
                            block_world_rect = pygame.Rect(world_x * block_size, world_y * block_size, block_size, block_size)
                            print(f"Attempting to place block: {block_to_place.name} at ({world_x}, {world_y})")  # Debugging
                            if world_chunks[chunk_index][world_y][local_x] == b.AIR and not player.rect.colliderect(block_world_rect):
                                # Check if we're placing a storage or furnace block and create a new instance
                                if isinstance(block_to_place, (b.StorageBlock, b.FurnaceBlock)):
                                    block_to_place = block_to_place.create_instance()
                                
                                world_chunks[chunk_index][world_y][local_x] = block_to_place
                                placed_water = True
                                print(f"Block placed: {block_to_place.name} at ({world_x}, {world_y})")
                                player_inventory.update_quantity(selected, -1)
                            else:
                                print(f"Cannot place block: {block_to_place.name} at ({world_x}, {world_y}) - Blocked or colliding")
                        else:
                            print(f"Cannot place non-block item: {item_obj.name}")
        # Apply gravity and update vertical position
        player.rect.y += player_vy
        # Check both bottom-left and bottom-right corners for water
        foot_left_x = player.rect.x + 2
        foot_right_x = player.rect.x + player.rect.width - 2
        foot_y = player.rect.y + player.rect.height
        tile_left_x, tile_y = foot_left_x // block_size, foot_y // block_size
        tile_right_x = foot_right_x // block_size
        ci_left, lx_left = tile_left_x // chunk_width, tile_left_x % chunk_width
        ci_right, lx_right = tile_right_x // chunk_width, tile_right_x % chunk_width

        in_water = False
        if ci_left in world_chunks and tile_y < world_height and world_chunks[ci_left][tile_y][lx_left] == b.WATER:
            in_water = True
        elif ci_right in world_chunks and tile_y < world_height and world_chunks[ci_right][tile_y][lx_right] == b.WATER:
            in_water = True

        if in_water:
            player_vy += GRAVITY * 0.5
        else:
            player_vy += GRAVITY

        # New: If shift is pressed and player's feet are on water, force a slow sink.
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            foot_x = player.rect.x + player.rect.width // 2
            foot_y = player.rect.y + player.rect.height + 1
            tile_x = foot_x // block_size
            tile_y = foot_y // block_size
            ci = tile_x // chunk_width
            lx = tile_x % chunk_width
            if ci in world_chunks and world_chunks[ci][tile_y][lx] == b.WATER:
                # Override any current upward velocity to let the player sink slowly.
                if player_vy < 0.2:
                    player_vy = 0.2

        # Build world_info dictionary for collisions.
        world_info = {
            "world_chunks": world_chunks,
            "chunk_width": chunk_width,
            "block_size": block_size,
            "world_height": world_height,
            "dropped_items": []  # Initialize dropped_items list
        }
        # Update player; pass world_info and mobs for optimized attack collision detection.
        keys = pygame.key.get_pressed()
        player.update(keys, dt, in_water, world_info, mobs, player_inventory)
        
        # Update mobs; pass world_info and player (not inventory) for collision detection.
        for mob in mobs:
            mob.update(dt, world_info, player)  # Changed from player_inventory to player

        # Handle item drops from dead mobs and add them to the player's inventory.
        for mob in mobs:
            if mob.await_respawn:
                dropped_items = mob.drop_loot(world_info, player_inventory)
                for item in dropped_items:
                    player_inventory.add_item(item)
                mobs.remove(mob)

        # Head collision detection (for upward jumps)
        if player_vy < 0:
            head_x = player.rect.x + player.rect.width // 2
            head_y = player.rect.y  # top of player
            tile_x = head_x // block_size
            tile_y = head_y // block_size
            ci = tile_x // chunk_width
            lx = tile_x % chunk_width
            # Ignore water blocks (b.WATER)
            if ci in world_chunks and tile_y >= 0 and world_chunks[ci][tile_y][lx] not in (b.AIR, b.WATER):
                player.rect.y = (tile_y + 1) * block_size  # push player down
                player_vy = 0

        # Ground collision detection (for feet)
        foot_x = player.rect.x + player.rect.width // 2
        foot_y = player.rect.y + player.rect.height
        tile_x = foot_x // block_size
        tile_y = foot_y // block_size
        ci = tile_x // chunk_width
        lx = tile_x % chunk_width
        if ci in world_chunks and tile_y < world_height and world_chunks[ci][tile_y][lx] not in (b.AIR, b.WATER) and player_vy >= 0:
            player.rect.y = tile_y * block_size - player.rect.height
            player_vy = 0
            player.on_ground = True  # mark as grounded
        else:
            player.on_ground = False

        # Water simulation update:
        for ci in list(world_chunks.keys()):
            distance_from_player = abs(current_chunk - ci)
            if distance_from_player < 2 or update_frame_count % 15 == 0:
                chunk = world_chunks[ci]
                # First pass: Check for downward flow
                for y in range(world_height - 2, -1, -1):
                    for x in range(chunk_width - 1, -1, -1):
                        if chunk[y][x] == b.WATER:
                            # Check directly below first
                            if y + 1 < world_height and chunk[y + 1][x] == b.AIR:
                                chunk[y + 1][x] = b.WATER
                                chunk[y][x] = b.AIR
                                continue
                            
                            # Check diagonal down-left and down-right
                            for dx in [-1, 1]:
                                new_x = x + dx
                                new_ci = ci
                                
                                # Handle chunk boundaries
                                if new_x >= chunk_width:
                                    new_ci = ci + 1
                                    new_x = 0
                                elif new_x < 0:
                                    new_ci = ci - 1
                                    new_x = chunk_width - 1

                                if new_ci in world_chunks:
                                    if y + 1 < world_height and world_chunks[new_ci][y + 1][new_x] == b.AIR:
                                        world_chunks[new_ci][y + 1][new_x] = b.WATER
                                        chunk[y][x] = b.AIR
                                        break

                # Second pass: Handle horizontal flow
                for y in range(world_height - 1, -1, -1):
                    for x in range(chunk_width - 1, -1, -1):
                        if chunk[y][x] == b.WATER:
                            # Only spread horizontally if we can't go down
                            if y + 1 >= world_height or (chunk[y + 1][x] != b.AIR and chunk[y + 1][x] != b.WATER):
                                # Try to spread horizontally
                                for dx in [-1, 1]:
                                    new_x = x + dx
                                    new_ci = ci
                                    
                                    # Handle chunk boundaries
                                    if new_x >= chunk_width:
                                        new_ci = ci + 1
                                        new_x = 0
                                    elif new_x < 0:
                                        new_ci = ci - 1
                                        new_x = chunk_width - 1

                                    if new_ci in world_chunks and world_chunks[new_ci][y][new_x] == b.AIR:
                                        # Only spread if there's support below
                                        if y + 1 >= world_height or world_chunks[new_ci][y + 1][new_x] != b.AIR:
                                            world_chunks[new_ci][y][new_x] = b.WATER
                                            # Don't remove source block for horizontal spread

        # Update world items: pass world_info for collision detection.
        for world_item in world_items:
            world_item.update(dt, world_info)

        # Optimized farm updates - FIXED
        update_counter += 1
        if update_counter >= FARM_UPDATE_INTERVAL:
            update_counter = 0
            
            # Only update chunks near player
            visible_chunks = []
            for ci in range(current_chunk - view_distance, current_chunk + view_distance + 1):
                if ci in world_chunks:
                    visible_chunks.append(ci)
                    
            # Update farming blocks in visible chunks
            for ci in visible_chunks:
                chunk = world_chunks[ci]
                chunk_changed = False
                
                for y in range(len(chunk)):
                    for x in range(len(chunk[y])):
                        block = chunk[y][x]
                        if isinstance(block, b.FarmingBlock) and block.script and block.script.plant:
                            if block.update(dt):
                                chunk_changed = True
                                print(f"[FARM DEBUG] Updated block at ({ci}, {x}, {y})")
                
                if chunk_changed:
                    chunk_updates[ci] = True

        # Update visible chunks periodically
        frame_counter += 1
        if frame_counter >= CHUNK_UPDATE_INTERVAL:
            visible_chunks = update_visible_chunks()
            frame_counter = 0

        # 2. World Rendering - Optimized
        for ci in world_chunks:
            if ci not in visible_chunks:
                continue
                
            chunk = world_chunks[ci]
            chunk_x_offset = ci * chunk_width * block_size - cam_offset_x
            
            # Skip if chunk is completely off screen
            if (chunk_x_offset + (chunk_width * block_size) < 0 or 
                chunk_x_offset > c.SCREEN_WIDTH):
                continue

            # Only render blocks within vertical screen bounds
            start_y = max(0, (cam_offset_y - block_size) // block_size)
            end_y = min(world_height, (cam_offset_y + c.SCREEN_HEIGHT + block_size) // block_size)

            for y in range(start_y, end_y):
                for x in range(chunk_width):
                    block = chunk[y][x]
                    if block == b.AIR:
                        continue

                    # Use texture caching
                    cache_key = (block.id, block.texture_coords)
                    if cache_key not in texture_cache:
                        texture = block.get_texture(texture_atlas)
                        if len(texture_cache) >= MAX_TEXTURE_CACHE:
                            texture_cache.pop(next(iter(texture_cache)))
                        texture_cache[cache_key] = texture
                    
                    texture = texture_cache[cache_key]
                    if texture:
                        screen.blit(texture, (
                            chunk_x_offset + x * block_size,
                            y * block_size - cam_offset_y
                        ))

        # 3. Entities Layer
        for world_item in world_items:
            world_item.draw(screen, texture_atlas)
        
        for mob in mobs:
            if mob.is_alive:
                mob.draw(screen, cam_offset_x, cam_offset_y)
        
        player.draw(screen, cam_offset_x, cam_offset_y)

        # 4. Lighting Layer
        # New: Optimized Lightmap rendering
        lightmap = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), flags=pygame.SRCALPHA)
        ambient_darkness = int((1 - brightness) * 250)
        lightmap.fill((0, 0, 0, ambient_darkness))
        # Existing light sources (e.g., for LIGHT blocks)
        for ci, chunk in world_chunks.items():
            chunk_x_offset = ci * chunk_width * block_size - cam_offset_x
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if block_obj == b.LIGHT:
                        screen_x = int(chunk_x_offset + x * block_size + block_size/2) - 100
                        screen_y = int(y * block_size - cam_offset_y + block_size/2) - 100
                        lightmap.blit(global_light_mask, (screen_x, screen_y), special_flags=pygame.BLEND_RGBA_SUB)
        # Merge lightning effects into the same lightmap.
        lightning_effect = parallax.get_light_effect(dt)
        lightmap.blit(lightning_effect, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        # Blit the final lightmap over the scene.
        screen.blit(lightmap, (0, 0))

        # 5. UI Layer - KEEP ON TOP
        health_bar.draw(screen, player.health, "Health")
        hunger_bar.draw(screen, player.hunger, "Hunger")
        thirst_bar.draw(screen, player.thirst, "Thirst")
        player_inventory.draw_hotbar(screen, texture_atlas)

        # 6. Debug Layer - KEEP ON TOP
        # Player coordinate debug text at top left
        font = pygame.font.SysFont(None, 24)  # reusing font instance

        current_chunk = player.rect.x // (chunk_width * block_size)
        player_coord = f"Player: X: {player.rect.x}, Y: {player.rect.y}, Z: {current_chunk}"
        coord_surface = font.render(player_coord, True, (255,165,0))  # changed to orange
        coord_rect = coord_surface.get_rect(topleft=(5, 5))
        screen.blit(coord_surface, coord_rect)
        
        # Debug text rendering at top-right corner
        font = pygame.font.SysFont(None, 24)
        mode_text = "Mode: Action" if action_mode else "Mode: Movement"
        debug_lines = [mode_text]
        if action_mode:
            # If action mode, add block coordinates info (now in X, Y, Z).
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = (mouse_x + cam_offset_x) // block_size
            world_y = (mouse_y + cam_offset_y) // block_size
            chunk_index = world_x // chunk_width
            debug_lines.append(f"X: {world_x}")
            debug_lines.append(f"Y: {world_y}")
            debug_lines.append(f"Z: {chunk_index}")
        y_offset = 5
        for line in debug_lines:
            text_surface = font.render(line, True, (255,165,0))  # changed to orange
            text_rect = text_surface.get_rect(topright=(screen.get_width() - 5, y_offset))
            screen.blit(text_surface, text_rect)
            y_offset += text_rect.height + 2

        # Add FPS debug display at top middle.
        fps = int(clock.get_fps())
        fps_text = f"FPS: {fps}"
        fps_surface = pygame.font.SysFont(None, 24).render(fps_text, True, (255, 255, 0))
        fps_rect = fps_surface.get_rect(center=(c.SCREEN_WIDTH//2, 10))
        screen.blit(fps_surface, fps_rect)

        # 7. Console/Menu Layer - KEEP ON TOP
        console.draw(screen)
        if death_menu and not player.is_alive:
            death_menu.draw(screen)

        # Update spawner debug stats every 5 seconds
        current_time = pygame.time.get_ticks()
        if current_time - spawner_debug['last_check'] > 5000:
            spawner_debug['last_check'] = current_time
            #print("\n[SPAWNER DEBUG] Status:")
            #print(f"Active spawners: {len(spawner_debug['active_spawners'])}")
            #print(f"Total mobs: {len(mobs)}")
            #print(f"Spawner locations: {list(spawner_debug['active_spawners'])}\n")

        # Replace the spawner section with this improved version
        for ci, chunk in world_chunks.items():
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if isinstance(block_obj, b.Block) and block_obj.id == 22:  # Check explicitly for spawner ID
                        spawner_pos = (ci, x, y)
                        spawner_x = ci * chunk_width * block_size + x * block_size
                        spawner_y = y * block_size
                        
                        # Calculate distance to player in pixels
                        dx = player.rect.centerx - (spawner_x + block_size/2)
                        dy = player.rect.centery - (spawner_y + block_size/2)
                        distance = math.sqrt(dx*dx + dy*dy)
                        
                        #print(f"[SPAWNER] Found spawner at ({spawner_x}, {spawner_y}), distance: {distance}")
                        
                        if distance < c.SPAWNER_RADIUS:
                            spawner_debug['active_spawners'].add(spawner_pos)
                            current_time = pygame.time.get_ticks()
                            
                            # Check if we can spawn
                            if spawner_pos not in last_spawn_time:
                                last_spawn_time[spawner_pos] = 0
                                #print(f"[SPAWNER] Initializing new spawner at {spawner_pos}")
                            
                            if current_time - last_spawn_time[spawner_pos] > c.SPAWN_COOLDOWN:
                                # Count existing mobs from this spawner
                                spawner_mob_count = sum(1 for mob in mobs if hasattr(mob, 'spawner') and mob.spawner == spawner_pos)
                                #print(f"[SPAWNER] Current mob count for spawner: {spawner_mob_count}")
                                
                                if spawner_mob_count < c.MAX_MOBS_PER_SPAWNER:
                                    #print(f"[SPAWNER] Attempting spawn near ({spawner_x}, {spawner_y})")
                                    # Try to spawn around the spawner
                                    for _ in range(10):  # Try 10 times to find valid spot
                                        offset_x = random.randint(-50, 50)
                                        offset_y = random.randint(-50, 50)
                                        spawn_x = spawner_x + offset_x
                                        spawn_y = spawner_y + offset_y
                                        
                                        # Convert to block coordinates
                                        block_x = spawn_x // block_size
                                        block_y = spawn_y // block_size
                                        chunk_i = block_x // chunk_width
                                        local_x = block_x % chunk_width
                                        
                                        # Verify spawn location
                                        if (chunk_i in world_chunks and 
                                            0 <= block_y < world_height - 1 and
                                            world_chunks[chunk_i][block_y][local_x] == b.AIR and
                                            world_chunks[chunk_i][block_y + 1][local_x] != b.AIR):  # Must have ground below
                                            
                                            new_mob = Mob(spawn_x, spawn_y)
                                            new_mob.spawner = spawner_pos  # Track which spawner created this mob
                                            mobs.append(new_mob)
                                            last_spawn_time[spawner_pos] = current_time
                                           # print(f"[SPAWNER] Successfully spawned mob at ({spawn_x}, {spawn_y})")
                                            break
                        else:
                            if spawner_pos in spawner_debug['active_spawners']:
                                spawner_debug['active_spawners'].remove(spawner_pos)
                               # print(f"[SPAWNER] Deactivated spawner at {spawner_pos} (distance: {distance})")

        # Draw death menu last (after console)
        if death_menu and not player.is_alive:
            death_menu.draw(screen)

        # Add plant growth updates to the game loop
        for ci, chunk in world_chunks.items():
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if isinstance(block_obj, b.FarmingBlock):
                        block_obj.update(dt)

        pygame.display.flip()
        
    return "quit"
        
if __name__ == "__main__":
    main()

def draw_block(block, x, y):
    # Skip rendering if it's an air block
    if block.id == 0:  # AIR block
        return
        
    texture = block.get_texture(texture_atlas)
    if texture:  # Only draw if texture exists
        screen.blit(texture, (x, y))

