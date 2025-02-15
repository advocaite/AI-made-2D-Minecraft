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
from item import Item  # new import for Item class
from world_item import WorldItem  # new import for WorldItem class
from crafting_ui import CraftingUI  # new import
from action_mode_controller import ActionModeController  # new import
from console import Console  # new import
from parallax_background import ParallaxBackground  # new import for parallax backgrounds

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

    # Load texture atlas
    texture_atlas = pygame.image.load("texture_atlas.png").convert()
    
    # Create inventory instance:
    player_inventory = inventory.Inventory()
    
    # Create ActionModeController instance.
    action_mode_controller = ActionModeController(texture_atlas, player_inventory)

    # Instantiate parallax background BEFORE creating console.
    parallax = ParallaxBackground(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
    parallax.set_weather("rain")
    
    # Create the Console instance
    console = Console(pygame.font.SysFont(None, 24), c.SCREEN_WIDTH, c.SCREEN_HEIGHT, player, player_inventory)
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
                        player_inventory.hotbar = inv.get("hotbar", player_inventory.hotbar)
                        player_inventory.armor = inv.get("armor", player_inventory.armor)
                        player_inventory.main = inv.get("main", player_inventory.main)
                        player_inventory.selected_hotbar_index = inv.get("selected_hotbar_index", player_inventory.selected_hotbar_index)
                        # Ensure hotbar items are Item objects
                        for slot in player_inventory.hotbar:
                            if slot and isinstance(slot["item"], b.Block):
                                slot["item"] = slot["item"].item_variant
                        # Refill hotbar if empty.
                        if not player_inventory.hotbar:
                            player_inventory.refill_hotbar()
                        print("Hotbar after loading:")
                        for idx, slot in enumerate(player_inventory.hotbar):
                            if slot and "item" in slot and slot["item"]:
                                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                            else:
                                print(f"Slot {idx}: Empty slot")
                        print("Armor after loading:")
                        for idx, slot in enumerate(player_inventory.armor):
                            if slot and "item" in slot and slot["item"]:
                                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                            else:
                                print(f"Slot {idx}: Empty slot")
                        print("Main inventory after loading:")
                        for idx, slot in enumerate(player_inventory.main):
                            if slot and "item" in slot and slot["item"]:
                                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                            else:
                                print(f"Slot {idx}: Empty slot")
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
        
        # Update horizontal movement and animations (pass dt to update)
        if not action_mode:
            keys = pygame.key.get_pressed()
            player.update(keys, dt)
        
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
                    selected = player_inventory.get_selected_item()
                    if selected and hasattr(selected["item"], "effective_against") and selected["item"].effective_against:
                        tool = selected["item"]
                        if block.name in tool.effective_against:
                            world_chunks[chunk_index][world_y][local_x] = b.AIR
                            broken_block = True
                            if block.drop_item:
                                player_inventory.add_item(block.drop_item, 1)
                            print(f"Effective break: {block.name} with {tool.name}")
                        else:
                            print(f"{tool.name} is not effective against {block.name}")
                    else:
                        world_chunks[chunk_index][world_y][local_x] = b.AIR
                        broken_block = True
                        if block.drop_item:
                            player_inventory.add_item(block.drop_item, 1)
                        print(f"Breaking block: {block.name}, drop_item: {block.drop_item}")
                # Right click: process placement in action mode
                if mouse_buttons[2] and not placed_water:
                    selected = player_inventory.get_selected_item()
                    print(f"Selected item: {selected}")  # Debugging information
                    if selected and isinstance(selected["item"], Item) and (selected["item"].is_block or selected["item"].name in ["Water Bottle", "Water"]):
                        block_to_place = selected["item"].block if selected["item"].is_block else b.WATER
                        block_world_rect = pygame.Rect(world_x * block_size, world_y * block_size, block_size, block_size)
                        print(f"Attempting to place block: {block_to_place.name} at ({world_x}, {world_y})")  # Debugging
                        if world_chunks[chunk_index][world_y][local_x] == b.AIR and not player.rect.colliderect(block_world_rect):
                            world_chunks[chunk_index][world_y][local_x] = block_to_place
                            placed_water = True
                            print(f"Block placed: {block_to_place.name} at ({world_x}, {world_y})")
                            player_inventory.update_quantity(selected, -1)
                        else:
                            print(f"Cannot place block: {block_to_place.name} at ({world_x}, {world_y}) - Blocked or colliding")
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
            "world_height": world_height
        }
        # Update player; pass world_info for optimized attack collision detection.
        keys = pygame.key.get_pressed()
        player.update(keys, dt, in_water, world_info)
        
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
                for y in range(world_height - 2, -1, -1):
                    for x in range(chunk_width):
                        if chunk[y][x] == b.WATER:
                            key = (ci, x, y)
                            def get_cell(ci_target, x_target, y_target):
                                if ci_target in world_chunks and 0 <= x_target < chunk_width and 0 <= y_target < world_height:
                                    return world_chunks[ci_target][y_target][x_target]
                                return None
                            def set_cell(ci_target, x_target, y_target, value):
                                if ci_target in world_chunks and 0 <= x_target < chunk_width and 0 <= y_target < world_height:
                                    world_chunks[ci_target][y_target][x_target] = value
                            # Move water downward if possible
                            if y + 1 < world_height and get_cell(ci, x, y + 1) == b.AIR:
                                set_cell(ci, x, y + 1, b.WATER)
                                set_cell(ci, x, y, b.AIR)
                                water_flow.pop(key, None)
                                continue
                            # Lateral movement based on water_flow
                            current_dir = water_flow.get(key, 0)
                            if current_dir:
                                if current_dir == -1:
                                    new_ci, new_x = (ci - 1, chunk_width - 1) if x == 0 else (ci, x - 1)
                                else:
                                    new_ci, new_x = (ci + 1, 0) if x == chunk_width - 1 else (ci, x + 1)
                                if get_cell(new_ci, new_x, y) == b.AIR:
                                    set_cell(new_ci, new_x, y, b.WATER)
                                    set_cell(ci, x, y, b.AIR)
                                    water_flow.pop(key, None)
                                    water_flow[(new_ci, new_x, y)] = current_dir
                                else:
                                    water_flow.pop(key, None)
                                continue
                            else:
                                choices = []
                                new_ci, new_x = (ci - 1, chunk_width - 1) if x == 0 else (ci, x - 1)
                                if get_cell(new_ci, new_x, y) == b.AIR:
                                    choices.append((-1, new_ci, new_x))
                                new_ci, new_x = (ci + 1, 0) if x == chunk_width - 1 else (ci, x + 1)
                                if get_cell(new_ci, new_x, y) == b.AIR:
                                    choices.append((1, new_ci, new_x))
                                if choices:
                                    d, target_ci, target_x = random.choice(choices)
                                    set_cell(target_ci, target_x, y, b.WATER)
                                    set_cell(ci, x, y, b.AIR)
                                    water_flow[(target_ci, target_x, y)] = d
        
        # Update world items: pass world_info for collision detection.
        for world_item in world_items:
            world_item.update(dt, world_info)

        # Render each loaded chunk using the texture atlas.
        for ci, chunk in world_chunks.items():
            chunk_x_offset = ci * chunk_width * block_size - cam_offset_x
            # Horizontal bounds
            if chunk_x_offset < -c.SCREEN_WIDTH * 2 or chunk_x_offset > c.SCREEN_WIDTH * 2:
                continue
            for y, row in enumerate(chunk):
                for x, block_obj in enumerate(row):
                    if block_obj != b.AIR:
                        texture = block_obj.get_texture(texture_atlas)
                        screen.blit(texture, (chunk_x_offset + x * block_size, y * block_size - cam_offset_y))
        
        # Render world items
        for world_item in world_items:
            world_item.draw(screen, texture_atlas)
        
        # Render player with updated camera offset.
        player.draw(screen, cam_offset_x, cam_offset_y)
        
        # New: Render HUD for health, hunger, and thirst.
        hud_font = pygame.font.SysFont(None, 24)
        stats_text = f"Health: {int(player.health)}  Hunger: {int(player.hunger)}  Thirst: {int(player.thirst)}"
        stats_surface = hud_font.render(stats_text, True, (255, 255, 255))
        screen.blit(stats_surface, (5, c.SCREEN_HEIGHT - 30))
        
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

        pygame.display.flip()
        
if __name__ == "__main__":
    main()
