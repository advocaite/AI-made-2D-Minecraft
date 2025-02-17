from item import Item, IRON_INGOT, GOLD_INGOT, COAL, MELTABLE_ITEMS, FUEL_ITEMS  # Add COAL to imports
import pygame
import config as c

class Block:
    def __init__(self, id, name, solid, color, texture_coords, drop_item=None, animation_frames=None, frame_duration=0, tint=None, entity_type=None):
        self.id = id
        self.name = name
        self.solid = solid
        self.color = color
        self.texture_coords = texture_coords  # (x, y) in the texture atlas
        self.drop_item = drop_item  # Optional item drop
        self.animation_frames = animation_frames  # List of (x, y) tuples for animation frames
        self.frame_duration = frame_duration  # Duration of each frame in milliseconds
        self.tint = tint  # Tint color to modify block appearance
        self.item_variant = None  # New: will hold the corresponding item
        self.entity_type = entity_type  # New: entity type to spawn

    def create_instance(self):
        """Base method to create a new instance of the block"""
        # Special case for AIR block - always return the same instance
        if self == AIR:
            return AIR
            
        # For normal blocks, create a new instance with all properties
        new_block = type(self)(
            id=self.id,
            name=self.name, 
            solid=self.solid,
            color=self.color,
            texture_coords=self.texture_coords,
            animation_frames=self.animation_frames,
            frame_duration=self.frame_duration,
            tint=self.tint,  # Added tint
            entity_type=self.entity_type
        )
        
        # Copy additional properties
        if hasattr(self, 'drop_item'):
            new_block.drop_item = self.drop_item
        if hasattr(self, 'item_variant'):
            new_block.item_variant = self.item_variant
            
        return new_block

    def to_dict(self):
        """Base serialization method for blocks"""
        data = {
            'id': self.id,
            'name': self.name,
            'texture_coords': self.texture_coords,
            'solid': self.solid
        }
        # Add tint if present
        if self.tint:
            data['tint'] = self.tint
        return data

    def from_dict(self, data, item_registry):
        """Base deserialization method for blocks"""
        self.id = data.get('id', self.id)
        self.name = data.get('name', self.name)  # Fixed syntax error here
        self.texture_coords = data.get('texture_coords', self.texture_coords)
        self.solid = data.get('solid', self.solid)
        self.tint = data.get('tint', self.tint)  # Restore tint

    # NEW: Helper method to get the block texture with tint applied if set.
    def get_texture(self, atlas):
        """Helper method to get the block texture with proper alpha handling"""
        if not hasattr(self, "_cached_base"):
            block_size = c.BLOCK_SIZE
            tx, ty = self.texture_coords
            texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
            base_img = atlas.subsurface(texture_rect).convert_alpha()
            
            # Create a new surface with per-pixel alpha
            self._cached_base = pygame.Surface((block_size, block_size), pygame.SRCALPHA, 32)
            self._cached_base = self._cached_base.convert_alpha()
            self._cached_base.blit(base_img, (0, 0))

        # Return base texture if no tint
        if not self.tint:
            return self._cached_base

        # Apply tint while preserving alpha
        if not hasattr(self, "_cached_texture"):
            self._cached_texture = self._cached_base.copy()
            tint_surface = pygame.Surface((c.BLOCK_SIZE, c.BLOCK_SIZE), pygame.SRCALPHA, 32)
            tint_surface = tint_surface.convert_alpha()
            tint_surface.fill((*self.tint, 255))
            self._cached_texture.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return self._cached_texture

class StorageBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (139, 69, 19), texture_coords)
        self.has_inventory = True
        self.max_slots = 27
        self.inventory = [None] * self.max_slots  # Initialize inventory here

    def create_instance(self):
        new_block = StorageBlock(self.id, self.name, self.texture_coords)
        new_block.inventory = [None] * self.max_slots
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def to_dict(self):
        """Serialize block data for saving"""
        return {
            'id': self.id,
            'name': self.name,
            'inventory': [
                {'item_id': slot['item'].id, 'quantity': slot['quantity']} 
                if slot and slot.get('item') else None 
                for slot in self.inventory
            ]
        }

    def from_dict(self, data, item_registry):
        """Deserialize block data when loading"""
        self.inventory = []
        for slot_data in data['inventory']:
            if slot_data is None:
                self.inventory.append(None)
            else:
                item = item_registry.get(slot_data['item_id'])
                if item:
                    self.inventory.append({
                        'item': item,
                        'quantity': slot_data['quantity']
                    })
                else:
                    self.inventory.append(None)

class FurnaceBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (100, 100, 100), texture_coords)
        self.has_inventory = True
        self.fuel_slot = None
        self.input_slot = None
        self.output_slot = None
        self.is_burning = False
        self.burn_time_remaining = 0
        self.melt_progress = 0

    def create_instance(self):
        """Create a new instance of the furnace with its own inventory"""
        new_block = FurnaceBlock(self.id, self.name, self.texture_coords)
        # Initialize slots
        new_block.fuel_slot = None
        new_block.input_slot = None
        new_block.output_slot = None
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def can_accept_fuel(self, item):
        """Check if item can be used as fuel"""
        print(f"Checking fuel: {item.name}, burn_time: {getattr(item, 'burn_time', 0)}")
        return item and hasattr(item, 'burn_time') and item.burn_time > 0

    def can_melt(self, item):
        """Check if item can be melted"""
        print(f"Checking meltable: {item.name}, has melt_result: {hasattr(item, 'melt_result')}")
        return item and hasattr(item, 'melt_result') and item.melt_result is not None

    def update(self, dt):
        """Process furnace smelting"""
        # Debug current state
        print(f"\nFurnace Update:")
        if self.input_slot and self.input_slot.get("item"):
            print(f"Input: {self.input_slot['item'].name} x{self.input_slot['quantity']}")
        else:
            print("Input: Empty")
            
        if self.fuel_slot and self.fuel_slot.get("item"):
            print(f"Fuel: {self.fuel_slot['item'].name} x{self.fuel_slot['quantity']}")
        else:
            print("Fuel: Empty")
            
        print(f"Is burning: {self.is_burning}")
        print(f"Burn time remaining: {self.burn_time_remaining}")
        print(f"Melt progress: {self.melt_progress}")

        # Check for valid input and fuel
        if not (self.input_slot and self.input_slot.get("item") and 
                self.fuel_slot and self.fuel_slot.get("item")):
            self.is_burning = False
            self.melt_progress = 0
            self.burn_time_remaining = 0
            return

        input_item = self.input_slot["item"]
        fuel_item = self.fuel_slot["item"]

        # Start new burn cycle if needed
        if not self.is_burning:
            if not hasattr(input_item, 'melt_result') or not input_item.melt_result:
                print(f"Item {input_item.name} cannot be melted")
                return

            if not hasattr(fuel_item, 'burn_time') or not fuel_item.burn_time:
                print(f"Item {fuel_item.name} cannot be used as fuel")
                return

            # Check if output allows for melting - FIXED LOGIC HERE
            melt_result = input_item.melt_result
            can_output = False
            
            # Can smelt if output is empty
            if not self.output_slot or not self.output_slot.get("item"):
                can_output = True
            # Or if output has same item and not at max stack
            elif (self.output_slot["item"].id == melt_result.id and 
                  self.output_slot["quantity"] < melt_result.stack_size):
                can_output = True

            if can_output:
                self.is_burning = True
                self.burn_time_remaining = fuel_item.burn_time
                self.fuel_slot["quantity"] -= 1
                if self.fuel_slot["quantity"] <= 0:
                    self.fuel_slot = None
                print(f"Started burning with {self.burn_time_remaining}ms remaining")

        # Process melting if burning
        if self.is_burning:
            self.burn_time_remaining -= dt
            self.melt_progress += dt

            if self.melt_progress >= 1000:  # 1 second to melt
                melt_result = input_item.melt_result
                
                # Create or update output slot - FIXED LOGIC HERE
                if not self.output_slot or not self.output_slot.get("item"):
                    self.output_slot = {"item": melt_result, "quantity": 1}
                elif self.output_slot["item"].id == melt_result.id:
                    self.output_slot["quantity"] += 1
                
                # Consume input
                self.input_slot["quantity"] -= 1
                if self.input_slot["quantity"] <= 0:
                    self.input_slot = None

                self.melt_progress = 0
                print(f"Melted item: created {melt_result.name}")

            # Stop burning if time expired or output full
            if self.burn_time_remaining <= 0:
                self.is_burning = False
                print("Burn cycle complete - fuel depleted")
            elif (self.output_slot and self.output_slot.get("item") and 
                  self.output_slot["quantity"] >= self.output_slot["item"].stack_size):
                self.is_burning = False
                print("Burn cycle complete - output full")

        # Final state debug
        print(f"End state - burning: {self.is_burning}, progress: {self.melt_progress}")
        if self.output_slot and self.output_slot.get("item"):
            print(f"Output slot: {self.output_slot['item'].name} x{self.output_slot['quantity']}")
        else:
            print("Output slot: Empty")

    def to_dict(self):
        """Serialize furnace data for saving"""
        return {
            'id': self.id,
            'name': self.name,
            'fuel_slot': self._slot_to_dict(self.fuel_slot),
            'input_slot': self._slot_to_dict(self.input_slot),
            'output_slot': self._slot_to_dict(self.output_slot),
            'is_burning': self.is_burning,
            'burn_time_remaining': self.burn_time_remaining,
            'melt_progress': self.melt_progress
        }

    def _slot_to_dict(self, slot):
        if slot and slot.get('item'):
            return {
                'item_id': slot['item'].id,
                'quantity': slot['quantity']
            }
        return None

    def from_dict(self, data, item_registry):
        """Deserialize furnace data when loading"""
        self.is_burning = data['is_burning']
        self.burn_time_remaining = data['burn_time_remaining']
        self.melt_progress = data['melt_progress']

        self.fuel_slot = self._dict_to_slot(data['fuel_slot'], item_registry)
        self.input_slot = self._dict_to_slot(data['input_slot'], item_registry)
        self.output_slot = self._dict_to_slot(data['output_slot'], item_registry)

    def _dict_to_slot(self, slot_data, item_registry):
        if slot_data:
            item = item_registry.get(slot_data['item_id'])
            if item:
                return {
                    'item': item,
                    'quantity': slot_data['quantity']
                }
        return None

class EnhancerBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (100, 50, 150), texture_coords)
        self.has_inventory = True
        self.can_interact = True  # Add this line
        self.input_slot = None
        self.ingredient_slot = None

    def create_instance(self):
        """Create a new instance of the enhancer with its own slots"""
        new_block = EnhancerBlock(self.id, self.name, self.texture_coords)
        new_block.input_slot = None
        new_block.ingredient_slot = None
        new_block.item_variant = self.item_variant  # Make sure this is copied
        new_block.drop_item = self.drop_item  # Make sure this is copied
        return new_block

    def to_dict(self):
        """Serialize enhancer data for saving"""
        data = {
            'id': self.id,
            'name': self.name,
            'input_slot': None,
            'ingredient_slot': None
        }

        # Save input slot
        if self.input_slot and self.input_slot.get('item'):
            data['input_slot'] = {
                'item_id': self.input_slot['item'].id,
                'quantity': self.input_slot['quantity'],
                'modifiers': getattr(self.input_slot['item'], 'modifiers', {}),
                'enhanced_suffix': getattr(self.input_slot['item'], 'enhanced_suffix', '')
            }

        # Save ingredient slot
        if self.ingredient_slot and self.ingredient_slot.get('item'):
            data['ingredient_slot'] = {
                'item_id': self.ingredient_slot['item'].id,
                'quantity': self.ingredient_slot['quantity']
            }

        print(f"Saving enhancer state: {data}")
        return data

    def from_dict(self, data, item_registry):
        """Deserialize enhancer data when loading"""
        # Load input slot
        if data.get('input_slot'):
            slot_data = data['input_slot']
            item = item_registry.get(slot_data['item_id'])
            if item:
                # Create new instance to avoid shared references
                item = type(item)(item.id, item.name, item.texture_coords)
                
                # Apply saved modifiers and suffix
                if 'modifiers' in slot_data:
                    item.modifiers = slot_data['modifiers']
                if 'enhanced_suffix' in slot_data and slot_data['enhanced_suffix']:
                    item.enhanced_suffix = slot_data['enhanced_suffix']
                    item.name = f"{item.name} {item.enhanced_suffix}"
                
                self.input_slot = {
                    'item': item,
                    'quantity': slot_data['quantity']
                }

        # Load ingredient slot
        if data.get('ingredient_slot'):
            slot_data = data['ingredient_slot']
            item = item_registry.get(slot_data['item_id'])
            if item:
                self.ingredient_slot = {
                    'item': item,
                    'quantity': slot_data['quantity']
                }

        print(f"Loaded enhancer state: input={self.input_slot}, ingredient={self.ingredient_slot}")

class FarmingBlock(Block):
    def __init__(self, id, name, texture_coords):
        super().__init__(id, name, True, (139, 69, 19), texture_coords)
        self.plantable = True
        self.plant = None
        self.tilled = False
        self.untilled_texture = texture_coords  # Store original texture
        self.tilled_texture = (13, 1)  # Tilled soil texture

    def create_instance(self):
        new_block = FarmingBlock(self.id, self.name, self.texture_coords)
        new_block.item_variant = self.item_variant
        new_block.drop_item = self.drop_item
        return new_block

    def plant_seed(self, seed_item):
        """Plant a seed if conditions are met"""
        if self.tilled and not self.plant and seed_item.is_seed:
            print(f"Planting seed: {seed_item.name}")
            self.plant = Plant(seed_item.plant_data)
            # Set initial texture to first growth stage
            self.texture_coords = seed_item.plant_data['texture_coords'][0]
            return True
        return False

    def till(self):
        """Till the soil with a hoe"""
        self.tilled = True
        self.texture_coords = self.tilled_texture  # Update texture immediately
        print(f"Tilled soil! New texture: {self.texture_coords}")

    def update(self, dt):
        """Update plant growth"""
        if self.plant:
            if self.plant.update(dt):
                # Update texture coords only when plant changes stage
                self.texture_coords = self.plant.get_texture_coords()
                print(f"Plant updated: stage {self.plant.current_stage}")
                return True
        return False

    def harvest(self, tool=None):
        """Harvest plant and return drops"""
        if not self.plant:
            return None
            
        drops = self.plant.get_drops(tool)
        print(f"Harvested plant with drops: {drops}")
        self.plant = None
        # Reset texture to tilled state after harvesting
        self.texture_coords = self.tilled_texture
        return drops

    def to_dict(self):
        """Serialize farming block data for saving"""
        data = super().to_dict()  # Now this will work
        data.update({
            'tilled': self.tilled,
            'plant': None,
            'is_block': True,  # Add this to ensure block property is saved
            'texture_coords': self.texture_coords
        })
        if self.plant:
            data['plant'] = {
                'plant_data': self.plant.plant_data,
                'current_stage': self.plant.current_stage,
                'time_in_stage': self.plant.time_in_stage
            }
        return data

    def from_dict(self, data, item_registry):
        """Deserialize farming block data when loading"""
        super().from_dict(data, item_registry)  # Load base block data first
        self.tilled = data.get('tilled', False)
        self.is_block = data.get('is_block', True)  # Restore block property
        if data.get('plant'):
            plant_data = data['plant']
            self.plant = Plant(plant_data['plant_data'])
            self.plant.current_stage = plant_data['current_stage']
            self.plant.time_in_stage = plant_data['time_in_stage']

    def get_texture(self, atlas):
        """Override get_texture to show both tilled soil and plant if present"""
        # Get base farmland texture (tilled or untilled)
        block_size = c.BLOCK_SIZE
        tx, ty = self.texture_coords
        texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
        base_texture = atlas.subsurface(texture_rect).convert_alpha()

        # If there's a plant, draw it on top
        if self.plant:
            plant_tx, plant_ty = self.plant.get_texture_coords()
            plant_rect = pygame.Rect(plant_tx * block_size, plant_ty * block_size, block_size, block_size)
            plant_texture = atlas.subsurface(plant_rect).convert_alpha()
            
            # Create a new surface combining soil and plant
            combined = base_texture.copy()
            combined.blit(plant_texture, (0, 0))
            return combined
            
        return base_texture

class Plant:
    def __init__(self, plant_data):
        self.growth_stages = plant_data['growth_stages']
        self.current_stage = 0
        self.growth_time = plant_data['growth_time']
        self.time_in_stage = 0
        self.drops = plant_data['drops']
        self.texture_coords = plant_data['texture_coords']
        self.solid = False  # Make plants non-collidable
        # Debugging output
        print(f"Plant initialized with texture coords: {self.texture_coords}")
        print(f"Growth stages: {self.growth_stages}")
        print(f"Current stage: {self.current_stage}")

    def update(self, dt):
        """Update plant growth and return True if stage changed"""
        if self.current_stage >= len(self.growth_stages) - 1:
            return False

        self.time_in_stage += dt
        if self.time_in_stage >= self.growth_time:
            self.current_stage += 1
            self.time_in_stage = 0
            print(f"Plant grew to stage {self.current_stage}")
            return True
        return False

    def get_drops(self, tool=None):
        stage_drops = self.drops[self.current_stage]
        if tool and tool.type == "hoe":
            # Instead of multiplying by 1.5, add +1 to quantity for using proper tool
            return [(item, qty + 1) for item, qty in stage_drops]
        return stage_drops

    def get_texture_coords(self):
        return self.texture_coords[self.current_stage]

    def to_dict(self):
        return {
            'current_stage': self.current_stage,
            'time_in_stage': self.time_in_stage
        }

    @staticmethod
    def from_dict(data):
        plant = Plant(data['plant_data'])
        plant.current_stage = data['current_stage']
        plant.time_in_stage = data['time_in_stage']
        return plant

# Define standard blocks
AIR = Block(0, "Air", False, (255, 255, 255), (0, 0))
GRASS = Block(1, "Grass", True, (34, 139, 34), (1, 10))
DIRT = Block(2, "Dirt", True, (139, 69, 19), (8, 5))
STONE = Block(4, "Stone", True, (105, 105, 105), (19, 6))
UNBREAKABLE = Block(8, "Unbreakable", True, (70, 70, 70), (4, 3))
WATER = Block(9, "Water", False, (0, 191, 255), (3, 0), animation_frames=[(3, 1), (3, 0),(2, 1), (2, 0)], frame_duration=200)
# New Light block for emitting light
LIGHT = Block(10, "Light", True, (255, 255, 200), (14, 9))
COAL_ORE = Block(16, "Coal Ore", True, (0, 0, 0), (1, 5))
IRON_ORE = Block(17, "Iron Ore", True, (220, 220, 220), (0, 12))
GOLD_ORE = Block(18, "Gold Ore", True, (255, 215, 0), (0, 10))
WOOD = Block(19, "Wood", True, (255, 215, 0), (1, 13))

# NEW: Define animated Leaves block with tint.
LEAVES = Block(
    20,
    "Leaves",
    True,
    (34, 139, 34),
    (9, 12),
    animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
    frame_duration=300,
    tint=(34, 139, 34)  # Tint color applied to leaves
)
LEAVESGG = Block(
    21,
    "Leavesgg",
    True,
    (85, 170, 47),
    (9, 12),
    animation_frames=[(9, 12), (10, 12), (11, 12), (12, 12)],
    frame_duration=300,
    tint=(85, 170, 47)  # Tint color applied to leaves
)

# Define the new Spawner block with entity type
SPAWNER = Block(22, "Spawner", True, (255, 0, 0), (5, 5), entity_type="mob")

# Create wood item variant separately with burn time
wood_item = Item(19, "Wood", WOOD.texture_coords, stack_size=64, is_block=True, burn_time=1000)
wood_item.block = WOOD
WOOD.item_variant = wood_item
WOOD.drop_item = wood_item

# Create blocks first
STORAGE = StorageBlock(23, "Storage", (15, 1))  # Adjust texture coordinates as needed
FURNACE = FurnaceBlock(24, "Furnace", (16, 1))  # Adjust texture coordinates as needed
ENHANCER = EnhancerBlock(50, "Enhancer", (17, 1))
FARMLAND = FarmingBlock(25, "Farmland", (13, 0))  # Untilled texture

# Add new biome blocks
SAND = Block(30, "Sand", True, (194, 178, 128), (18, 5))
SANDSTONE = Block(31, "Sandstone", True, (219, 211, 160), (18, 6))
SNOW_GRASS = Block(32, "Snowy Grass", True, (200, 200, 200), (3, 10), tint=(200, 200, 200))
SNOW_DIRT = Block(33, "Frozen Dirt", True, (150, 150, 150), (8, 5), tint=(200, 200, 200))
SAVANNA_GRASS = Block(34, "Savanna Grass", True, (169, 178, 37), (8, 6), tint=(169, 178, 37))
SAVANNA_DIRT = Block(35, "Savanna Dirt", True, (130, 100, 60), (8, 5), tint=(169, 178, 37))

# Create item variants for other blocks
for blk in (GRASS, DIRT, STONE, UNBREAKABLE, WATER, LIGHT, COAL_ORE, IRON_ORE, GOLD_ORE, LEAVES, LEAVESGG, SPAWNER, SAND, SANDSTONE, SNOW_GRASS, SNOW_DIRT, SAVANNA_GRASS, SAVANNA_DIRT):
    item_variant = Item(blk.id, blk.name, blk.texture_coords, stack_size=64, is_block=True)
    item_variant.block = blk
    blk.item_variant = item_variant
    blk.drop_item = item_variant
    
    # Set melt results for ores
    if blk == IRON_ORE:
        item_variant.melt_result = IRON_INGOT
    elif blk == GOLD_ORE:
        item_variant.melt_result = GOLD_INGOT
    elif blk == COAL_ORE:
        item_variant.melt_result = COAL

# Update registries
MELTABLE_ITEMS.update({
    IRON_ORE.id: IRON_INGOT,
    GOLD_ORE.id: GOLD_INGOT,
    COAL_ORE.id: COAL
})

FUEL_ITEMS.update({
    19: 1000,     # Wood ID -> burn time
    202: 2000    # Coal ID -> burn time
})

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

# Ensure SPAWNER_ITEM is defined
SPAWNER_ITEM = SPAWNER.item_variant

# NEW: Mapping from integer block codes to Block objects
BLOCK_MAP = {
    0: AIR,
    1: GRASS,
    2: DIRT,
    4: STONE,
    8: UNBREAKABLE,
    9: WATER,
    10: LIGHT,
    16: COAL_ORE,
    17: IRON_ORE,
    18: GOLD_ORE,
    19: WOOD,
    20: LEAVES,  # NEW: Leaves block added
    21: LEAVESGG,  # NEW: Leaves block added
    22: SPAWNER,  # NEW: Spawner block added
    23: STORAGE,  # NEW: Storage block added
    24: FURNACE,  # NEW: Furnace block added
    25: FARMLAND,  # NEW: Farmland block added
    30: SAND,  # NEW: Sand block added
    31: SANDSTONE,  # NEW: Sandstone block added
    32: SNOW_GRASS,  # NEW: Snowy Grass block added
    33: SNOW_DIRT,  # NEW: Frozen Dirt block added
    34: SAVANNA_GRASS,  # NEW: Savanna Grass block added
    35: SAVANNA_DIRT,  # NEW: Savanna Dirt block added
    50: ENHANCER  # Make sure this is included
}
