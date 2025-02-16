import config as c  # Add this import

class CommandManager:
    def __init__(self):
        pass  # no initialization needed for now

    def execute_command(self, command_str, player, inventory, mobs):
        tokens = command_str.strip().split()
        print("[DEBUG] Received command:", command_str)
        print("[DEBUG] Tokens:", tokens)
        if not tokens:
            return
        # Combine "spawn entity" into "spawn_entity" if applicable.
        if len(tokens) >= 2 and tokens[0].lower() == "spawn" and tokens[1].lower() == "entity":
            tokens[0] = "spawn_entity"
            tokens = [tokens[0]] + tokens[2:]
            print("[DEBUG] Combined 'spawn entity' into 'spawn_entity'. Tokens now:", tokens)
        cmd = tokens[0].lower()
        print("[DEBUG] Processing command:", cmd)
        if cmd == "teleport":
            try:
                x = int(tokens[1])
                y = int(tokens[2])
                player.rect.x = x
                player.rect.y = y
                print(f"[INFO] Teleported player to {x}, {y}")
            except Exception as e:
                print("[ERROR] Teleport command failed. Exception:", e)
                print("Usage: teleport <x> <y>")
        elif cmd == "spawn_item":
            try:
                try:
                    key = int(tokens[1])
                except ValueError:
                    key = tokens[1].upper()
                quantity = int(tokens[2]) if len(tokens) > 2 else 1
                print(f"[DEBUG] Spawning item. Key: {key}, Quantity: {quantity}")

                # Import all needed items and blocks
                from item import ITEM_PICKAXE, ITEM_SWORD, ITEM_AXE, APPLE, WATER_BOTTLE
                from block import SPAWNER_ITEM, STORAGE, FURNACE
                
                # Create proper item dictionary structure
                item_dict = {
                    "item": None,
                    "quantity": quantity
                }

                item_map = {
                    # ...existing items...
                    "SPAWNER": SPAWNER_ITEM,
                    "STORAGE": STORAGE.item_variant,
                    STORAGE.id: STORAGE.item_variant,
                    "FURNACE": FURNACE.item_variant,
                    FURNACE.id: FURNACE.item_variant,
                    "IRON_HELMET": IRON_HELMET,
                    "IRON_CHESTPLATE": IRON_CHESTPLATE,
                    "IRON_LEGGINGS": IRON_LEGGINGS,
                    "IRON_BOOTS": IRON_BOOTS,
                    "IRON_SWORD": IRON_SWORD,
                    "IRON_PICKAXE": IRON_PICKAXE,
                    "IRON_AXE": IRON_AXE,
                    "IRON_SHOVEL": IRON_SHOVEL,
                    # Add item IDs as well
                    30: IRON_HELMET,
                    31: IRON_CHESTPLATE,
                    32: IRON_LEGGINGS,
                    33: IRON_BOOTS,
                    40: IRON_SWORD,
                    41: IRON_PICKAXE,
                    42: IRON_AXE,
                    43: IRON_SHOVEL,
                }

                if key in item_map:
                    # Create a copy of the item variant for blocks that need instancing
                    if key in ["FURNACE", FURNACE.id, "STORAGE", STORAGE.id]:
                        block = item_map[key].block.create_instance()
                        item = block.item_variant
                    else:
                        item = item_map[key]
                    
                    inventory.add_item(item, quantity)
                    print(f"[INFO] Spawned {quantity} of {item.name}")
                else:
                    print("[WARN] Item id/name not recognized.")
                    
            except Exception as e:
                print("[ERROR] Spawn item command failed. Exception:", str(e))
                print("Usage: spawn_item <item_id|item_name> <quantity>")
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
