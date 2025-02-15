import json
import os

def save_world(world_chunks, filename="world_save.json"):
    # Serialize the world_chunks dict (keys converted to strings)
    serializable = {str(ci): chunk for ci, chunk in world_chunks.items()}
    with open(filename, "w") as f:
        json.dump(serializable, f)

def load_world(filename="world_save.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        return {int(ci): chunk for ci, chunk in data.items()}
    return None
