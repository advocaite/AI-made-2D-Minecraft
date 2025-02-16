import json
import os
import time
from block import (
    BLOCK_MAP, ENHANCER,
    StorageBlock, FurnaceBlock, EnhancerBlock  # Add direct imports for block types
)
from item import (  # Add item imports
    IRON_INGOT, GOLD_INGOT, IRON_HELMET, IRON_CHESTPLATE,
    IRON_LEGGINGS, IRON_BOOTS, IRON_SWORD, IRON_PICKAXE,
    IRON_AXE, IRON_SHOVEL, COAL
)

class SaveManager:
    def __init__(self, seed=None):
        self.seed = seed
        self.save_dir = "saves"
        # Create a seed-specific directory
        if self.seed is not None:
            self.save_dir = os.path.join("saves", f"world_{self.seed}")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        # Create item registry for loading
        self.item_registry = {
            # Block items will be added automatically from BLOCK_MAP
            # Add crafted/smelted items
            200: IRON_INGOT,
            201: GOLD_INGOT,
            202: COAL,
            # Add tools and armor
            30: IRON_HELMET,
            31: IRON_CHESTPLATE,
            32: IRON_LEGGINGS,
            33: IRON_BOOTS,
            40: IRON_SWORD,
            41: IRON_PICKAXE,
            42: IRON_AXE,
            43: IRON_SHOVEL,
            # Add enhancer by ID and name
            25: ENHANCER.item_variant,
            "ENHANCER": ENHANCER.item_variant,
        }
        
        # Add block item variants to registry
        for block_id, block in BLOCK_MAP.items():
            if hasattr(block, 'item_variant'):
                self.item_registry[block_id] = block.item_variant

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
        # Create seed-specific metadata
        metadata = {
            "seed": self.seed,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Prepare world data with metadata
        world_data = {
            "metadata": metadata,
            "chunks": {}
        }

        # Add chunks to world data with proper block serialization
        for ci, chunk in world_chunks.items():
            chunk_data = []
            for row in chunk:
                row_data = []
                for block in row:
                    if hasattr(block, 'to_dict'):  # Special blocks like Storage/Furnace/Enhancer
                        block_dict = block.to_dict()
                        # Ensure block maintains its ID in serialization
                        if not "id" in block_dict:
                            block_dict["id"] = block.id
                        row_data.append(block_dict)
                    else:
                        row_data.append(block.id)
                chunk_data.append(row_data)
            world_data["chunks"][str(ci)] = chunk_data

        # Save player data with the same metadata
        player_data = {
            "metadata": metadata,
            "player": {
                "x": player.rect.x,
                "y": player.rect.y,
                "health": player.health,
                "hunger": player.hunger,
                "thirst": player.thirst
            },
            "inventory": {
                "hotbar": self._serialize_inventory(inventory.hotbar),
                "main": self._serialize_inventory(inventory.main),
                "armor": self._serialize_inventory(inventory.armor),
                "selected_hotbar_index": inventory.selected_hotbar_index
            }
        }

        # Save to seed-specific files
        world_file = os.path.join(self.save_dir, "world.json")
        player_file = os.path.join(self.save_dir, "player.json")
        
        with open(world_file, "w") as f:
            json.dump(world_data, f)
        with open(player_file, "w") as f:
            json.dump(player_data, f)
        
        print(f"Saved world with seed {self.seed} to {self.save_dir}")

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

    def load_all(self, block_map):
        try:
            world_file = os.path.join(self.save_dir, "world.json")
            player_file = os.path.join(self.save_dir, "player.json")

            world_chunks = {}
            if os.path.exists(world_file):
                with open(world_file, "r") as f:
                    world_data = json.load(f)
                    # Verify seed matches
                    saved_seed = world_data.get("metadata", {}).get("seed")
                    if saved_seed != self.seed:
                        print(f"Warning: Loading world with seed {saved_seed}, but current seed is {self.seed}")
                    
                    # Load chunks
                    for ci_str, chunk_data in world_data.get("chunks", {}).items():
                        ci = int(ci_str)
                        chunk = []
                        for row in chunk_data:
                            new_row = []
                            for block_data in row:
                                if isinstance(block_data, dict):  # Special block
                                    block_id = block_data["id"]
                                    block = block_map[block_id].create_instance()
                                    # Enhanced debugging for special blocks
                                    print(f"Loading special block ID {block_id}: {block_data}")
                                    print(f"Block type: {type(block)}")  # Add type debugging
                                    block.from_dict(block_data, self.item_registry)
                                    print(f"Block loaded: {block.name}")
                                    # Additional debug for enhancer blocks
                                    if isinstance(block, EnhancerBlock):
                                        print(f"Enhancer slots after loading:")
                                        print(f"Input: {block.input_slot}")
                                        print(f"Ingredient: {block.ingredient_slot}")
                                else:
                                    block = block_map[block_data]
                                new_row.append(block)
                            chunk.append(new_row)
                        world_chunks[ci] = chunk

            # Load player data
            player_data = None
            if os.path.exists(player_file):
                with open(player_file, "r") as f:
                    player_data = json.load(f)
                    if "inventory" in player_data:
                        # Convert serialized inventory data back to proper format
                        player_data["inventory"]["hotbar"] = self._deserialize_inventory(
                            player_data["inventory"]["hotbar"]
                        )
                        player_data["inventory"]["main"] = self._deserialize_inventory(
                            player_data["inventory"]["main"]
                        )
                        player_data["inventory"]["armor"] = self._deserialize_inventory(
                            player_data["inventory"]["armor"]
                        )

            return world_chunks, player_data
        except Exception as e:
            print(f"Error loading save data: {e}")
            return None, None

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
