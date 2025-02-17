import json
import os
import time
from block import (
    BLOCK_MAP, ENHANCER,
    StorageBlock, FurnaceBlock, EnhancerBlock
)
from item import ITEM_REGISTRY  # Just import ITEM_REGISTRY directly

class SaveManager:
    def __init__(self, seed=None):
        self.seed = seed
        self.save_dir = "saves"
        if self.seed is not None:
            self.save_dir = os.path.join("saves", f"world_{self.seed}")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.world_file = os.path.join(self.save_dir, "world.json")
        self.player_file = os.path.join(self.save_dir, "player.json")
        
        # Use ITEM_REGISTRY directly and add block variants
        self.item_registry = {}  # Start with empty registry
        
        # Add valid items from ITEM_REGISTRY
        for item_id, item in ITEM_REGISTRY.items():
            if item is not None:  # Only add non-None items
                self.item_registry[item_id] = item
        
        # Add block item variants
        for block_id, block in BLOCK_MAP.items():
            if hasattr(block, 'item_variant') and block.item_variant is not None:
                self.item_registry[block_id] = block.item_variant

        # Add debug output
        print("Initialized item registry with:")
        for item_id, item in self.item_registry.items():
            if item:  # Double-check item is not None
                print(f"ID: {item_id}, Item: {item.name}")

    def load_world_chunk(self, chunk_data, block_map):
        """Helper function to properly load chunk data"""
        new_chunk = []
        for row in chunk_data:
            new_row = []
            for block_id in row:
                # If it's a dict, it's a special block that needs to be instantiated
                if isinstance(block_id, dict):
                    block_type = block_map[block_id['id']]
                    block = block_type.create_instance()
                    block.from_dict(block_id, self.item_registry)  # Now self is accessible
                else:
                    # For simple blocks, just reference them directly from block_map
                    block = block_map[block_id]
                new_row.append(block)
            new_chunk.append(new_row)
        return new_chunk

    def save_world(self, world_chunks):
        # Convert each chunk to a grid of block IDs for serialization.
        serializable = {}
        for ci, chunk in world_chunks.items():
            serializable[ci] = [[block.id if block else 0 for block in row] for row in chunk]
        with open(self.world_file, "w") as f:
            json.dump(serializable, f)
        print(f"World saved to {self.world_file}.")

    def load_world(self, block_map):
        if os.path.exists(self.world_file):
            with open(self.world_file, "r") as f:
                data = json.load(f)
            loaded_chunks = {}
            for ci, grid in data.items():
                # Reconstruct chunk using block_map to obtain Block objects by their id.
                loaded_chunks[int(ci)] = [[block_map.get(block_id) for block_id in row] for row in grid]
            return loaded_chunks
        return None

    def _slot_to_dict(self, slot):
        if not slot or "item" not in slot or not slot["item"]:
            return {"item_id": 0, "quantity": 0}
        quantity = slot.get("quantity", 1)
        return {
            "item_id": slot["item"].id,
            "quantity": quantity
        }

    def _dict_to_slot(self, slot_data, item_map):
        if not slot_data or slot_data["item_id"] == 0:
            return {"item": None, "quantity": 0}
        item_id = slot_data.get("item_id")
        quantity = slot_data.get("quantity", 1)
        item_obj = item_map.get(item_id)
        if item_obj:
            return {
                "item": item_obj,
                "quantity": quantity
            }
        return {"item": None, "quantity": 0}

    def save_player(self, player, inventory):
        # Save key player properties and inventory.
        player_data = {
            "x": player.rect.x,
            "y": player.rect.y,
            "health": player.health,
            "hunger": player.hunger,
            "thirst": player.thirst
            # ... add other player properties if needed...
        }
        inv_data = {
            "hotbar": [self._slot_to_dict(slot) for slot in inventory.hotbar],
            "armor": [self._slot_to_dict(slot) for slot in inventory.armor],
            "main": [self._slot_to_dict(slot) for slot in inventory.main],
            "selected_hotbar_index": inventory.selected_hotbar_index
        }
        data = {
            "player": player_data,
            "inventory": inv_data
        }
        with open(self.player_file, "w") as f:
            json.dump(data, f)
        print(f"Player data saved to {self.player_file}.")
        print("Current hotbar items:")
        for idx, slot in enumerate(inventory.hotbar):
            if slot and "item" in slot and slot["item"]:
                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
            else:
                print(f"Slot {idx}: Empty slot")
        print("Current armor items:")
        for idx, slot in enumerate(inventory.armor):
            if slot and "item" in slot and slot["item"]:
                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
            else:
                print(f"Slot {idx}: Empty slot")
        print("Current main items:")
        for idx, slot in enumerate(inventory.main):
            if slot and "item" in slot and slot["item"]:
                print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
            else:
                print(f"Slot {idx}: Empty slot")

    def load_player(self, item_map):
        if os.path.exists(self.player_file):
            print(f"Loading player data from {self.player_file}.")
            with open(self.player_file, "r") as f:
                data = json.load(f)
            if data:
                inv = data.get("inventory", {})
                if inv:
                    inv["hotbar"] = [self._dict_to_slot(slot, item_map) for slot in inv.get("hotbar", [])]
                    inv["armor"] = [self._dict_to_slot(slot, item_map) for slot in inv.get("armor", [])]
                    inv["main"] = [self._dict_to_slot(slot, item_map) for slot in inv.get("main", [])]
                data["inventory"] = inv
                print("Loaded hotbar items:")
                for idx, slot in enumerate(inv.get("hotbar", [])):
                    if slot and "item" in slot and slot["item"]:
                        print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                    else:
                        print(f"Slot {idx}: Empty slot")
                print("Loaded armor items:")
                for idx, slot in enumerate(inv.get("armor", [])):
                    if slot and "item" in slot and slot["item"]:
                        print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                    else:
                        print(f"Slot {idx}: Empty slot")
                print("Loaded main items:")
                for idx, slot in enumerate(inv.get("main", [])):
                    if slot and "item" in slot and slot["item"]:
                        print(f"Slot {idx}: Item: {slot['item'].name}, Quantity: {slot['quantity']}")
                    else:
                        print(f"Slot {idx}: Empty slot")
            return data
        else:
            print(f"Player file {self.player_file} does not exist.")
        return None

    def save_all(self, world_chunks, player, inventory):
        """Save both world and player data"""
        # Create save data structure
        world_data = {
            'metadata': {
                'seed': self.seed,
                'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
            },
            'chunks': self.serialize_world(world_chunks)
        }

        player_data = {
            'metadata': {
                'seed': self.seed,
                'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
            },
            'player': {
                'x': player.rect.x,
                'y': player.rect.y,
                'health': player.health,
                'hunger': player.hunger,
                'thirst': player.thirst
            },
            'inventory': self.serialize_inventory(inventory)
        }

        # Save to files with consistent naming
        world_file = os.path.join(self.save_dir, f'world_{self.seed}.json')
        player_file = os.path.join(self.save_dir, f'player_{self.seed}.json')
        
        with open(world_file, 'w') as f:
            json.dump(world_data, f)
        with open(player_file, 'w') as f:
            json.dump(player_data, f)
            
        print(f"Saved world to {world_file}")
        print(f"Saved player data to {player_file}")

    def serialize_inventory(self, inventory):
        """Convert inventory to serializable format"""
        def serialize_slot(slot):
            # Return explicit None if slot is empty
            if not slot or not slot.get('item'):
                return {
                    'item_id': 0,
                    'quantity': 0,
                    'is_empty': True
                }
            
            item = slot['item']
            # Create base item data
            item_data = {
                'item_id': item.id,
                'quantity': slot['quantity'],
                'name': item.name,
                'is_block': getattr(item, 'is_block', False),
                'texture_coords': item.texture_coords,
                'type': getattr(item, 'type', None),
                'stack_size': getattr(item, 'stack_size', 64),
                'is_empty': False
            }
            
            # Add special properties
            if hasattr(item, 'modifiers'):
                item_data['modifiers'] = item.modifiers
            if hasattr(item, 'enhanced_suffix'):
                item_data['enhanced_suffix'] = item.enhanced_suffix
            if hasattr(item, 'burn_time'):
                item_data['burn_time'] = item.burn_time

            return item_data

        return {
            'hotbar': [serialize_slot(slot) for slot in inventory.hotbar],
            'armor': [serialize_slot(slot) for slot in inventory.armor],
            'main': [serialize_slot(slot) for slot in inventory.main],
            'selected_hotbar_index': inventory.selected_hotbar_index
        }

    def deserialize_inventory(self, inv_data):
        """Convert saved inventory data back to inventory format"""
        def deserialize_slot(slot_data):
            # Always return a valid slot dictionary
            if not slot_data or slot_data.get('is_empty', True):
                return {"item": None, "quantity": 0}

            item_id = slot_data['item_id']
            if item_id in self.item_registry:
                base_item = self.item_registry[item_id]
                
                # Create new instance
                new_item = type(base_item)(
                    id=item_id,
                    name=slot_data['name'],
                    texture_coords=slot_data['texture_coords'],
                    stack_size=slot_data.get('stack_size', 64),
                    is_block=slot_data.get('is_block', False)
                )

                # Restore special properties
                if 'modifiers' in slot_data:
                    new_item.modifiers = slot_data['modifiers']
                if 'enhanced_suffix' in slot_data:
                    new_item.enhanced_suffix = slot_data['enhanced_suffix']
                    if slot_data['enhanced_suffix']:
                        new_item.name = f"{new_item.name} {new_item.enhanced_suffix}"
                if 'burn_time' in slot_data:
                    new_item.burn_time = slot_data['burn_time']
                if 'type' in slot_data and slot_data['type']:
                    new_item.type = slot_data['type']

                # Important: For block items, make sure to set the block reference
                if slot_data.get('is_block') and hasattr(base_item, 'block'):
                    new_item.block = base_item.block
                    
                return {
                    "item": new_item,
                    "quantity": slot_data['quantity']
                }
            print(f"Warning: Unknown item ID {item_id}")
            return {"item": None, "quantity": 0}

        # Make sure we preserve all slots, even empty ones
        return {
            'hotbar': [deserialize_slot(slot) for slot in inv_data['hotbar']],
            'armor': [deserialize_slot(slot) for slot in inv_data['armor']],
            'main': [deserialize_slot(slot) for slot in inv_data['main']],
            'selected_hotbar_index': inv_data['selected_hotbar_index']
        }

    def _serialize_inventory(self, slots):
        """Convert inventory slots to serializable format"""
        serialized = []
        for slot in slots:
            if slot and slot.get("item"):
                # Include any enhancement data if present
                modifiers = {}
                enhanced_suffix = ""
                if hasattr(slot["item"], "modifiers"):
                    modifiers = slot["item"].modifiers
                if hasattr(slot["item"], "enhanced_suffix"):
                    enhanced_suffix = slot["item"].enhanced_suffix
                
                serialized.append({
                    "item_id": slot["item"].id,
                    "quantity": slot["quantity"],
                    "modifiers": modifiers,
                    "enhanced_suffix": enhanced_suffix
                })
            else:
                serialized.append(None)
        return serialized

    def _deserialize_inventory(self, slots):
        """Convert serialized inventory data back to proper format"""
        deserialized = []
        for slot_data in slots:
            if slot_data is None:
                deserialized.append(None)
            else:
                item_id = slot_data["item_id"]
                if item_id in self.item_registry:
                    item = self.item_registry[item_id]
                    # Create a new instance for items that might have state
                    if hasattr(item, "__dict__"):
                        item = type(item)(item.id, item.name, item.texture_coords)
                    
                    # Apply any saved enhancements
                    if "modifiers" in slot_data:
                        item.modifiers = slot_data["modifiers"]
                    if "enhanced_suffix" in slot_data and slot_data["enhanced_suffix"]:
                        item.enhanced_suffix = slot_data["enhanced_suffix"]
                        item.name = f"{item.name} {item.enhanced_suffix}"
                    
                    deserialized.append({
                        "item": item,
                        "quantity": slot_data["quantity"]
                    })
                else:
                    print(f"Warning: Unknown item ID {item_id}")
                    deserialized.append(None)
        return deserialized

    def serialize_world(self, world_chunks):
        """Convert world chunks to serializable format"""
        serialized = {}
        for ci, chunk in world_chunks.items():
            chunk_data = []
            for row in chunk:
                row_data = []
                for block in row:
                    if isinstance(block, (StorageBlock, FurnaceBlock, EnhancerBlock)):
                        # Special blocks need their state saved
                        block_data = block.to_dict()
                        row_data.append(block_data)
                    else:
                        # Regular blocks just save their ID
                        row_data.append(block.id)
                chunk_data.append(row_data)
            serialized[str(ci)] = chunk_data
        return serialized

    def deserialize_world(self, world_data, block_map):
        """Convert serialized world data back to chunks"""
        deserialized = {}
        for ci_str, chunk_data in world_data.items():
            ci = int(ci_str)
            chunk = []
            for row in chunk_data:
                new_row = []
                for block_data in row:
                    if isinstance(block_data, dict):
                        # Special block with saved state
                        block_id = block_data['id']
                        block = block_map[block_id].create_instance()
                        block.from_dict(block_data, self.item_registry)
                        new_row.append(block)
                    else:
                        # Regular block
                        new_row.append(block_map[block_data])
                chunk.append(new_row)
            deserialized[ci] = chunk
        return deserialized

    def load_all(self, block_map):
        """Load both world and player data"""
        try:
            world_file = os.path.join(self.save_dir, f'world_{self.seed}.json')
            player_file = os.path.join(self.save_dir, f'player_{self.seed}.json')
            
            if not os.path.exists(world_file) or not os.path.exists(player_file):
                print(f"Save files not found: {world_file} or {player_file}")
                return None, None

            print(f"Loading world from {world_file}")
            with open(world_file, 'r') as f:
                world_data = json.load(f)

            print(f"Loading player from {player_file}")
            with open(player_file, 'r') as f:
                player_data = json.load(f)

            # Verify seeds match
            world_seed = world_data.get('metadata', {}).get('seed')
            player_seed = player_data.get('metadata', {}).get('seed')
            
            if world_seed != self.seed or player_seed != self.seed:
                print(f"Warning: Seed mismatch. World: {world_seed}, Player: {player_seed}, Current: {self.seed}")

            # Get chunks from world data
            world_chunks = self.deserialize_world(world_data['chunks'], block_map)
            
            # Get inventory from player data
            if 'inventory' in player_data:
                player_data['inventory'] = self.deserialize_inventory(player_data['inventory'])
            
            print("World and player data loaded successfully")
            return world_chunks, player_data
            
        except Exception as e:
            print(f"Error loading save data: {e}")
            import traceback
            traceback.print_exc()
            return None, None
