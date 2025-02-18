import importlib.util
from pathlib import Path
from item import Item, IRON_INGOT, GOLD_INGOT, COAL, MELTABLE_ITEMS, FUEL_ITEMS
import pygame
import config as c

class Block:
    def __init__(self, id, name, solid, color, texture_coords, drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        self.id = id
        self.name = name
        self.solid = solid
        self.color = color
        self.texture_coords = texture_coords
        self.drop_item = drop_item
        self.animation_frames = animation_frames
        self.frame_duration = frame_duration
        self.tint = tint
        self.item_variant = None
        self.entity_type = entity_type
        self.script = None
        self.type = "basic"

        # Pre-create surfaces for performance
        if tint:
            self._tint_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
            self._tint_surface.fill((*tint, 128))
        
        # Initialize texture cache for animations
        if animation_frames:
            self._texture_cache = {}
            self._anim_tick = 0

    def create_base_instance(self):
        return type(self)(
            id=self.id,
            name=self.name,
            solid=self.solid,
            color=self.color,
            texture_coords=self.texture_coords,
            animation_frames=self.animation_frames,
            frame_duration=self.frame_duration,
            tint=self.tint,
            entity_type=self.entity_type
        )

    def create_instance(self):
        new_block = self.create_base_instance()
        if self.script:
            new_block.script = self.script.__class__(new_block)
        return new_block

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'solid': self.solid,
            'color': list(self.color),
            'texture_coords': list(self.texture_coords)
        }
        
        if self.script:
            data['script_data'] = self.script.to_dict()
            
        if self.animation_frames:
            data['animation_frames'] = [list(frame) for frame in self.animation_frames]
            data['frame_duration'] = self.frame_duration
        if self.tint:
            data['tint'] = list(self.tint)
        if self.entity_type:
            data['entity_type'] = self.entity_type
        if self.drop_item:
            data['drop_item'] = self.drop_item
            
        return data

    def from_dict(self, data, item_registry=None):
        """Load block state from dictionary"""
        for key, value in data.items():
            if key == 'script_data' and self.script and hasattr(self.script, 'from_dict'):
                self.script.from_dict(value, item_registry)
            elif hasattr(self, key):
                setattr(self, key, value)
        return self

    def get_texture(self, atlas):
        """Get block texture with optimized caching"""
        # Cache the texture coordinates
        if self.animation_frames:
            if not hasattr(self, '_anim_tick'):
                self._anim_tick = 0
                self._texture_cache = {}
            
            self._anim_tick += 1
            frame_index = (self._anim_tick // self.frame_duration) % len(self.animation_frames)
            tx, ty = self.animation_frames[frame_index]
            
            # Check cache for this frame
            cache_key = (tx, ty)
            if cache_key in self._texture_cache:
                return self._texture_cache[cache_key]
        else:
            tx, ty = self.texture_coords
            
            # Use static texture cache
            if hasattr(self, '_static_texture'):
                return self._static_texture

        # Get base texture
        block_size = 16
        texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
        base_texture = atlas.subsurface(texture_rect).convert_alpha()
        
        # Apply tint if needed
        if self.tint:
            if not hasattr(self, '_tint_surface'):
                self._tint_surface = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
                self._tint_surface.fill((*self.tint, 128))
            
            tinted = base_texture.copy()
            tinted.blit(self._tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            texture = tinted
        else:
            texture = base_texture

        # Cache the result
        if self.animation_frames:
            self._texture_cache[cache_key] = texture
            # Limit cache size
            if len(self._texture_cache) > len(self.animation_frames):
                self._texture_cache.clear()
        else:
            self._static_texture = texture

        return texture

class StorageBlock(Block):
    def __init__(self, id, name, solid, color, texture_coords, **kwargs):
        super().__init__(id, name, solid, color, texture_coords, **kwargs)
        self.type = "storage"
        self.has_inventory = True
        self.max_slots = 27
        self.inventory = [None] * self.max_slots
        
        # Load storage script
        script_path = Path(__file__).parent / 'scripts' / 'blocks' / 'storage_block.py'
        if script_path.exists():
            spec = importlib.util.spec_from_file_location("storage_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.script = module.BlockScript(self)

class FurnaceBlock(Block):
    def __init__(self, id, name, solid, color, texture_coords, **kwargs):
        super().__init__(id, name, solid, color, texture_coords, **kwargs)
        self.type = "furnace"
        self.has_inventory = True
        self.fuel_slot = None
        self.input_slot = None
        self.output_slot = None
        self.is_burning = False
        self.burn_time_remaining = 0
        self.melt_progress = 0
        
        # Load furnace script
        script_path = Path(__file__).parent / 'scripts' / 'blocks' / 'furnace_block.py'
        if script_path.exists():
            spec = importlib.util.spec_from_file_location("furnace_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.script = module.BlockScript(self)

class EnhancerBlock(Block):
    def __init__(self, id, name, solid, color, texture_coords, **kwargs):
        super().__init__(id, name, solid, color, texture_coords, **kwargs)
        self.type = "enhancer"
        self.has_inventory = True
        self.input_slot = None
        self.ingredient_slot = None
        
        # Load enhancer script
        script_path = Path(__file__).parent / 'scripts' / 'blocks' / 'enhancer_block.py'
        if script_path.exists():
            spec = importlib.util.spec_from_file_location("enhancer_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.script = module.BlockScript(self)

class FarmingBlock(Block):
    def __init__(self, id, name, solid, color, texture_coords, **kwargs):
        super().__init__(id, name, solid, color, texture_coords, **kwargs)
        self.type = "farming"
        self.plantable = True
        self.plant = None
        self.tilled = False
        self.untilled_texture = texture_coords
        self.tilled_texture = (13, 1)
        
        # Load farming script
        script_path = Path(__file__).parent / 'scripts' / 'blocks' / 'farming_block.py'
        if script_path.exists():
            spec = importlib.util.spec_from_file_location("farming_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.script = module.BlockScript(self)

# Keep original block definitions for backwards compatibility
# These will eventually be replaced by the JSON system
AIR = Block(0, "Air", False, (255, 255, 255), (0, 0))
GRASS = Block(1, "Grass", True, (34, 139, 34), (1, 10))
DIRT = Block(2, "Dirt", True, (139, 69, 19), (8, 5))
STONE = Block(4, "Stone", True, (105, 105, 105), (19, 6))
UNBREAKABLE = Block(8, "Unbreakable", True, (70, 70, 70), (4, 3))
WATER = Block(9, "Water", False, (0, 191, 255), (3, 0), animation_frames=[(3, 1), (3, 0),(2, 1), (2, 0)], frame_duration=200)
LIGHT = Block(10, "Light", True, (255, 255, 200), (14, 9))
COAL_ORE = Block(16, "Coal Ore", True, (0, 0, 0), (1, 5))
IRON_ORE = Block(17, "Iron Ore", True, (220, 220, 220), (0, 12))
GOLD_ORE = Block(18, "Gold Ore", True, (255, 215, 0), (0, 10))
WOOD = Block(19, "Wood", True, (139, 69, 19), (1, 13))
LEAVES = Block(20, "Leaves", True, (34, 139, 34), (9, 12), 
               animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
               frame_duration=300, tint=(34, 139, 34))
LEAVESGG = Block(21, "Leavesgg", True, (85, 170, 47), (9, 12),
                 animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
                 frame_duration=300, tint=(85, 170, 47))
SPAWNER = Block(22, "Spawner", True, (255, 0, 0), (5, 5), entity_type="mob")
STORAGE = StorageBlock(23, "Storage", True, (139, 69, 19), (15, 1))
FURNACE = FurnaceBlock(24, "Furnace", True, (100, 100, 100), (16, 1))
FARMLAND = FarmingBlock(25, "Farmland", True, (139, 69, 19), (13, 0))
ENHANCER = EnhancerBlock(50, "Enhancer", True, (100, 50, 150), (17, 1))

SAND = Block(30, "Sand", True, (194, 178, 128), (18, 5))
SANDSTONE = Block(31, "Sandstone", True, (219, 211, 160), (18, 6))
SNOW_GRASS = Block(32, "Snowy Grass", True, (200, 200, 200), (3, 10), tint=(200, 200, 200))
SNOW_DIRT = Block(33, "Frozen Dirt", True, (150, 150, 150), (8, 5), tint=(200, 200, 200))
SAVANNA_GRASS = Block(34, "Savanna Grass", True, (169, 178, 37), (8, 6), tint=(169, 178, 37))
SAVANNA_DIRT = Block(35, "Savanna Dirt", True, (130, 100, 60), (8, 5), tint=(169, 178, 37))

# Create item variants for blocks
wood_item = Item(19, "Wood", WOOD.texture_coords, stack_size=64, is_block=True, burn_time=1000)
wood_item.block = WOOD
WOOD.item_variant = wood_item
WOOD.drop_item = wood_item

for blk in [GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE,
            LEAVES, LEAVESGG, SPAWNER, SAND, SANDSTONE, SNOW_GRASS, SNOW_DIRT, 
            SAVANNA_GRASS, SAVANNA_DIRT]:
    item_variant = Item(blk.id, blk.name, blk.texture_coords, stack_size=64, is_block=True)
    item_variant.block = blk
    blk.item_variant = item_variant
    blk.drop_item = item_variant
    
    if blk == IRON_ORE:
        item_variant.melt_result = IRON_INGOT
    elif blk == GOLD_ORE:
        item_variant.melt_result = GOLD_INGOT
    elif blk == COAL_ORE:
        item_variant.melt_result = COAL

# Create special block items
storage_item = Item(23, "Storage", STORAGE.texture_coords, stack_size=64, is_block=True)
storage_item.block = STORAGE
STORAGE.item_variant = storage_item
STORAGE.drop_item = storage_item

furnace_item = Item(24, "Furnace", FURNACE.texture_coords, stack_size=64, is_block=True)
furnace_item.block = FURNACE
FURNACE.item_variant = furnace_item
FURNACE.drop_item = furnace_item

enhancer_item = Item(50, "Enhancer", ENHANCER.texture_coords, stack_size=64, is_block=True)
enhancer_item.block = ENHANCER
ENHANCER.item_variant = enhancer_item
ENHANCER.drop_item = enhancer_item

farmland_item = Item(25, "Farmland", FARMLAND.texture_coords, stack_size=64, is_block=True)
farmland_item.block = FARMLAND
FARMLAND.item_variant = farmland_item
FARMLAND.drop_item = farmland_item

# Block mapping populated with original blocks for now
BLOCK_MAP = {
    block.id: block for block in [
        AIR, GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT,
        COAL_ORE, IRON_ORE, GOLD_ORE, WOOD, LEAVES, LEAVESGG,
        SPAWNER, STORAGE, FURNACE, FARMLAND, ENHANCER,
        SAND, SANDSTONE, SNOW_GRASS, SNOW_DIRT,
        SAVANNA_GRASS, SAVANNA_DIRT
    ]
}
