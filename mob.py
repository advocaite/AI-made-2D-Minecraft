import os
import pygame
import random  # Add this import
import config as c
from entity import Entity
from item import Item, APPLE, WATER_BOTTLE  # Import example items

class Mob(Entity):
    def __init__(self, x, y):
        sprite_sheet_path = os.path.join("characters", "knight")
        super().__init__(x, y, sprite_sheet_path, 128, 128)
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 100  # milliseconds per frame
        self.health = 50  # Example health value for the mob

        # Define loot table with items and their drop chances (100% drop rate for testing)
        self.loot_table = [
            (APPLE, 1.0),  # 100% chance to drop an apple
            (WATER_BOTTLE, 1.0)  # 100% chance to drop a water bottle
        ]

    def update(self, dt, world_info, player_inventory):
        if not self.is_alive:
            self.current_animation = "dead"
            self.animation_timer += dt
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                if self.frame_index < len(self.animations["dead"]) - 1:
                    self.frame_index += 1
                else:
                    # Drop loot and mark for removal
                    self.drop_loot(world_info, player_inventory)
                    self.await_respawn = True
            return

        super().update(dt)
        self.apply_gravity()
        self.check_collisions(world_info)

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
        dropped_items = []
        for item, chance in self.loot_table:
            if random.random() < chance:
                # Directly add the item to the player's inventory
                player_inventory.add_item(item)
                dropped_items.append(item)
        return dropped_items
