import pygame
import os
import config as c

def load_animation(filename, frame_width, frame_height):
    if not os.path.exists(filename):
        print(f"WARNING: File not found: {filename}. Using fallback frame.")
        fallback = pygame.Surface((frame_width, frame_height))
        fallback.fill((255, 0, 255))  # visible magenta color for missing asset
        return [fallback]
    sheet = pygame.image.load(filename).convert_alpha()
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for y in range(0, sheet_height, frame_height):
        for x in range(0, sheet_width, frame_width):
            frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
            frames.append(frame)
    return frames

class Character:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, c.BLOCK_SIZE, c.BLOCK_SIZE)
        self.speed = c.PLAYER_SPEED
        self.vy = 0
        self.on_ground = False
        self.facing = "right"  # new: track direction
        self.landing_timer = None  # new: for jump landing delay
        self.attacking = False      # new: track attack state
        self.attack_timer = 0       # new: timer for finishing attack
        self.attack_collided = False  # NEW flag for attack collision
        self.animation_speed = 1.0  # new: multiplier (1.0 = normal; >1 faster, <1 slower)
        self.health = 100
        self.hunger = 100
        self.thirst = 100
        self.is_alive = True
        self.death_triggered = False
        self.await_respawn = False
        self.console_active = False  # NEW: Track console state
        self.paused = False  # NEW: Track paused state
        self.inventory = None  # Add this line to store inventory reference

        # Add base stats
        self.base_stats = {
            'damage': 10,
            'defense': 5,
            'health': 100,
            'attack_speed': 1.0,
            'movement_speed': 4.0
        }
        
        # Add current stats (will include equipment bonuses)
        self.current_stats = dict(self.base_stats)
        
        # Add equipped items tracking
        self.equipped_items = []

        # Animation setup: load animations from characters/knight using 128x128 cells (added jump animation)
        base_path = os.path.join("characters", "knight")
        self.animations = {
            "idle": load_animation(os.path.join(base_path, "Idle.png"), 128, 128),
            "run": load_animation(os.path.join(base_path, "Run.png"), 128, 128),
            "walk": load_animation(os.path.join(base_path, "Walk.png"), 128, 128),
            "jump": load_animation(os.path.join(base_path, "Jump.png"), 128, 128),  # jump frames: first 3 up, next 2 falling, last landing
            "attack": load_animation(os.path.join(base_path, "Attack_1.png"), 128, 128),
            "attack_second": load_animation(os.path.join(base_path, "Attack_2.png"), 128, 128),
            "dead": load_animation(os.path.join(base_path, "Dead.png"), 128, 128)
        }
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 100  # milliseconds per frame

    def move(self, dx):
        self.rect.x += dx

    def jump(self):
        if self.on_ground:
            self.vy = -c.JUMP_SPEED
            self.on_ground = False
            # Removed jump state change.
            self.frame_index = 0
            self.animation_timer = 0

    def start_attack(self):
        if not self.attacking:
            self.attacking = True
            self.current_animation = "attack"
            self.frame_index = 0
            self.animation_timer = 0
            self.attack_timer = 200  # hold final frame for 200ms
            self.attack_collided = False  # reset collision flag

    def perform_attack_collision(self, world_info, mobs):
        block_size = world_info["block_size"]
        chunk_width = world_info["chunk_width"]
        world_height = world_info["world_height"]
        world_chunks = world_info["world_chunks"]

        attack_range = 20  # collision distance in pixels
        if self.facing == "right":
            attack_rect = pygame.Rect(self.rect.right, self.rect.top, attack_range, self.rect.height)
        else:
            attack_rect = pygame.Rect(self.rect.left - attack_range, self.rect.top, attack_range, self.rect.height)

        # Check for collisions with mobs first
        mobs_to_remove = []  # Track mobs that need to be removed
        for mob in mobs:
            if attack_rect.colliderect(mob.rect):
                if mob.is_alive:  # Only damage living mobs
                    mob.health -= 10  # Example damage value
                    print(f"Attack hit mob: {mob} - Health remaining: {mob.health}")
                    if mob.health <= 0:
                        mob.is_alive = False
                        mob.death_triggered = True
                        mob.current_animation = "dead"
                        mob.frame_index = 0
                        mob.animation_timer = 0
                        mobs_to_remove.append(mob)
                break

        # Remove dead mobs from the list
        for mob in mobs_to_remove:
            if mob in mobs:  # Check if mob is still in the list
                if self.inventory:  # Check if inventory exists
                    mob.drop_loot(world_info, self.inventory)  # Drop loot before removing
                mobs.remove(mob)
                print(f"Mob removed after death")

        # Check for block collisions
        # Calculate tile range based on attack rectangle
        tile_x_start = attack_rect.left // block_size
        tile_x_end = attack_rect.right // block_size
        tile_y_start = attack_rect.top // block_size
        tile_y_end = attack_rect.bottom // block_size

        hit_block = None
        for tile_x in range(tile_x_start, tile_x_end + 1):
            chunk_index = tile_x // chunk_width
            local_x = tile_x % chunk_width
            for tile_y in range(tile_y_start, tile_y_end + 1):
                if chunk_index in world_chunks and 0 <= tile_y < world_height:
                    block = world_chunks[chunk_index][tile_y][local_x]
                    if block.solid:
                        block_rect = pygame.Rect(chunk_index * chunk_width * block_size + local_x * block_size,
                                              tile_y * block_size, block_size, block_size)
                        if attack_rect.colliderect(block_rect):
                            hit_block = block
                            break
            if hit_block:
                break

        if hit_block:
            print(f"Attack hit block: {hit_block.name}")
        else:
            print("Attack hit: None")

    def apply_gravity(self):
        self.vy += c.GRAVITY
        self.rect.y += self.vy

    def update_status(self, dt, in_water):
        seconds = dt / 1000
        if in_water:
            self.thirst = min(100, self.thirst + seconds * 10)  # gain 1 per second in water
        else:
            self.thirst -= seconds * 0.5  # lose 0.5 per second when not in water
        self.hunger -= seconds * 0.2  # lose 0.2 per second
        if self.hunger < 0:
            self.hunger = 0
        if self.thirst < 0:
            self.thirst = 0
        if self.hunger == 0 or self.thirst == 0:
            self.health -= seconds * 5
            if self.health < 0:
                self.health = 0
        if self.health <= 0 and self.is_alive:
            self.is_alive = False
            self.current_animation = "dead"
            self.frame_index = 0
            self.animation_timer = 0
            self.death_triggered = True

    def update(self, keys, dt, in_water=False, world_info=None, mobs=None, player_inventory=None):
        # Store inventory reference when it's passed
        if player_inventory is not None:
            self.inventory = player_inventory

        # Pause character movement if paused
        if self.paused:
            return

        # Pause character movement if console is active
        if self.console_active:
            return

        # Update status (hunger, thirst, health) first.
        self.update_status(dt, in_water)

        # If dead, advance death animation and signal respawn if finished.
        if not self.is_alive:
            self.animation_timer += dt * self.animation_speed
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                if self.frame_index < len(self.animations["dead"]) - 1:
                    self.frame_index += 1
                else:
                    self.await_respawn = True
            return

        # If attacking but movement keys pressed, cancel attack for fluid motion.
        movement_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_LEFT] or keys[pygame.K_a]
        if self.attacking:
            if movement_pressed:
                self.attacking = False
                # Continue with normal updates below.
            else:
                self.animation_timer += dt * self.animation_speed
                if self.animation_timer >= self.frame_duration:
                    self.animation_timer = 0
                    if self.frame_index < len(self.animations["attack"]) - 1:
                        self.frame_index += 1
                    else:
                        # On the last frame, perform attack collision if not already done.
                        if not self.attack_collided and world_info:
                            self.perform_attack_collision(world_info, mobs)
                            self.attack_collided = True
                        self.attack_timer -= dt * self.animation_speed
                        if self.attack_timer <= 0:
                            self.attacking = False
                            new_anim = "run" if movement_pressed else "idle"
                            self.current_animation = new_anim
                            self.frame_index = 0
                # Even when attacking without cancelation, allow horizontal movement.
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.move(self.speed)
                    self.facing = "right"
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.move(-self.speed)
                    self.facing = "left"
                return

        # Normal animation update.
        moving = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move(self.speed)
            moving = True
            self.facing = "right"
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move(-self.speed)
            moving = True
            self.facing = "left"

        if not self.on_ground:
            if self.current_animation != "jump":
                self.current_animation = "jump"
                self.frame_index = 3 if self.vy > 0 else 0
                self.animation_timer = 0
            else:
                if self.vy > 0 and self.frame_index < 3:
                    self.frame_index = 3
                self.animation_timer += dt * self.animation_speed
                if self.animation_timer >= self.frame_duration:
                    self.animation_timer = 0
                    if self.frame_index < len(self.animations["jump"]) - 1:
                        self.frame_index += 1
            self.landing_timer = None
        else:
            if self.current_animation == "jump":
                if self.landing_timer is None:
                    self.landing_timer = 200
                    self.frame_index = len(self.animations["jump"]) - 1
                else:
                    self.landing_timer -= dt * self.animation_speed
                    if self.landing_timer <= 0:
                        new_anim = "run" if moving else "idle"
                        self.current_animation = new_anim
                        self.frame_index = 0
                        self.animation_timer = 0
                        self.landing_timer = None
            else:
                new_anim = "run" if moving else "idle"
                if new_anim != self.current_animation:
                    self.current_animation = new_anim
                    self.frame_index = 0
                    self.animation_timer = 0
                else:
                    self.animation_timer += dt * self.animation_speed
                    if self.animation_timer >= self.frame_duration:
                        self.animation_timer = 0
                        self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])

    def draw(self, surface, cam_offset_x, cam_offset_y):
        frame = self.animations[self.current_animation][self.frame_index]
        scale = 4
        new_width = self.rect.width * scale
        new_height = self.rect.height * scale
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        if self.facing == "left":  # flip if facing left
            scaled_frame = pygame.transform.flip(scaled_frame, True, False)
        # Center horizontally; align bottom of scaled sprite with collision rect bottom.
        draw_x = self.rect.x - cam_offset_x - (new_width - self.rect.width) // 2
        draw_y = self.rect.y + self.rect.height - new_height - cam_offset_y
        surface.blit(scaled_frame, (draw_x, draw_y))

    def update_stats(self):
        """Recalculate stats based on equipped items"""
        # Reset to base stats
        self.current_stats = dict(self.base_stats)
        
        # Add bonuses from equipped items
        for item in self.equipped_items:
            if hasattr(item, 'modifiers'):
                for stat, value in item.modifiers.items():
                    self.current_stats[stat] += value
        
        # Update derived attributes based on stats
        self.max_health = self.current_stats['health']
        self.speed = self.current_stats['movement_speed']
        
        print(f"Stats updated: {self.current_stats}")

    def equip_item(self, item):
        """Equip an item and update stats"""
        if item not in self.equipped_items:
            self.equipped_items.append(item)
            self.update_stats()
            print(f"Equipped {item.name}")

    def unequip_item(self, item):
        """Unequip an item and update stats"""
        if item in self.equipped_items:
            self.equipped_items.remove(item)
            self.update_stats()
            print(f"Unequipped {item.name}")

    def get_damage(self):
        """Get current attack damage including equipment bonuses"""
        return self.current_stats['damage']

    def get_defense(self):
        """Get current defense including equipment bonuses"""
        return self.current_stats['defense']

    def take_damage(self, amount):
        """Take damage considering defense stat"""
        # Defense reduces damage by a percentage
        defense_multiplier = 1 - (self.get_defense() / 100)
        actual_damage = max(1, amount * defense_multiplier)
        self.health -= actual_damage
        if self.health <= 0:
            self.is_alive = False
            self.death_triggered = True
        print(f"Took {actual_damage} damage (reduced from {amount} by defense)")

    def update_modifiers(self, inventory):
        """Update character stats based on equipped items"""
        # Reset to base stats first
        self.current_stats = dict(self.base_stats)
        
        # Clear equipped items list
        self.equipped_items = []
        
        # Check armor slots
        for armor_slot in inventory.armor:
            if armor_slot and armor_slot.get("item"):
                item = armor_slot["item"]
                if item not in self.equipped_items:
                    self.equipped_items.append(item)
        
        # Check selected hotbar slot for weapon/tool
        selected = inventory.get_selected_item()
        if selected and selected.get("item"):
            item = selected["item"]
            if item.type in ["weapon", "tool"] and item not in self.equipped_items:
                self.equipped_items.append(item)
        
        # Apply all modifiers from equipped items
        for item in self.equipped_items:
            if hasattr(item, "modifiers"):
                for stat, value in item.modifiers.items():
                    if stat in self.current_stats:
                        self.current_stats[stat] += value
        
        # Update derived stats
        self.speed = self.current_stats["movement_speed"]
        self.health = min(self.health, self.current_stats["health"])  # Cap health at max
        
        print(f"Updated modifiers: {self.current_stats}")
