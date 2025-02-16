import pygame
import config as c
from ui_tooltip import Tooltip, get_item_tooltip

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

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            clicked_slot = self.get_slot_at_pos(mouse_pos)
            
            print(f"DEBUG: Clicked at {mouse_pos}, slot: {clicked_slot}")
            
            if clicked_slot:
                slot_type, slot = clicked_slot
                print(f"DEBUG: Checking slot type: {slot_type}, index: {slot}")

                # Handle hotbar slots first
                if slot_type == "hotbar":
                    if 0 <= slot < len(self.player_inventory.hotbar):
                        if self.player_inventory.hotbar[slot] and self.player_inventory.hotbar[slot].get("item"):
                            self.dragging_item = dict(self.player_inventory.hotbar[slot])
                            self.player_inventory.hotbar[slot] = {"item": None, "quantity": 0}
                            self.drag_source = ("hotbar", slot)
                            print(f"DEBUG: Picked up from hotbar: {self.dragging_item}")
                            return

                # Get item from source with deep copy
                source_item = None
                if slot_type == "input" and self.furnace.input_slot and self.furnace.input_slot.get("item"):
                    source_item = dict(self.furnace.input_slot)
                    self.furnace.input_slot = {"item": None, "quantity": 0}
                elif slot_type == "fuel" and self.furnace.fuel_slot and self.furnace.fuel_slot.get("item"):
                    source_item = dict(self.furnace.fuel_slot)
                    self.furnace.fuel_slot = {"item": None, "quantity": 0}
                elif slot_type == "output" and self.furnace.output_slot and self.furnace.output_slot.get("item"):
                    source_item = dict(self.furnace.output_slot)
                    self.furnace.output_slot = {"item": None, "quantity": 0}
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
                mouse_pos = pygame.mouse.get_pos()
                target_slot = self.get_slot_at_pos(mouse_pos)
                
                if not target_slot:
                    print("DEBUG: No target slot, returning to source")
                    self.return_to_source()
                else:
                    slot_type, slot = target_slot
                    print(f"DEBUG: Target slot type: {slot_type}, slot: {slot}")
                    
                    target_item = self.get_slot_contents(slot_type, slot)
                    print(f"DEBUG: Target contains: {target_item}")

                    if not target_item or not target_item.get("item"):
                        # Place in empty slot
                        if slot_type == "fuel" and not hasattr(self.dragging_item["item"], "burn_time"):
                            print("DEBUG: Cannot place non-fuel item in fuel slot")
                            self.return_to_source()
                        else:
                            dragged_copy = {"item": self.dragging_item["item"], "quantity": self.dragging_item["quantity"]}
                            self.place_item(slot_type, slot, dragged_copy)
                            print(f"DEBUG: Placed item in {slot_type} slot {slot}")
                            self.dragging_item = None
                    else:
                        # Handle stacking or swapping
                        if target_item["item"].id == self.dragging_item["item"].id:
                            total = target_item["quantity"] + self.dragging_item["quantity"]
                            stack_size = target_item["item"].stack_size
                            if total <= stack_size:
                                target_item["quantity"] = total
                                self.dragging_item = None
                                print(f"DEBUG: Stacked items, new quantity: {total}")
                            else:
                                target_item["quantity"] = stack_size
                                self.dragging_item["quantity"] = total - stack_size
                                print(f"DEBUG: Partial stack, remaining: {self.dragging_item['quantity']}")
                        else:
                            # Swap items
                            temp = {"item": target_item["item"], "quantity": target_item["quantity"]}
                            self.place_item(slot_type, slot, self.dragging_item)
                            self.dragging_item = temp
                            print("DEBUG: Swapped items")

                if self.dragging_item:
                    print("DEBUG: Returning remaining items to source")
                    self.return_to_source()
                self.dragging_item = None
                self.drag_source = None

    def get_slot_contents(self, slot_type, slot):
        """Helper method to get contents of a slot"""
        if slot_type == "input":
            return self.furnace.input_slot
        elif slot_type == "fuel":
            return self.furnace.fuel_slot
        elif slot_type == "output":
            return self.furnace.output_slot
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
        item_copy = {"item": item["item"], "quantity": item["quantity"]}
        if slot_type == "input":
            self.furnace.input_slot = item_copy
        elif slot_type == "fuel":
            self.furnace.fuel_slot = item_copy
        elif slot_type == "output":
            self.furnace.output_slot = item_copy
        elif slot_type == "inventory":
            self.player_inventory.main[slot] = item_copy
        elif slot_type == "hotbar":
            self.player_inventory.hotbar[slot] = item_copy
        print(f"DEBUG: Placed {item_copy['quantity']} {item_copy['item'].name} in {slot_type} slot {slot}")

    def return_to_source(self):
        if self.drag_source:
            source_type, slot = self.drag_source
            if source_type == "input":
                self.furnace.input_slot = self.dragging_item
            elif source_type == "fuel":
                self.furnace.fuel_slot = self.dragging_item
            elif source_type == "output":
                self.furnace.output_slot = self.dragging_item
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
            if self.furnace.input_slot and self.furnace.input_slot.get("item"):
                self.hovered_item = self.furnace.input_slot["item"]
        elif self.fuel_rect.collidepoint(pos):
            slot_info = ("fuel", None)
            if self.furnace.fuel_slot and self.furnace.fuel_slot.get("item"):
                self.hovered_item = self.furnace.fuel_slot["item"]
        elif self.output_rect.collidepoint(pos):
            slot_info = ("output", None)
            if self.furnace.output_slot and self.furnace.output_slot.get("item"):
                self.hovered_item = self.furnace.output_slot["item"]

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

    def draw(self):
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
        if self.furnace.is_burning:
            burn_height = int((self.furnace.burn_time_remaining / 1000) * self.slot_size)
            burn_rect = pygame.Rect(self.fuel_rect.right + 10, 
                                  self.fuel_rect.bottom - burn_height,
                                  10, burn_height)
            pygame.draw.rect(self.screen, (255, 128, 0), burn_rect)

            melt_width = int((self.furnace.melt_progress / 1000) * (self.output_rect.left - self.input_rect.right - 20))
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
