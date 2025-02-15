class CommandManager:
    def __init__(self):
        pass  # no initialization needed for now

    def execute_command(self, command_str, player, inventory):
        tokens = command_str.strip().split()
        if not tokens:
            return
        cmd = tokens[0].lower()
        if cmd == "teleport":
            try:
                x = int(tokens[1])
                y = int(tokens[2])
                player.rect.x = x
                player.rect.y = y
                print(f"Teleported player to {x}, {y}")
            except Exception:
                print("Usage: teleport <x> <y>")
        elif cmd == "spawn_item":
            try:
                # Try to interpret token as an integer id; if not, use it as an item name.
                try:
                    key = int(tokens[1])
                except ValueError:
                    key = tokens[1].upper()
                quantity = int(tokens[2]) if len(tokens) > 2 else 1
                # Import a few items for lookup
                from item import ITEM_PICKAXE, ITEM_SWORD, ITEM_AXE, APPLE, WATER_BOTTLE
                # Build mapping by both id and name.
                item_map = {
                    ITEM_PICKAXE.id: ITEM_PICKAXE,
                    ITEM_SWORD.id: ITEM_SWORD,
                    ITEM_AXE.id: ITEM_AXE,
                    APPLE.id: APPLE,
                    WATER_BOTTLE.id: WATER_BOTTLE,
                    "PICKAXE": ITEM_PICKAXE,
                    "SWORD": ITEM_SWORD,
                    "AXE": ITEM_AXE,
                    "APPLE": APPLE,
                    "WATER_BOTTLE": WATER_BOTTLE
                }
                if key in item_map:
                    inventory.add_item(item_map[key], quantity)
                    print(f"Spawned {quantity} of {item_map[key].name}")
                else:
                    print("Item id/name not recognized.")
            except Exception:
                print("Usage: spawn_item <item_id|item_name> <quantity>")
        else:
            print("Unknown command")
