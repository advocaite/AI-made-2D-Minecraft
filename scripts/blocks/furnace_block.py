class BlockScript:
    def __init__(self, block):
        self.block = block
        self.has_inventory = True
        self.fuel_slot = None
        self.input_slot = None
        self.output_slot = None
        self.is_burning = False
        self.burn_time_remaining = 0
        self.melt_progress = 0

    def create_instance(self):
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def update(self, dt):
        if not (self.input_slot and self.input_slot.get("item") and 
                self.fuel_slot and self.fuel_slot.get("item")):
            self.is_burning = False
            self.melt_progress = 0
            self.burn_time_remaining = 0
            return

        input_item = self.input_slot["item"]
        fuel_item = self.fuel_slot["item"]

        # Process furnace mechanics
        if not self.is_burning:
            if hasattr(input_item, 'melt_result') and input_item.melt_result:
                if hasattr(fuel_item, 'burn_time') and fuel_item.burn_time:
                    self.start_burning(fuel_item)

        if self.is_burning:
            self.process_melting(dt, input_item)

    def start_burning(self, fuel_item):
        self.is_burning = True
        self.burn_time_remaining = fuel_item.burn_time
        self.fuel_slot["quantity"] -= 1
        if self.fuel_slot["quantity"] <= 0:
            self.fuel_slot = None

    def process_melting(self, dt, input_item):
        self.burn_time_remaining -= dt
        self.melt_progress += dt

        if self.melt_progress >= 1000:  # 1 second to melt
            self.complete_melting(input_item)

        if self.burn_time_remaining <= 0:
            self.is_burning = False

    def complete_melting(self, input_item):
        melt_result = input_item.melt_result
        if not self.output_slot:
            self.output_slot = {"item": melt_result, "quantity": 1}
        elif self.output_slot["item"].id == melt_result.id:
            self.output_slot["quantity"] += 1

        self.input_slot["quantity"] -= 1
        if self.input_slot["quantity"] <= 0:
            self.input_slot = None
        self.melt_progress = 0

    def to_dict(self):
        return {
            'fuel_slot': self._slot_to_dict(self.fuel_slot),
            'input_slot': self._slot_to_dict(self.input_slot),
            'output_slot': self._slot_to_dict(self.output_slot),
            'is_burning': self.is_burning,
            'burn_time_remaining': self.burn_time_remaining,
            'melt_progress': self.melt_progress
        }

    def from_dict(self, data, item_registry):
        self.is_burning = data['is_burning']
        self.burn_time_remaining = data['burn_time_remaining']
        self.melt_progress = data['melt_progress']
        self.fuel_slot = self._dict_to_slot(data['fuel_slot'], item_registry)
        self.input_slot = self._dict_to_slot(data['input_slot'], item_registry)
        self.output_slot = self._dict_to_slot(data['output_slot'], item_registry)

    def _slot_to_dict(self, slot):
        if slot and slot.get('item'):
            return {'item_id': slot['item'].id, 'quantity': slot['quantity']}
        return None

    def _dict_to_slot(self, slot_data, item_registry):
        if slot_data:
            item = item_registry.get(slot_data['item_id'])
            if item:
                return {'item': item, 'quantity': slot_data['quantity']}
        return None
