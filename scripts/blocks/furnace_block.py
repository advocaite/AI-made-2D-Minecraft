from item import FUEL_ITEMS, MELTABLE_ITEMS

class BlockScript:
    def __init__(self, block):
        self.block = block
        # Initialize slots with proper dictionary structure
        self.input_slot = {"item": None, "quantity": 0}
        self.fuel_slot = {"item": None, "quantity": 0}
        self.output_slot = {"item": None, "quantity": 0}
        self.is_burning = False
        self.burn_time_remaining = 0
        self.melt_progress = 0

    def create_instance(self):
        """Create a new instance of the furnace script"""
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block

    def can_accept_fuel(self, item):
        """Check if item can be used as fuel"""
        # Check FUEL_ITEMS registry first, then item's burn_time attribute
        burn_time = FUEL_ITEMS.get(item.id, getattr(item, 'burn_time', 0))
        print(f"Checking fuel: {item.name}, burn_time from FUEL_ITEMS={FUEL_ITEMS.get(item.id)}, from item={getattr(item, 'burn_time', 0)}")
        return burn_time > 0

    def can_melt(self, item):
        """Check if item can be melted"""
        from item import MELTABLE_ITEMS
        print(f"Checking meltable: {item.name}")
        print(f"Available meltable items: {MELTABLE_ITEMS}")
        print(f"Item ID: {item.id}, Found in meltables: {item.id in MELTABLE_ITEMS}")
        return item.id in MELTABLE_ITEMS

    def update(self, dt):
        """Process furnace smelting"""
        print(f"\nFurnace Update:")
        if self.input_slot and self.input_slot.get("item"):
            print(f"Input: {self.input_slot['item'].name} x{self.input_slot['quantity']}")
            print(f"Can melt: {self.can_melt(self.input_slot['item'])}")
            if self.can_melt(self.input_slot['item']):
                from item import MELTABLE_ITEMS
                print(f"Melt result would be: {MELTABLE_ITEMS[self.input_slot['item'].id].name}")
        else:
            print("Input: Empty")
            
        if self.fuel_slot and self.fuel_slot.get("item"):
            print(f"Fuel: {self.fuel_slot['item'].name} x{self.fuel_slot['quantity']}")
        else:
            print("Fuel: Empty")
            
        print(f"Is burning: {self.is_burning}")
        print(f"Burn time remaining: {self.burn_time_remaining}")
        print(f"Melt progress: {self.melt_progress}")

        # Check for fuel and input
        if not (self.input_slot and self.input_slot.get("item")):
            print("No input - resetting furnace state")
            self.is_burning = False
            self.melt_progress = 0
            return

        # Start new burn cycle if needed
        if not self.is_burning:
            if not (self.fuel_slot and self.fuel_slot.get("item")):
                print("No fuel - waiting for fuel")
                return

            fuel_item = self.fuel_slot["item"]
            input_item = self.input_slot["item"]
            
            print(f"Checking new burn cycle:")
            print(f"Fuel: {fuel_item.name}, Input: {input_item.name}")
            
            if self.can_accept_fuel(fuel_item) and self.can_melt(input_item):
                melt_result = MELTABLE_ITEMS[input_item.id]
                print(f"Can melt {input_item.name} into {melt_result.name}")
                
                # Check if output slot allows for melting
                can_output = False
                if not self.output_slot or not self.output_slot.get("item"):
                    can_output = True
                    self.output_slot = {"item": None, "quantity": 0}
                    print("Output slot initialized")
                elif (self.output_slot["item"].id == melt_result.id and 
                      self.output_slot["quantity"] < self.output_slot["item"].stack_size):
                    can_output = True
                    print("Output slot can stack more items")
                
                if can_output:
                    self.is_burning = True
                    # Get burn time from either item or FUEL_ITEMS
                    self.burn_time_remaining = (
                        getattr(fuel_item, 'burn_time', 0) or 
                        FUEL_ITEMS.get(fuel_item.id, 0)
                    )
                    self.fuel_slot["quantity"] -= 1
                    if self.fuel_slot["quantity"] <= 0:
                        self.fuel_slot = {"item": None, "quantity": 0}
                    print(f"Started burning: time={self.burn_time_remaining}")

        # Process melting if burning
        if self.is_burning and self.input_slot.get("item"):
            self.burn_time_remaining -= dt
            self.melt_progress += dt
            print(f"Burning: progress={self.melt_progress}, remaining={self.burn_time_remaining}")

            if self.melt_progress >= 1000:  # 1 second to melt
                input_item = self.input_slot["item"]
                melt_result = MELTABLE_ITEMS[input_item.id]
                print(f"Melt complete: creating {melt_result.name}")
                
                # Create or update output slot
                if not self.output_slot or not self.output_slot.get("item"):
                    self.output_slot = {"item": melt_result, "quantity": 1}
                    print("Created new output stack")
                else:
                    self.output_slot["quantity"] += 1
                    print(f"Added to existing stack: now {self.output_slot['quantity']}")

                # Update input slot
                self.input_slot["quantity"] -= 1
                if self.input_slot["quantity"] <= 0:
                    self.input_slot = {"item": None, "quantity": 0}
                print("Consumed input item")

                self.melt_progress = 0

            # Check if burning should stop
            if self.burn_time_remaining <= 0:
                self.is_burning = False
                print("Burn cycle complete")

    def to_dict(self):
        """Convert furnace state to dictionary for saving"""
        data = {
            'input_slot': self._slot_to_dict(self.input_slot),
            'fuel_slot': self._slot_to_dict(self.fuel_slot),
            'output_slot': self._slot_to_dict(self.output_slot),
            'is_burning': self.is_burning,
            'burn_time_remaining': self.burn_time_remaining,
            'melt_progress': self.melt_progress
        }
        print(f"Saving furnace state: {data}")  # Debug output
        return data

    def from_dict(self, data, item_registry):
        """Load furnace state from dictionary"""
        print(f"Loading furnace data: {data}")  # Debug output
        
        # Initialize empty slots
        self.input_slot = {"item": None, "quantity": 0}
        self.fuel_slot = {"item": None, "quantity": 0}
        self.output_slot = {"item": None, "quantity": 0}
        
        # Load state
        if data.get('input_slot'):
            self.input_slot = self._dict_to_slot(data['input_slot'], item_registry) or self.input_slot
        if data.get('fuel_slot'):
            self.fuel_slot = self._dict_to_slot(data['fuel_slot'], item_registry) or self.fuel_slot
        if data.get('output_slot'):
            self.output_slot = self._dict_to_slot(data['output_slot'], item_registry) or self.output_slot
        
        self.is_burning = data.get('is_burning', False)
        self.burn_time_remaining = data.get('burn_time_remaining', 0)
        self.melt_progress = data.get('melt_progress', 0)
        
        print(f"Loaded furnace state:")
        print(f"Input: {self.input_slot.get('item').name if self.input_slot.get('item') else 'None'}")
        print(f"Fuel: {self.fuel_slot.get('item').name if self.fuel_slot.get('item') else 'None'}")
        print(f"Output: {self.output_slot.get('item').name if self.output_slot.get('item') else 'None'}")

    def _slot_to_dict(self, slot):
        """Helper to serialize a slot"""
        if slot and slot.get("item") and slot["item"] is not None:
            print(f"Saving slot with item: {slot['item'].name} x{slot['quantity']}")  # Debug
            return {
                'item_id': str(slot['item'].id),  # Convert ID to string
                'quantity': slot['quantity']
            }
        return None

    def _dict_to_slot(self, slot_data, item_registry):
        """Helper to deserialize a slot"""
        if slot_data and 'item_id' in slot_data:
            item_id = str(slot_data['item_id'])  # Ensure ID is string
            print(f"Looking up item ID: {item_id} in registry")  # Debug
            item = item_registry.get(item_id)
            if item:
                print(f"Found item: {item.name}")  # Debug
                return {
                    'item': item,
                    'quantity': slot_data['quantity']
                }
            else:
                print(f"Item not found for ID: {item_id}")  # Debug
        return {"item": None, "quantity": 0}
