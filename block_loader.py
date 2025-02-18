import json
import jsonschema
from pathlib import Path
import importlib.util
from block import Block, StorageBlock, FurnaceBlock, EnhancerBlock, FarmingBlock

class BlockLoader:
    def __init__(self):
        self.blocks = {}
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / 'data' / 'blocks'
        self.schema_path = self.base_dir / 'data' / 'schemas' / 'block_schema.json'
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load schema
        with open(self.schema_path) as f:
            self.schema = json.load(f)

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
        block_type = block_data.get('type', 'basic')
        
        # Map of block types to their classes
        block_classes = {
            'basic': Block,
            'storage': StorageBlock,
            'furnace': FurnaceBlock,
            'enhancer': EnhancerBlock,
            'farming': FarmingBlock
        }
        
        BlockClass = block_classes.get(block_type, Block)
        
        # Create block instance with basic properties
        block = BlockClass(
            id=block_data['id'],
            name=block_data['name'],
            solid=block_data['solid'],
            color=tuple(block_data.get('color', (255, 255, 255))),
            texture_coords=tuple(block_data['texture_coords']),
            animation_frames=[tuple(frame) for frame in block_data.get('animation_frames', [])] if block_data.get('animation_frames') else None,
            frame_duration=block_data.get('frame_duration', 0),
            tint=tuple(block_data.get('tint', ())) if block_data.get('tint') else None,
            entity_type=block_data.get('entity_type')
        )
        
        # Add additional properties directly to block instance
        if 'burn_time' in block_data:
            block.burn_time = block_data['burn_time']
        
        # Load script if specified
        if script_path := block_data.get('script'):
            if script_class := self.load_script(script_path):
                block.script = script_class(block)
        
        # Create item variant for the block
        from item import Item
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

    def load_blocks(self):
        """Load all block definitions from JSON files"""
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, encoding='utf-8') as f:
                    blocks_data = json.load(f)
                    
                for block_id, block_data in blocks_data.items():
                    # Validate against schema
                    jsonschema.validate(instance=block_data, schema=self.schema)
                    
                    # Create block instance
                    block = self.create_block(block_data)
                    self.blocks[block_id] = block
                    
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

        return self.blocks

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
