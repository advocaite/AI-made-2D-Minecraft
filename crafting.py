import json
from item import Item
from block import BLOCK_MAP, STORAGE  # Import STORAGE block

class Crafting:
    def __init__(self, recipe_file="recipes.json"):
        self.recipes = self.load_recipes(recipe_file)
    
    def load_recipes(self, recipe_file):
        with open(recipe_file, "r") as f:
            return json.load(f)
    
    def craft_item(self, inventory, recipe_key):
        recipe = self.recipes.get(recipe_key)
        if not recipe:
            print("Recipe not found.")
            return None

        # Check ingredients
        available = {}
        for container in (inventory.hotbar, inventory.armor, inventory.main):
            for slot in container:
                if slot and slot["item"]:
                    item_id = slot["item"].id
                    available[item_id] = available.get(item_id, 0) + slot["quantity"]

        # Verify all ingredients are available
        for ingredient in recipe["ingredients"]:
            req_id = ingredient["item_id"]
            req_qty = ingredient["quantity"]
            if available.get(req_id, 0) < req_qty:
                print("Not enough ingredients for", recipe_key)
                return None

        # Remove ingredients
        for ingredient in recipe["ingredients"]:
            req_id = ingredient["item_id"]
            req_qty = ingredient["quantity"]
            for container in (inventory.hotbar, inventory.armor, inventory.main):
                for slot in container:
                    if req_qty <= 0:
                        break
                    if slot and slot["item"] and slot["item"].id == req_id:
                        take = min(slot["quantity"], req_qty)
                        slot["quantity"] -= take
                        req_qty -= take
                        if slot["quantity"] <= 0:
                            slot["item"] = None
                if req_qty <= 0:
                    break

        # Create result item
        result = recipe["result"]
        
        # Special handling for storage block
        if result["item_id"] == 23:  # Storage block ID
            block = STORAGE.create_instance()  # Create new storage instance
            crafted_item = block.item_variant
        else:
            # Normal item creation
            crafted_item = Item(
                result["item_id"],
                result["name"],
                tuple(result["texture_coords"]),
                result.get("stack_size", 1),
                result.get("is_block", False)
            )
            # If it's a block item, associate with corresponding block
            if result.get("is_block", False) and result["item_id"] in BLOCK_MAP:
                crafted_item.block = BLOCK_MAP[result["item_id"]]

        return crafted_item
