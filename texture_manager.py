import pygame
import config as c
from PIL import Image
import numpy as np
from texture_packer import TexturePacker
from typing import Dict, List, Tuple

class TextureManager:
    def __init__(self):
        self.texture_cache = {}
        self.block_textures = {}
        self.item_textures = {}
        self.atlas = None
        self.atlas_surface = None
        self._load_counter = 0
        self._last_clear = 0
        self.packer = TexturePacker()
        self.texture_batches = {}

    def load_atlas(self, atlas_path):
        """Load and optimize the texture atlas"""
        # Load image with PIL first for processing
        pil_image = Image.open(atlas_path)
        if (pil_image.mode != 'RGBA'):
            pil_image = pil_image.convert('RGBA')
        
        # Extract individual textures
        block_size = c.BLOCK_SIZE
        textures = {}
        
        for y in range(pil_image.height // block_size):
            for x in range(pil_image.width // block_size):
                # Extract texture region
                region = pil_image.crop((
                    x * block_size, 
                    y * block_size, 
                    (x + 1) * block_size, 
                    (y + 1) * block_size
                ))
                
                # Skip empty textures
                if region.getextrema()[-1][1] == 0:  # Check alpha channel
                    continue
                
                # Convert to pygame surface
                texture_string = region.tobytes()
                texture_surface = pygame.image.fromstring(
                    texture_string, 
                    (block_size, block_size), 
                    'RGBA'
                )
                
                # Store texture
                textures[f"{x}_{y}"] = texture_surface
        
        # Pack textures into optimized atlas
        self.atlas_surface = self.packer.pack_textures(textures)
        self.atlas_surface = self.packer.optimize_atlas(self.atlas_surface)
        
        return self.atlas_surface

    def get_texture(self, coords, tint=None):
        """Get a cached texture with optimized batching"""
        cache_key = (coords, tuple(tint) if isinstance(tint, (list, tuple)) else tint)
        
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]
            
        # Get texture coordinates from packer
        texture_id = f"{coords[0]}_{coords[1]}"
        tex_coords = self.packer.get_texture_coords(texture_id)
        
        # Create texture from atlas region
        region = pygame.Surface((c.BLOCK_SIZE, c.BLOCK_SIZE), pygame.SRCALPHA)
        region.blit(
            self.atlas_surface,
            (0, 0),
            (
                tex_coords[0] * self.atlas_surface.get_width(),
                tex_coords[1] * self.atlas_surface.get_height(),
                c.BLOCK_SIZE,
                c.BLOCK_SIZE
            )
        )
        
        # Apply tint if needed
        if tint:
            tinted = region.copy()
            tinted.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)
            self.texture_cache[cache_key] = tinted
            return tinted
            
        self.texture_cache[cache_key] = region
        return region

    def begin_batch(self, batch_id: str):
        """Start a new rendering batch"""
        self.texture_batches[batch_id] = []

    def add_to_batch(self, batch_id: str, texture_coords: Tuple[int, int], position: Tuple[int, int], tint=None):
        """Add a texture to a batch for rendering"""
        if batch_id in self.texture_batches:
            self.texture_batches[batch_id].append((texture_coords, position, tint))

    def render_batch(self, batch_id: str, target_surface: pygame.Surface):
        """Render all textures in a batch efficiently"""
        if batch_id not in self.texture_batches:
            return
            
        # Sort by texture coords to minimize texture switches
        self.texture_batches[batch_id].sort(key=lambda x: x[0])
        
        # Render batch
        current_texture = None
        for coords, pos, tint in self.texture_batches[batch_id]:
            if current_texture != coords:
                current_texture = coords
                texture = self.get_texture(coords, tint)
            target_surface.blit(texture, pos)
        
        # Clear batch
        self.texture_batches[batch_id].clear()
