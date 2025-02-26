import pygame
from typing import Dict, List, Tuple
import config as c

class UIBatch:
    def __init__(self):
        self.surfaces = {}  # Cache for UI surfaces
        self.text_cache = {}  # Cache for rendered text
        self.dirty = set()  # Track which elements need updating

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.batches = {}  # Dictionary of UI batches by group
        self.font_cache = {}
        self.current_frame = 0
        
    def get_font(self, size: int) -> pygame.font.Font:
        """Get cached font"""
        if size not in self.font_cache:
            self.font_cache[size] = pygame.font.SysFont(None, size)
        return self.font_cache[size]

    def create_batch(self, name: str) -> UIBatch:
        """Create a new UI batch"""
        batch = UIBatch()
        self.batches[name] = batch
        return batch

    def render_text(self, batch: UIBatch, text: str, size: int, color: Tuple[int, int, int], pos: Tuple[int, int]):
        """Render text with caching"""
        cache_key = (text, size, color)
        if cache_key not in batch.text_cache:
            font = self.get_font(size)
            batch.text_cache[cache_key] = font.render(text, True, color)
        
        surface = batch.text_cache[cache_key]
        self.screen.blit(surface, pos)

    def draw_ui_element(self, batch: UIBatch, element_id: str, surface: pygame.Surface, pos: Tuple[int, int], force_update: bool = False):
        """Draw a UI element with caching"""
        if force_update or element_id in batch.dirty:
            batch.surfaces[element_id] = surface
            batch.dirty.discard(element_id)
        
        if element_id in batch.surfaces:
            self.screen.blit(batch.surfaces[element_id], pos)

    def clear_cache(self, batch_name: str = None):
        """Clear cached surfaces"""
        if batch_name:
            if batch_name in self.batches:
                self.batches[batch_name].surfaces.clear()
                self.batches[batch_name].text_cache.clear()
        else:
            for batch in self.batches.values():
                batch.surfaces.clear()
                batch.text_cache.clear()

    def mark_dirty(self, batch_name: str, element_id: str):
        """Mark an element as needing update"""
        if batch_name in self.batches:
            self.batches[batch_name].dirty.add(element_id)

    def begin_frame(self):
        """Start a new frame"""
        self.current_frame += 1
        for batch in self.batches.values():
            batch.dirty = set()
