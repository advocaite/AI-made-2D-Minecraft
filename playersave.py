import json
import os

def save_player(pos, filename="player_save.json"):
    data = {"x": pos[0], "y": pos[1]}
    with open(filename, "w") as f:
        json.dump(data, f)

def load_player(filename="player_save.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        return data["x"], data["y"]
    return None
