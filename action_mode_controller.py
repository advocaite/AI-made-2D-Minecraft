from block import StorageBlock, FurnaceBlock, EnhancerBlock, AIR
import block as b  # Add this import

class ActionModeController:
    def __init__(self, texture_atlas, inventory):
        self.texture_atlas = texture_atlas
        self.inventory = inventory

    def handle_mouse_event(self, event, world_chunks, player, cam_offset_x, cam_offset_y, block_size, chunk_width, world_height):
        if event.button == 1:  # Left click to break
            mouse_x, mouse_y = event.pos
            world_x = int((mouse_x + cam_offset_x) // block_size)
            world_y = int((mouse_y + cam_offset_y) // block_size)
            chunk_index = world_x // chunk_width
            local_x = world_x % chunk_width

            if chunk_index in world_chunks and 0 <= world_y < world_height:
                block = world_chunks[chunk_index][world_y][local_x]
                # Only collect non-AIR blocks
                if block.id != 0 and block != b.AIR:  # Check both id and direct comparison
                    print(f"Breaking block: {block.name}")
                    world_chunks[chunk_index][world_y][local_x] = b.AIR
                    # Only add to inventory if block has an item variant
                    if hasattr(block, 'item_variant') and block.item_variant:
                        self.inventory.add_item(block.item_variant, 1)
                        print(f"Added {block.item_variant.name} to inventory")

        # Get block at mouse position
        mouse_x, mouse_y = event.pos
        world_x = int((mouse_x + cam_offset_x) // block_size)
        world_y = int((mouse_y + cam_offset_y) // block_size)
        chunk_index = world_x // chunk_width
        local_x = world_x % chunk_width
        
        # Get clicked block if valid position
        clicked_block = None
        clicked_pos = (world_x, world_y)
        if chunk_index in world_chunks and 0 <= world_y < world_height:
            clicked_block = world_chunks[chunk_index][world_y][local_x]

        # Check for interactive blocks
        if clicked_block and (isinstance(clicked_block, StorageBlock) or 
                            isinstance(clicked_block, FurnaceBlock) or 
                            isinstance(clicked_block, EnhancerBlock)):
            return ("interact", clicked_block, clicked_pos)

        return None
