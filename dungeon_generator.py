import random
import block as b

class DungeonGenerator:
    def __init__(self, min_rooms=3, max_rooms=5):
        self.min_rooms = min_rooms
        self.max_rooms = max_rooms
        self.rooms = []
        self.chunks_to_modify = {}
        self.current_chunk_index = 0
        self.room_size = 10  # Fixed 10x10 rooms
        self.has_spawner = False
        self.has_storage = False
        self.corridors = []  # Initialize corridors list

    def generate(self, chunk, start_x, start_y, chunk_index=0):
        chunk_width = len(chunk[0])
        chunk_height = len(chunk)
        
        self.current_chunk_index = chunk_index
        self.chunks_to_modify = {chunk_index: chunk}
        
        # Find dirt/grass layer
        dirt_layer = 0
        for y in range(chunk_height):
            if chunk[y][chunk_width//2] in [b.DIRT, b.GRASS]:
                dirt_layer = y
                break

        # Start position (below dirt layer)
        start_y = dirt_layer + 20  # Good distance below surface
        
        # Track special room counts
        self.has_spawner = False
        self.has_storage = False

        # Create first room (random type)
        first_room = {
            'x': chunk_width//2 - self.room_size//2,
            'y': start_y,
            'width': self.room_size,
            'height': self.room_size,
            'type': random.choice(['spawner', 'loot'])
        }
        
        if first_room['type'] == 'spawner':
            self.has_spawner = True
        else:
            self.has_storage = True
        
        self.rooms.append(first_room)
        last_room = first_room

        # Generate additional rooms
        room_count = random.randint(self.min_rooms, self.max_rooms)
        for i in range(1, room_count):
            # Decide direction (right or down)
            direction = random.choice(['right', 'down'])
            hallway_length = random.randint(5, 8)  # Shorter hallways
            
            # Calculate new room position
            if direction == 'right':
                new_x = last_room['x'] + last_room['width'] + hallway_length
                new_y = last_room['y']
            else:  # down
                new_x = last_room['x']
                new_y = last_room['y'] + last_room['height'] + hallway_length

            # Determine room type
            if i == room_count - 1:  # Last room
                if not self.has_spawner and not self.has_storage:
                    # Force either spawner or storage if neither exists
                    room_type = random.choice(['spawner', 'loot'])
                elif not self.has_spawner:
                    room_type = 'spawner'
                elif not self.has_storage:
                    room_type = 'loot'
                else:
                    room_type = 'empty'
            else:
                # Random type with preference for missing special rooms
                if not self.has_spawner and random.random() < 0.4:
                    room_type = 'spawner'
                elif not self.has_storage and random.random() < 0.4:
                    room_type = 'loot'
                else:
                    room_type = 'empty'

            # Update tracking flags
            if room_type == 'spawner':
                self.has_spawner = True
            elif room_type == 'loot':
                self.has_storage = True

            # Create new room
            new_room = {
                'x': new_x,
                'y': new_y,
                'width': self.room_size,
                'height': self.room_size,
                'type': room_type,
                'connected_from': direction,
                'hallway_length': hallway_length
            }

            # Check if room fits in chunk
            if (0 <= new_x < chunk_width - self.room_size and 
                new_y < chunk_height - self.room_size):
                self.rooms.append(new_room)
                last_room = new_room

        self._carve_dungeon()
        return self.chunks_to_modify

    def _carve_dungeon(self):
        chunk = self.chunks_to_modify[self.current_chunk_index]
        
        def set_block(x, y, block):
            if 0 <= x < len(chunk[0]) and 0 <= y < len(chunk):
                # Always convert water to air in dungeon areas
                if chunk[y][x] == b.WATER:
                    chunk[y][x] = b.AIR
                chunk[y][x] = block

        def clear_water_around(x, y, width, height, padding=2):
            """Clear water from an area around a room or hallway"""
            for dy in range(y - padding, y + height + padding):
                for dx in range(x - padding, x + width + padding):
                    if 0 <= dx < len(chunk[0]) and 0 <= dy < len(chunk):
                        if chunk[dy][dx] == b.WATER:
                            chunk[dy][dx] = b.AIR

        # First pass: clear water from all dungeon areas
        for room in self.rooms:
            clear_water_around(room['x'], room['y'], room['width'], room['height'])

        # Carve rooms and hallways
        for i, room in enumerate(self.rooms):
            # Carve room
            for y in range(room['y'], room['y'] + room['height']):
                for x in range(room['x'], room['x'] + room['width']):
                    if (x == room['x'] or x == room['x'] + room['width'] - 1 or 
                        y == room['y'] or y == room['y'] + room['height'] - 1):
                        set_block(x, y, b.SANDSTONE)
                    else:
                        set_block(x, y, b.AIR)
                        set_block(x, y + 1, b.AIR)  # Make 2 blocks high

            # Add room features
            if room['type'] in ['spawner', 'loot']:
                center_x = room['x'] + room['width']//2
                center_y = room['y'] + room['height']//2
                if room['type'] == 'spawner':
                    set_block(center_x, center_y, b.SPAWNER)
                else:  # loot
                    storage = b.STORAGE.create_instance()
                    storage.inventory = [None] * storage.max_slots
                    storage.inventory[0] = {"item": b.IRON_INGOT, "quantity": 5}
                    set_block(center_x, center_y, storage)

            # Carve hallway to next room
            if i < len(self.rooms) - 1 and 'connected_from' in self.rooms[i + 1]:
                next_room = self.rooms[i + 1]
                hallway_length = next_room['hallway_length']
                
                if next_room['connected_from'] == 'right':
                    # Horizontal hallway
                    start_x = room['x'] + room['width']
                    y = room['y'] + room['height']//2
                    for x in range(start_x, start_x + hallway_length + 1):
                        set_block(x, y - 1, b.SANDSTONE)  # Floor
                        set_block(x, y, b.AIR)  # Path
                        set_block(x, y + 1, b.AIR)  # Headroom
                        set_block(x, y + 2, b.SANDSTONE)  # Ceiling
                        set_block(x, y - 2, b.SANDSTONE)  # Lower wall
                        set_block(x, y + 3, b.SANDSTONE)  # Upper wall
                
                else:  # down
                    # Vertical hallway
                    x = room['x'] + room['width']//2
                    start_y = room['y'] + room['height']
                    for y in range(start_y, start_y + hallway_length + 1):
                        set_block(x - 1, y, b.SANDSTONE)  # Left wall
                        set_block(x, y, b.AIR)  # Path
                        set_block(x + 1, y, b.SANDSTONE)  # Right wall
                        set_block(x, y + 1, b.AIR)  # Headroom

        for (x1, y1), (x2, y2) in self.corridors:
            min_x, max_x = min(int(x1), int(x2)), max(int(x1), int(x2))
            min_y, max_y = min(int(y1), int(y2)), max(int(y1), int(y2))
            clear_water_around(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
