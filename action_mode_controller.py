# Minimal implementation for ActionModeController
class ActionModeController:
    def __init__(self, texture_atlas, inventory):
        self.texture_atlas = texture_atlas
        self.inventory = inventory

    def handle_mouse_event(self, event, world_chunks, player, cam_offset_x, cam_offset_y, block_size, chunk_width, world_height):
        # ...existing implementation...
        print("Action mode mouse event handled")
