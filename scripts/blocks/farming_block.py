class BlockScript:
    def __init__(self, block):
        self.block = block
        self.plantable = True
        self.plant = None
        self.tilled = False
        self.untilled_texture = block.texture_coords
        self.tilled_texture = (13, 1)

    def create_instance(self):
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def till(self):
        self.tilled = True
        self.block.texture_coords = self.tilled_texture
        return True

    def plant_seed(self, seed_item):
        if not (self.tilled and not self.plant and seed_item.is_seed):
            return False
            
        self.plant = Plant(seed_item.plant_data)
        self.block.texture_coords = seed_item.plant_data['texture_coords'][0]
        return True

    def update(self, dt):
        if not self.plant:
            return False
            
        if self.plant.update(dt):
            self.block.texture_coords = self.plant.get_texture_coords()
            return True
        return False

    def harvest(self, tool=None):
        if not self.plant:
            return None
            
        drops = self.plant.get_drops(tool)
        self.plant = None
        self.block.texture_coords = self.tilled_texture
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
        self.growth_stages = plant_data['growth_stages']
        self.current_stage = 0
        self.growth_time = plant_data['growth_time']
        self.time_in_stage = 0
        self.drops = plant_data.get('drops', [])
        self.texture_coords = plant_data['texture_coords']
        self.solid = False

    def update(self, dt):
        if self.current_stage >= len(self.growth_stages) - 1:
            return False

        self.time_in_stage += dt
        if self.time_in_stage >= self.growth_time:
            self.current_stage += 1
            self.time_in_stage = 0
            return True
        return False

    def get_drops(self, tool=None):
        stage_drops = self.drops[self.current_stage] if self.drops else []
        if tool and tool.type == "hoe":
            return [(item, qty + 1) for item, qty in stage_drops]
        return stage_drops

    def get_texture_coords(self):
        return self.texture_coords[self.current_stage]
