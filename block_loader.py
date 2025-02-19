import json
import jsonschema
from pathlib import Path
import importlib.util
from registry import REGISTRY

class BlockLoader:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / 'data' / 'blocks'
        self.schema_path = self.base_dir / 'data' / 'schemas' / 'block_schema.json'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load schema
        with open(self.schema_path) as f:
            self.schema = json.load(f)
        
        self.blocks = {}  # Add this line to store blocks locally

    def load_script(self, script_path):
        """Load a block script from file"""
        if not script_path:
            return None

        try:
            full_path = self.base_dir / script_path
            spec = importlib.util.spec_from_file_location("block_script", full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.BlockScript
        except Exception as e:
            print(f"Error loading block script {script_path}: {e}")
            return None

    def create_block(self, block_data):
        """Create a block instance with item variant"""
        # Import here to avoid circular imports
        from block import Block, StorageBlock, FurnaceBlock, EnhancerBlock, FarmingBlock, UNBREAKABLE
        from item import Item, UNBREAKABLE as UNBREAKABLE_ITEM
        
        # Special case for unbreakable blocks
        if block_data.get('id') == 8 or block_data.get('name') == "Unbreakable":
            return UNBREAKABLE  # Return the singleton instance
        
        block_type = block_data.get('type', 'basic')
        
        # Common arguments for all block types
        common_args = {
            'id': block_data['id'],
            'name': block_data['name'],
            'solid': block_data.get('solid', True),
            'color': tuple(block_data.get('color', (255, 255, 255))),
            'texture_coords': tuple(block_data['texture_coords']),
            'drop_item': None,  # This will be set later with item variant
            'animation_frames': [tuple(frame) for frame in block_data.get('animation_frames', [])] if block_data.get('animation_frames') else None,
            'frame_duration': block_data.get('frame_duration', 0),
            'tint': tuple(block_data.get('tint', ())) if block_data.get('tint') else None,
            'entity_type': block_data.get('entity_type')
        }

        # Create block based on type
        BlockClass = {
            'basic': Block,
            'storage': StorageBlock,
            'furnace': FurnaceBlock,
            'enhancer': EnhancerBlock,
            'farming': FarmingBlock
        }.get(block_type, Block)
        
        block = BlockClass(**common_args)
        
        # Store block in local registry
        self.blocks[str(block.id)] = block
        
        # Always create item variant
        item_variant = Item(
            id=block.id,
            name=block.name,
            texture_coords=block.texture_coords,
            stack_size=64,
            is_block=True,
            burn_time=block_data.get('burn_time')
        )
        item_variant.block = block
        block.item_variant = item_variant
        block.drop_item = item_variant

        return block

    def register_predefined_block(self, block):
        """Register a predefined block in the loader"""
        self.blocks[str(block.id)] = block
        return block

    def load_blocks(self):
        """Load all block definitions from JSON files"""
        result = {}
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, encoding='utf-8') as f:
                    blocks_data = json.load(f)
                    
                for block_id, block_data in blocks_data.items():
                    # Convert BLOCK_MAP style keys to actual blocks
                    if isinstance(block_data, str):
                        block = REGISTRY.get_block(block_id)
                        if block:
                            result[str(block_id)] = block
                            continue
                            
                    if str(block_id) not in REGISTRY.blocks:
                        jsonschema.validate(instance=block_data, schema=self.schema)
                        block = self.create_block(block_data)
                        result[str(block_id)] = block
                    
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

        return result

    def save_blocks(self):
        """Save all blocks back to their respective files"""
        block_files = {}
        
        # Group blocks by their original files
        for block_id, block in self.blocks.items():
            file_name = f"{block.type.lower()}.json"
            if file_name not in block_files:
                block_files[file_name] = {}
            block_files[file_name][block_id] = block.to_dict()
        
        # Save each file
        for file_name, blocks_data in block_files.items():
            file_path = self.data_dir / file_name
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(blocks_data, f, indent=4)
