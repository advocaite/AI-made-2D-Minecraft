import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from pathlib import Path
import json
import pygame
from PIL import Image, ImageTk
import sys
sys.path.append(str(Path(__file__).parent.parent))
from block_loader import BlockLoader

class BlockEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Block Editor")
        self.root.geometry("1024x768")
        
        # Set up data directory
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data' / 'blocks'
        
        # Initialize components
        self.block_loader = BlockLoader()
        self.setup_frames()
        self.setup_menu()
        
        # Initialize Pygame with a display
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)  # Minimal hidden window
        
        self.load_texture_atlas()
        self.setup_block_list()
        self.setup_edit_form()
        self.setup_preview_panel()
        self.load_blocks()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Block", command=self.new_block)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reload All", command=self.load_blocks)
        tools_menu.add_command(label="Edit Scripts", command=self.edit_scripts)

    def setup_frames(self):
        # Left panel (block list)
        self.left_panel = ttk.Frame(self.root, padding="5")
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        # Middle panel (edit form)
        self.edit_panel = ttk.Frame(self.root, padding="5")
        self.edit_panel.grid(row=0, column=1, sticky="nsew")

        # Right panel (preview)
        self.preview_panel = ttk.Frame(self.root, padding="5")
        self.preview_panel.grid(row=0, column=2, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=1)

    def setup_block_list(self):
        # Search frame
        search_frame = ttk.Frame(self.left_panel)
        search_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_blocks)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)

        # Block list with headers
        columns = ("Name", "ID", "Type", "File")
        self.block_list = ttk.Treeview(self.left_panel, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        widths = {"Name": 150, "ID": 50, "Type": 100, "File": 100}
        for col in columns:
            self.block_list.heading(col, text=col, command=lambda c=col: self.sort_blocks(c))
            self.block_list.column(col, width=widths[col])
        
        self.block_list.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.block_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.block_list.configure(yscrollcommand=scrollbar.set)
        
        # Selection event
        self.block_list.bind('<<TreeviewSelect>>', self.on_block_select)

    def setup_edit_form(self):
        self.notebook = ttk.Notebook(self.edit_panel)
        self.notebook.pack(fill="both", expand=True)

        # Basic properties tab
        basic_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(basic_frame, text="Basic")

        self.entries = {}
        basic_fields = [
            ("ID", "id", "number"),
            ("Name", "name", "text"),
            ("Type", "type", "combo", ["basic", "storage", "furnace", "enhancer", "farming"]),
            ("Texture X", "texture_x", "number"),
            ("Texture Y", "texture_y", "number"),
            ("Solid", "solid", "check")
        ]

        for i, (label, key, field_type, *args) in enumerate(basic_fields):
            ttk.Label(basic_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            
            if field_type == "combo":
                widget = ttk.Combobox(basic_frame, values=args[0])
                widget.state(['readonly'])
            elif field_type == "check":
                widget = ttk.Checkbutton(basic_frame)
            else:
                widget = ttk.Entry(basic_frame)
            
            widget.grid(row=i, column=1, sticky="ew", pady=2)
            self.entries[key] = widget

        # Color picker
        color_frame = ttk.Frame(basic_frame)
        color_frame.grid(row=len(basic_fields), column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(color_frame, text="Color:").pack(side="left")
        self.color_preview = tk.Canvas(color_frame, width=30, height=20)
        self.color_preview.pack(side="left", padx=5)
        ttk.Button(color_frame, text="Pick Color", command=self.pick_color).pack(side="left")

        # Advanced properties tab
        adv_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(adv_frame, text="Advanced")

        adv_fields = [
            ("Light Level", "light_level", "number"),
            ("Burn Time", "burn_time", "number"),
            ("Mine Level", "mine_level", "number"),
            ("Drop Item", "drop_item", "text"),
            ("Script Path", "script", "text"),
            ("Is Light Source", "is_light_source", "check"),
            ("Entity Type", "entity_type", "text")  # Added entity type field
        ]

        self.adv_entries = {}
        for i, (label, key, field_type) in enumerate(adv_fields):
            ttk.Label(adv_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            if field_type == "check":
                widget = ttk.Checkbutton(adv_frame)
            else:
                widget = ttk.Entry(adv_frame)
            widget.grid(row=i, column=1, sticky="ew", pady=2)
            self.adv_entries[key] = widget

        # Animation tab
        anim_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(anim_frame, text="Animation")

        ttk.Label(anim_frame, text="Animation Frames (x,y pairs):").pack(anchor="w")
        self.anim_frames_text = tk.Text(anim_frame, height=4)
        self.anim_frames_text.pack(fill="x", pady=5)

        ttk.Label(anim_frame, text="Frame Duration (ms):").pack(anchor="w")
        self.frame_duration_entry = ttk.Entry(anim_frame)
        self.frame_duration_entry.pack(fill="x")

        # Save button at bottom
        save_frame = ttk.Frame(self.edit_panel)
        save_frame.pack(fill="x", pady=5)
        
        ttk.Button(save_frame, text="Save Changes", command=self.save_block).pack(side="right")
        ttk.Button(save_frame, text="Delete Block", command=self.delete_block).pack(side="right", padx=5)

    def setup_preview_panel(self):
        preview_frame = ttk.LabelFrame(self.preview_panel, text="Preview", padding="5")
        preview_frame.pack(fill="both", expand=True)

        # Texture preview
        self.preview_canvas = tk.Canvas(preview_frame, width=128, height=128, bg="gray")
        self.preview_canvas.pack(pady=10)

        # Block info preview
        self.info_text = tk.Text(preview_frame, height=10, width=30)
        self.info_text.pack(fill="both", expand=True)
        self.info_text.config(state="disabled")

    def load_texture_atlas(self):
        """Load the texture atlas with proper initialization"""
        try:
            atlas_path = Path(__file__).parent.parent / 'assets' / 'textures' / 'blocks.png'
            if not atlas_path.exists():
                print("Creating default texture atlas...")
                # Create directories if they don't exist
                atlas_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create default texture atlas (32x32 grid of 16x16 textures)
                surface = pygame.Surface((512, 512))
                surface.fill((200, 200, 200))  # Light gray background
                
                # Draw grid
                for y in range(32):
                    for x in range(32):
                        # Create numbered tile
                        tile = pygame.Surface((16, 16))
                        tile.fill((230, 230, 230) if (x + y) % 2 == 0 else (200, 200, 200))
                        
                        # Add coordinates text
                        if pygame.font.get_init():
                            font = pygame.font.SysFont('arial', 7)
                            text = font.render(f'{x},{y}', True, (0, 0, 0))
                            text_rect = text.get_rect(center=(8, 8))
                            tile.blit(text, text_rect)
                        
                        # Draw border
                        pygame.draw.rect(tile, (150, 150, 150), tile.get_rect(), 1)
                        
                        # Copy tile to atlas
                        surface.blit(tile, (x * 16, y * 16))
                
                # Save the atlas
                pygame.image.save(surface, str(atlas_path))
                print(f"Created default texture atlas at {atlas_path}")
            
            self.texture_atlas = pygame.image.load(str(atlas_path))
            print(f"Loaded texture atlas: {self.texture_atlas.get_width()}x{self.texture_atlas.get_height()} pixels")
            
        except Exception as e:
            print(f"Error loading texture atlas: {e}")
            import traceback
            traceback.print_exc()
            # Create dummy texture atlas if all else fails
            self.texture_atlas = pygame.Surface((512, 512))
            self.texture_atlas.fill((255, 0, 255))

    def load_blocks(self):
        """Load blocks and update UI"""
        self.blocks = {}
        try:
            self.blocks = self.block_loader.load_blocks()
            self.update_block_list()
        except Exception as e:
            print(f"Error loading blocks: {e}")
            messagebox.showerror("Error", f"Failed to load blocks: {e}")

    def update_block_list(self):
        """Update the block list display"""
        self.block_list.delete(*self.block_list.get_children())
        try:
            for block_id, block in self.blocks.items():
                self.block_list.insert("", "end", values=(
                    block.name,
                    block.id,
                    block.type,
                    f"{block.type.lower()}.json"
                ))
        except Exception as e:
            print(f"Error updating block list: {e}")
            messagebox.showerror("Error", f"Failed to update block list: {e}")

    def filter_blocks(self, *args):
        # Implement block filtering
        search_term = self.search_var.get().lower()
        self.block_list.delete(*self.block_list.get_children())
        for block_id, block in self.blocks.items():
            if search_term in block_id.lower() or search_term in block.name.lower():
                self.block_list.insert("", "end", values=(block.id, block.type))

    def on_block_select(self, event):
        """Handle block selection"""
        selected = self.block_list.selection()
        if not selected:
            return

        try:
            # Get block by name since that's our first column
            values = self.block_list.item(selected[0])['values']
            name = values[0]  # Name is first column
            
            # Find block with matching name
            block = None
            for block_id, b in self.blocks.items():
                if b.name == name:
                    block = b
                    break

            if block:
                # Pass the full block object to both methods
                self.fill_form(block)
                self.update_preview(block)
            
        except Exception as e:
            print(f"Error in block selection: {e}")
            import traceback
            traceback.print_exc()

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose Block Color")[0]
        if color:
            self.color_preview.configure(bg='#{:02x}{:02x}{:02x}'.format(*map(int, color)))

    def save_all(self):
        """Save all blocks back to their files"""
        try:
            # Use block_loader's save method
            self.block_loader.save_blocks()
            messagebox.showinfo("Success", "All blocks saved successfully!")
        except Exception as e:
            print(f"Error saving blocks: {e}")
            messagebox.showerror("Error", f"Failed to save blocks: {e}")

    def save_block(self):
        """Save current block"""
        selected = self.block_list.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a block to save")
            return
            
        try:
            values = self.block_list.item(selected[0])['values']
            block_name = values[0]
            block_id = values[1]
            file_name = values[3]
            
            # Build block data
            data = {
                "id": int(self.entries['id'].get()),
                "name": self.entries['name'].get(),
                "type": self.entries['type'].get(),
                "solid": self.entries['solid'].instate(['selected']),
                "texture_coords": [
                    int(self.entries['texture_x'].get()),
                    int(self.entries['texture_y'].get())
                ]
            }
            
            # Add color if set
            try:
                color = self.color_preview.cget('bg')
                if color.startswith('#'):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    data['color'] = [r, g, b]
            except:
                pass

            # Add advanced properties
            for key, entry in self.adv_entries.items():
                if isinstance(entry, ttk.Checkbutton):
                    value = bool(entry.instate(['selected']))
                else:
                    value = entry.get()
                if value:
                    if key in ['light_level', 'burn_time', 'mine_level']:
                        value = int(value)
                    data[key] = value
            
            # Add animation data if present
            frames_text = self.anim_frames_text.get("1.0", tk.END).strip()
            if frames_text:
                try:
                    frames = eval(frames_text)  # Safely evaluate frame coordinates
                    if isinstance(frames, list):
                        data['animation_frames'] = frames
                        duration = self.frame_duration_entry.get()
                        if duration:
                            data['frame_duration'] = int(duration)
                except Exception as e:
                    print(f"Error parsing animation frames: {e}")

            # Save to file
            file_path = self.block_loader.data_dir / file_name
            with open(file_path, 'r') as f:
                blocks = json.load(f)
            
            # Find block ID by name
            for bid, bdata in blocks.items():
                if bdata['name'] == block_name:
                    blocks[bid] = data
                    break
                    
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(blocks, f, indent=4)
                
            messagebox.showinfo("Success", "Block saved successfully!")
            self.load_blocks()  # Refresh list
            
        except Exception as e:
            print(f"Error saving block: {e}")
            messagebox.showerror("Error", f"Failed to save block: {e}")

    def update_preview(self, block):
        """Update preview with better texture handling"""
        try:
            # Get texture coordinates
            tx, ty = block.texture_coords
            
            # Debug info
            print(f"Loading texture at coordinates ({tx}, {ty})")
            print(f"Atlas size: {self.texture_atlas.get_size()}")
            
            # Size of each tile in the texture atlas
            TILE_SIZE = 16
            
            # Calculate pixel coordinates
            px = tx * TILE_SIZE
            py = ty * TILE_SIZE
            
            # Extract texture
            try:
                # Ensure we stay within bounds
                atlas_width, atlas_height = self.texture_atlas.get_size()
                if px < 0 or py < 0 or px + TILE_SIZE > atlas_width or py + TILE_SIZE > atlas_height:
                    raise ValueError(f"Texture coordinates out of bounds: ({tx}, {ty})")

                # Extract the texture
                texture = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                texture.blit(self.texture_atlas, (0, 0), (px, py, TILE_SIZE, TILE_SIZE))
                
                # Scale up for preview
                scaled = pygame.transform.scale(texture, (128, 128))
                
                # Apply tint if present
                if hasattr(block, 'tint') and block.tint:
                    tint_surface = pygame.Surface((128, 128), pygame.SRCALPHA)
                    tint_surface.fill((*block.tint, 128))  # Semi-transparent tint
                    scaled.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(
                    Image.frombytes('RGBA', scaled.get_size(), 
                                  pygame.image.tostring(scaled, 'RGBA')))
                
                # Update canvas
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(64, 64, image=photo)
                self.preview_canvas.image = photo  # Keep reference
                
            except Exception as e:
                print(f"Error extracting texture: {e}")
                self._show_missing_texture()
            
            # Update info text
            self.info_text.config(state="normal")
            self.info_text.delete(1.0, tk.END)
            
            # Basic info
            info = [
                f"Name: {block.name}",
                f"ID: {block.id}",
                f"Type: {block.type}",
                f"Solid: {block.solid}",
                f"Texture: ({tx}, {ty})"
            ]
            
            # Extra properties
            if hasattr(block, 'light_level'):
                info.append(f"Light Level: {block.light_level}")
            if hasattr(block, 'burn_time'):
                info.append(f"Burn Time: {block.burn_time}")
            if hasattr(block, 'mine_level'):
                info.append(f"Mine Level: {block.mine_level}")
            if hasattr(block, 'script'):
                info.append(f"Has Script: {bool(block.script)}")
            if hasattr(block, 'tint'):
                info.append(f"Tint: {block.tint}")
            
            self.info_text.insert(tk.END, "\n".join(info))
            self.info_text.config(state="disabled")
            
        except Exception as e:
            print(f"Error updating preview: {e}")
            import traceback
            traceback.print_exc()
            self._show_missing_texture()

    def new_block(self):
        """Create a new block"""
        # Create new dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("New Block")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Basic info frame
        basic_frame = ttk.LabelFrame(dialog, text="Basic Information", padding="5")
        basic_frame.pack(fill="x", padx=5, pady=5)

        # Entry fields
        ttk.Label(basic_frame, text="Block ID:").grid(row=0, column=0, sticky="w")
        id_entry = ttk.Entry(basic_frame)
        id_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(basic_frame, text="Name:").grid(row=1, column=0, sticky="w")
        name_entry = ttk.Entry(basic_frame)
        name_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(basic_frame, text="Type:").grid(row=2, column=0, sticky="w")
        type_combo = ttk.Combobox(basic_frame, values=["basic", "storage", "furnace", "enhancer", "farming"])
        type_combo.set("basic")
        type_combo.grid(row=2, column=1, sticky="ew")

        # File selection
        ttk.Label(basic_frame, text="Save to:").grid(row=3, column=0, sticky="w")
        file_combo = ttk.Combobox(basic_frame, values=["basic.json", "special.json", "resources.json", "nature.json", "biomes.json"])
        file_combo.set("basic.json")
        file_combo.grid(row=3, column=1, sticky="ew")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        def create_block():
            try:
                block_id = id_entry.get().strip().upper()
                if not block_id:
                    raise ValueError("Block ID is required")
                    
                block_data = {
                    "id": int(block_id),
                    "name": name_entry.get().strip(),
                    "type": type_combo.get(),
                    "solid": True,
                    "color": [255, 255, 255],
                    "texture_coords": [0, 0]
                }
                
                # Save to selected file
                file_path = self.block_loader.data_dir / file_combo.get()
                try:
                    with open(file_path, 'r') as f:
                        blocks = json.load(f)
                except FileNotFoundError:
                    blocks = {}
                    
                blocks[block_id] = block_data
                
                with open(file_path, 'w') as f:
                    json.dump(blocks, f, indent=4)
                    
                dialog.destroy()
                self.load_blocks()
                messagebox.showinfo("Success", "Block created successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create block: {e}")

        ttk.Button(btn_frame, text="Create", command=create_block).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right")

    def delete_block(self):
        """Delete the selected block"""
        selected = self.block_list.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a block to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this block?"):
            try:
                values = self.block_list.item(selected[0])['values']
                block_name = values[0]  # Name is first column
                file_name = values[3]   # File is fourth column
                
                # Load the file and remove the block
                file_path = self.block_loader.data_dir / file_name
                with open(file_path, 'r') as f:
                    blocks = json.load(f)
                
                # Find and remove the block by name
                block_id = None
                for bid, data in blocks.items():
                    if data['name'] == block_name:
                        block_id = bid
                        break
                
                if block_id:
                    del blocks[block_id]
                    
                    # Save the file
                    with open(file_path, 'w') as f:
                        json.dump(blocks, f, indent=4)
                        
                    self.load_blocks()
                    messagebox.showinfo("Success", "Block deleted successfully!")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete block: {e}")

    def edit_scripts(self):
        """Open script editor for selected block"""
        selected = self.block_list.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a block first")
            return
            
        values = self.block_list.item(selected[0])['values']
        block_name = values[0]
        file_name = values[3]
        
        try:
            # Load the block data
            file_path = self.block_loader.data_dir / file_name
            with open(file_path, 'r') as f:
                blocks = json.load(f)
                
            # Find the block by name
            block_data = None
            for data in blocks.values():
                if data['name'] == block_name:
                    block_data = data
                    break
                    
            if block_data and 'script' in block_data:
                script_path = Path(self.block_loader.base_dir) / block_data['script']
                if not script_path.exists():
                    script_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(script_path, 'w') as f:
                        f.write('''class BlockScript:
    def __init__(self, block):
        self.block = block
        
    def create_instance(self):
        new_block = self.block.create_base_instance()
        new_block.script = BlockScript(new_block)
        return new_block
''')
                
                # Open script in system default editor
                import os
                os.startfile(script_path) if os.name == 'nt' else os.system(f'xdg-open {script_path}')
            else:
                messagebox.showinfo("Info", "This block type doesn't have a script")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open script: {e}")

    def sort_blocks(self, column):
        """Sort block list by column"""
        col_index = {"Name": 0, "ID": 1, "Type": 2, "File": 3}[column]
        items = [(self.block_list.set(item, column), item) 
                for item in self.block_list.get_children("")]
        items.sort()
        
        for idx, (_, item) in enumerate(items):
            self.block_list.move(item, "", idx)

    def fill_form(self, block):
        """Fill form fields with better property handling"""
        try:
            # Basic fields
            self.entries['id'].delete(0, tk.END)
            self.entries['id'].insert(0, str(block.id))
            
            self.entries['name'].delete(0, tk.END)
            self.entries['name'].insert(0, block.name)
            
            self.entries['type'].set(block.type)
            
            tx, ty = block.texture_coords
            self.entries['texture_x'].delete(0, tk.END)
            self.entries['texture_x'].insert(0, str(tx))
            
            self.entries['texture_y'].delete(0, tk.END)
            self.entries['texture_y'].insert(0, str(ty))
            
            # Set solid state
            if isinstance(self.entries['solid'], ttk.Checkbutton):
                self.entries['solid'].state(['selected' if block.solid else '!selected'])
            
            # Set color preview
            if hasattr(block, 'color'):
                self.color_preview.configure(bg=f'#{block.color[0]:02x}{block.color[1]:02x}{block.color[2]:02x}')

            # Clear all advanced fields first
            for entry in self.adv_entries.values():
                if isinstance(entry, ttk.Checkbutton):
                    entry.state(['!selected'])
                else:
                    entry.delete(0, tk.END)

            # Fill advanced properties with better burn time handling
            properties = {
                'light_level': getattr(block, 'light_level', None),
                'burn_time': getattr(block, 'burn_time', None),  # Check block first
                'mine_level': getattr(block, 'mine_level', None),
                'drop_item': getattr(block, 'drop_item', None),
                'script': block.script.__class__.__name__ if block.script else "",
                'is_light_source': getattr(block, 'is_light_source', False),
                'entity_type': getattr(block, 'entity_type', None)
            }

            # Check item variant for burn time if not on block
            if properties['burn_time'] is None and hasattr(block, 'item_variant') and block.item_variant:
                properties['burn_time'] = getattr(block.item_variant, 'burn_time', None)

            # Fill the form fields
            for key, value in properties.items():
                if value is not None:
                    entry = self.adv_entries[key]
                    if isinstance(entry, ttk.Checkbutton):
                        entry.state(['selected' if value else '!selected'])
                    else:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(value))

            # Fill animation data
            self.anim_frames_text.delete(1.0, tk.END)
            if hasattr(block, 'animation_frames') and block.animation_frames:
                self.anim_frames_text.insert(tk.END, str(block.animation_frames))
                self.frame_duration_entry.delete(0, tk.END)
                if hasattr(block, 'frame_duration'):
                    self.frame_duration_entry.insert(0, str(block.frame_duration))

        except Exception as e:
            print(f"Error filling form: {e}")
            import traceback
            traceback.print_exc()

    def _show_missing_texture(self):
        """Show better missing texture pattern"""
        self.preview_canvas.delete("all")
        # Create purple/black checkerboard pattern
        size = 16  # Size of each checker square
        for y in range(8):
            for x in range(8):
                color = "#FF00FF" if (x + y) % 2 == 0 else "#000000"
                self.preview_canvas.create_rectangle(
                    x * size, y * size, 
                    (x + 1) * size, (y + 1) * size,
                    fill=color, outline="#808080"
                )
        # Add text indicator
        self.preview_canvas.create_text(
            64, 64,
            text="Missing\nTexture",
            fill="white",
            font=("Arial", 12, "bold"),
            justify="center"
        )

    def run(self):
        self.root.mainloop()

    def __del__(self):
        """Cleanup Pygame on exit"""
        pygame.quit()

if __name__ == "__main__":
    editor = BlockEditor()
    editor.run()
