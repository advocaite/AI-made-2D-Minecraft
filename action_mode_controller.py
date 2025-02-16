from block import StorageBlock, FurnaceBlock, EnhancerBlock

class ActionModeController:
    def __init__(self, texture_atlas, inventory):
        self.texture_atlas = texture_atlas
        self.inventory = inventory

    def handle_mouse_event(self, event, world_chunks, player, cam_offset_x, cam_offset_y, block_size, chunk_width, world_height):
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
