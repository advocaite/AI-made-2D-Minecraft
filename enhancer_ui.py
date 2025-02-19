import pygame
import json
import config as c
from block import ENHANCER  # Add this import
from ui_tooltip import Tooltip, get_item_tooltip

class EnhancerUI:
    def __init__(self, screen, player_inventory, atlas):
        self.screen = screen
        self.inventory = player_inventory
        self.atlas = atlas
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.tooltip = Tooltip(self.font)
        
        # Load enhancement recipes
        with open('enhancement_recipes.json', 'r') as f:
            self.recipes = json.load(f)

        # UI setup similar to furnace UI
        self.slot_size = 50
        self.padding = 10

        # Enhancement slots
        center_x = c.SCREEN_WIDTH // 2
        self.item_slot = pygame.Rect(center_x - 80, 100, self.slot_size, self.slot_size)
        self.ingredient_slot = pygame.Rect(center_x + 30, 100, self.slot_size, self.slot_size)
        
        # Add enhance button
        button_width = 100
        button_height = 40
        self.enhance_button = pygame.Rect(
            center_x - button_width//2,
            self.item_slot.bottom + 20,
            button_width,
            button_height
        )
        
        # Slots state
        self.item_in_slot = None
        self.ingredient_in_slot = None
        self.dragging_item = None
        self.drag_source = None
        self.hovered_item = None

        # Add inventory section calculations
        self.inventory_width = 8 * (self.slot_size + self.padding) - self.padding
        self.hotbar_width = 9 * (self.slot_size + self.padding) - self.padding
        self.max_width = max(self.inventory_width, self.hotbar_width)

        # Position inventory in middle of remaining space
        self.inventory_start_x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding)
        self.inventory_start_y = 250  # Position below enhancer slots

        # Position hotbar at bottom
        self.hotbar_start_x = c.SCREEN_WIDTH//2 - 4*(self.slot_size + self.padding)
        self.hotbar_start_y = c.SCREEN_HEIGHT - self.slot_size - 40

        self.debug_log = []  # Add debug log list
        self.enhancer_block = ENHANCER.create_instance()  # Add this line to create an instance!

        # Add glow effect properties
        self.glow_active = False
        self.glow_timer = 0
        self.glow_duration = 1500  # 1.5 seconds
        self.glow_colors = [
            (255, 215, 0, 255),  # Gold
            (255, 255, 200, 255),  # Light yellow
            (255, 215, 0, 255)   # Gold again
        ]

    def log_debug(self, message):
        """Add timestamped debug message"""
        import time
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.debug_log.append(f"[{timestamp}] {message}")
        print(f"[EnhancerUI Debug] {message}")

    def can_enhance(self):
        """Check if current items match any enhancement recipe"""
        if not self.item_in_slot or not self.ingredient_in_slot:
            return None

        for recipe_id, recipe in self.recipes.items():
            if (self.item_in_slot["item"].id == recipe["base_item"]["item_id"] and
                self.ingredient_in_slot["item"].id == recipe["ingredients"][0]["item_id"] and
                self.ingredient_in_slot["quantity"] >= recipe["ingredients"][0]["quantity"]):
                return recipe
        return None

    def enhance_item(self):
        """Apply enhancement if possible"""
        recipe = self.can_enhance()
        if recipe:
            # Trigger glow effect
            self.glow_active = True
            self.glow_timer = 0
            
            # Create enhanced copy of item
            enhanced_item = dict(self.item_in_slot)
            enhanced_item["item"].apply_enhancement(
                recipe["modifiers"],
                recipe["result_suffix"]
            )
            
            # If item is equipped, update player stats
            if enhanced_item["item"] in self.inventory.player.equipped_items:
                self.inventory.player.unequip_item(self.item_in_slot["item"])
                self.inventory.player.equip_item(enhanced_item["item"])
                
            # Consume ingredients
            self.ingredient_in_slot["quantity"] -= recipe["ingredients"][0]["quantity"]
            if self.ingredient_in_slot["quantity"] <= 0:
                self.ingredient_in_slot = None
                
            # Replace original item with enhanced version
            self.item_in_slot = enhanced_item
            return True
        return False

    def draw_glow_effect(self):
        """Draw gradient glow effect over the input slot"""
        if not self.glow_active:
            return
            
        # Calculate glow progress
        progress = self.glow_timer / self.glow_duration
        if progress >= 1:
            self.glow_active = False
            return
            
        # Create surface for glow
        glow_surf = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Calculate gradient position
        gradient_height = self.slot_size
        gradient_y = int((1 - progress) * gradient_height)
        
        # Draw gradient
        for i in range(gradient_height):
            rel_pos = i / gradient_height
            if i < gradient_y:
                continue
                
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
            
            # Fade alpha based on progress
            color[3] = int(color[3] * (1 - progress))
            
            # Draw line of gradient
            pygame.draw.line(glow_surf, color, (0, i), (self.slot_size, i))
            
        # Draw glow surface
        self.screen.blit(glow_surf, self.item_slot.topleft)

    def draw(self):
        """Draw the enhancer UI"""
        # Background
        self.screen.fill((30, 30, 30))
        title = self.font.render("Item Enhancer", True, (255, 255, 255))
        self.screen.blit(title, (c.SCREEN_WIDTH//2 - title.get_width()//2, 20))

        # Draw slots
        pygame.draw.rect(self.screen, (70, 70, 70), self.item_slot)
        pygame.draw.rect(self.screen, (70, 70, 70), self.ingredient_slot)
        pygame.draw.rect(self.screen, (200, 200, 200), self.item_slot, 2)
        pygame.draw.rect(self.screen, (200, 200, 200), self.ingredient_slot, 2)

        # Draw glow effect after slots but before items
        if self.glow_active:
            self.draw_glow_effect()
            self.glow_timer += pygame.time.get_ticks() / 1000.0  # Update timer
        
        # Draw items in slots after glow
        if self.item_in_slot:
            self.draw_item(self.item_in_slot, self.item_slot)
        if self.ingredient_in_slot:
            self.draw_item(self.ingredient_in_slot, self.ingredient_slot)

        # Draw inventory section
        inventory_label = self.font.render("Inventory", True, (255, 255, 255))
        self.screen.blit(inventory_label, (self.inventory_start_x, self.inventory_start_y - 25))

        # Draw main inventory
        for i in range(len(self.inventory.main)):
            row = i // 8
            col = i % 8
            x = self.inventory_start_x + col * (self.slot_size + self.padding)
            y = self.inventory_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            slot = self.inventory.main[i]
            if slot and slot.get("item"):
                self.draw_item(slot, rect)

        # Draw hotbar section
        hotbar_label = self.font.render("Hotbar", True, (255, 255, 255))
        self.screen.blit(hotbar_label, (self.hotbar_start_x, self.hotbar_start_y - 25))

        # Draw hotbar slots
        for i in range(len(self.inventory.hotbar)):
            x = self.hotbar_start_x + i * (self.slot_size + self.padding)
            rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            if i == self.inventory.selected_hotbar_index:
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(6, 6), 3)
            
            slot = self.inventory.hotbar[i]
            if slot and slot.get("item"):
                self.draw_item(slot, rect)

        # Draw dragged item
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            self.draw_item(self.dragging_item, pygame.Rect(
                mouse_pos[0] - self.slot_size//2,
                mouse_pos[1] - self.slot_size//2,
                self.slot_size,
                self.slot_size
            ))

        # Draw tooltip if hovering over item
        if self.hovered_item and not self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            tooltip_text = get_item_tooltip(self.hovered_item)
            # Add enhancement recipe info if applicable
            if self.hovered_item.id in [recipe["base_item"]["item_id"] for recipe in self.recipes.values()]:
                tooltip_text += "\n\nCan be enhanced"
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

        # Draw enhance button
        pygame.draw.rect(self.screen, (50, 150, 50), self.enhance_button)
        pygame.draw.rect(self.screen, (200, 200, 200), self.enhance_button, 2)
        
        # Draw button text
        enhance_text = self.font.render("Enhance", True, (255, 255, 255))
        text_rect = enhance_text.get_rect(center=self.enhance_button.center)
        self.screen.blit(enhance_text, text_rect)

        # Draw recipe hint if valid combination
        recipe = self.can_enhance()
        if recipe:
            hint_text = f"Click enhance to create: {self.item_in_slot['item'].name} {recipe['result_suffix']}"
            hint_surface = self.font.render(hint_text, True, (0, 255, 0))
            self.screen.blit(hint_surface, (self.enhance_button.x, self.enhance_button.bottom + 10))

        # Draw debug log (last 5 messages)
        debug_y = 10
        for message in self.debug_log[-5:]:
            debug_surface = self.font.render(message, True, (255, 255, 0))
            self.screen.blit(debug_surface, (10, debug_y))
            debug_y += 20

    def draw_item(self, slot, rect):
        """Draw an item in a slot"""
        if slot and slot["item"]:
            tx, ty = slot["item"].texture_coords
            texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
            item_img = self.atlas.subsurface(texture_rect)
            item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
            self.screen.blit(item_img, rect.topleft)
            if slot["quantity"] > 1:
                quantity = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                self.screen.blit(quantity, (rect.right - quantity.get_width() - 5, rect.bottom - quantity.get_height() - 5))

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return

        # Add mouse motion handling for tooltips
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.hovered_item = None

            # Check enhancer slots
            if self.item_slot.collidepoint(mouse_pos) and self.item_in_slot:
                self.hovered_item = self.item_in_slot["item"]
            elif self.ingredient_slot.collidepoint(mouse_pos) and self.ingredient_in_slot:
                self.hovered_item = self.ingredient_in_slot["item"]
            else:
                # Check inventory slots
                for i in range(len(self.inventory.main)):
                    row = i // 8
                    col = i % 8
                    x = self.inventory_start_x + col * (self.slot_size + self.padding)
                    y = self.inventory_start_y + row * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos) and self.inventory.main[i] and self.inventory.main[i].get("item"):
                        self.hovered_item = self.inventory.main[i]["item"]
                        break

                # Check hotbar slots if no inventory item was hovered
                if not self.hovered_item:
                    for i in range(len(self.inventory.hotbar)):
                        x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                        rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                        if rect.collidepoint(mouse_pos) and self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                            self.hovered_item = self.inventory.hotbar[i]["item"]
                            break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Add enhance button click handling
            if self.enhance_button.collidepoint(event.pos):
                if self.enhance_item():
                    self.log_debug("Enhancement successful!")
                else:
                    self.log_debug("Cannot enhance - invalid combination")
                return

            mouse_pos = event.pos
            self.log_debug(f"Mouse down at {mouse_pos}")
            
            # Track the original state before modifying anything
            source_slot = None
            source_location = None

            # Check hotbar slots first for better debugging
            for i in range(len(self.inventory.hotbar)):
                x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                if rect.collidepoint(mouse_pos):
                    self.log_debug(f"Clicked hotbar slot {i}")
                    if self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                        # Store the original state
                        source_slot = dict(self.inventory.hotbar[i])
                        source_location = ("hotbar", i)
                        self.log_debug(f"Storing original item state: {source_slot['item'].name} x{source_slot['quantity']}")
                        
                        # Set dragging state
                        self.dragging_item = dict(source_slot)
                        self.inventory.hotbar[i] = None
                        self.drag_source = source_location
                        self.log_debug(f"Set drag state with item: {self.dragging_item['item'].name}")
                        return

            # Check enhancer slots first
            if self.item_slot.collidepoint(mouse_pos):
                self.log_debug("Clicked item slot")
                if self.item_in_slot and self.item_in_slot.get("item"):
                    self.log_debug(f"Picking up from item slot: {self.item_in_slot['item'].name} x{self.item_in_slot['quantity']}")
                    self.dragging_item = dict(self.item_in_slot)
                    self.item_in_slot = None
                    self.drag_source = "item"
            elif self.ingredient_slot.collidepoint(mouse_pos):
                self.log_debug("Clicked ingredient slot")
                if self.ingredient_in_slot and self.ingredient_in_slot.get("item"):
                    self.log_debug(f"Picking up from ingredient slot: {self.ingredient_in_slot['item'].name} x{self.ingredient_in_slot['quantity']}")
                    self.dragging_item = dict(self.ingredient_in_slot)
                    self.ingredient_in_slot = None
                    self.drag_source = "ingredient"
            else:
                # Check inventory slots
                for i in range(len(self.inventory.main)):
                    row = i // 8
                    col = i % 8
                    x = self.inventory_start_x + col * (self.slot_size + self.padding)
                    y = self.inventory_start_y + row * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Clicked inventory slot {i}")
                        if self.inventory.main[i] and self.inventory.main[i].get("item"):
                            item = self.inventory.main[i]
                            self.log_debug(f"Picking up from inventory: {item['item'].name} x{item['quantity']}")
                            self.dragging_item = dict(item)
                            self.inventory.main[i] = None
                            self.drag_source = ("inventory", i)
                            return

                # Check hotbar slots
                for i in range(len(self.inventory.hotbar)):
                    x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Clicked hotbar slot {i}")
                        if self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                            item = self.inventory.hotbar[i]
                            self.log_debug(f"Picking up from hotbar: {item['item'].name} x{item['quantity']}")
                            self.dragging_item = dict(item)
                            self.inventory.hotbar[i] = None
                            self.drag_source = ("hotbar", i)
                            return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_item:
                mouse_pos = event.pos
                self.log_debug(f"Mouse up at {mouse_pos} with {self.dragging_item['item'].name}")
                dropped = False

                self.log_debug(f"START SWAP - Dragging: {self.dragging_item['item'].name} x{self.dragging_item['quantity']}")

                # Handle hotbar slots first
                for i in range(len(self.inventory.hotbar)):
                    x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Attempting hotbar slot {i} swap")
                        
                        # Always make deep copies
                        dragged = dict(self.dragging_item)
                        
                        if self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                            # Swap items
                            self.log_debug(f"Target slot contains: {self.inventory.hotbar[i]['item'].name}")
                            temp = dict(self.inventory.hotbar[i])
                            self.inventory.hotbar[i] = dragged
                            
                            # Return swapped item to original slot
                            if isinstance(self.drag_source, tuple):
                                source_type, idx = self.drag_source
                                if source_type == "inventory":
                                    self.inventory.main[idx] = temp
                                elif source_type == "hotbar":
                                    self.inventory.hotbar[idx] = temp
                            
                            self.log_debug(f"Completed swap between slots")
                        else:
                            # Place in empty slot
                            self.log_debug("Target slot is empty, placing item")
                            self.inventory.hotbar[i] = dragged
                            self.log_debug(f"Placed {dragged['item'].name} in hotbar slot {i}")
                        
                        dropped = True
                        break

                if self.item_slot.collidepoint(mouse_pos) and self.drag_source != "item":
                    # Handle enhancer item slot
                    self.log_debug("Dropping in item slot")
                    if self.item_in_slot:
                        self.log_debug(f"Swapping with item slot containing {self.item_in_slot['item'].name}")
                        temp = dict(self.item_in_slot)
                        self.item_in_slot = dict(self.dragging_item)
                        self.dragging_item = dict(temp)
                    else:
                        self.item_in_slot = dict(self.dragging_item)
                        self.dragging_item = None
                    dropped = True

                elif self.ingredient_slot.collidepoint(mouse_pos) and self.drag_source != "ingredient":
                    # Handle enhancer ingredient slot
                    self.log_debug("Dropping in ingredient slot")
                    if self.ingredient_in_slot:
                        self.log_debug(f"Swapping with ingredient slot containing {self.ingredient_in_slot['item'].name}")
                        temp = dict(self.ingredient_in_slot)
                        self.ingredient_in_slot = dict(self.dragging_item)
                        self.dragging_item = dict(temp)
                    else:
                        self.ingredient_in_slot = dict(self.dragging_item)
                        self.dragging_item = None
                    dropped = True

                else:
                    # Check inventory slots
                    for i in range(len(self.inventory.main)):
                        rect = pygame.Rect(
                            self.inventory_start_x + (i % 8) * (self.slot_size + self.padding),
                            self.inventory_start_y + (i // 8) * (self.slot_size + self.padding),
                            self.slot_size, self.slot_size
                        )
                        if rect.collidepoint(mouse_pos):
                            self.log_debug(f"Attempting inventory slot {i} swap")
                            
                            # Store the dragged item in a temporary variable
                            dragged = dict(self.dragging_item)
                            
                            if self.inventory.main[i] and self.inventory.main[i].get("item"):
                                # If target slot has an item, perform swap
                                self.log_debug(f"Target slot contains: {self.inventory.main[i]['item'].name} x{self.inventory.main[i]['quantity']}")
                                temp = dict(self.inventory.main[i])
                                self.inventory.main[i] = dragged
                                
                                # Return swapped item to original slot
                                if isinstance(self.drag_source, tuple):
                                    source_type, idx = self.drag_source
                                    if source_type == "inventory":
                                        self.inventory.main[idx] = temp
                                    elif source_type == "hotbar":
                                        self.inventory.hotbar[idx] = temp
                                elif self.drag_source == "item":
                                    self.item_in_slot = temp
                                elif self.drag_source == "ingredient":
                                    self.ingredient_in_slot = temp
                                    
                                self.log_debug(f"Completed swap: {dragged['item'].name} <-> {temp['item'].name}")
                            else:
                                # If target slot is empty, just place the item
                                self.log_debug("Target slot is empty, placing item")
                                self.inventory.main[i] = dragged
                                
                                # Clear original slot
                                if isinstance(self.drag_source, tuple):
                                    source_type, idx = self.drag_source
                                    if source_type == "inventory":
                                        self.inventory.main[idx] = None
                                    elif source_type == "hotbar":
                                        self.inventory.hotbar[idx] = None
                                elif self.drag_source == "item":
                                    self.item_in_slot = None
                                elif self.drag_source == "ingredient":
                                    self.ingredient_in_slot = None
                            
                            dropped = True
                            break

                    # Similar logic for hotbar slots
                    if not dropped:
                        for i in range(len(self.inventory.hotbar)):
                            # ...same logic as above for hotbar slots...
                            rect = pygame.Rect(
                                self.hotbar_start_x + i * (self.slot_size + self.padding),
                                self.hotbar_start_y,
                                self.slot_size, self.slot_size
                            )
                            if rect.collidepoint(mouse_pos):
                                self.log_debug(f"Attempting hotbar slot {i} swap")
                                
                                # Store the dragged item
                                dragged = dict(self.dragging_item)
                                
                                if self.inventory.hotbar[i] and self.inventory.hotbar[i].get("item"):
                                    # Swap items
                                    self.log_debug(f"Target slot contains: {self.inventory.hotbar[i]['item'].name} x{self.inventory.hotbar[i]['quantity']}")
                                    temp = dict(self.inventory.hotbar[i])
                                    self.inventory.hotbar[i] = dragged
                                    
                                    # Return swapped item to original slot
                                    if isinstance(self.drag_source, tuple):
                                        source_type, idx = self.drag_source
                                        if source_type == "inventory":
                                            self.inventory.main[idx] = temp
                                        elif source_type == "hotbar":
                                            self.inventory.hotbar[idx] = temp
                                    elif self.drag_source == "item":
                                        self.item_in_slot = temp
                                    elif self.drag_source == "ingredient":
                                        self.ingredient_in_slot = temp
                                        
                                    self.log_debug(f"Completed swap: {dragged['item'].name} <-> {temp['item'].name}")
                                else:
                                    # Place in empty slot
                                    self.log_debug("Target slot is empty, placing item")
                                    self.inventory.hotbar[i] = dragged
                                    
                                    # Clear original slot
                                    if isinstance(self.drag_source, tuple):
                                        source_type, idx = self.drag_source
                                        if source_type == "inventory":
                                            self.inventory.main[idx] = None
                                        elif source_type == "hotbar":
                                            self.inventory.hotbar[idx] = None
                                    elif self.drag_source == "item":
                                        self.item_in_slot = None
                                    elif self.drag_source == "ingredient":
                                        self.ingredient_in_slot = None
                                
                                dropped = True
                                break

                # Return item to original slot if not dropped
                if not dropped and self.dragging_item:
                    self.log_debug("Item not dropped, returning to source")
                    if isinstance(self.drag_source, tuple):
                        source_type, idx = self.drag_source
                        if source_type == "inventory":
                            self.log_debug(f"Returning to inventory slot {idx}")
                            self.inventory.main[idx] = dict(self.dragging_item)
                        elif source_type == "hotbar":
                            self.log_debug(f"Returning to hotbar slot {idx}")
                            self.inventory.hotbar[idx] = dict(self.dragging_item)
                    elif self.drag_source == "item":
                        self.log_debug("Returning to item slot")
                        self.item_in_slot = dict(self.dragging_item)
                    elif self.drag_source == "ingredient":
                        self.log_debug("Returning to ingredient slot")
                        self.ingredient_in_slot = dict(self.dragging_item)

                self.dragging_item = None
                self.drag_source = None
                self.log_debug("END SWAP")

    def run(self):
        """Main UI loop"""
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)

            # Update the actual enhancer block's slots
            self.enhancer_block.input_slot = self.item_in_slot
            self.enhancer_block.ingredient_slot = self.ingredient_in_slot

            self.draw()
            pygame.display.flip()
            clock.tick(60)
