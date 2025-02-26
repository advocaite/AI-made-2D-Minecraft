import pygame
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple
import config as c

class TexturePacker:
    def __init__(self):
        self.atlas_size = (1024, 1024)  # Power of 2 for better GPU performance
        self.padding = 1  # Pixels of padding between textures
        self.texture_map = {}  # Maps texture IDs to atlas coordinates
        self.next_position = [0, 0]
        self.current_row_height = 0
        self.atlas_surface = None

    def pack_textures(self, textures: Dict[str, pygame.Surface]) -> pygame.Surface:
        """Pack multiple textures into a single atlas"""
        # Create atlas surface
        atlas = pygame.Surface(self.atlas_size, pygame.SRCALPHA)
        
        for texture_id, texture in textures.items():
            # Get texture dimensions
            width, height = texture.get_size()
            
            # Check if we need to move to next row
            if self.next_position[0] + width > self.atlas_size[0]:
                self.next_position[0] = 0
                self.next_position[1] += self.current_row_height + self.padding
                self.current_row_height = 0
            
            # Update row height if needed
            self.current_row_height = max(self.current_row_height, height)
            
            # Store texture position
            position = tuple(self.next_position)
            self.texture_map[texture_id] = (
                position[0] / self.atlas_size[0],
                position[1] / self.atlas_size[1],
                width / self.atlas_size[0],
                height / self.atlas_size[1]
            )
            
            # Blit texture to atlas
            atlas.blit(texture, position)
            
            # Update next position
            self.next_position[0] += width + self.padding

        self.atlas_surface = atlas
        return atlas

    def get_texture_coords(self, texture_id: str) -> Tuple[float, float, float, float]:
        """Get normalized texture coordinates (u1, v1, u2, v2)"""
        return self.texture_map.get(texture_id, (0, 0, 1, 1))

    def optimize_atlas(self, atlas_surface: pygame.Surface) -> pygame.Surface:
        """Optimize the atlas for GPU usage"""
        # Convert to PIL Image for processing
        atlas_string = pygame.image.tostring(atlas_surface, 'RGBA')
        atlas_pil = Image.frombytes('RGBA', atlas_surface.get_size(), atlas_string)
        
        # Optimize image
        atlas_pil = atlas_pil.quantize(colors=256, method=2).convert('RGBA')
        
        # Convert back to Pygame surface
        optimized_string = atlas_pil.tobytes()
        optimized_surface = pygame.image.fromstring(
            optimized_string, 
            atlas_surface.get_size(), 
            'RGBA'
        )
        
        return optimized_surface
