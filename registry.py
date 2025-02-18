class Registry:
    def __init__(self):
        self.blocks = {}
        self.items = {}
        self.meltable_items = {}
        self.fuel_items = {}

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
        """Get an item by ID"""
        return self.items.get(str(item_id))

# Create global registry instance
REGISTRY = Registry()
