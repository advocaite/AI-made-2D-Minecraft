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

    def _set_texture(self, coords):
        """Helper to update block texture"""
        self.block.texture_coords = coords
        print(f"[FARM SCRIPT] Set texture to: {coords}")

    def update_texture(self):
        """Update block texture based on state"""
        if self.plant:
            # Use plant's current growth stage texture
            self.block.texture_coords = self.plant.get_texture_coords()
        else:
            # Use tilled or untilled texture
            self.block.texture_coords = self.tilled_coords if self.tilled else self.untilled_coords
        print(f"Updated texture to: {self.block.texture_coords}")

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
        print(f"Attempting to plant seed. Tilled: {self.tilled}, Has plant: {self.plant is not None}")
        
        if not hasattr(seed_item, 'plant_data'):
            print(f"No plant data for seed: {seed_item.name}")
            return False

        if not self.tilled or self.plant:
            print(f"Cannot plant: tilled={self.tilled}, has_plant={self.plant is not None}")
            return False
        
        print(f"Planting seed: {seed_item.name}")
        self.plant = Plant(seed_item.plant_data)
        self.update_texture()
        return True

    def update(self, dt):
        """Update plant growth"""
        if not self.plant:
            return False
            
        if self.plant.update(dt):
            self.update_texture()
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

    def is_fully_grown(self):
        """Check if plant has reached final growth stage"""
        return self.current_stage >= len(self.growth_stages) - 1

    def get_drops(self, tool=None):
        """Get drops when harvesting the plant"""
        from registry import REGISTRY
        
        print(f"[FARM DEBUG] Looking up items by name")
        wheat_seed = REGISTRY.get_item("WHEAT_SEED")
        wheat = REGISTRY.get_item("WHEAT")
        
        print(f"[FARM DEBUG] Found items:")
        print(f"Wheat Seed: {wheat_seed.name if wheat_seed else 'Not found'}")
        print(f"Wheat: {wheat.name if wheat else 'Not found'}")
        
        # Always return at least one seed
        drops = []
        if wheat_seed:
            drops.append((wheat_seed, 1))
            print(f"[FARM DEBUG] Added seed drop: {wheat_seed.name}")
        
        # Add crop only if fully grown
        if self.is_fully_grown() and wheat:
            drops.append((wheat, 1))
            print(f"[FARM DEBUG] Added crop drop: {wheat.name}")
        
        if not drops:
            print("[FARM DEBUG] Warning: No valid drops found!")
            print(f"[FARM DEBUG] Available items: {list(REGISTRY.items.keys())}")
            
        return drops

    def update(self, dt):
        if self.current_stage >= len(self.growth_stages) - 1:
            return False

        self.time_in_stage += dt
        if self.time_in_stage >= self.growth_time:
            self.current_stage += 1
            self.time_in_stage = 0
            return True
        return False

    def get_texture_coords(self):
        return self.texture_coords[self.current_stage]
