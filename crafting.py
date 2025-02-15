import json
from item import Item

class Crafting:
    def __init__(self, recipe_file="recipes.json"):
        self.recipes = self.load_recipes(recipe_file)
    
    def load_recipes(self, recipe_file):
        with open(recipe_file, "r") as f:
            return json.load(f)
    
    def craft_item(self, inventory, recipe_key):
        # Get the recipe by key (e.g., "pickaxe")
        recipe = self.recipes.get(recipe_key)
        if not recipe:
            print("Recipe not found.")
            return None
        # Check if inventory has all required ingredients.
        # This is a simplified check; real logic should iterate through all containers.
        available = {}
        for container in (inventory.hotbar, inventory.armor, inventory.main):
            for slot in container:
                if slot and slot["item"]:
                    item_id = slot["item"].id
                    available[item_id] = available.get(item_id, 0) + slot["quantity"]
        for ingredient in recipe["ingredients"]:
            req_id = ingredient["item_id"]
            req_qty = ingredient["quantity"]
            if available.get(req_id, 0) < req_qty:
                print("Not enough ingredients for", recipe_key)
                return None
        # Remove ingredients from inventory.
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
        # Create the resulting item.
        result = recipe["result"]
        crafted_item = Item(
            result["item_id"],
            result["name"],
            tuple(result["texture_coords"]),
            result.get("stack_size", 1),
            result.get("is_block", False)
        )
        return crafted_item
