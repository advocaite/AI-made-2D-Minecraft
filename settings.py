import json
import os

class Settings:
    def __init__(self, filename="options.json"):
        self.filename = filename
        self.defaults = {
            "screen_width": 800,
            "screen_height": 600,
            "sound_volume": 0.5,
            "fullscreen": False
        }
        self.options = self.load_settings()
    
    def load_settings(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        return self.defaults.copy()
    
    def save_settings(self):
        with open(self.filename, "w") as f:
            json.dump(self.options, f, indent=4)
    
    def update(self, key, value):
        self.options[key] = value
        self.save_settings()
