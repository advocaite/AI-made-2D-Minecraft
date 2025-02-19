class Registry:
    def __init__(self):
        self.blocks = {}
        self.items = {}
        
        # Create base items dictionary
        self.items = {}
        
        # Load items from JSON files first
        from item_loader import ItemLoader
        self.item_loader = ItemLoader()
        self.item_loader.load_items()
        
        # Add loaded items to registry
        self.items.update(self.item_loader.items)
        
        print("[REGISTRY] Initialized with items:", list(self.items.keys()))
    
    def register_block(self, block):
        """Register a block and return it"""
        if isinstance(block, str):
            # Handle string IDs by returning the actual block
            registered_block = self.blocks.get(block)
            if registered_block:
                return registered_block
            # Try converting numeric ID to string
            registered_block = self.blocks.get(str(block))
            if registered_block:
                return registered_block
            return None

        # Create item variant if it doesn't exist
        if not hasattr(block, 'item_variant') or block.item_variant is None:
            from item import Item
            item_variant = Item(
                id=block.id,
                name=block.name,
                texture_coords=block.texture_coords,
                stack_size=64,
                is_block=True
            )
            item_variant.block = block
            block.item_variant = item_variant
            block.drop_item = item_variant
            # Register the item variant in items registry
            self.items[str(item_variant.id)] = item_variant
            print(f"Created and registered item variant for {block.name}")

        self.blocks[str(block.id)] = block
        return block

    def register_item(self, item):
        """Register an item and return it"""
        self.items[str(item.id)] = item
        return item

    def register_meltable(self, item_id, result):
        """Register a meltable item"""
        self.meltable_items[item_id] = result

    def register_fuel(self, item_id, burn_time):
        """Register a fuel item"""
        self.fuel_items[item_id] = burn_time

    def get_block(self, block_id):
        """Get a block by ID"""
        if isinstance(block_id, (int, str)):
            return self.blocks.get(str(block_id))
        return None

    def get_item(self, item_id):
        """Get an item by ID or name"""
        if isinstance(item_id, str):
            # Try direct lookup first
            item = self.items.get(item_id)
            if item:
                return item
                
            # Try numeric ID
            item = self.items.get(str(item_id))
            if item:
                return item
                
            # Try case-insensitive name search
            for key, value in self.items.items():
                if value.name.upper() == item_id.upper():
                    return value
                    
        print(f"[REGISTRY] Warning: Item '{item_id}' not found")
        print(f"[REGISTRY] Available items: {list(self.items.keys())}")
        return None

# Create global registry instance
REGISTRY = Registry()
