import config as c
from block import BLOCK_MAP, Block, StorageBlock, FurnaceBlock, EnhancerBlock
from item import Item

class CommandManager:
    def __init__(self):
        self.item_map = {}
        self.build_item_map()

    def build_item_map(self):
        """Dynamically build the item map from all available blocks and items"""
        # Add all blocks from BLOCK_MAP
        for block_id, block in BLOCK_MAP.items():
            if block.item_variant:
                # Add by ID
                self.item_map[block_id] = block.item_variant
                # Add by name (uppercase)
                self.item_map[block.name.upper()] = block.item_variant
                
                # Special handling for blocks that need instances
                if isinstance(block, (StorageBlock, FurnaceBlock, EnhancerBlock)):
                    def create_instanced_item(block=block):
                        instance = block.create_instance()
                        return instance.item_variant
                    self.item_map[block_id] = create_instanced_item
                    self.item_map[block.name.upper()] = create_instanced_item

        # Import all defined items from item module
        import item as item_module
        for attr_name in dir(item_module):
            attr = getattr(item_module, attr_name)
            if isinstance(attr, Item):
                # Add by name if it's in uppercase (conventional for constants)
                if attr_name.isupper():
                    self.item_map[attr_name] = attr
                # Add by ID if the item has one
                if hasattr(attr, 'id'):
                    self.item_map[attr.id] = attr

    def execute_command(self, command_str, player, inventory, mobs):
        """Handle command execution"""
        tokens = command_str.strip().split()
        if not tokens:
            return

        cmd = tokens[0].lower()
        
        if cmd == "spawn_item":
            try:
                try:
                    key = int(tokens[1])
                except ValueError:
                    key = tokens[1].upper()
                quantity = int(tokens[2]) if len(tokens) > 2 else 1
                
                if key in self.item_map:
                    item_source = self.item_map[key]
                    
                    # Handle factory functions for instanced blocks
                    if callable(item_source):
                        item = item_source()
                    else:
                        item = item_source
                        
                    inventory.add_item(item, quantity)
                    print(f"[INFO] Spawned {quantity} of {item.name}")
                else:
                    print(f"[WARN] Item id/name not recognized: {key}")
                    print("Available items:", ", ".join(str(k) for k in self.item_map.keys()))
            except Exception as e:
                print(f"[ERROR] Spawn item command failed: {str(e)}")
                print("Usage: spawn_item <item_id|item_name> <quantity>")

        # ... rest of execute_command implementation ...
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
