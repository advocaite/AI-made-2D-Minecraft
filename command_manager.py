import config as c
from block_loader import BlockLoader
from item import ITEM_REGISTRY  # Add this to access items

class CommandManager:
    def __init__(self, game=None):
        self.game = game
        self.inventory = None
        self.block_loader = BlockLoader()
        self.blocks = self.block_loader.load_blocks()
        self.items = ITEM_REGISTRY  # Add access to item registry
        print("Available items:", [item_id for item_id in self.items.keys()])

    def execute_command(self, command_str, player, inventory, mobs):
        """Handle command execution"""
        self.inventory = inventory
        tokens = command_str.strip().split()
        if not tokens:
            return

        cmd = tokens[0].lower()
        
        if cmd == "spawn_item":
            self.handle_spawn_item(tokens[1:])
        elif cmd == "teleport":
            try:
                x = int(tokens[1])
                y = int(tokens[2])
                player.rect.x = x
                player.rect.y = y
                print(f"[INFO] Teleported player to {x}, {y}")
            except Exception as e:
                print("[ERROR] Teleport command failed. Exception:", e)
                print("Usage: teleport <x> <y>")
        elif cmd == "setweather":
            # Let Console handle this command.
            return
        elif cmd == "spawn_entity":
            try:
                entity_type = tokens[1]
                if len(tokens) > 3:
                    x = int(tokens[2])
                    y = int(tokens[3])
                else:
                    # Calculate spawn position based on player's facing direction
                    x = player.rect.x + (5 * c.BLOCK_SIZE if player.facing == "right" else -5 * c.BLOCK_SIZE)
                    y = player.rect.y
                print(f"[DEBUG] Spawning entity. Type: {entity_type}, x: {x}, y: {y}")
                if entity_type.lower() == "mob":
                    from mob import Mob
                    entity = Mob(x, y)
                    print(f"[DEBUG] Created entity: {entity}")
                else:
                    print("[WARN] Entity type not recognized:", entity_type)
                    return
                mobs.append(entity)
                print(f"[INFO] Spawned entity '{entity_type}' at {x}, {y}")
            except Exception as e:
                print("[ERROR] Spawn entity command failed. Exception:", e)
                print("Usage: spawn_entity <entity_type> [<x> <y>]")
        else:
            print("[WARN] Unknown command:", cmd)

    def handle_spawn_item(self, args):
        if len(args) < 2:
            print("Usage: spawn_item <item_id|item_name> <quantity>")
            return False

        item_id = args[0].upper()
        try:
            quantity = int(args[1])
        except ValueError:
            print("Quantity must be a number")
            return False

        print(f"Looking for item: {item_id}")
        print(f"Available item IDs: {list(self.items.keys())}")
        print(f"Available item names: {[item.name for item in self.items.values()]}")

        # Try to find item by ID or name
        found_item = None
        
        # Check direct item ID match
        if item_id in self.items:
            found_item = self.items[item_id]
        else:
            # Try to find by name
            for registry_item in self.items.values():
                if (registry_item.name.upper() == item_id or 
                    registry_item.name.upper().replace(" ", "_") == item_id):
                    found_item = registry_item
                    break

        if found_item:
            if self.inventory:
                self.inventory.add_item(found_item, quantity)
                print(f"Spawned {quantity}x {found_item.name}")
                return True
            return False

        # If not found in items, try blocks (existing block lookup code)
        for block in self.blocks.values():
            if (str(block.id) == item_id or 
                block.name.upper() == item_id or 
                block.name.upper().replace(" ", "_") == item_id):
                if block.item_variant:
                    if self.inventory:
                        self.inventory.add_item(block.item_variant, quantity)
                        print(f"Spawned {quantity}x {block.name}")
                        return True
                break

        print(f"Item '{item_id}' not found")
        return False
