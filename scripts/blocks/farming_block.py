import pygame

class BlockScript:
    def __init__(self, block):
        self.block = block
        self.plantable = True
        self.plant = None
        self.tilled = False
        
        # Define texture coordinates
        self.untilled_coords = (13, 0)  # Untilled farmland
        self.tilled_coords = (13, 1)    # Tilled soil
        self._set_texture(self.untilled_coords)
        
        print(f"[FARM SCRIPT] Created new farming block script with texture: {self.block.texture_coords}")
        self._needs_texture_update = True  # Changed to True initially
        self._last_update_time = pygame.time.get_ticks()  # Initialize with current time
        self._update_interval = 1000  # Update every 1 second instead of every frame

    def _set_texture(self, coords):
        """Helper to update block texture"""
        self.block.texture_coords = coords
        print(f"[FARM SCRIPT] Set texture to: {coords}")

    def update_texture(self):
        """Optimized texture update"""
        if not self._needs_texture_update:
            return False
            
        if self.plant:
            coords = self.plant.get_texture_coords()
            if coords != self.block.texture_coords:
                self.block.texture_coords = coords
                self._needs_texture_update = False
                return True
        else:
            new_coords = self.tilled_coords if self.tilled else self.untilled_coords
            if new_coords != self.block.texture_coords:
                self.block.texture_coords = new_coords
                self._needs_texture_update = False
                return True
        return False

    def create_instance(self):
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def till(self):
        """Handle tilling the farmland"""
        print(f"[FARM SCRIPT] Till requested. Current state: tilled={self.tilled}")
        if not self.tilled:
            print(f"[FARM SCRIPT] Tilling soil. Old texture: {self.block.texture_coords}")
            self.tilled = True
            self._set_texture(self.tilled_coords)
            print(f"[FARM SCRIPT] Tilled soil. New texture: {self.block.texture_coords}")
            return True
        else:
            print(f"[FARM SCRIPT] Already tilled!")
            return False

    def plant_seed(self, seed_item):
        """Plant a seed in the tilled farmland"""
        print(f"[FARM DEBUG] Plant attempt - Block at {id(self)}")
        print(f"[FARM DEBUG] Current state: tilled={self.tilled}, has_plant={self.plant is not None}")
        
        if not hasattr(seed_item, 'plant_data'):
            print(f"[FARM DEBUG] No plant data for seed: {seed_item.name}")
            return False

        if not self.tilled or self.plant:
            print(f"[FARM DEBUG] Cannot plant: tilled={self.tilled}, has_plant={self.plant is not None}")
            return False
        
        print(f"[FARM DEBUG] Planting {seed_item.name} in block {id(self)}")
        self.plant = Plant(seed_item.plant_data)
        self._needs_texture_update = True  # Force texture update
        self.update_texture()  # Immediately update texture
        print(f"[FARM DEBUG] Plant texture set to: {self.plant.get_texture_coords()}")
        return True

    def update(self, dt):
        """Optimized plant growth update"""
        if not self.plant:
            return False

        current_time = pygame.time.get_ticks()
        if current_time - self._last_update_time < self._update_interval:
            return False
            
        self._last_update_time = current_time
        
        # Add debug prints
        print(f"[FARM DEBUG] Plant growing: Stage {self.plant.current_stage}, Time: {self.plant.time_in_stage}/{self.plant.growth_time}")
        
        if self.plant.update(dt):
            self._needs_texture_update = True
            # Force texture update
            old_coords = self.block.texture_coords
            new_coords = self.plant.get_texture_coords()
            self.block.texture_coords = new_coords
            print(f"[FARM DEBUG] Plant grew! Stage: {self.plant.current_stage}, Texture: {old_coords} -> {new_coords}")
            return True
        return False

    def harvest(self, tool=None):
        """Harvest the plant and get drops"""
        if not self.plant:
            return None
            
        if not self.plant.is_fully_grown():
            print("[FARM DEBUG] Plant not fully grown yet")
            return None

        drops = self.plant.get_drops(tool)
        self.plant = None
        self._set_texture(self.tilled_coords)  # Return to tilled state
        print(f"[FARM DEBUG] Harvested plant, got drops: {drops}")
        return drops

    def to_dict(self):
        data = {
            'tilled': self.tilled,
            'plant': None
        }
        if self.plant:
            data['plant'] = {
                'plant_data': self.plant.plant_data,
                'current_stage': self.plant.current_stage,
                'time_in_stage': self.plant.time_in_stage
            }
        return data

    def from_dict(self, data, item_registry):
        self.tilled = data.get('tilled', False)
        if data.get('plant'):
            plant_data = data['plant']
            self.plant = Plant(plant_data['plant_data'])
            self.plant.current_stage = plant_data['current_stage']
            self.plant.time_in_stage = plant_data['time_in_stage']

class Plant:
    def __init__(self, plant_data):
        self.plant_data = plant_data
        self.growth_stages = plant_data['growth_stages']
        self.current_stage = 0
        self.growth_time = plant_data['growth_time']
        self.time_in_stage = 0
        self.texture_coords = plant_data['texture_coords']
        self.solid = False
        self._cached_texture_coords = None  # Cache for texture coordinates

    def is_fully_grown(self):
        """Check if plant has reached final growth stage"""
        return self.current_stage >= len(self.growth_stages) - 1

    def get_drops(self, tool=None):
        """Get drops when harvesting the plant"""
        from registry import REGISTRY
        import random
        
        drops = []
        if 'drops' not in self.plant_data:
            print("[FARM DEBUG] No drops specified in plant_data")
            return []
            
        drop_data = self.plant_data['drops']
        print(f"[FARM DEBUG] Processing drops: {drop_data}")
        
        # Process seed drops
        if 'seed' in drop_data and drop_data['seed']:
            seed_info = drop_data['seed']
            print(f"[FARM DEBUG] Looking for seed item: {seed_info['id']}")
            seed_item = REGISTRY.get_item(seed_info['id'])
            if seed_item:
                # Handle random quantity ranges like "1-3"
                quantity = seed_info['quantity']
                if isinstance(quantity, str) and '-' in quantity:
                    min_q, max_q = map(int, quantity.split('-'))
                    quantity = random.randint(min_q, max_q)
                else:
                    quantity = int(quantity)
                    
                drops.append((seed_item, quantity))
                print(f"[FARM DEBUG] Found seed item: {seed_item.name}")
                print(f"[FARM DEBUG] Adding seed drop: {seed_item.name} x{quantity}")
            else:
                print(f"[FARM DEBUG] Failed to find seed item: {seed_info['id']}")

        # Process crop drops if fully grown
        if self.is_fully_grown() and 'crop' in drop_data and drop_data['crop']:
            crop_info = drop_data['crop']
            print(f"[FARM DEBUG] Looking for crop item: {crop_info['id']}")
            crop_item = REGISTRY.get_item(crop_info['id'])
            if crop_item:
                # Handle random quantity ranges
                quantity = crop_info['quantity']
                if isinstance(quantity, str) and '-' in quantity:
                    min_q, max_q = map(int, quantity.split('-'))
                    quantity = random.randint(min_q, max_q)
                else:
                    quantity = int(quantity)
                    
                drops.append((crop_item, quantity))
                print(f"[FARM DEBUG] Found crop item: {crop_item.name}")
                print(f"[FARM DEBUG] Adding crop drop: {crop_item.name} x{quantity}")
            else:
                print(f"[FARM DEBUG] Failed to find crop item: {crop_info['id']}")
        
        return drops

    def update(self, dt):
        """Update plant growth with fixed dt"""
        if self.current_stage >= len(self.growth_stages) - 1:
            return False

        print(f"[FARM DEBUG] Growing... Time: {self.time_in_stage}/{self.growth_time}")
        self.time_in_stage += dt
        if self.time_in_stage >= self.growth_time:
            self.current_stage += 1
            self.time_in_stage = 0
            print(f"[FARM DEBUG] Advanced to stage {self.current_stage}")
            return True
        return False

    def get_texture_coords(self):
        """Cached texture coordinate lookup"""
        if self._cached_texture_coords is None or self._cached_texture_coords[0] != self.current_stage:
            # Convert texture coordinates to tuple
            coords = tuple(self.texture_coords[self.current_stage])
            self._cached_texture_coords = (self.current_stage, coords)
        return self._cached_texture_coords[1]
