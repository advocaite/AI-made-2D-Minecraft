class BlockScript:
    def __init__(self, block):
        self.block = block
        self.has_inventory = True
        self.max_slots = 27
        self.inventory = [None] * self.max_slots

    def create_instance(self):
        """Create a new instance of the block with its own inventory"""
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        new_block.script.inventory = [None] * self.max_slots
        return new_block

    def to_dict(self):
        return {
            'inventory': [
                {'item_id': slot['item'].id, 'quantity': slot['quantity']} 
                if slot and slot.get('item') else None 
                for slot in self.inventory
            ]
        }

    def from_dict(self, data, item_registry):
        self.inventory = []
        for slot_data in data.get('inventory', []):
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
