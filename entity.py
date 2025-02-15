import pygame
import os
import random
import config as c
from item import Item

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

class Entity:
    def __init__(self, x, y, sprite_sheet_path, frame_width, frame_height):
        self.rect = pygame.Rect(x, y, c.BLOCK_SIZE, c.BLOCK_SIZE)
        self.speed = c.PLAYER_SPEED
        self.vy = 0
        self.on_ground = False
        self.facing = "right"
        self.health = 100
        self.is_alive = True
        self.death_triggered = False
        self.await_respawn = False
        self.paused = False

        # Animation setup
        self.animations = {
            "idle": load_animation(os.path.join(sprite_sheet_path, "Idle.png"), frame_width, frame_height),
            "run": load_animation(os.path.join(sprite_sheet_path, "Run.png"), frame_width, frame_height),
            "walk": load_animation(os.path.join(sprite_sheet_path, "Walk.png"), frame_width, frame_height),
            "jump": load_animation(os.path.join(sprite_sheet_path, "Jump.png"), frame_width, frame_height),
            "attack": load_animation(os.path.join(sprite_sheet_path, "Attack_1.png"), frame_width, frame_height),
            "dead": load_animation(os.path.join(sprite_sheet_path, "Dead.png"), frame_width, frame_height)
        }
        self.current_animation = "idle"
        self.frame_index = 0
        self.animation_timer = 0
        self.frame_duration = 100  # milliseconds per frame

        # Loot table setup
        self.loot_table = []

    def move(self, dx):
        self.rect.x += dx

    def jump(self):
        if self.on_ground:
            self.vy = -c.JUMP_SPEED
            self.on_ground = False
            self.frame_index = 0
            self.animation_timer = 0

    def apply_gravity(self):
        self.vy += c.GRAVITY
        self.rect.y += self.vy

    def update_status(self, dt):
        seconds = dt / 1000
        if self.health <= 0 and self.is_alive:
            self.is_alive = False
            self.current_animation = "dead"
            self.frame_index = 0
            self.animation_timer = 0
            self.death_triggered = True

    def update(self, dt):
        if self.paused:
            return

        self.update_status(dt)

        if not self.is_alive:
            self.animation_timer += dt
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                if self.frame_index < len(self.animations["dead"]) - 1:
                    self.frame_index += 1
                else:
                    self.await_respawn = True
            return

        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])

    def draw(self, surface, cam_offset_x, cam_offset_y):
        frame = self.animations[self.current_animation][self.frame_index]
        scale = 4
        new_width = self.rect.width * scale
        new_height = self.rect.height * scale
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        if self.facing == "left":
            scaled_frame = pygame.transform.flip(scaled_frame, True, False)
        draw_x = self.rect.x - cam_offset_x - (new_width - self.rect.width) // 2
        draw_y = self.rect.y + self.rect.height - new_height - cam_offset_y
        surface.blit(scaled_frame, (draw_x, draw_y))

    def drop_loot(self):
        dropped_items = []
        for item, chance in self.loot_table:
            if random.random() < chance:
                dropped_items.append(item)
        return dropped_items

    # Placeholder for future AI behavior
    def ai_behavior(self, player):
        pass

    # Placeholder for future pathfinding
    def pathfind(self, target_x, target_y):
        pass

    def load_animations(self, base_path, frame_width, frame_height):
        animation_types = ["idle", "walk", "run", "jump", "attack", "dead"]
        for anim_type in animation_types:
            filename = os.path.join(base_path, f"{anim_type.capitalize()}.png")
            if os.path.exists(filename):
                sheet = pygame.image.load(filename).convert_alpha()
                sheet_width, sheet_height = sheet.get_size()
                frames = []
                for y in range(0, sheet_height, frame_height):
                    for x in range(0, sheet_width, frame_width):
                        frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                        frames.append(frame)
                self.animations[anim_type.lower()] = frames
            else:
                # Create a fallback frame for missing animations
                fallback = pygame.Surface((frame_width, frame_height))
                fallback.fill((255, 0, 255))  # magenta for visibility
                self.animations[anim_type.lower()] = [fallback]

    def update(self, dt):
        if self.paused:
            return

        # Update animation
        if self.current_animation in self.animations:
            max_frames = len(self.animations[self.current_animation])
            self.animation_timer += dt
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % max_frames
        else:
            # Fallback to idle if animation doesn't exist
            self.current_animation = "idle"
            self.frame_index = 0

    def draw(self, surface, cam_offset_x, cam_offset_y):
        if not self.current_animation in self.animations:
            self.current_animation = "idle"
        if not self.animations[self.current_animation]:
            # Fallback if no frames available
            return

        # Ensure frame_index is within bounds
        max_frames = len(self.animations[self.current_animation])
        if self.frame_index >= max_frames:
            self.frame_index = 0

        frame = self.animations[self.current_animation][self.frame_index]
        
        # Scale the frame
        scale = 4
        new_width = self.rect.width * scale
        new_height = self.rect.height * scale
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        
        # Flip if facing left
        if self.facing == "left":
            scaled_frame = pygame.transform.flip(scaled_frame, True, False)
        
        # Draw centered on the entity's position
        draw_x = self.rect.x - cam_offset_x - (new_width - self.rect.width) // 2
        draw_y = self.rect.y + self.rect.height - new_height - cam_offset_y
        surface.blit(scaled_frame, (draw_x, draw_y))

    def apply_gravity(self):
        self.vy += c.GRAVITY

    def move(self, dx):
        self.rect.x += dx
