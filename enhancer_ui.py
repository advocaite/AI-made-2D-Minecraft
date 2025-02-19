import pygame
import json
import config as c
from block import ENHANCER  # Add this import
from ui_tooltip import Tooltip, get_item_tooltip

class EnhancerUI:
    def __init__(self, screen, player_inventory, block, texture_atlas):
        self.screen = screen
        self.player_inventory = player_inventory
        self.block = block
        self.texture_atlas = texture_atlas  # Fixed variable name from self.atlas
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.tooltip = Tooltip(self.font)
        self.inventory = player_inventory  # Add this line for backward compatibility
        
        # Load enhancement recipes
        with open('enhancement_recipes.json', 'r') as f:
            self.recipes = json.load(f)

        # UI setup similar to furnace UI
        self.slot_size = 50
        self.padding = 10

        # Enhancement slots - Create proper Rect objects
        center_x = c.SCREEN_WIDTH // 2
        self.item_slot_rect = pygame.Rect(center_x - 80, 100, self.slot_size, self.slot_size)
        self.ingredient_slot_rect = pygame.Rect(center_x + 30, 100, self.slot_size, self.slot_size)
        
        # Add enhance button
        button_width = 100
        button_height = 40
        self.enhance_button = pygame.Rect(
            center_x - button_width//2,
            self.item_slot_rect.bottom + 20,
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

        # Use block's existing slots for items
        self.item_slot = block.script.input_slot
        self.ingredient_slot = block.script.ingredient_slot

        # Initialize slots with proper null checks
        self.item_in_slot = (
            block.script.input_slot.copy() 
            if block.script.input_slot and block.script.input_slot.get("item") 
            else {"item": None, "quantity": 0}
        )
        
        self.ingredient_in_slot = (
            block.script.ingredient_slot.copy() 
            if block.script.ingredient_slot and block.script.ingredient_slot.get("item") 
            else {"item": None, "quantity": 0}
        )

    def log_debug(self, message):
        """Add timestamped debug message"""
        import time
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.debug_log.append(f"[{timestamp}] {message}")
        print(f"[EnhancerUI Debug] {message}")

    def can_enhance(self):
        """Check if current items match any enhancement recipe"""
        # First check that both slots have valid items
        if (not self.item_in_slot or 
            not self.item_in_slot.get("item") or 
            not self.ingredient_in_slot or 
            not self.ingredient_in_slot.get("item")):
            return None

        # Only proceed if we have valid items
        input_item = self.item_in_slot["item"]
        ingredient_item = self.ingredient_in_slot["item"]
        
        try:
            for recipe_id, recipe in self.recipes.items():
                if (input_item.id == recipe["base_item"]["item_id"] and
                    ingredient_item.id == recipe["ingredients"][0]["item_id"] and
                    self.ingredient_in_slot["quantity"] >= recipe["ingredients"][0]["quantity"]):
                    return recipe
        except (KeyError, AttributeError) as e:
            print(f"[ENHANCER] Error checking recipe: {e}")
            return None
            
        return None

    def enhance_item(self):
        """Apply enhancement if possible"""
        recipe = self.can_enhance()
        if recipe:
            # Create enhanced copy of item
            enhanced_item = dict(self.item_in_slot)
            enhanced_item["item"].apply_enhancement(
                recipe["modifiers"],
                recipe["result_suffix"]
            )
            
            # If item is equipped, update player stats
            if enhanced_item["item"] in self.player_inventory.player.equipped_items:
                self.player_inventory.player.unequip_item(self.item_in_slot["item"])
                self.player_inventory.player.equip_item(enhanced_item["item"])
                
            # Consume ingredients
            self.ingredient_in_slot["quantity"] -= recipe["ingredients"][0]["quantity"]
            if self.ingredient_in_slot["quantity"] <= 0:
                self.ingredient_in_slot = None
                
            # Replace original item with enhanced version
            self.item_in_slot = enhanced_item
            return True
        return False

    def draw(self):
        """Draw the enhancer UI"""
        # Background
        self.screen.fill((30, 30, 30))
        title = self.font.render("Item Enhancer", True, (255, 255, 255))
        self.screen.blit(title, (c.SCREEN_WIDTH//2 - title.get_width()//2, 20))

        # Draw slots using the rect objects
        pygame.draw.rect(self.screen, (70, 70, 70), self.item_slot_rect)
        pygame.draw.rect(self.screen, (70, 70, 70), self.ingredient_slot_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.item_slot_rect, 2)
        pygame.draw.rect(self.screen, (200, 200, 200), self.ingredient_slot_rect, 2)

        # Draw items in slots - Fix this section
        if self.item_in_slot and self.item_in_slot.get("item"):
            try:
                self.draw_item(self.item_in_slot, self.item_slot_rect)
            except Exception as e:
                print(f"Error drawing input slot item: {e}")

        if self.ingredient_in_slot and self.ingredient_in_slot.get("item"):
            try:
                self.draw_item(self.ingredient_in_slot, self.ingredient_slot_rect)
            except Exception as e:
                print(f"Error drawing ingredient slot item: {e}")

        # Draw inventory section
        inventory_label = self.font.render("Inventory", True, (255, 255, 255))
        self.screen.blit(inventory_label, (self.inventory_start_x, self.inventory_start_y - 25))

        # Draw main inventory
        for i in range(len(self.player_inventory.main)):  # Use player_inventory instead of inventory
            row = i // 8
            col = i % 8
            x = self.inventory_start_x + col * (self.slot_size + self.padding)
            y = self.inventory_start_y + row * (self.slot_size + self.padding)
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            slot = self.player_inventory.main[i]  # Use player_inventory
            if slot and slot.get("item"):
                self.draw_item(slot, rect)

        # Draw hotbar section
        hotbar_label = self.font.render("Hotbar", True, (255, 255, 255))
        self.screen.blit(hotbar_label, (self.hotbar_start_x, self.hotbar_start_y - 25))

        # Draw hotbar slots
        for i in range(len(self.player_inventory.hotbar)):  # Use player_inventory
            x = self.hotbar_start_x + i * (self.slot_size + self.padding)
            rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
            
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            if i == self.player_inventory.selected_hotbar_index:
                pygame.draw.rect(self.screen, (255, 215, 0), rect.inflate(6, 6), 3)
            
            slot = self.player_inventory.hotbar[i]  # Use player_inventory
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
        try:
            recipe = self.can_enhance()
            if recipe and self.item_in_slot and self.item_in_slot.get("item"):
                hint_text = f"Click enhance to create: {self.item_in_slot['item'].name} {recipe['result_suffix']}"
                hint_surface = self.font.render(hint_text, True, (0, 255, 0))
                self.screen.blit(hint_surface, (self.enhance_button.x, self.enhance_button.bottom + 10))
        except Exception as e:
            print(f"[ENHANCER] Error drawing recipe hint: {e}")

        # Draw debug log (last 5 messages)
        debug_y = 10
        for message in self.debug_log[-5:]:
            debug_surface = self.font.render(message, True, (255, 255, 0))
            self.screen.blit(debug_surface, (10, debug_y))
            debug_y += 20

    def draw_item(self, slot, rect):
        """Draw an item in a slot with proper error checking"""
        if not slot or "item" not in slot or not slot["item"]:
            return
            
        try:
            item = slot["item"]
            if not hasattr(item, 'texture_coords'):
                print(f"Warning: Item {item} has no texture coordinates")
                return
                
            tx, ty = item.texture_coords
            texture_rect = pygame.Rect(
                tx * c.BLOCK_SIZE, 
                ty * c.BLOCK_SIZE, 
                c.BLOCK_SIZE, 
                c.BLOCK_SIZE
            )
            
            # Use self.texture_atlas instead of self.atlas
            item_img = self.texture_atlas.subsurface(texture_rect)
            item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
            self.screen.blit(item_img, rect.topleft)
            
            # Draw quantity if more than 1
            if slot.get("quantity", 0) > 1:
                quantity_text = self.font.render(str(slot["quantity"]), True, (255, 255, 255))
                self.screen.blit(quantity_text, (
                    rect.right - quantity_text.get_width() - 5,
                    rect.bottom - quantity_text.get_height() - 5
                ))
        except Exception as e:
            print(f"Error drawing item: {e}")

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
            if self.item_slot_rect.collidepoint(mouse_pos) and self.item_in_slot:
                self.hovered_item = self.item_in_slot["item"]
            elif self.ingredient_slot_rect.collidepoint(mouse_pos) and self.ingredient_in_slot:
                self.hovered_item = self.ingredient_in_slot["item"]
            else:
                # Check inventory slots
                for i in range(len(self.player_inventory.main)):
                    row = i // 8
                    col = i % 8
                    x = self.inventory_start_x + col * (self.slot_size + self.padding)
                    y = self.inventory_start_y + row * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos) and self.player_inventory.main[i] and self.player_inventory.main[i].get("item"):
                        self.hovered_item = self.player_inventory.main[i]["item"]
                        break

                # Check hotbar slots if no inventory item was hovered
                if not self.hovered_item:
                    for i in range(len(self.player_inventory.hotbar)):
                        x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                        rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                        if rect.collidepoint(mouse_pos) and self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                            self.hovered_item = self.player_inventory.hotbar[i]["item"]
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
            for i in range(len(self.player_inventory.hotbar)):
                x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                if rect.collidepoint(mouse_pos):
                    self.log_debug(f"Clicked hotbar slot {i}")
                    if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                        # Store the original state
                        source_slot = dict(self.player_inventory.hotbar[i])
                        source_location = ("hotbar", i)
                        self.log_debug(f"Storing original item state: {source_slot['item'].name} x{source_slot['quantity']}")
                        
                        # Set dragging state
                        self.dragging_item = dict(source_slot)
                        self.player_inventory.hotbar[i] = None
                        self.drag_source = source_location
                        self.log_debug(f"Set drag state with item: {self.dragging_item['item'].name}")
                        return

            # Check enhancer slots first
            if self.item_slot_rect.collidepoint(mouse_pos):
                self.log_debug("Clicked item slot")
                if self.item_in_slot and self.item_in_slot.get("item"):
                    item_name = self.item_in_slot["item"].name if self.item_in_slot["item"] else "Unknown"
                    self.log_debug(f"Picking up from item slot: {item_name} x{self.item_in_slot['quantity']}")
                    self.dragging_item = dict(self.item_in_slot)
                    self.item_in_slot = None
                    self.drag_source = "item"
            elif self.ingredient_slot_rect.collidepoint(mouse_pos):
                self.log_debug("Clicked ingredient slot")
                if self.ingredient_in_slot and self.ingredient_in_slot.get("item"):
                    item_name = self.ingredient_in_slot["item"].name if self.ingredient_in_slot["item"] else "Unknown"
                    self.log_debug(f"Picking up from ingredient slot: {item_name} x{self.ingredient_in_slot['quantity']}")
                    self.dragging_item = dict(self.ingredient_in_slot)
                    self.ingredient_in_slot = None
                    self.drag_source = "ingredient"
            else:
                # Check inventory slots
                for i in range(len(self.player_inventory.main)):
                    row = i // 8
                    col = i % 8
                    x = self.inventory_start_x + col * (self.slot_size + self.padding)
                    y = self.inventory_start_y + row * (self.slot_size + self.padding)  # Fixed: changed "the padding" to "self.padding"
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Clicked inventory slot {i}")
                        if self.player_inventory.main[i] and self.player_inventory.main[i].get("item"):
                            item = self.player_inventory.main[i]
                            self.log_debug(f"Picking up from inventory: {item['item'].name} x{item['quantity']}")
                            self.dragging_item = dict(item)
                            self.player_inventory.main[i] = None
                            self.drag_source = ("inventory", i)
                            return

                # Check hotbar slots
                for i in range(len(self.player_inventory.hotbar)):
                    x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Clicked hotbar slot {i}")
                        if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                            item = self.player_inventory.hotbar[i]
                            self.log_debug(f"Picking up from hotbar: {item['item'].name} x{item['quantity']}")
                            self.dragging_item = dict(item)
                            self.player_inventory.hotbar[i] = None
                            self.drag_source = ("hotbar", i)
                            return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_item:
                mouse_pos = event.pos
                self.log_debug(f"Mouse up at {mouse_pos} with {self.dragging_item['item'].name}")
                dropped = False

                self.log_debug(f"START SWAP - Dragging: {self.dragging_item['item'].name} x{self.dragging_item['quantity']}")

                # Handle hotbar slots first
                for i in range(len(self.player_inventory.hotbar)):
                    x = self.hotbar_start_x + i * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, self.hotbar_start_y, self.slot_size, self.slot_size)
                    if rect.collidepoint(mouse_pos):
                        self.log_debug(f"Attempting hotbar slot {i} swap")
                        
                        # Always make deep copies
                        dragged = dict(self.dragging_item)
                        
                        if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                            # Swap items
                            self.log_debug(f"Target slot contains: {self.player_inventory.hotbar[i]['item'].name}")
                            temp = dict(self.player_inventory.hotbar[i])
                            self.player_inventory.hotbar[i] = dragged
                            
                            # Return swapped item to original slot
                            if isinstance(self.drag_source, tuple):
                                source_type, idx = self.drag_source
                                if source_type == "inventory":
                                    self.player_inventory.main[idx] = temp
                                elif source_type == "hotbar":
                                    self.player_inventory.hotbar[idx] = temp
                            
                            self.log_debug(f"Completed swap between slots")
                        else:
                            # Place in empty slot
                            self.log_debug("Target slot is empty, placing item")
                            self.player_inventory.hotbar[i] = dragged
                            self.log_debug(f"Placed {dragged['item'].name} in hotbar slot {i}")
                        
                        dropped = True
                        break

                if self.item_slot_rect.collidepoint(mouse_pos) and self.drag_source != "item":
                    # Handle enhancer item slot
                    self.log_debug("Dropping in item slot")
                    if self.item_in_slot and self.item_in_slot.get("item"):
                        item_name = self.item_in_slot["item"].name if self.item_in_slot["item"] else "Unknown"
                        self.log_debug(f"Swapping with item slot containing {item_name}")
                        temp = dict(self.item_in_slot)
                        self.item_in_slot = dict(self.dragging_item)
                        self.dragging_item = dict(temp)
                    else:
                        self.item_in_slot = dict(self.dragging_item)
                        self.dragging_item = None
                    dropped = True

                elif self.ingredient_slot_rect.collidepoint(mouse_pos) and self.drag_source != "ingredient":
                    # Handle enhancer ingredient slot
                    self.log_debug("Dropping in ingredient slot")
                    if self.ingredient_in_slot and self.ingredient_in_slot.get("item"):
                        item_name = self.ingredient_in_slot["item"].name if self.ingredient_in_slot["item"] else "Unknown"
                        self.log_debug(f"Swapping with ingredient slot containing {item_name}")
                        temp = dict(self.ingredient_in_slot)
                        self.ingredient_in_slot = dict(self.dragging_item)
                        self.dragging_item = dict(temp)
                    else:
                        self.ingredient_in_slot = dict(self.dragging_item)
                        self.dragging_item = None
                    dropped = True

                else:
                    # Check inventory slots
                    for i in range(len(self.player_inventory.main)):
                        rect = pygame.Rect(
                            self.inventory_start_x + (i % 8) * (self.slot_size + self.padding),
                            self.inventory_start_y + (i // 8) * (self.slot_size + self.padding),
                            self.slot_size, self.slot_size
                        )
                        if rect.collidepoint(mouse_pos):
                            self.log_debug(f"Attempting inventory slot {i} swap")
                            
                            # Store the dragged item in a temporary variable
                            dragged = dict(self.dragging_item)
                            
                            # If dropping on original slot, just put it back
                            if isinstance(self.drag_source, tuple):
                                source_type, idx = self.drag_source
                                if source_type == "inventory" and idx == i:
                                    self.log_debug(f"Dropping item back in its original slot {i}")
                                    self.player_inventory.main[i] = dragged
                                    dropped = True
                                    break

                            if self.player_inventory.main[i] and self.player_inventory.main[i].get("item"):
                                # If target slot has an item, perform swap
                                self.log_debug(f"Target slot contains: {self.player_inventory.main[i]['item'].name} x{self.player_inventory.main[i]['quantity']}")
                                temp = dict(self.player_inventory.main[i])
                                self.player_inventory.main[i] = dragged
                                
                                # Return swapped item to original slot
                                if isinstance(self.drag_source, tuple):
                                    source_type, idx = self.drag_source
                                    if source_type == "inventory":
                                        self.player_inventory.main[idx] = temp
                                    elif source_type == "hotbar":
                                        self.player_inventory.hotbar[idx] = temp
                                elif self.drag_source == "item":
                                    self.item_in_slot = temp
                                elif self.drag_source == "ingredient":
                                    self.ingredient_in_slot = temp
                                    
                                self.log_debug(f"Completed swap: {dragged['item'].name} <-> {temp['item'].name}")
                            else:
                                # If target slot is empty, just place the item
                                self.log_debug("Target slot is empty, placing item")
                                self.player_inventory.main[i] = dragged
                                
                                # Clear original slot
                                if isinstance(self.drag_source, tuple):
                                    source_type, idx = self.drag_source
                                    if source_type == "inventory":
                                        self.player_inventory.main[idx] = None
                                    elif source_type == "hotbar":
                                        self.player_inventory.hotbar[idx] = None
                                elif self.drag_source == "item":
                                    self.item_in_slot = None
                                elif self.drag_source == "ingredient":
                                    self.ingredient_in_slot = None
                            
                            dropped = True
                            break

                    # Similar logic for hotbar slots
                    if not dropped:
                        for i in range(len(self.player_inventory.hotbar)):
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
                                
                                if self.player_inventory.hotbar[i] and self.player_inventory.hotbar[i].get("item"):
                                    # Swap items
                                    self.log_debug(f"Target slot contains: {self.player_inventory.hotbar[i]['item'].name} x{self.player_inventory.hotbar[i]['quantity']}")
                                    temp = dict(self.player_inventory.hotbar[i])
                                    self.player_inventory.hotbar[i] = dragged
                                    
                                    # Return swapped item to original slot
                                    if isinstance(self.drag_source, tuple):
                                        source_type, idx = self.drag_source
                                        if source_type == "inventory":
                                            self.player_inventory.main[idx] = temp
                                        elif source_type == "hotbar":
                                            self.player_inventory.hotbar[idx] = temp
                                    elif self.drag_source == "item":
                                        self.item_in_slot = temp
                                    elif self.drag_source == "ingredient":
                                        self.ingredient_in_slot = temp
                                        
                                    self.log_debug(f"Completed swap: {dragged['item'].name} <-> {temp['item'].name}")
                                else:
                                    # Place in empty slot
                                    self.log_debug("Target slot is empty, placing item")
                                    self.player_inventory.hotbar[i] = dragged
                                    
                                    # Clear original slot
                                    if isinstance(self.drag_source, tuple):
                                        source_type, idx = self.drag_source
                                        if source_type == "inventory":
                                            self.player_inventory.main[idx] = None
                                        elif source_type == "hotbar":
                                            self.player_inventory.hotbar[idx] = None
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
                            self.player_inventory.main[idx] = dict(self.dragging_item)
                        elif source_type == "hotbar":
                            self.log_debug(f"Returning to hotbar slot {idx}")
                            self.player_inventory.hotbar[idx] = dict(self.dragging_item)
                    elif self.drag_source == "item":
                        self.log_debug("Returning to item slot")
                        self.item_in_slot = dict(self.dragging_item)
                    elif self.drag_source == "ingredient":
                        self.log_debug("Returning to ingredient slot")
                        self.ingredient_in_slot = dict(self.dragging_item)

                self.dragging_item = None
                self.drag_source = None
                self.log_debug("END SWAP")

    def handle_item_transfer(self, from_slot, to_slot, amount=1):
        """Handle item transfers between slots"""
        if not from_slot or not from_slot.get("item"):
            return False

        # Handle transfers to/from block slots
        if to_slot in [self.input_slot, self.ingredient_slot]:
            self.block.handle_item_transfer(
                'input_slot' if to_slot == self.input_slot else 'ingredient_slot',
                {"item": from_slot["item"], "quantity": amount}
            )
            
        # Update source slot
        from_slot["quantity"] -= amount
        if from_slot["quantity"] <= 0:
            from_slot["item"] = None
            from_slot["quantity"] = 0

        return True

    def close(self):
        """Save state when UI is closed"""
        if self.item_in_slot:
            self.block.script.input_slot = dict(self.item_in_slot)
        if self.ingredient_in_slot:
            self.block.script.ingredient_slot = dict(self.ingredient_in_slot)

    def run(self):
        """Main UI loop"""
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)

                # Sync block state after every event
                if self.item_in_slot:
                    self.block.script.input_slot = dict(self.item_in_slot)
                if self.ingredient_in_slot:
                    self.block.script.ingredient_slot = dict(self.ingredient_in_slot)

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        # Save final state when closing
        if self.item_in_slot:
            self.block.script.input_slot = dict(self.item_in_slot)
        else:
            self.block.script.input_slot = {"item": None, "quantity": 0}
            
        if self.ingredient_in_slot:
            self.block.script.ingredient_slot = dict(self.ingredient_in_slot)
        else:
            self.block.script.ingredient_slot = {"item": None, "quantity": 0}

        print(f"[ENHANCER UI] Saving final state:")
        print(f"Input slot: {self.block.script.input_slot}")
        print(f"Ingredient slot: {self.block.script.ingredient_slot}")
