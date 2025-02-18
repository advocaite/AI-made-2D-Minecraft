import os
import json
import importlib.util
import jsonschema
from pathlib import Path

# Remove "from item import Item" to avoid circular import
class ItemLoader:
    def __init__(self):
        self.items = {}
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / 'data' / 'items'
        self.schema_path = self.base_dir / 'data' / 'schemas' / 'item_schema.json'
        self.scripts_dir = self.base_dir / 'scripts'
        
        # Create all required directories
        self._ensure_directories()
        
        # If schema doesn't exist, create default
        if not self.schema_path.exists():
            self._create_default_schema()
        
        # Load schema
        try:
            with open(self.schema_path) as f:
                self.schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading schema: {e}")
            self.schema = {}

    def _ensure_directories(self):
        """Create all required directories and example files if missing"""
        directories = [
            self.data_dir,
            self.scripts_dir,
            self.base_dir / 'data' / 'schemas'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Ensured directory exists: {directory}")

    def _create_default_schema(self):
        """Create default schema file if missing"""
        default_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["weapon", "tool", "armor", "consumable", "material", "block", "seed"]
                },
                "id": {"type": "integer", "minimum": 0},
                "name": {"type": "string"},
                "texture_coords": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                }
            },
            "required": ["category", "id", "name", "texture_coords"]
        }
        with open(self.schema_path, 'w') as f:
            json.dump(default_schema, f, indent=4)

    def load_script(self, script_path):
        """Load a Python script for custom item behavior"""
        if not script_path:
            return None
            
        full_path = self.scripts_dir / script_path
        print(f"Looking for script at: {full_path}")
        
        if not full_path.exists():
            print(f"Warning: Script {script_path} not found. Creating default script...")
            self._create_default_script(script_path)
            
        try:
            spec = importlib.util.spec_from_file_location(full_path.stem, full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"Successfully loaded script for {script_path}")
            return module.ItemScript
        except Exception as e:
            print(f"Error loading script {script_path}: {e}")
            return None

    def _create_default_script(self, script_path):
        """Create a default script file if missing"""
        script_content = '''# Auto-generated script
class ItemScript:
    def __init__(self, item):
        self.item = item

    def on_hit(self, target):
        """Custom hit behavior"""
        import random
        if random.random() < 0.1:  # 10% chance
            if hasattr(target, 'apply_effect'):
                target.apply_effect('bleeding', duration=5000)
                print(f"{self.item.name} caused bleeding effect!")
'''
        full_path = self.scripts_dir / script_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(script_content)
        print(f"Created default script at {full_path}")

    def process_inheritance(self, data, all_items):
        """Process item inheritance"""
        if "inherits" in data:
            parent_id = data["inherits"]
            if parent_id in all_items:
                # Instead of copying the Item object, copy the parent's data
                parent_json = {
                    "category": all_items[parent_id].type,
                    "id": all_items[parent_id].id,
                    "name": all_items[parent_id].name,
                    "texture_coords": all_items[parent_id].texture_coords,
                    "stack_size": all_items[parent_id].stack_size,
                    "modifiers": all_items[parent_id].modifiers.copy() if all_items[parent_id].modifiers else {},
                    "effective_against": all_items[parent_id].effective_against.copy() if all_items[parent_id].effective_against else []
                }
                # Merge parent data with child data
                parent_json.update(data)
                return parent_json
            else:
                print(f"Warning: Parent item {parent_id} not found")
        return data

    def create_item(self, item_id, data, category):
        """Create an item based on its category"""
        try:
            from item import Item
            
            # Convert all keys to strings
            data = {str(k): v for k, v in data.items()}
            
            # Ensure coordinates are integers
            if 'texture_coords' in data:
                data['texture_coords'] = [int(x) for x in data['texture_coords']]
            
            # Create base item
            item = Item(
                id=int(data['id']),
                name=str(data['name']),
                texture_coords=tuple(data['texture_coords']),
                stack_size=int(data.get('stack_size', 64))
            )
            
            # Apply category-specific properties
            if category == "weapon":
                item.type = "weapon"
                item.modifiers = data.get("modifiers", {})
            elif category == "tool":
                item.type = "tool"
                item.effective_against = data.get("effective_against", [])
                item.modifiers = data.get("modifiers", {})
            elif category == "armor":
                item.type = "armor"
                item.is_armor = True
                item.modifiers = data.get("modifiers", {})
            elif category == "consumable":
                item.consumable_type = data.get("consumable_type")
                effects = data.get("effects", {})
                for effect, value in effects.items():
                    setattr(item, effect, value)
            elif category == "seed":
                item.is_seed = True
                item.plant_data = data.get("plant_data")

            # Add burn time if specified
            if "burn_time" in data:
                item.burn_time = data["burn_time"]

            # Apply custom script if available
            if "script" in data:
                script_class = self.load_script(data["script"])
                if script_class:
                    item.script = script_class(item)

            return item
            
        except Exception as e:
            print(f"Error creating item {item_id}: {e}")
            return None

    def load_all_items(self):
        """Load all item definitions from JSON files"""
        if not self.data_dir.exists():
            print(f"Warning: Data directory {self.data_dir} does not exist")
            return

        all_item_data = {}
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, encoding='utf-8') as f:
                    items = json.load(f)
                    for item_id, item_data in items.items():
                        # Ensure all strings are properly decoded
                        decoded_data = self._decode_data(item_data)
                        all_item_data[item_id] = (decoded_data, file.stem)
            except Exception as e:
                print(f"Error loading {file}: {e}")
                continue

        # Process items after all data is loaded
        for item_id, (data, category) in all_item_data.items():
            item = self.create_item(item_id, data, category)
            if item:
                self.items[item_id] = item
                print(f"Loaded {item.name} from {category}")

    def load_items(self):
        """Load all item definitions from JSON files"""
        if not self.data_dir.exists():
            print(f"Warning: Data directory {self.data_dir} does not exist")
            return

        all_item_data = {}
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, encoding='utf-8') as f:
                    items = json.load(f)
                    for item_id, item_data in items.items():
                        # Ensure all strings are properly decoded
                        decoded_data = self._decode_data(item_data)
                        all_item_data[item_id] = (decoded_data, file.stem)
            except Exception as e:
                print(f"Error loading {file}: {e}")
                continue

        # Process items after all data is loaded
        for item_id, (data, category) in all_item_data.items():
            item = self.create_item(item_id, data, category)
            if item:
                self.items[item_id] = item
                print(f"Loaded {item.name} from {category}")

    def _decode_data(self, data):
        """Recursively decode all strings in the data structure"""
        if isinstance(data, dict):
            return {str(k): self._decode_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._decode_data(item) for item in data]
        elif isinstance(data, bytes):
            return data.decode('utf-8')
        else:
            return data
