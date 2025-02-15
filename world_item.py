import pygame
import config as c
import block as b  # to check block types

class WorldItem:
    def __init__(self, item, x, y):
        self.item = item
        self.rect = pygame.Rect(x, y, c.BLOCK_SIZE, c.BLOCK_SIZE)
        self.vx = 0
        self.vy = 0

    def update(self, dt, world_info):
        self.vy += c.GRAVITY * (dt / 16)
        new_rect = self.rect.copy()
        new_rect.y += self.vy
        block_size = world_info["block_size"]
        chunk_width = world_info["chunk_width"]
        world_height = world_info["world_height"]
        world_chunks = world_info["world_chunks"]

        # Vertical collision resolution:
        collision_detected = False
        collided_block = None
        for ty in range(new_rect.top // block_size, new_rect.bottom // block_size + 1):
            for tx in range(new_rect.left // block_size, new_rect.right // block_size + 1):
                ci = tx // chunk_width
                lx = tx % chunk_width
                if ci in world_chunks and 0 <= ty < world_height:
                    tile = world_chunks[ci][ty][lx]
                    print(f"Checking collision at ({tx}, {ty}) in chunk {ci}, local ({lx}, {ty}): {tile.name}")
                    if tile not in (b.AIR, b.WATER):
                        # Collision found: item should sit on top of this block
                        block_top = ty * block_size
                        if self.vy > 0 and new_rect.bottom > block_top:
                            new_rect.bottom = block_top
                            self.vy = 0
                            collision_detected = True
                            collided_block = tile
        self.rect = new_rect

        # Debug information
        if collision_detected:
            print(f"Item '{self.item.name}' position: ({self.rect.x}, {self.rect.y}), velocity: {self.vy}, collision: {collision_detected}, block: {collided_block.name}")
        else:
            print(f"Item '{self.item.name}' position: ({self.rect.x}, {self.rect.y}), velocity: {self.vy}, collision: {collision_detected}")

    def draw(self, surface, atlas):
        block_size = c.BLOCK_SIZE
        new_size = block_size // 2  # shrink texture size to half
        tx, ty = self.item.texture_coords
        texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
        try:
            item_img = atlas.subsurface(texture_rect)
        except Exception as e:
            print(f"Error drawing item '{self.item.name}': {e}")
            pygame.draw.rect(surface, (255, 0, 0), self.rect)  # fallback: red rectangle
            return
        item_img = pygame.transform.scale(item_img, (new_size, new_size))
        offset_x = self.rect.x + (self.rect.width - new_size) // 2
        offset_y = self.rect.y + (self.rect.height - new_size) // 2
        surface.blit(item_img, (offset_x, offset_y))
