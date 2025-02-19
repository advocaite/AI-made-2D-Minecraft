class BlockScript:
    def __init__(self, block):
        self.block = block
        self.input_slot = {"item": None, "quantity": 0}
        self.ingredient_slot = {"item": None, "quantity": 0}
        
    def create_instance(self):
        """Create new instance with preserved items"""
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        # Copy slot contents
        new_block.script.input_slot = self.input_slot.copy()
        new_block.script.ingredient_slot = self.ingredient_slot.copy()
        return new_block

    def enhance_item(self):
        """Process item enhancement"""
        if not (self.input_slot["item"] and self.ingredient_slot["item"]):
            print("[ENHANCER] Missing input or ingredient")
            return False

        input_item = self.input_slot["item"]
        ingredient = self.ingredient_slot["item"]

        # Initialize modifiers if they don't exist
        if not hasattr(input_item, 'modifiers'):
            input_item.modifiers = {
                'damage': 0,
                'defense': 0,
                'health': 0,
                'attack_speed': 0,
                'movement_speed': 0
            }

        # Check if ingredient has enhancement properties
        if hasattr(ingredient, 'enhancement_power'):
            print(f"[ENHANCER] Applying enhancement from {ingredient.name}")
            # Apply enhancements
            for stat, value in ingredient.enhancement_power.items():
                if stat in input_item.modifiers:
                    input_item.modifiers[stat] += value
                    print(f"[ENHANCER] Added {value} to {stat}")

            # Update item name with enhancement
            suffix = getattr(ingredient, 'enhancement_name', 'Enhanced')
            if not hasattr(input_item, 'enhanced_suffix'):
                input_item.enhanced_suffix = suffix
                input_item.name = f"{input_item.name} {suffix}"
                print(f"[ENHANCER] New item name: {input_item.name}")

            # Consume ingredient
            self.ingredient_slot["quantity"] -= 1
            if self.ingredient_slot["quantity"] <= 0:
                self.ingredient_slot = {"item": None, "quantity": 0}
            
            return True
        
        print("[ENHANCER] Ingredient has no enhancement properties")
        return False

    def to_dict(self):
        """Serialize enhancer state"""
        data = {
            'id': self.block.id,  # Add block ID
            'type': 'enhancer',   # Add block type
            'slots': {
                'input_slot': None,
                'ingredient_slot': None
            }
        }

        # Serialize input slot
        if self.input_slot and self.input_slot.get("item"):
            data['slots']['input_slot'] = {
                "item_id": self.input_slot["item"].id,
                "quantity": self.input_slot["quantity"],
                "modifiers": getattr(self.input_slot["item"], "modifiers", {}),
                "enhanced_suffix": getattr(self.input_slot["item"], "enhanced_suffix", "")
            }

        # Serialize ingredient slot
        if self.ingredient_slot and self.ingredient_slot.get("item"):
            data['slots']['ingredient_slot'] = {
                "item_id": self.ingredient_slot["item"].id,
                "quantity": self.ingredient_slot["quantity"],
                "modifiers": getattr(self.ingredient_slot["item"], "modifiers", {}),
                "enhanced_suffix": getattr(self.ingredient_slot["item"], "enhanced_suffix", "")
            }

        print(f"[ENHANCER] Serializing state: {data}")
        return data

    def from_dict(self, data, item_registry):
        """Deserialize enhancer state"""
        if not data or 'slots' not in data:
            return

        slots_data = data['slots']
        
        # Load input slot
        if slots_data.get('input_slot'):
            slot_data = slots_data['input_slot']
            item_id = str(slot_data['item_id'])
            if item_id in item_registry:
                from copy import deepcopy
                item = deepcopy(item_registry[item_id])
                if slot_data.get('modifiers'):
                    item.modifiers = slot_data['modifiers']
                if slot_data.get('enhanced_suffix'):
                    item.enhanced_suffix = slot_data['enhanced_suffix']
                    item.name = f"{item.name} {slot_data['enhanced_suffix']}"
                self.input_slot = {
                    'item': item,
                    'quantity': slot_data['quantity']
                }

        # Load ingredient slot
        if slots_data.get('ingredient_slot'):
            slot_data = slots_data['ingredient_slot']
            item_id = str(slot_data['item_id'])
            if item_id in item_registry:
                from copy import deepcopy
                item = deepcopy(item_registry[item_id])
                if slot_data.get('modifiers'):
                    item.modifiers = slot_data['modifiers']
                if slot_data.get('enhanced_suffix'):
                    item.enhanced_suffix = slot_data['enhanced_suffix']
                    item.name = f"{item.name} {slot_data['enhanced_suffix']}"
                self.ingredient_slot = {
                    'item': item,
                    'quantity': slot_data['quantity']
                }

        print(f"[ENHANCER] Loaded state: input={self.input_slot}, ingredient={self.ingredient_slot}")
