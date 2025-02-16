import json
import os

class SaveManager:
    def __init__(self, seed):
        self.seed = seed
        self.save_dir = os.path.join(os.getcwd(), "saves")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.world_file = os.path.join(self.save_dir, f"world_{self.seed}.json")
        self.player_file = os.path.join(self.save_dir, f"player_{self.seed}.json")

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
        world_data = {}
        for chunk_index, chunk in world_chunks.items():
            chunk_data = []
            for row in chunk:
                row_data = []
                for block in row:
                    if hasattr(block, 'to_dict'):
                        # Save special block data (Storage, Furnace)
                        row_data.append(block.to_dict())
                    else:
                        # Save regular block
                        row_data.append(block.id if block else 0)
                chunk_data.append(row_data)
            world_data[str(chunk_index)] = chunk_data

        with open(self.world_file, 'w') as f:
            json.dump(world_data, f)

        # Save player data
        self.save_player(player, inventory)

    def load_all(self, block_map):
        """Load both world and player data"""
        try:
            # Load world data
            if not os.path.exists(self.world_file):
                print(f"World file not found: {self.world_file}")
                return None, None

            with open(self.world_file, 'r') as f:
                world_data = json.load(f)

            from item import MELTABLE_ITEMS, FUEL_ITEMS, Item  # Get item registry
            from block import BLOCK_MAP  # Get block registry
            # Combine all item registries
            item_registry = {}
            item_registry.update(MELTABLE_ITEMS)
            item_registry.update(FUEL_ITEMS)
            # Add block items to registry
            for block_id, block in BLOCK_MAP.items():
                if hasattr(block, 'item_variant'):
                    item_registry[block_id] = block.item_variant

            loaded_chunks = {}
            for chunk_index_str, chunk_data in world_data.items():
                chunk_index = int(chunk_index_str)
                chunk = []
                for row in chunk_data:
                    new_row = []
                    for block_data in row:
                        if isinstance(block_data, dict):
                            # Load special block data (Storage, Furnace)
                            block_id = block_data['id']
                            block = block_map[block_id].create_instance()
                            block.from_dict(block_data, item_registry)
                            new_row.append(block)
                        else:
                            # Load regular block
                            new_row.append(block_map[block_data])
                    chunk.append(new_row)
                loaded_chunks[chunk_index] = chunk

            # Load player data
            player_data = self.load_player(item_registry)

            return loaded_chunks, player_data

        except Exception as e:
            print(f"Error loading game data: {e}")
            return None, None

    # ...rest of existing code...
