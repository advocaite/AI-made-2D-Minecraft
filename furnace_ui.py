import pygame
import config as c
from ui_tooltip import Tooltip, get_item_tooltip
import random  # Add this import

class FurnaceUI:
    def __init__(self, screen, player_inventory, furnace_block, atlas):
        self.screen = screen
        self.player_inventory = player_inventory
        self.furnace = furnace_block
        self.atlas = atlas
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.dragging_item = None
        self.drag_source = None

        # Calculate UI dimensions
        self.slot_size = 50
        self.padding = 10
        screen_center_x = c.SCREEN_WIDTH // 2
        screen_center_y = c.SCREEN_HEIGHT // 2

        # Center the furnace UI at the top
        furnace_y_offset = 50  # Move furnace section up near top of screen
        furnace_section_width = self.slot_size * 4  # Total width of furnace section

        # Calculate furnace background rectangle
        furnace_padding = 20
        furnace_width = self.slot_size * 5  # Width to encompass all slots
        furnace_height = self.slot_size * 3  # Height to encompass all slots
        self.furnace_rect = pygame.Rect(
            screen_center_x - furnace_width//2,
            furnace_y_offset - furnace_padding,
            furnace_width,
            furnace_height + furnace_padding * 2
        )

        # Calculate furnace slot positions (centered at top)
        self.input_rect = pygame.Rect(
            screen_center_x - self.slot_size - 50,
            furnace_y_offset,  # Position from top
            self.slot_size,
            self.slot_size
        )
        self.fuel_rect = pygame.Rect(
            screen_center_x - self.slot_size - 50,
            furnace_y_offset + self.slot_size + 20,  # Below input slot
            self.slot_size,
            self.slot_size
        )
        self.output_rect = pygame.Rect(
            screen_center_x + 50,
            furnace_y_offset + (self.slot_size + 20) // 2,  # Centered between input and fuel
            self.slot_size,
            self.slot_size
        )

        # Center inventory section in middle of screen
        self.inventory_width = 8 * (self.slot_size + self.padding) - self.padding
        self.hotbar_width = 9 * (self.slot_size + self.padding) - self.padding
        self.max_width = max(self.inventory_width, self.hotbar_width)

        # Calculate vertical spacing
        total_height = (
            4 * self.slot_size +  # 4 rows of main inventory
            3 * self.padding +    # padding between rows
            self.slot_size        # hotbar height
        )

        # Position inventory in middle of remaining space
        remaining_height = c.SCREEN_HEIGHT - (furnace_y_offset + self.slot_size * 3)
        inventory_start_y = furnace_y_offset + self.slot_size * 3 + (remaining_height - total_height) // 2

        self.inventory_start_x = screen_center_x - self.inventory_width // 2
        self.inventory_start_y = inventory_start_y

        # Position hotbar at bottom with padding
        self.hotbar_start_x = screen_center_x - self.hotbar_width // 2
        self.hotbar_start_y = self.inventory_start_y + 4 * (self.slot_size + self.padding) + self.padding

        # Add labels for sections
        self.font = pygame.font.SysFont(None, 24)
        self.input_label = self.font.render("Input", True, (255, 255, 255))
        self.fuel_label = self.font.render("Fuel", True, (255, 255, 255))
        self.output_label = self.font.render("Output", True, (255, 255, 255))
        self.tooltip = Tooltip(self.font)
        self.hovered_item = None

        # Add glow effect properties
        self.glow_colors = [
            (255, 100, 0, 255),   # Orange
            (255, 200, 0, 255),   # Yellow
            (255, 100, 0, 255)    # Orange
        ]

        # Add default minimum burn time to prevent division by zero
        self.min_burn_time = 1000  # 1 second minimum

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            clicked_slot = self.get_slot_at_pos(mouse_pos)
            print("\n=== DRAG START ===")
            print(f"Mouse position: {mouse_pos}")
            print(f"Clicked slot: {clicked_slot}")
            
            if clicked_slot:
                slot_type, slot = clicked_slot
                print(f"Slot contents before pickup:")
                if slot_type == "fuel":
                    print(f"Fuel slot: {self.furnace.script.fuel_slot}")
                elif slot_type == "input":
                    print(f"Input slot: {self.furnace.script.input_slot}")
                elif slot_type == "output":
                    print(f"Output slot: {self.furnace.script.output_slot}")
                elif slot_type == "inventory":
                    print(f"Inventory slot {slot}: {self.player_inventory.main[slot]}")
                elif slot_type == "hotbar":
                    print(f"Hotbar slot {slot}: {self.player_inventory.hotbar[slot]}")

                # Get item from source with deep copy
                source_item = None
                if slot_type == "input":
                    source_item = dict(self.furnace.script.input_slot)  # Use script
                    self.furnace.script.input_slot = {"item": None, "quantity": 0}
                elif slot_type == "fuel":
                    source_item = dict(self.furnace.script.fuel_slot)  # Use script
                    self.furnace.script.fuel_slot = {"item": None, "quantity": 0}
                elif slot_type == "output":
                    source_item = dict(self.furnace.script.output_slot)  # Use script
                    self.furnace.script.output_slot = {"item": None, "quantity": 0}
                elif slot_type == "inventory":
                    if 0 <= slot < len(self.player_inventory.main):
                        slot_data = self.player_inventory.main[slot]
                        if slot_data and slot_data.get("item"):
                            source_item = {"item": slot_data["item"], "quantity": slot_data["quantity"]}
                            self.player_inventory.main[slot] = {"item": None, "quantity": 0}
                elif slot_type == "hotbar":
                    if 0 <= slot < len(self.player_inventory.hotbar):
                        slot_data = self.player_inventory.hotbar[slot]
                        if slot_data and slot_data.get("item"):
                            source_item = {"item": slot_data["item"], "quantity": slot_data["quantity"]}
                            self.player_inventory.hotbar[slot] = {"item": None, "quantity": 0}

                if source_item and source_item.get("item"):
                    print(f"DEBUG: Picked up item: {source_item}")
                    self.dragging_item = source_item
                    self.drag_source = (slot_type, slot)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_item and self.dragging_item.get("item"):
                print("\n=== DROP ATTEMPT ===")
                print(f"Dragging item: {self.dragging_item}")
                mouse_pos = pygame.mouse.get_pos()
                target_slot = self.get_slot_at_pos(mouse_pos)
                print(f"Target slot: {target_slot}")
                
                if target_slot:
                    slot_type, slot = target_slot
                    target_contents = self.get_slot_contents(slot_type, slot)
                    print(f"Target contents: {target_contents}")
                    
                    # Additional debug for fuel slot
                    if slot_type == "fuel":
                        item = self.dragging_item.get("item")
                        print(f"Item being dropped: {item.name if item else None}")
                        print(f"Item burn time: {getattr(item, 'burn_time', None) if item else None}")
                        print(f"Is fuel?: {hasattr(item, 'burn_time') if item else False}")

                if not target_slot:
                    print("DEBUG: No target slot, returning to source")
                    self.return_to_source()
                else:
                    slot_type, slot = target_slot
                    print(f"DEBUG: Target slot type: {slot_type}, slot: {slot}")
                    
                    target_item = self.get_slot_contents(slot_type, slot)
                    print(f"DEBUG: Target contains: {target_item}")

                    # Check if item can be placed in furnace slots
                    if slot_type == "fuel" and not hasattr(self.dragging_item["item"], "burn_time"):
                        print("DEBUG: Cannot place non-fuel item in fuel slot")
                        self.return_to_source()
                        self.dragging_item = None
                        self.drag_source = None
                        return

                    # Place or swap items
                    if not target_item or not target_item.get("item"):
                        dragged_copy = {"item": self.dragging_item["item"], "quantity": self.dragging_item["quantity"]}
                        self.place_item(slot_type, slot, dragged_copy)
                        self.dragging_item = None
                    else:
                        # Handle stacking or swapping
                        if target_item["item"].id == self.dragging_item["item"].id:
                            self.handle_stacking(slot_type, slot, target_item)
                        else:
                            # Swap items
                            temp = dict(target_item)  # Make a copy of target item
                            self.place_item(slot_type, slot, dict(self.dragging_item))
                            self.dragging_item = temp
                            print("DEBUG: Swapped items")

                if self.dragging_item:
                    print("DEBUG: Returning remaining items to source")
                    self.return_to_source()
                self.dragging_item = None
                self.drag_source = None

                print("\n=== AFTER DROP ===")
                if target_slot:
                    slot_type, slot = target_slot
                    if slot_type == "fuel":
                        print(f"Fuel slot after: {self.furnace.script.fuel_slot}")
                    elif slot_type == "input":
                        print(f"Input slot after: {self.furnace.script.input_slot}")
                    print(f"Dragging item after: {self.dragging_item}")

    def get_slot_contents(self, slot_type, slot):
        """Helper method to get contents of a slot"""
        if slot_type == "input":
            return self.furnace.script.input_slot  # Use script
        elif slot_type == "fuel":
            return self.furnace.script.fuel_slot   # Use script
        elif slot_type == "output":
            return self.furnace.script.output_slot # Use script
        elif slot_type == "inventory":
            return self.player_inventory.main[slot]
        elif slot_type == "hotbar":
            return self.player_inventory.hotbar[slot]
        return None

    def swap_items(self, slot_type, slot, target_item):
        """Helper method to swap items between slots"""
        if slot_type == "input":
            self.furnace.input_slot = self.dragging_item
            self.dragging_item = target_item
        elif slot_type == "fuel":
            if hasattr(self.dragging_item["item"], "burn_time"):
                self.furnace.fuel_slot = self.dragging_item
                self.dragging_item = target_item
            else:
                self.return_to_source()
        elif slot_type == "output":
            self.furnace.output_slot = self.dragging_item
            self.dragging_item = target_item
        elif slot_type == "inventory":
            self.player_inventory.main[slot] = self.dragging_item
            self.dragging_item = target_item
        elif slot_type == "hotbar":
            self.player_inventory.hotbar[slot] = self.dragging_item
            self.dragging_item = target_item

    def place_item(self, slot_type, slot, item):
        """Place a deep copy of the item in the target slot"""
        print(f"\n=== PLACING ITEM ===")
        print(f"Slot type: {slot_type}")
        print(f"Item being placed: {item}")
        
        item_copy = {"item": item["item"], "quantity": item["quantity"]}
        
        if slot_type == "fuel":
            print(f"Placing in fuel slot. Item burn time: {getattr(item['item'], 'burn_time', None)}")
            self.furnace.script.fuel_slot = item_copy
            print(f"Fuel slot after placement: {self.furnace.script.fuel_slot}")
        elif slot_type == "input":
            self.furnace.script.input_slot = item_copy
        elif slot_type == "output":
            self.furnace.script.output_slot = item_copy
        elif slot_type == "inventory":
            self.player_inventory.main[slot] = item_copy
        elif slot_type == "hotbar":
            self.player_inventory.hotbar[slot] = item_copy

        print(f"DEBUG: Placed {item_copy['quantity']} {item_copy['item'].name} in {slot_type} slot {slot}")

    def return_to_source(self):
        if self.drag_source:
            source_type, slot = self.drag_source
            if source_type == "input":
                self.furnace.script.input_slot = self.dragging_item   # Use script
            elif source_type == "fuel":
                self.furnace.script.fuel_slot = self.dragging_item    # Use script
            elif source_type == "output":
                self.furnace.script.output_slot = self.dragging_item  # Use script
            elif source_type == "inventory":
                self.player_inventory.main[slot] = self.dragging_item
            elif source_type == "hotbar":
                self.player_inventory.hotbar[slot] = self.dragging_item

    def get_slot_at_pos(self, pos):
        """Fixed slot detection logic"""
        mx, my = pos
        slot_info = None
        self.hovered_item = None  # Reset hovered item

        # Check furnace slots first
        if self.input_rect.collidepoint(pos):
            slot_info = ("input", None)
            if self.furnace.script.input_slot and self.furnace.script.input_slot.get("item"):  # Use script
                self.hovered_item = self.furnace.script.input_slot["item"]
        elif self.fuel_rect.collidepoint(pos):
            slot_info = ("fuel", None)
            if self.furnace.script.fuel_slot and self.furnace.script.fuel_slot.get("item"):    # Use script
                self.hovered_item = self.furnace.script.fuel_slot["item"]
        elif self.output_rect.collidepoint(pos):
            slot_info = ("output", None)
            if self.furnace.script.output_slot and self.furnace.script.output_slot.get("item"): # Use script
                self.hovered_item = self.furnace.script.output_slot["item"]

        # Check main inventory slots
        if not slot_info:
            for i in range(len(self.player_inventory.main)):
                row = i // 8
                col = i % 8
                x = self.inventory_start_x + col * (self.slot_size + self.padding)
                y = self.inventory_start_y + row * (self.slot_size + self.padding)
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                if rect.collidepoint(mx, my):
                    slot_info = ("inventory", i)
                    if self.player_inventory.main[i] and self.player_inventory.main[i].get("item"):
                        self.hovered_item = self.player_inventory.main[i]["item"]
                    break

        # Check hotbar slots
        if not slot_info:
            for i in range(len(self.player_inventory.hotbar)):
                x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                y = self.hotbar_start_y
                rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                if rect.collidepoint(mx, my):
                    slot_info = ("hotbar", i)
                    if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                        self.hovered_item = self.player_inventory.hotbar[i]["item"]
                    break

        return slot_info

    def handle_stacking(self, slot_type, slot, target_item):
        """Helper method to handle item stacking"""
        space = target_item["item"].stack_size - target_item["quantity"]
        if space > 0:
            amount = min(space, self.dragging_item["quantity"])
            target_item["quantity"] += amount
            self.dragging_item["quantity"] -= amount
            if self.dragging_item["quantity"] <= 0:
                self.dragging_item = None
            else:
                self.return_to_source()
        else:
            self.swap_items(slot_type, slot, dict(target_item))

    def draw_smelting_glow(self):
        """Draw glow effect synchronized with smelting progress"""
        if not self.furnace.script.is_burning:
            return
            
        # Create surfaces for input and fuel slot glows
        input_glow = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        fuel_glow = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Calculate progress percentages with safety checks
        melt_progress = self.furnace.script.melt_progress / 1000  # Convert to 0-1 range
        
        # Prevent division by zero for burn progress
        max_burn_time = max(self.furnace.script.max_burn_time, self.min_burn_time)
        burn_progress = self.furnace.script.burn_time_remaining / max_burn_time

        # Draw input slot glow (moves up as item melts)
        gradient_height = self.slot_size
        for i in range(gradient_height):
            rel_pos = i / gradient_height
            if rel_pos < melt_progress:
                # Calculate color based on position
                color_idx = rel_pos * (len(self.glow_colors) - 1)
                base_idx = int(color_idx)
                next_idx = min(base_idx + 1, len(self.glow_colors) - 1)
                blend = color_idx - base_idx
                
                # Interpolate between colors
                c1 = self.glow_colors[base_idx]
                c2 = self.glow_colors[next_idx]
                color = [
                    int(c1[j] * (1 - blend) + c2[j] * blend) for j in range(4)
                ]
                
                # Draw line of gradient
                pygame.draw.line(input_glow, color, (0, gradient_height - i), (self.slot_size, gradient_height - i))
        
        # Draw fuel slot glow (fades out as fuel burns)
        fuel_alpha = int(255 * burn_progress)
        for i in range(gradient_height):
            rel_pos = i / gradient_height
            color = (*self.glow_colors[0][:3], int(fuel_alpha * (1 - rel_pos)))
            pygame.draw.line(fuel_glow, color, (0, i), (self.slot_size, i))
        
        # Draw glow surfaces under slots
        self.screen.blit(input_glow, self.input_rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)
        self.screen.blit(fuel_glow, self.fuel_rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)
        
        # Draw ember particles from fuel slot
        if self.furnace.script.is_burning:
            self.draw_ember_particles(burn_progress)

    def draw_ember_particles(self, burn_progress):
        """Draw floating ember particles based on burn progress"""
        num_particles = int(5 * burn_progress)
        for _ in range(num_particles):
            x = self.fuel_rect.centerx + random.randint(-10, 10)
            y = self.fuel_rect.top + random.randint(-15, 0)
            size = random.randint(2, 4)
            alpha = int(255 * burn_progress * random.random())
            
            pygame.draw.circle(
                self.screen,
                (255, 200, 0, alpha),
                (x, y),
                size
            )

    def draw(self):
        """Draw the furnace UI"""
        # Draw UI background
        self.screen.fill((30, 30, 30))
        overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Draw furnace interface
        pygame.draw.rect(self.screen, (139, 69, 19), self.furnace_rect)
        pygame.draw.rect(self.screen, (101, 67, 33), self.furnace_rect, 2)

        # Draw slots
        slots = [
            (self.input_rect, self.furnace.script.input_slot),
            (self.fuel_rect, self.furnace.script.fuel_slot),
            (self.output_rect, self.furnace.script.output_slot)
        ]

        for rect, slot in slots:
            # Draw slot background
            pygame.draw.rect(self.screen, (50, 50, 50), rect)
            pygame.draw.rect(self.screen, (100, 100, 100), rect, 1)
            
            # Draw item in slot if present
            if slot and slot.get("item"):
                item = slot["item"]
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.atlas.subsurface(texture_rect)  # Changed from self.texture_atlas to self.atlas
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                self.screen.blit(scaled_texture, (rect.x+4, rect.y+4))
                
                # Draw quantity if more than 1
                if slot["quantity"] > 1:
                    quantity_text = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    self.screen.blit(quantity_text, (rect.x + rect.width - 20, rect.y + rect.height - 20))

        # Get current mouse position and update hovered item at start of draw
        mouse_pos = pygame.mouse.get_pos()
        self.get_slot_at_pos(mouse_pos)  # This updates self.hovered_item

        # Create single translucent background
        bg_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_overlay.fill((0, 0, 0, 160))  # Reduced opacity (160 instead of 180)
        self.screen.blit(bg_overlay, (0, 0))

        # Draw slots with semi-transparent backgrounds
        slot_bg = (70, 70, 70, 200)
        slot_border = (200, 200, 200, 255)

        # Draw section labels
        self.screen.blit(self.input_label, (self.input_rect.centerx - self.input_label.get_width()//2, 
                                          self.input_rect.top - 25))
        self.screen.blit(self.fuel_label, (self.fuel_rect.centerx - self.fuel_label.get_width()//2, 
                                         self.fuel_rect.top - 25))
        self.screen.blit(self.output_label, (self.output_rect.centerx - self.output_label.get_width()//2, 
                                           self.output_rect.top - 25))

        # Draw furnace slots
        slots = [
            (self.input_rect, self.furnace.input_slot),
            (self.fuel_rect, self.furnace.fuel_slot),
            (self.output_rect, self.furnace.output_slot)
        ]

        for rect, slot in slots:
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            if slot and slot["item"]:
                item = slot["item"]
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
                self.screen.blit(item_img, rect.topleft)
                if slot["quantity"] > 1:
                    quantity = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    self.screen.blit(quantity, (rect.right - quantity.get_width() - 5, rect.bottom - quantity.get_height() - 5))

        # Draw progress indicators if furnace is burning
        if self.furnace.script.is_burning:
            burn_height = int((self.furnace.script.burn_time_remaining / 1000) * self.slot_size)
            burn_rect = pygame.Rect(self.fuel_rect.right + 10, 
                                  self.fuel_rect.bottom - burn_height,
                                  10, burn_height)
            pygame.draw.rect(self.screen, (255, 128, 0), burn_rect)

            melt_width = int((self.furnace.script.melt_progress / 1000) * (self.output_rect.left - self.input_rect.right - 20))
            melt_rect = pygame.Rect(self.input_rect.right + 10,
                                  self.input_rect.centery - 5,
                                  melt_width, 10)
            pygame.draw.rect(self.screen, (255, 0, 0), melt_rect)

        # Draw main inventory
        for i in range(len(self.player_inventory.main)):
            row = i // 8
            col = i % 8
            x = self.inventory_start_x + col * (self.slot_size + self.padding)
            y = self.inventory_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            # Draw slot
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            
            # Draw item if present
            slot = self.player_inventory.main[i]
            if slot and slot["item"]:
                item = slot["item"]
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
                self.screen.blit(item_img, rect.topleft)
                if slot["quantity"] > 1:
                    quantity = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    self.screen.blit(quantity, (rect.right - quantity.get_width() - 5, rect.bottom - quantity.get_height() - 5))

        # Draw inventory title
        inventory_label = self.font.render("Inventory", True, (255, 255, 255))
        self.screen.blit(inventory_label, (self.inventory_start_x + self.max_width//2 - inventory_label.get_width()//2, 
                                         self.inventory_start_y - 25))

        # Draw hotbar section
        hotbar_label = self.font.render("Hotbar", True, (255, 255, 255))
        self.screen.blit(hotbar_label, (self.hotbar_start_x + self.max_width//2 - hotbar_label.get_width()//2, 
                                      self.hotbar_start_y - 25))

        # Draw hotbar slots
        for i in range(len(self.player_inventory.hotbar)):
            x = self.hotbar_start_x + i * (self.slot_size + self.padding)
            y = self.hotbar_start_y
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            # Draw slot background
            pygame.draw.rect(self.screen, slot_bg, rect)
            pygame.draw.rect(self.screen, slot_border, rect, 2)
            if i == self.player_inventory.selected_hotbar_index:
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(6, 6), 3)
            
            # Draw item if present
            slot = self.player_inventory.hotbar[i]
            if slot and slot.get("item"):
                item = slot["item"]
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_img = self.atlas.subsurface(texture_rect)
                item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
                self.screen.blit(item_img, rect.topleft)
                if slot["quantity"] > 1:
                    quantity = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                    self.screen.blit(quantity, (rect.right - quantity.get_width() - 5, rect.bottom - quantity.get_height() - 5))

        # Draw glow effects before items
        self.draw_smelting_glow()

        # Draw dragged item
        if self.dragging_item and self.dragging_item["item"]:
            mx, my = pygame.mouse.get_pos()
            tx, ty = self.dragging_item["item"].texture_coords
            texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
            item_img = self.atlas.subsurface(texture_rect)
            item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
            self.screen.blit(item_img, (mx - self.slot_size//2, my - self.slot_size//2))

        # Draw tooltip last (after dragged item)
        if self.hovered_item and not self.dragging_item:
            tooltip_text = get_item_tooltip(self.hovered_item)
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            self.furnace.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
