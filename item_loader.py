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
        """Create an item instance with proper attributes"""
        try:
            from item import Item, ITEM_REGISTRY
            
            # Create base item with all possible attributes
            item = Item(
                id=data['id'],  # Keep as integer for item creation
                name=str(data['name']),
                texture_coords=tuple(data['texture_coords']),
                stack_size=int(data.get('stack_size', 64)),
                is_block=False
            )
            
            # Set category/type
            item.type = data.get('category', 'material')
            
            # Handle special categories
            if item.type == 'seed':
                item.is_seed = True
                # Store plant data if available
                if 'plant_data' in data:
                    item.plant_data = data['plant_data']
            
            # Register item by both ID and name
            ITEM_REGISTRY[item.id] = item
            ITEM_REGISTRY[item_id] = item  # Also register by name (e.g., "BEETROOT_SEED")
            print(f"[ITEM LOADER] Created and registered item: {item.name} (ID: {item.id}, Type: {item.type})")
            print(f"[ITEM LOADER] Registered under keys: {item.id} and {item_id}")
            
            return item
            
        except Exception as e:
            print(f"[ITEM LOADER] Error creating item {item_id}: {e}")
            return None

    def load_items(self):
        """Load all item definitions from JSON files"""
        if not self.data_dir.exists():
            print(f"Warning: Data directory {self.data_dir} does not exist")
            return

        print(f"Looking for item files in: {self.data_dir}")
        
        for file in self.data_dir.glob("*.json"):
            print(f"\nProcessing item file: {file}")
            try:
                with open(file, encoding='utf-8') as f:
                    items = json.load(f)
                    print(f"Found {len(items)} items in {file.name}")
                    
                    for item_id, item_data in items.items():
                        try:
                            # Process inheritance if any
                            processed_data = self.process_inheritance(item_data, self.items)
                            
                            # Create and register the item
                            item = self.create_item(item_id, processed_data, file.stem)
                            if item:
                                self.items[item_id] = item
                                print(f"Successfully loaded item: {item.name} from {file.name}")
                            
                        except Exception as e:
                            print(f"Error processing item {item_id}: {e}")
                            continue
                            
            except Exception as e:
                print(f"Error loading {file}: {e}")
                continue

        print(f"\nTotal items loaded: {len(self.items)}")
        print("Item Registry contents:", self.items.keys())

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
