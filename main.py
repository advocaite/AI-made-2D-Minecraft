import pygame
import math
import random
import time
import block as b
from worldgen import generate_chunk
import config as c
from sound_manager import SoundManager
from character import Character
from save_manager import SaveManager
from item import Item, IRON_PICKAXE, IRON_SWORD, IRON_AXE, APPLE, WATER_BOTTLE
from world_item import WorldItem
from crafting_ui import CraftingUI
from action_mode_controller import ActionModeController
from console import Console
from parallax_background import ParallaxBackground
from mob import Mob
from death_menu import DeathMenu
from storage_ui import StorageUI
from furnace_ui import FurnaceUI
from enhancer_ui import EnhancerUI
from ui.progress_bar import ProgressBar
from collections import deque
from typing import Dict, Set
import psutil
import cProfile
from async_chunk_manager import AsyncChunkManager
from texture_manager import TextureManager
import inventory
import inventory_ui

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

class ChunkManager:
    def __init__(self, chunk_width, view_distance):
        self.chunk_width = chunk_width
        self.view_distance = view_distance
        self.loaded_chunks = {}
        self.visible_chunks = set()
        self.chunk_load_queue = deque()
        self.chunk_unload_queue = deque()
        self.cached_surfaces = {}
        self.last_render_time = {}
        self.stats = {
            'chunks_rendered': 0,
            'blocks_rendered': 0,
            'render_time': 0,
            'memory_usage': 0
        }
        # Add async chunk manager
        self.async_manager = AsyncChunkManager(chunk_width, view_distance)
        self.texture_manager = TextureManager()
        self.texture_manager.load_atlas("texture_atlas.png")

    def update_visible_chunks(self, camera_x, screen_width):
        """Calculate which chunks should be visible"""
        left_chunk = (camera_x - screen_width//2) // (self.chunk_width * c.BLOCK_SIZE)
        right_chunk = (camera_x + screen_width//2) // (self.chunk_width * c.BLOCK_SIZE) + 1
        
        new_visible = set(range(left_chunk - 1, right_chunk + 1))
        
        # Queue chunks to load/unload
        for chunk_idx in new_visible - self.visible_chunks:
            self.chunk_load_queue.append(chunk_idx)
        for chunk_idx in self.visible_chunks - new_visible:
            self.chunk_unload_queue.append(chunk_idx)
        
        self.visible_chunks = new_visible

    def render_chunk(self, chunk_index, chunk, texture_atlas):
        """Optimized chunk rendering with texture manager"""
        if chunk_index in self.cached_surfaces:
            last_update = self.last_render_time.get(chunk_index, 0)
            if time.time() - last_update < 0.016:  # Reduced from 1.0 to ~1 frame at 60fps
                return self.cached_surfaces[chunk_index]

        surface = pygame.Surface((self.chunk_width * c.BLOCK_SIZE, c.WORLD_HEIGHT * c.BLOCK_SIZE), pygame.SRCALPHA)
        
        # Pre-calculate block size to avoid repeated lookups
        block_size = c.BLOCK_SIZE
        
        # Group blocks by texture coordinates and tint
        render_batches = {}
        for y, row in enumerate(chunk):
            for x, block in enumerate(row):
                if block != b.AIR:
                    # Convert texture coordinates to tuple if they're a list
                    coords = tuple(block.texture_coords) if isinstance(block.texture_coords, list) else block.texture_coords
                    # Ensure tint has alpha channel
                    tint = None
                    if hasattr(block, 'tint') and block.tint:
                        if len(block.tint) == 3:
                            tint = (*block.tint, 128)  # Add alpha if missing
                        else:
                            tint = block.tint
                    key = (coords, tint)
            for x, y in positions:
                surface.blit(texture, (x, y))

        self.cached_surfaces[chunk_index] = surface
        self.last_render_time[chunk_index] = time.time()
        return surface

    def process_queues(self, world_chunks, seed):
        """Process chunk loading/unloading queues"""
        # Request chunks asynchronously
        current_chunk = max(world_chunks.keys()) if world_chunks else 0
        self.async_manager.request_chunks(current_chunk, seed)
        
        # Get any completed chunks
        new_chunks = self.async_manager.get_ready_chunks()
        world_chunks.update(new_chunks)
        
        # Process unload queue
        while self.chunk_unload_queue and len(world_chunks) > self.view_distance * 2:
            chunk_idx = self.chunk_unload_queue.popleft()
            if chunk_idx in world_chunks:
                del world_chunks[chunk_idx]
            if chunk_idx in self.cached_surfaces:
                del self.cached_surfaces[chunk_idx]
            if chunk_idx in self.last_render_time:
                del self.last_render_time[chunk_idx]

    def update_stats(self):
        """Update performance statistics"""
        self.stats['memory_usage'] = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.stats['chunks_rendered'] = len(self.visible_chunks)

    def invalidate_chunk(self, chunk_index):
        """Mark a chunk for re-rendering with immediate update flag"""
        if chunk_index in self.cached_surfaces:
            del self.cached_surfaces[chunk_index]
            self.last_render_time[chunk_index] = 0  # Force immediate update

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

    # Add chunk manager
    chunk_manager = ChunkManager(chunk_width, view_distance)
    
    # Add performance monitoring variables
    frame_times = deque(maxlen=60)
    profiler = cProfile.Profile()
    show_debug = False

    def handle_block_break(chunk_index, local_x, world_y, block, player_inventory):
        """Handle block breaking logic"""
        selected = player_inventory.get_selected_item()
        if selected and hasattr(selected["item"], "effective_against") and selected["item"].effective_against:
            tool = selected["item"]
            if block.name in tool.effective_against:
                world_chunks[chunk_index][world_y][local_x] = b.AIR
                if block.item_variant and block != b.AIR:
                    player_inventory.add_item(block.item_variant, 1)
                return True
        else:
            world_chunks[chunk_index][world_y][local_x] = b.AIR
            if block.item_variant and block != b.AIR:
                player_inventory.add_item(block.item_variant, 1)
            return True
        return False

    def handle_block_place(chunk_index, local_x, world_y, player_inventory, player, block_size):
        """Handle block placing logic"""
        selected = player_inventory.get_selected_item()
        if not (selected and selected.get("item")):
            return False
            
        item_obj = selected["item"]
        if not (item_obj.is_block and hasattr(item_obj, "block")):
            return False
            
        block_to_place = item_obj.block
        if isinstance(block_to_place, (b.StorageBlock, b.FurnaceBlock, b.EnhancerBlock)):
            block_to_place = block_to_place.create_instance()
            
        block_world_rect = pygame.Rect(
            chunk_index * chunk_width * block_size + local_x * block_size,
            world_y * block_size,
            block_size,
            block_size
        )
        
        if (world_chunks[chunk_index][world_y][local_x] == b.AIR and 
            not player.rect.colliderect(block_world_rect)):
            world_chunks[chunk_index][world_y][local_x] = block_to_place
            player_inventory.update_quantity(selected, -1)
            return True
            
        return False

    while True:
        start_time = time.time()
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
                    if event.button in (1, 3):  # Left or right click
                        selected = player_inventory.get_selected_item()
                        if selected and selected.get("item"):
                            item_obj = selected["item"]
                            
                            # Handle farming/seeds first for both mouse buttons
                            if event.button == 3:  # Right click only for planting
                                mouse_x, mouse_y = event.pos
                                world_x = int((mouse_x + cam_offset_x) // block_size)
                                world_y = int((mouse_y + cam_offset_y) // block_size)
                                chunk_index = world_x // chunk_width
                                local_x = world_x % chunk_width
                                
                                if chunk_index in world_chunks and 0 <= world_y < world_height:
                                    block = world_chunks[chunk_index][world_y][local_x]
                                    if isinstance(block, b.FarmingBlock):
                                        # Check for hoe type
                                        if item_obj.type == "hoe" and not block.tilled:
                                            block.till()
                                            print(f"Tilled soil at ({world_x}, {world_y})")
                                            continue
                                        # Handle seed planting
                                        elif hasattr(item_obj, 'is_seed') and item_obj.is_seed:
                                            if block.tilled and hasattr(block, 'plant_seed'):
                                                if block.plant_seed(item_obj):
                                                    player_inventory.update_quantity(selected, -1)
                                                    print(f"Planted {item_obj.name}")
                                                    continue

                            # Skip attack action for seeds
                            if hasattr(item_obj, 'is_seed') and item_obj.is_seed:
                                continue

                            # Handle consumables
                            if item_obj is not None and event.button == 3 and item_obj.consumable_type is not None:
                                consumed = item_obj.consume(player)
                                if consumed:
                                    player_inventory.update_quantity(selected, -1)
                                    print(f"Consumed {item_obj.name}")
                                continue
                            # NEW: Check if it's a seed item before allowing attack action
                            if item_obj is not None and hasattr(item_obj, 'is_seed') and item_obj.is_seed:
                                continue  # Skip attack action for seed items
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
                        if isinstance(block, b.FarmingBlock):
                            if selected and selected.get("item"):
                                item = selected["item"]
                                print(f"DEBUG: Selected item type: {item.type}")
                                
                                # Check specifically for hoe type
                                if item.type == "hoe" and not block.tilled:
                                    block.till()
                                    print(f"Tilled soil at ({world_x}, {world_y})")
                                    continue
                                # Handle seed planting
                                elif hasattr(item, 'is_seed') and item.is_seed and block.tilled:
                                    if hasattr(block, 'plant_seed'):
                                        if block.plant_seed(item):
                                            player_inventory.update_quantity(selected, -1)
                                            print(f"Planted {item.name}")
                                            continue
                                    else:
                                        print("Error: FarmingBlock missing plant_seed method")

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
        
        # Clear screen first; use sky color.
        screen.fill((135, 206, 235))
        # Render parallax background after clearing the screen.
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
                if mouse_buttons[0] and world_chunks[chunk_index][world_y][local_x] != b.UNBREAKABLE and not broken_block:
                    block = world_chunks[chunk_index][world_y][local_x]
                    if block == b.AIR:
                        continue
                        
                    selected = player_inventory.get_selected_item()
                    broken = False
                    
                    # Handle tool-specific breaking
                    if selected and hasattr(selected["item"], "effective_against") and selected["item"].effective_against:
                        tool = selected["item"]
                        if block.name in tool.effective_against:
                            world_chunks[chunk_index][world_y][local_x] = b.AIR
                            if block.item_variant and block != b.AIR:
                                player_inventory.add_item(block.item_variant, 1)
                            broken = True
                    else:
                        world_chunks[chunk_index][world_y][local_x] = b.AIR
                        if block.item_variant and block != b.AIR:
                            player_inventory.add_item(block.item_variant, 1)
                        broken = True
                        
                    if broken:
                        broken_block = True
                        # Force immediate chunk update
                        chunk_manager.invalidate_chunk(chunk_index)
                        # Check if we need to update adjacent chunks (for connected textures)
                        if local_x == 0 and chunk_index - 1 in world_chunks:
                            chunk_manager.invalidate_chunk(chunk_index - 1)
                        elif local_x == chunk_width - 1 and chunk_index + 1 in world_chunks:
                            chunk_manager.invalidate_chunk(chunk_index + 1)
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
                            chunk_manager.invalidate_chunk(chunk_index)
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

        # Update visible chunks based on camera position
        chunk_manager.update_visible_chunks(player.rect.x, c.SCREEN_WIDTH)
        
        # Process chunk loading/unloading
        chunk_manager.process_queues(world_chunks, seed)

        # Clear screen and draw background
        screen.fill((135, 206, 235))
        parallax.draw(screen, cam_offset_x, dt)

        # Batch render visible chunks
        render_start = time.time()
        chunks_rendered = 0
        for chunk_index in chunk_manager.visible_chunks:
            if chunk_index in world_chunks:
                chunk_surface = chunk_manager.render_chunk(chunk_index, world_chunks[chunk_index], texture_atlas)
                screen.blit(chunk_surface, 
                          (chunk_index * chunk_width * block_size - cam_offset_x,
                           -cam_offset_y))
                chunks_rendered += 1
        chunk_manager.stats['render_time'] = time.time() - render_start

        # Render world items
        for world_item in world_items:
            world_item.draw(screen, texture_atlas)
        
        # Render player with updated camera offset.
        player.draw(screen, cam_offset_x, cam_offset_y)
        
        # Render mobs with updated camera offset.
        for mob in mobs:
            if mob.is_alive:
                mob.draw(screen, cam_offset_x, cam_offset_y)
        
        # New: Render HUD for health, hunger, and thirst.
        health_bar.draw(screen, player.health, "Health")
        hunger_bar.draw(screen, player.hunger, "Hunger")
        thirst_bar.draw(screen, player.thirst, "Thirst")
        
        # Remove old overlay code.
        
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

        # Draw hotbar UI
        player_inventory.draw_hotbar(screen, texture_atlas)

        # Draw console on top of the game if active
        console.draw(screen)

        # Check for player proximity to spawner blocks and spawn entities
        for ci, chunk in world_chunks.items():
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if block_obj == b.SPAWNER:
                        spawner_x = ci * chunk_width * block_size + x * block_size
                        spawner_y = y * block_size
                        distance = math.sqrt((player.rect.x - spawner_x) ** 2 + (player.rect.y - spawner_y) ** 2)
                        if distance < c.SPAWNER_RADIUS:
                            current_time = pygame.time.get_ticks()
                            if (ci, x, y) not in last_spawn_time or current_time - last_spawn_time[(ci, x, y)] > c.SPAWN_COOLDOWN:
                                # Try to spawn mob at a random air block around the spawner
                                found_spawn = False
                                for attempt in range(10):
                                    offset_x = random.randint(-c.SPAWNER_RADIUS, c.SPAWNER_RADIUS)
                                    offset_y = random.randint(-c.SPAWNER_RADIUS, c.SPAWNER_RADIUS)
                                    new_spawn_x = spawner_x + offset_x
                                    new_spawn_y = spawner_y + offset_y
                                    block_x = new_spawn_x // block_size
                                    block_y = new_spawn_y // block_size
                                    new_ci = block_x // chunk_width
                                    new_local_x = block_x % chunk_width
                                    if new_ci in world_chunks and block_y < world_height:
                                        if world_chunks[new_ci][block_y][new_local_x] == b.AIR:
                                            new_mob = Mob(new_spawn_x, new_spawn_y)
                                            mobs.append(new_mob)
                                            last_spawn_time[(ci, x, y)] = current_time
                                            print(f"Spawned new mob at ({new_spawn_x}, {new_spawn_y})")
                                            found_spawn = True
                                            break
                                if not found_spawn:
                                    # Fallback to spawner coordinates if no valid air block was found
                                    new_mob = Mob(spawner_x, spawner_y)
                                    mobs.append(new_mob)
                                    last_spawn_time[(ci, x, y)] = current_time
                                    print(f"Spawned fallback mob at ({spawner_x}, {spawner_y})")

        # Draw death menu last (after console)
        if death_menu and not player.is_alive:
            death_menu.draw(screen)

        # Add plant growth updates to the game loop
        for ci, chunk in world_chunks.items():
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if isinstance(block_obj, b.FarmingBlock):
                        block_obj.update(dt)

        # Draw performance stats if debug mode is on
        if show_debug:
            stats_surface = pygame.Surface((200, 100), pygame.SRCALPHA)
            stats_surface.fill((0, 0, 0, 128))
            y = 5
            for stat, value in chunk_manager.stats.items():
                text = f"{stat}: {value:.2f}"
                text_surf = font.render(text, True, (255, 255, 255))
                stats_surface.blit(text_surf, (5, y))
                y += 20
            screen.blit(stats_surface, (5, 5))

        pygame.display.flip()
        
        # Update frame time tracking
        frame_time = time.time() - start_time
        frame_times.append(frame_time)
        current_fps = 1.0 / (sum(frame_times) / len(frame_times))
        
        # Update window title with FPS
        pygame.display.set_caption(f"Reriara Clone - FPS: {int(current_fps)}")

    return "quit"
        
if __name__ == "__main__":
    main()

