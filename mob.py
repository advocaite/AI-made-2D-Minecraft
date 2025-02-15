import os
import pygame
import random
import math
import config as c
from entity import Entity
from item import Item, APPLE, WATER_BOTTLE  # Import example items

class AIState:
    IDLE = "idle"
    WANDER = "wander"
    CHASE = "chase"
    FLEE = "flee"

class Mob(Entity):
    def __init__(self, x, y):
        sprite_sheet_path = os.path.join("characters", "knight")
        super().__init__(x, y, sprite_sheet_path, 128, 128)
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 100  # milliseconds per frame
        self.health = 50  # Example health value for the mob

        # Define guaranteed loot table for testing
        self.loot_table = [
            (APPLE, 1.0),       # 100% chance to drop an apple
            (WATER_BOTTLE, 0.5)  # 50% chance to drop a water bottle
        ]
        print(f"Mob initialized with loot table: {self.loot_table}")

        self.state = AIState.IDLE
        self.state_timer = 0
        self.wander_direction = 0  # -1 for left, 1 for right
        self.speed = c.ENTITY_IDLE_SPEED
        self.aggressive = True  # Can be set to False for passive mobs
        self.world_info = None  # Add this line to store world_info
        self.void_death_y = c.WORLD_HEIGHT * c.BLOCK_SIZE  # Y position threshold for void death
        self.vy = 0  # Add vertical velocity
        self.on_ground = False
        self.attack_cooldown = 0
        self.attacking = False
        self.last_attack_time = 0

    def decide_state(self, player_pos, world_info):
        px, py = player_pos
        # First check if player is alive, if not return to wandering
        if not self.last_player.is_alive:  # Add this line to store player reference
            if self.state != AIState.IDLE and self.state != AIState.WANDER:
                self.state = AIState.IDLE
                self.speed = c.ENTITY_IDLE_SPEED
                self.state_timer = c.ENTITY_REST_TIME
            return

        # Calculate distance to player
        distance = math.sqrt((self.rect.centerx - px)**2 + (self.rect.centery - py)**2)
        
        # Check line of sight
        has_los = self.check_line_of_sight((px, py), world_info)

        if distance < c.ENTITY_SIGHT_RANGE and has_los:
            if self.aggressive and self.last_player.is_alive:  # Only chase if player is alive
                self.state = AIState.CHASE
                self.speed = c.ENTITY_CHASE_SPEED
            else:
                self.state = AIState.FLEE
                self.speed = c.ENTITY_FLEE_SPEED
        else:
            if self.state not in (AIState.IDLE, AIState.WANDER):
                self.state = AIState.IDLE
                self.speed = c.ENTITY_IDLE_SPEED
                self.state_timer = c.ENTITY_REST_TIME

    def check_line_of_sight(self, target_pos, world_info):
        tx, ty = target_pos
        start_x, start_y = self.rect.center
        
        # Bresenham's line algorithm to check for obstacles
        dx = abs(tx - start_x)
        dy = abs(ty - start_y)
        x, y = start_x, start_y
        sx = -1 if start_x > tx else 1
        sy = -1 if start_y > ty else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != tx:
                if self.is_solid_at((x, y), world_info):
                    return False
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != ty:
                if self.is_solid_at((x, y), world_info):
                    return False
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
                
        return True

    def is_solid_at(self, pos, world_info):
        x, y = pos
        block_size = world_info["block_size"]
        chunk_width = world_info["chunk_width"]
        world_chunks = world_info["world_chunks"]
        
        block_x = int(x // block_size)
        block_y = int(y // block_size)
        chunk_index = block_x // chunk_width
        local_x = block_x % chunk_width
        
        if chunk_index in world_chunks and 0 <= block_y < world_info["world_height"]:
            block = world_chunks[chunk_index][block_y][local_x]
            return block.solid
        return False

    def update_ai(self, dt, player_pos, world_info, player):
        self.last_player = player
        self.state_timer -= dt
        current_time = pygame.time.get_ticks()
        
        # Update state and force animation update on state change
        old_state = self.state
        self.decide_state(player_pos, world_info)
        
        # If state changed, reset attack animation
        if old_state != self.state:
            self.attacking = False
            if self.state == AIState.IDLE:
                self.current_animation = "idle"
            elif self.state == AIState.WANDER:
                self.current_animation = "walk"
        
        # Execute current state behavior
        if self.state == AIState.IDLE:
            if self.state_timer <= 0:
                self.state = AIState.WANDER
                self.state_timer = c.ENTITY_WANDER_TIME
                self.wander_direction = random.choice([-1, 1])
                self.current_animation = "walk"
                
        elif self.state == AIState.WANDER:
            if self.state_timer <= 0:
                self.state = AIState.IDLE
                self.state_timer = c.ENTITY_REST_TIME
                self.current_animation = "idle"
            else:
                direction = self.wander_direction
                self.move(direction * self.speed)
                self.current_animation = "walk"
                
        elif self.state == AIState.CHASE:
            px, py = player_pos
            distance = math.sqrt((self.rect.centerx - px)**2 + (self.rect.centery - py)**2)
            
            if distance < c.ENTITY_ATTACK_RANGE:
                self.perform_attack(player, current_time)
            else:
                direction = 1 if px > self.rect.x else -1
                self.move(direction * self.speed)
                self.current_animation = "walk"
            
        elif self.state == AIState.FLEE:
            px, py = player_pos
            direction = -1 if px > self.rect.x else 1
            self.move(direction * self.speed)
            self.current_animation = "walk"

    def update(self, dt, world_info, player):
        if not self.is_alive or self.paused:
            super().update(dt)
            return

        # Check for void death before any other updates
        if self.check_void_death():
            return

        # Store world_info for use in other methods
        self.world_info = world_info

        # Apply gravity with increased collision checks
        self.vy += c.GRAVITY
        new_y = self.rect.y + self.vy
        
        # Vertical collision check with multiple points and increased precision
        self.on_ground = False
        if self.vy > 0:  # Moving down
            # Check multiple points along the bottom
            foot_points = [
                (self.rect.left + 2, new_y + self.rect.height),
                (self.rect.centerx, new_y + self.rect.height),
                (self.rect.right - 2, new_y + self.rect.height)
            ]
            for foot_x, foot_y in foot_points:
                block_x = int(foot_x // world_info["block_size"])  # Convert to int
                block_y = int(foot_y // world_info["block_size"])  # Convert to int
                chunk_index = int(block_x // world_info["chunk_width"])  # Convert to int
                local_x = int(block_x % world_info["chunk_width"])  # Convert to int
                
                if (chunk_index in world_info["world_chunks"] and 
                    0 <= block_y < world_info["world_height"]):
                    block = world_info["world_chunks"][chunk_index][block_y][local_x]
                    if block.solid:
                        self.rect.bottom = block_y * world_info["block_size"]
                        new_y = self.rect.y
                        self.vy = 0
                        self.on_ground = True
                        break
        
        elif self.vy < 0:  # Moving up
            # Check head
            head_points = [
                (self.rect.left + 5, new_y),
                (self.rect.right - 5, new_y)
            ]
            for head_x, head_y in head_points:
                block_x = int(head_x // world_info["block_size"])  # Convert to int
                block_y = int(head_y // world_info["block_size"])  # Convert to int
                chunk_index = int(block_x // world_info["chunk_width"])  # Convert to int
                local_x = int(block_x % world_info["chunk_width"])  # Convert to int
                
                if (chunk_index in world_info["world_chunks"] and 
                    0 <= block_y < world_info["world_height"]):
                    block = world_info["world_chunks"][chunk_index][block_y][local_x]
                    if block.solid:
                        self.rect.top = (block_y + 1) * world_info["block_size"]
                        new_y = self.rect.y
                        self.vy = 0
                        break
        
        self.rect.y = new_y

        # Update AI behavior
        player_pos = (player.rect.centerx, player.rect.centery)
        self.update_ai(dt, player_pos, world_info, player)
        
        # Update animation based on state
        if self.attacking:
            self.animation_timer += dt
            if self.animation_timer >= c.ENTITY_ATTACK_DURATION / len(self.animations["attack"]):
                self.animation_timer = 0
                if self.frame_index < len(self.animations["attack"]) - 1:
                    self.frame_index += 1
                else:
                    # Reset attack state when animation completes
                    self.attacking = False
                    self.frame_index = 0
                    # Set animation based on current state
                    self.current_animation = "idle" if self.state == AIState.IDLE else "walk"
        
        # Update frame for current animation
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])

        super().update(dt)

    def should_jump(self):
        """Check if there's a block in front of the mob that requires jumping"""
        if not self.on_ground:
            return False

        # Check for obstacles at head height
        check_x = self.rect.right + 5 if self.facing == "right" else self.rect.left - 5
        head_y = self.rect.centery
        
        block_x = int(check_x // self.world_info["block_size"])
        block_y = int(head_y // self.world_info["block_size"])
        chunk_index = int(block_x // self.world_info["chunk_width"])
        local_x = int(block_x % self.world_info["chunk_width"])
        
        if (chunk_index in self.world_info["world_chunks"] and 
            0 <= block_y < self.world_info["world_height"]):
            block = self.world_info["world_chunks"][chunk_index][block_y][local_x]
            # If there's a solid block in front, check if we can jump over it
            if block.solid:
                # Check if there's space to jump (2 blocks above the obstacle)
                for y_offset in range(1, 3):
                    check_y = block_y - y_offset
                    if check_y >= 0:
                        above_block = self.world_info["world_chunks"][chunk_index][check_y][local_x]
                        if above_block.solid:
                            return False
                return True
        return False

    def jump(self):
        """Make the mob jump"""
        if self.on_ground:
            self.vy = -c.JUMP_SPEED * 0.7  # Slightly lower jump than player
            self.on_ground = False

    def move(self, dx):
        # Update facing BEFORE moving
        if dx != 0:
            self.facing = "right" if dx > 0 else "left"
            
        # Check if we need to jump
        if self.should_jump():
            self.jump()
            
        # Add horizontal collision checking
        new_x = self.rect.x + dx
        
        # Check for collisions at new position
        test_points = [
            (new_x, self.rect.y + 5),  # Left/right top
            (new_x + self.rect.width, self.rect.y + 5),  # Left/right top
            (new_x, self.rect.bottom - 5),  # Left/right bottom
            (new_x + self.rect.width, self.rect.bottom - 5)  # Left/right bottom
        ]
        
        can_move = True
        for test_x, test_y in test_points:
            block_x = int(test_x // self.world_info["block_size"])
            block_y = int(test_y // self.world_info["block_size"])
            chunk_index = int(block_x // self.world_info["chunk_width"])
            local_x = int(block_x % self.world_info["chunk_width"])
            
            if (chunk_index in self.world_info["world_chunks"] and 
                0 <= block_y < self.world_info["world_height"]):
                block = self.world_info["world_chunks"][chunk_index][block_y][local_x]
                if block.solid:
                    can_move = False
                    break
        
        if can_move:
            self.rect.x = new_x

    def check_collisions(self, world_info):
        block_size = c.BLOCK_SIZE
        chunk_width = c.CHUNK_WIDTH
        world_height = c.WORLD_HEIGHT
        world_chunks = world_info["world_chunks"]

        # Check for collisions with the ground
        tile_x_start = self.rect.left // block_size
        tile_x_end = self.rect.right // block_size
        tile_y_start = self.rect.top // block_size
        tile_y_end = self.rect.bottom // block_size

        for tile_x in range(tile_x_start, tile_x_end + 1):
            chunk_index = tile_x // chunk_width
            local_x = tile_x % chunk_width
            for tile_y in range(tile_y_start, tile_y_end + 1):
                if chunk_index in world_chunks and 0 <= tile_y < world_height:
                    block = world_chunks[chunk_index][tile_y][local_x]
                    if block.solid:
                        block_rect = pygame.Rect(chunk_index * chunk_width * block_size + local_x * block_size,
                                                 tile_y * block_size, block_size, block_size)
                        if self.rect.colliderect(block_rect):
                            if self.vy > 0:  # Falling
                                self.rect.bottom = block_rect.top
                                self.vy = 0
                                self.on_ground = True
                            elif self.vy < 0:  # Jumping
                                self.rect.top = block_rect.bottom
                                self.vy = 0
                            return
        self.on_ground = False

    def drop_loot(self, world_info, player_inventory):
        """Drop items when mob dies"""
        dropped_items = []
        if not self.is_alive and not self.await_respawn:
            print(f"Mob died, checking loot table: {self.loot_table}")
            for item, chance in self.loot_table:
                if random.random() < chance:
                    # Add directly to player inventory
                    player_inventory.add_item(item, 1)
                    dropped_items.append(item)
                    print(f"Dropped {item.name}")
            self.await_respawn = True
            print(f"Total items dropped: {len(dropped_items)}")
        return dropped_items

    def check_void_death(self):
        """Check if mob has fallen into the void and should die"""
        if self.rect.y > self.void_death_y:
            self.health = 0
            self.is_alive = False
            self.await_respawn = True
            return True
        return False

    def can_attack(self, current_time):
        return current_time - self.last_attack_time >= c.ENTITY_ATTACK_COOLDOWN

    def perform_attack(self, player, current_time):
        # Only check attack cooldown, don't prevent attack if already attacking
        if not self.can_attack(current_time):
            return

        # Don't attack dead players
        if not player.is_alive:
            return

        # Check if player is in attack range
        distance_x = abs(self.rect.centerx - player.rect.centerx)
        distance_y = abs(self.rect.centery - player.rect.centery)
        
        if distance_x < c.ENTITY_ATTACK_RANGE and distance_y < c.ENTITY_ATTACK_RANGE:
            # Start attack animation
            self.attacking = True
            self.current_animation = "attack"
            self.frame_index = 0
            self.animation_timer = 0
            self.last_attack_time = current_time
            
            # Deal damage to player immediately if they're alive
            if player.is_alive:
                player.health = max(0, player.health - c.ENTITY_ATTACK_DAMAGE)
                
                # Apply knockback
                knockback_force = c.ENTITY_KNOCKBACK_FORCE
                knockback_dir = 1 if player.rect.centerx > self.rect.centerx else -1
                player.rect.x += knockback_dir * knockback_force
                player.vy = -c.ENTITY_KNOCKBACK_LIFT
                
                print(f"Mob attacked player! Player health: {player.health}")
