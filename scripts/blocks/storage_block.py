class BlockScript:
    def __init__(self, block):
        self.block = block
        self.has_inventory = True
        self.max_slots = 27  # Define max_slots here
        self.inventory = [{"item": None, "quantity": 0} for _ in range(self.max_slots)]

    def create_instance(self):
        """Create a new instance of the block with its own inventory"""
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def to_dict(self):
        """Convert storage state to dictionary for saving"""
        return {
            'inventory': [
                self._slot_to_dict(slot) for slot in self.inventory
            ]
        }

    def from_dict(self, data, item_registry):
        """Load storage state from dictionary"""
        if 'inventory' in data:
            self.inventory = [
                self._dict_to_slot(slot_data, item_registry) 
                for slot_data in data['inventory']
            ]

    def _slot_to_dict(self, slot):
        """Helper to serialize a slot"""
        if slot and slot.get("item"):
            return {
                'item_id': str(slot['item'].id),
                'quantity': slot['quantity']
            }
        return None

    def _dict_to_slot(self, slot_data, item_registry):
        """Helper to deserialize a slot"""
        if slot_data and 'item_id' in slot_data:
            item = item_registry.get(str(slot_data['item_id']))
            if item:
                return {
                    'item': item,
                    'quantity': slot_data['quantity']
                }
        return {"item": None, "quantity": 0}
