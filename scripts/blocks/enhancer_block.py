class BlockScript:
    def __init__(self, block):
        self.block = block
        self.has_inventory = True
        self.input_slot = None
        self.ingredient_slot = None

    def create_instance(self):
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def enhance_item(self):
        if not (self.input_slot and self.ingredient_slot):
            return False
            
        input_item = self.input_slot['item']
        ingredient = self.ingredient_slot['item']
        
        if not hasattr(input_item, 'modifiers'):
            input_item.modifiers = {}
            
        # Apply enhancement
        if 'enhancement_power' in ingredient.__dict__:
            for stat, value in ingredient.enhancement_power.items():
                if stat in input_item.modifiers:
                    input_item.modifiers[stat] += value
                else:
                    input_item.modifiers[stat] = value
                    
            # Update name with enhancement
            if not hasattr(input_item, 'enhanced_suffix'):
                input_item.enhanced_suffix = ingredient.enhancement_name
                input_item.name = f"{input_item.name} {ingredient.enhancement_name}"
                
            # Consume ingredient
            self.ingredient_slot['quantity'] -= 1
            if self.ingredient_slot['quantity'] <= 0:
                self.ingredient_slot = None
                
            return True
            
        return False

    def to_dict(self):
        return {
            'input_slot': self._slot_to_dict(self.input_slot),
            'ingredient_slot': self._slot_to_dict(self.ingredient_slot)
        }

    def from_dict(self, data, item_registry):
        self.input_slot = self._dict_to_slot(data.get('input_slot'), item_registry)
        self.ingredient_slot = self._dict_to_slot(data.get('ingredient_slot'), item_registry)

    def _slot_to_dict(self, slot):
        if slot and slot.get('item'):
            return {
                'item_id': slot['item'].id,
                'quantity': slot['quantity'],
                'modifiers': getattr(slot['item'], 'modifiers', {}),
                'enhanced_suffix': getattr(slot['item'], 'enhanced_suffix', '')
            }
        return None

    def _dict_to_slot(self, slot_data, item_registry):
        if not slot_data:
            return None
            
        item = item_registry.get(slot_data['item_id'])
        if not item:
            return None
            
        # Create new instance to avoid shared references
        item = type(item)(item.id, item.name, item.texture_coords)
        
        # Apply saved modifiers and suffix
        if 'modifiers' in slot_data:
            item.modifiers = slot_data['modifiers']
        if 'enhanced_suffix' in slot_data and slot_data['enhanced_suffix']:
            item.enhanced_suffix = slot_data['enhanced_suffix']
            item.name = f"{item.name} {item.enhanced_suffix}"
        
        return {
            'item': item,
            'quantity': slot_data['quantity']
        }
