import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import shutil
from pathlib import Path
import pygame

class ItemEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Item Editor")
        self.root.geometry("1024x768")
        
        # Setup main frames
        self.setup_frames()
        self.setup_menu()
        
        # Load schema for validation
        self.load_schema()
        
        # Initialize texture preview
        pygame.init()
        self.load_texture_atlas()
        
        # Add item list with headers
        self.setup_item_list()
        self.setup_edit_form()
        self.setup_preview_panel()
        self.load_items()

    def setup_frames(self):
        # Left panel for item list
        self.left_panel = ttk.Frame(self.root, padding="5")
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        # Middle panel for editing
        self.edit_panel = ttk.Frame(self.root, padding="5")
        self.edit_panel.grid(row=0, column=1, sticky="nsew")

        # Right panel for preview
        self.preview_panel = ttk.LabelFrame(self.root, text="Preview", padding="5")
        self.preview_panel.grid(row=0, column=2, sticky="nsew")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)  # List panel
        self.root.columnconfigure(1, weight=2)  # Edit panel
        self.root.columnconfigure(2, weight=1)  # Preview panel
        self.root.rowconfigure(0, weight=1)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Item", command=self.new_item)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reload All", command=self.load_items)
        tools_menu.add_command(label="Edit Scripts", command=self.edit_scripts)

    def setup_item_list(self):
        # Search frame
        search_frame = ttk.Frame(self.left_panel)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_items)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)

        # Item list
        self.item_list = ttk.Treeview(self.left_panel, columns=("ID", "Category", "File"),
                                     show='headings', selectmode="browse")
        self.item_list.grid(row=1, column=0, sticky="nsew")
        
        # Configure columns
        self.item_list.heading("ID", text="ID", command=lambda: self.sort_items("ID"))
        self.item_list.heading("Category", text="Category", command=lambda: self.sort_items("Category"))
        self.item_list.heading("File", text="File", command=lambda: self.sort_items("File"))
        
        self.item_list.column("ID", width=50)
        self.item_list.column("Category", width=100)
        self.item_list.column("File", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.item_list.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.item_list.configure(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.item_list.bind('<<TreeviewSelect>>', self.on_item_select)
        
        # Configure grid weights
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(1, weight=1)

    def setup_edit_form(self):
        # Create notebook for different property categories
        self.notebook = ttk.Notebook(self.edit_panel)
        self.notebook.pack(fill="both", expand=True)

        # Basic properties tab
        basic_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(basic_frame, text="Basic")
        
        # Add basic fields
        basic_fields = [
            ("ID", "id", "number"),
            ("Name", "name", "text"),
            ("Category", "category", "combo", ["weapon", "tool", "armor", "consumable", "material", "block", "seed"]),
            ("Stack Size", "stack_size", "number"),
            ("Texture X", "texture_x", "number"),
            ("Texture Y", "texture_y", "number")
        ]

        self.entries = {}
        for i, (label, key, field_type, *args) in enumerate(basic_fields):
            ttk.Label(basic_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            
            if field_type == "combo":
                widget = ttk.Combobox(basic_frame, values=args[0])
                widget.state(['readonly'])
            else:
                widget = ttk.Entry(basic_frame)
                
            widget.grid(row=i, column=1, sticky="ew", pady=2)
            self.entries[key] = widget
            
            if field_type == "number":
                widget.bind('<KeyRelease>', lambda e, w=widget: self.validate_numeric(w))

        # Modifiers tab
        modifier_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(modifier_frame, text="Modifiers")
        
        # Add modifier fields
        modifier_fields = ["damage", "defense", "health", "attack_speed", "movement_speed"]
        self.modifier_entries = {}
        for i, field in enumerate(modifier_fields):
            ttk.Label(modifier_frame, text=field.replace('_', ' ').title()).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(modifier_frame)
            entry.grid(row=i, column=1, sticky="ew")
            self.modifier_entries[field] = entry
            entry.bind('<KeyRelease>', lambda e, w=entry: self.validate_numeric(w))

        # Effects tab
        effects_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(effects_frame, text="Effects")
        
        # Add effects fields
        effects_fields = ["healing", "hunger_restore", "thirst_restore"]
        self.effects_entries = {}
        for i, field in enumerate(effects_fields):
            ttk.Label(effects_frame, text=field.replace('_', ' ').title()).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(effects_frame)
            entry.grid(row=i, column=1, sticky="ew")
            self.effects_entries[field] = entry
            entry.bind('<KeyRelease>', lambda e, w=entry: self.validate_numeric(w))

        # Scripts tab
        script_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(script_frame, text="Scripts")
        
        self.script_text = tk.Text(script_frame, height=20)
        self.script_text.pack(fill="both", expand=True)

        # Add save button at bottom
        save_frame = ttk.Frame(self.edit_panel)
        save_frame.pack(fill="x", pady=5)
        
        ttk.Button(save_frame, text="Save Changes", command=self.save_item).pack(side="right")
        ttk.Button(save_frame, text="Delete Item", command=self.delete_item).pack(side="right", padx=5)

    def setup_preview_panel(self):
        # Texture preview
        self.preview_canvas = tk.Canvas(self.preview_panel, width=128, height=128)
        self.preview_canvas.pack(pady=10)

        # Item stats preview
        self.stats_text = tk.Text(self.preview_panel, height=10, width=30)
        self.stats_text.pack(fill="both", expand=True)
        self.stats_text.config(state="disabled")

    def load_schema(self):
        schema_path = Path(__file__).parent / 'item_schema.json'
        with open(schema_path) as f:
            self.schema = json.load(f)

    def load_texture_atlas(self):
        """Load the texture atlas with proper error handling"""
        try:
            atlas_path = Path(__file__).parent.parent / 'assets' / 'textures' / 'items.png'
            if not atlas_path.exists():
                self.create_default_texture_atlas(atlas_path)
            self.texture_atlas = pygame.image.load(str(atlas_path))
            self.texture_size = 16  # Set texture size to 16x16
        except Exception as e:
            print(f"Error loading texture atlas: {e}")
            self.texture_atlas = pygame.Surface((256, 256))  # Smaller default size
            self.texture_atlas.fill((255, 0, 255))
            self.texture_size = 16

    def create_default_texture_atlas(self, path):
        """Create a default texture atlas with missing texture pattern"""
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a 512x512 texture atlas (16x16 grid of 32x32 textures)
        atlas = pygame.Surface((512, 512))
        
        # Fill with missing texture pattern (black and magenta checkerboard)
        for y in range(16):
            for x in range(16):
                rect = pygame.Rect(x * 32, y * 32, 32, 32)
                color = (255, 0, 255) if (x + y) % 2 == 0 else (0, 0, 0)
                pygame.draw.rect(atlas, color, rect)
                pygame.draw.rect(atlas, (128, 128, 128), rect, 1)

        # Save the atlas
        pygame.image.save(atlas, str(path))
        print(f"Created default texture atlas at {path}")

    def load_items(self):
        """Load items with explicit UTF-8 encoding"""
        self.item_list.delete(*self.item_list.get_children())
        data_dir = Path(__file__).parent.parent / 'data' / 'items'
        
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    for item_id, data in items.items():
                        # Ensure basic fields exist and are the correct type
                        if not isinstance(data.get('id'), int):
                            data['id'] = int(str(data['id']).strip())
                        if not isinstance(data.get('texture_coords'), list):
                            data['texture_coords'] = [0, 0]
                        self.item_list.insert("", "end", text=item_id, 
                                            values=(data["id"], data["category"], json_file.name))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {json_file}: {e}")

    def on_item_select(self, event):
        selected = self.item_list.selection()
        if not selected:
            return
            
        try:
            item_id = str(self.item_list.item(selected[0])['text'])
            json_file = str(self.item_list.item(selected[0])['values'][2])
            
            file_path = Path(__file__).parent.parent / 'data' / 'items' / json_file
            with open(file_path, encoding='utf-8') as f:
                raw_data = json.load(f)
                data = raw_data[item_id]
                
            # Ensure all data fields are properly decoded
            if isinstance(data, bytes):
                data = json.loads(data.decode('utf-8'))
            
            # Ensure numeric fields are numbers
            data['id'] = int(data['id'])
            data['stack_size'] = int(data.get('stack_size', 64))
            
            if 'modifiers' in data:
                data['modifiers'] = {k: float(v) for k, v in data['modifiers'].items()}
            
            if 'effects' in data:
                data['effects'] = {k: float(v) for k, v in data['effects'].items()}

            # Fill form fields and update preview with sanitized data
            self._fill_form_fields(data)
            self.update_preview(data)
                    
        except Exception as e:
            print(f"Error details - file: {json_file}, item: {item_id}")
            print(f"Error loading item data: {e}")
            print(f"Raw data: {data}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load item data: {e}")

    def _fill_form_fields(self, data):
        """Fill form fields with sanitized data"""
        # Basic fields
        self.entries['id'].delete(0, tk.END)
        self.entries['id'].insert(0, str(data['id']))
        
        self.entries['name'].delete(0, tk.END)
        self.entries['name'].insert(0, str(data['name']))
        
        self.entries['category'].set(str(data['category']))
        
        self.entries['stack_size'].delete(0, tk.END)
        self.entries['stack_size'].insert(0, str(data.get('stack_size', 64)))
        
        # Texture coordinates
        coords = data['texture_coords']
        self.entries['texture_x'].delete(0, tk.END)
        self.entries['texture_x'].insert(0, str(coords[0]))
        
        self.entries['texture_y'].delete(0, tk.END)
        self.entries['texture_y'].insert(0, str(coords[1]))
        
        # Clear and fill modifiers
        for key, entry in self.modifier_entries.items():
            entry.delete(0, tk.END)
            if 'modifiers' in data and key in data['modifiers']:
                entry.insert(0, str(data['modifiers'][key]))
        
        # Clear and fill effects
        for key, entry in self.effects_entries.items():
            entry.delete(0, tk.END)
            if 'effects' in data and key in data['effects']:
                entry.insert(0, str(data['effects'][key]))
        
        # Script
        self.script_text.delete(1.0, tk.END)
        if 'script' in data:
            self.script_text.insert(tk.END, str(data['script']))

    def save_item(self):
        selected = self.item_list.selection()
        if not selected:
            return
            
        item_id = self.item_list.item(selected[0])['text']
        json_file = self.item_list.item(selected[0])['values'][2]
        
        try:
            # Build item data
            data = {
                "id": int(self.entries['id'].get()),
                "name": self.entries['name'].get(),
                "category": self.entries['category'].get(),
                "stack_size": int(self.entries['stack_size'].get()),
                "texture_coords": [
                    int(self.entries['texture_x'].get()),
                    int(self.entries['texture_y'].get())
                ]
            }
            
            # Add modifiers if any
            modifiers = {}
            for key, entry in self.modifier_entries.items():
                if entry.get():
                    modifiers[key] = float(entry.get())
            if modifiers:
                data['modifiers'] = modifiers
            
            # Add effects if any
            effects = {}
            for key, entry in self.effects_entries.items():
                if entry.get():
                    effects[key] = float(entry.get())
            if effects:
                data['effects'] = effects
            
            # Add script if any
            script = self.script_text.get(1.0, tk.END).strip()
            if script:
                data['script'] = script
            
            # Load existing file
            file_path = Path(__file__).parent.parent / 'data' / 'items' / json_file
            with open(file_path) as f:
                all_items = json.load(f)
            
            # Update item
            all_items[item_id] = data
            
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(all_items, f, indent=4)
                
            messagebox.showinfo("Success", "Item saved successfully!")
            self.load_items()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save item: {e}")

    def new_item(self):
        # TODO: Implement new item creation
        messagebox.showinfo("Info", "New item creation not implemented yet")

    def delete_item(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this item?"):
            # TODO: Implement item deletion
            messagebox.showinfo("Info", "Item deletion not implemented yet")

    def save_all(self):
        """Save all changes to all JSON files"""
        try:
            data_dir = Path(__file__).parent.parent / 'data' / 'items'
            files_saved = 0
            
            for json_file in data_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        items = json.load(f)
                    
                    # Save back to file with proper formatting
                    with open(json_file, 'w') as f:
                        json.dump(items, f, indent=4)
                    files_saved += 1
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {json_file.name}: {e}")
            
            messagebox.showinfo("Success", f"Saved {files_saved} item files successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save items: {e}")

    def edit_scripts(self):
        """Open script editor for selected item"""
        selected = self.item_list.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select an item first")
            return
            
        item_id = self.item_list.item(selected[0])['text']
        script_path = Path(__file__).parent.parent / 'scripts' / f"{item_id.lower()}.py"
        
        # Create script if it doesn't exist
        if not script_path.exists():
            default_script = '''class ItemScript:
    def __init__(self, item):
        self.item = item

    def on_hit(self, target):
        """Custom hit behavior"""
        import random
        if random.random() < 0.1:  # 10% chance
            if hasattr(target, 'apply_effect'):
                target.apply_effect('bleeding', duration=5000)
'''
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, 'w') as f:
                f.write(default_script)
        
        # Open script in system default editor
        import os
        os.startfile(script_path) if os.name == 'nt' else os.system(f'xdg-open {script_path}')

    def filter_items(self, *args):
        """Filter items based on search text"""
        search_term = self.search_var.get().lower()
        self.item_list.delete(*self.item_list.get_children())
        
        data_dir = Path(__file__).parent.parent / 'data' / 'items'
        for json_file in data_dir.glob("*.json"):
            with open(json_file) as f:
                items = json.load(f)
                for item_id, data in items.items():
                    if (search_term in item_id.lower() or 
                        search_term in data["name"].lower() or 
                        search_term in data["category"].lower()):
                        self.item_list.insert("", "end", text=item_id,
                                            values=(data["id"], data["category"], json_file.name))

    def sort_items(self, column):
        """Sort items by column"""
        items = [(self.item_list.set(item, column), item) 
                for item in self.item_list.get_children("")]
        items.sort()
        
        for index, (_, item) in enumerate(items):
            self.item_list.move(item, "", index)

    def validate_numeric(self, widget):
        """Validate numeric input"""
        value = widget.get()
        if value:
            try:
                float(value)
                widget.config(style='TEntry')
            except ValueError:
                widget.config(style='Error.TEntry')
                return False
        return True

    def update_preview(self, data):
        """Update preview with better error handling"""
        try:
            # Handle texture preview
            tx, ty = data.get('texture_coords', [0, 0])
            if not isinstance(tx, int): tx = int(str(tx).strip())
            if not isinstance(ty, int): ty = int(str(ty).strip())
            
            # Get texture from atlas and render preview
            if 0 <= tx * self.texture_size < self.texture_atlas.get_width() and 0 <= ty * self.texture_size < self.texture_atlas.get_height():
                # Extract texture from atlas
                texture = self.texture_atlas.subsurface((
                    tx * self.texture_size,
                    ty * self.texture_size,
                    self.texture_size,
                    self.texture_size
                ))
                
                # Scale up to preview size
                scaled = pygame.transform.scale(texture, (128, 128))
                
                # Convert to PhotoImage
                from PIL import Image, ImageTk
                import io
                
                # Convert Pygame surface to PNG bytes
                png_bytes = io.BytesIO()
                pygame.image.save(scaled, png_bytes, "PNG")
                png_bytes.seek(0)
                
                # Create PIL Image and PhotoImage
                image = Image.open(png_bytes)
                photo = ImageTk.PhotoImage(image)
                
                # Update canvas
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(64, 64, image=photo, anchor="center")
                self.preview_canvas.image = photo  # Keep reference
            else:
                self._show_missing_texture()
                
            # Update stats text
            # ...rest of existing stats code...

        except Exception as e:
            print(f"Error in preview: {e}")
            print(f"Data received: {data}")
            self._show_missing_texture()

    def _show_missing_texture(self):
        """Show missing texture pattern in preview"""
        self.preview_canvas.delete("all")
        # Create a more visible missing texture pattern
        for y in range(8):
            for x in range(8):
                color = "#FF00FF" if (x + y) % 2 == 0 else "#000000"
                self.preview_canvas.create_rectangle(
                    x * 16, y * 16, (x + 1) * 16, (y + 1) * 16,
                    fill=color, outline="#808080"
                )

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    editor = ItemEditor()
    editor.run()
