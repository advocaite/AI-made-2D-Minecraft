import pygame
import config as c
from crafting import Crafting
from scrollable_list import ScrollableList
from item import Item
from ui_tooltip import Tooltip, get_item_tooltip
from ui_manager import UIManager

class CraftingUI:
    def __init__(self, screen, inventory, atlas):
        self.screen = screen
        self.inventory = inventory
        self.atlas = atlas
        self.crafting = Crafting()
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.recipes = list(self.crafting.recipes.keys())
        self.selected_recipe = 0  # ensure selected_recipe is defined

        # Build items with name/cost info and image:
        recipe_items = []
        for key in self.recipes:
            cost_str = self.build_recipe_cost_str(key)
            recipe = self.crafting.recipes.get(key, {})
            result = recipe.get("result", {})
            block_size = c.BLOCK_SIZE
            tx, ty = result.get("texture_coords", (0, 0))
            texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
            image = self.atlas.subsurface(texture_rect).convert_alpha()
            # NEW: Apply tint if set in result (ensuring transparency).
            if "tint" in result:
                tinted = image.copy()
                tinted.fill(result["tint"], special_flags=pygame.BLEND_RGBA_MULT)
                image = tinted
            image = pygame.transform.smoothscale(image, (32, 32)).convert_alpha()
            recipe_items.append({"name": key.capitalize(), "info": cost_str, "image": image})

        self.recipe_list = ScrollableList(50, 60, 300, 400)
        self.recipe_list.set_items(recipe_items)
        self.recipe_list.font = self.font  # Add font reference
        self.recipe_rects = None

        self.dragging_item = None
        self.drag_source = None
        self.margin = 10
        self.slot_size = 40
        self.slot_padding = 5

        # Recipe list takes up left side
        self.recipe_list.rect.x = self.margin
        self.recipe_list.rect.width = c.SCREEN_WIDTH // 2 - self.margin * 2

        # Add inventory section on the right side
        self.inventory_x = c.SCREEN_WIDTH // 2 + self.margin
        self.inventory_y = c.SCREEN_HEIGHT - 200  # Position above bottom of screen

        # Define the scrollable area rectangle (adjust x, y, width, height as needed)
        self.scroll_rect = pygame.Rect(100, 150, 300, 400)

        self.ui_manager = UIManager(screen)
        self.crafting_batch = self.ui_manager.create_batch('crafting')
        self.ingredients_batch = self.ui_manager.create_batch('ingredients')
        self.result_batch = self.ui_manager.create_batch('result')
        
        # Add frame tracking
        self._last_frame_ingredients = {}
        self._last_frame_result = None

        # Add position calculations for all UI elements
        screen_center_x = c.SCREEN_WIDTH // 2
        
        # Recipe list section (left side)
        self.recipe_list_x = 20
        self.recipe_list_y = 60
        
        # Ingredients section (right side)
        self.ingredients_start_x = screen_center_x + 20
        self.ingredients_start_y = 100
        
        # Result section
        self.result_x = screen_center_x + 150
        self.result_y = 100
        
        # Crafting button
        self.craft_button_rect = pygame.Rect(
            self.result_x,  # Align with result slot
            self.result_y + self.slot_size + 10,  # Position below result slot
            self.slot_size,  # Match slot width
            40  # Keep same height
        )

        # Calculate inventory grid positions
        self.inventory_start_x = screen_center_x - ((8 * (self.slot_size + self.slot_padding)) // 2)
        self.inventory_start_y = c.SCREEN_HEIGHT - 200
        
        # Track visible recipes and ingredients
        self.visible_recipes = []
        self.current_ingredients = []
        self.result_item = None
        
        # Initialize crafting state
        self.crafting_progress = 0
        self.crafting_time = 1000  # 1 second to craft
        self.is_crafting = False

        # Add tooltip
        self.tooltip = Tooltip(self.font)
        self.hovered_item = None

    def build_recipe_cost_str(self, recipe_key):
        recipe = self.crafting.recipes.get(recipe_key, {})
        ingredients = recipe.get("ingredients", [])
        # e.g. "2x Pickaxe, 1x Wood"
        parts = []
        for ingr in ingredients:
            # Use ingr["name"] if available; fallback to ingr["item_id"]
            item_name = ingr.get("name", ingr["item_id"])
            parts.append(f'{ingr["quantity"]}x {item_name}')
        return ", ".join(parts)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_UP:
                        self.selected_recipe = (self.selected_recipe - 1) % len(self.recipes)
                    elif event.key == pygame.K_DOWN:
                        self.selected_recipe = (self.selected_recipe + 1) % len(self.recipes)
                    elif event.key == pygame.K_RETURN:
                        recipe_key = self.recipes[self.selected_recipe]
                        crafted = self.crafting.craft_item(self.inventory, recipe_key)
                        if crafted:
                            self.inventory.add_item(crafted)
                self.recipe_list.handle_event(event)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    button_rect = pygame.Rect(c.SCREEN_WIDTH//2 - 40, c.SCREEN_HEIGHT - 80, 80, 40)
                    if button_rect.collidepoint(pos):
                        recipe_key = self.recipes[self.selected_recipe]
                        crafted = self.crafting.craft_item(self.inventory, recipe_key)
                        if crafted:
                            self.inventory.add_item(crafted)
                    idx = (self.recipe_list.scroll_offset // 60)
                    mouse_y = event.pos[1] - self.recipe_list.rect.y + self.recipe_list.scroll_offset
                    item_index = mouse_y // self.recipe_list.item_height
                    if 0 <= item_index < len(self.recipes):
                        self.selected_recipe = item_index
            self.draw()
            pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_UP:
                self.selected_recipe = (self.selected_recipe - 1) % len(self.recipes)
            elif event.key == pygame.K_DOWN:
                self.selected_recipe = (self.selected_recipe + 1) % len(self.recipes)
            elif event.key == pygame.K_RETURN:
                recipe_key = self.recipes[self.selected_recipe]
                crafted = self.crafting.craft_item(self.inventory, recipe_key)
                if crafted:
                    self.inventory.add_item(crafted)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.recipe_list.rect.collidepoint(pos):
                idx = (self.recipe_list.scroll_offset // 60)
                mouse_y = event.pos[1] - self.recipe_list.rect.y + self.recipe_list.scroll_offset
                item_index = mouse_y // self.recipe_list.item_height
                if 0 <= item_index < len(self.recipes):
                    self.selected_recipe = item_index
                return

            # Check inventory slots
            inv_slot = self.get_inventory_slot_at_pos(pos)
            if inv_slot is not None:
                slot = self.inventory.main[inv_slot]
                if slot and slot["item"]:
                    self.dragging_item = dict(slot)
                    self.inventory.main[inv_slot] = None
                    self.drag_source = ("inventory", inv_slot)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_item:
                pos = event.pos
                inv_slot = self.get_inventory_slot_at_pos(pos)
                if inv_slot is not None:
                    # Place item in inventory
                    if not self.inventory.main[inv_slot]:
                        self.inventory.main[inv_slot] = self.dragging_item
                    else:
                        # Return to original slot if target is occupied
                        source_type, source_idx = self.drag_source
                        if source_type == "inventory":
                            self.inventory.main[source_idx] = self.dragging_item
                    self.dragging_item = None
                    self.drag_source = None

    def get_inventory_slot_at_pos(self, pos):
        mx, my = pos
        rows = 4
        cols = 8
        for i in range(len(self.inventory.main)):
            row = i // cols
            col = i % cols
            x = self.inventory_x + col * (self.slot_size + self.slot_padding)
            y = self.inventory_y + row * (self.slot_size + self.slot_padding)
            if pygame.Rect(x, y, self.slot_size, self.slot_size).collidepoint(mx, my):
                return i
        return None

    def draw(self):
        """Draw the crafting UI with batched rendering"""
        self.ui_manager.begin_frame()
        
        # Draw background
        self.screen.fill((30, 30, 30))
        bg_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_overlay.fill((0, 0, 0, 200))
        self.screen.blit(bg_overlay, (0, 0))
        
        # Draw section titles
        title_color = (200, 200, 200)
        crafting_title = self.font.render("Crafting", True, title_color)
        ingredients_title = self.font.render("Ingredients", True, title_color)
        result_title = self.font.render("Result", True, title_color)
        
        # Position titles
        self.screen.blit(crafting_title, (c.SCREEN_WIDTH//2 - crafting_title.get_width()//2, 20))
        self.screen.blit(ingredients_title, (self.ingredients_start_x, self.ingredients_start_y - 25))
        self.screen.blit(result_title, (self.result_x, self.result_y - 25))
        
        # Draw crafting slots
        for i, recipe in enumerate(self.visible_recipes):
            slot_id = f"recipe_{i}"
            if slot_id in self.crafting_batch.dirty or recipe != self._last_frame_recipes.get(i):
                surface = self._render_recipe_slot(recipe, i == self.selected_recipe)
                self.ui_manager.draw_ui_element(self.crafting_batch, slot_id, surface,
                    (self.crafting_start_x + i * (self.slot_size + self.padding), self.crafting_start_y), True)
        
        # Draw ingredient slots
        for i, slot in enumerate(self.current_ingredients):
            slot_id = f"ingredient_{i}"
            if slot_id in self.ingredients_batch.dirty or slot != self._last_frame_ingredients.get(i):
                surface = self._render_ingredient_slot(slot)
                self.ui_manager.draw_ui_element(self.ingredients_batch, slot_id, surface,
                    self._get_ingredient_pos(i), True)
        
        # Draw result slot
        if self.result_item != self._last_frame_result:
            surface = self._render_result_slot()
            self.ui_manager.draw_ui_element(self.result_batch, "result", surface,
                (self.result_x, self.result_y), True)
        
        # Update frame cache
        self._last_frame_recipes = {i: recipe for i, recipe in enumerate(self.visible_recipes)}
        self._last_frame_ingredients = {i: slot for i, slot in enumerate(self.current_ingredients)}
        self._last_frame_result = self.result_item
        
        # Draw crafting progress if active
        if self.crafting_progress > 0:
            progress_width = int(self.slot_size * (self.crafting_progress / self.crafting_time))
            progress_rect = pygame.Rect(self.result_x, self.result_y + self.slot_size + 5,
                                     progress_width, 5)
            pygame.draw.rect(self.screen, (0, 255, 0), progress_rect)
        
        # Draw dragged item last
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            self._render_dragged_item(mx, my)

        # Draw tooltip if hovering over an item
        mouse_pos = pygame.mouse.get_pos()
        if self.hovered_item and not self.dragging_item:
            tooltip_text = get_item_tooltip(self.hovered_item)
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

        # Draw recipe list background
        recipe_bg = pygame.Rect(self.recipe_list_x - 10, self.recipe_list_y - 10,
                              320, 420)
        pygame.draw.rect(self.screen, (40, 40, 40), recipe_bg)
        pygame.draw.rect(self.screen, (100, 100, 100), recipe_bg, 2)

        # Update recipe list draw call with required arguments
        self.recipe_list.draw(self.screen, self.font, self.selected_recipe)

        # Draw inventory grid background
        inventory_bg = pygame.Rect(
            self.inventory_start_x - 10,
            self.inventory_start_y - 10,
            8 * (self.slot_size + self.slot_padding) + 20,
            4 * (self.slot_size + self.slot_padding) + 20
        )
        pygame.draw.rect(self.screen, (40, 40, 40), inventory_bg)
        pygame.draw.rect(self.screen, (100, 100, 100), inventory_bg, 2)

        # Draw inventory slots
        for i in range(len(self.inventory.main)):
            row = i // 8
            col = i % 8
            x = self.inventory_start_x + col * (self.slot_size + self.slot_padding)
            y = self.inventory_start_y + row * (self.slot_size + self.slot_padding)
            
            # Draw slot background
            slot_rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            pygame.draw.rect(self.screen, (50, 50, 50), slot_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), slot_rect, 1)
            
            # Draw item if present
            slot = self.inventory.main[i]
            if slot and slot.get("item"):
                self.draw_item(slot, slot_rect)

        # Draw selected recipe details
        if 0 <= self.selected_recipe < len(self.recipes):
            recipe_key = self.recipes[self.selected_recipe]
            recipe = self.crafting.recipes[recipe_key]
            
            # Draw ingredients list
            y_offset = self.ingredients_start_y
            ingredients_header = self.font.render("Required:", True, (200, 200, 200))
            self.screen.blit(ingredients_header, (self.ingredients_start_x, y_offset))
            y_offset += 30
            
            for ingredient in recipe["ingredients"]:
                # Get ingredient name - try different keys or use item_id as fallback
                ingredient_name = ingredient.get("name",                  # Try name key first
                               ingredient.get("item_name",                # Try item_name second
                               str(ingredient.get("item_id", "Unknown"))) # Use item_id as fallback
                               )
                
                text = f"{ingredient['quantity']}x {ingredient_name}"
                # Check if player has enough
                has_enough = self.inventory.has_items([(ingredient["item_id"], ingredient["quantity"])])
                color = (0, 255, 0) if has_enough else (255, 0, 0)
                surf = self.font.render(text, True, color)
                self.screen.blit(surf, (self.ingredients_start_x, y_offset))
                y_offset += 25

            # Draw result preview with fixed result handling
            result_text = self.font.render("Result:", True, (200, 200, 200))
            self.screen.blit(result_text, (self.result_x, self.result_y - 30))
            
            result_rect = pygame.Rect(self.result_x, self.result_y, self.slot_size, self.slot_size)
            pygame.draw.rect(self.screen, (60, 60, 60), result_rect)
            pygame.draw.rect(self.screen, (120, 120, 120), result_rect, 2)
            
            # Draw craft button with updated style
            can_craft = self.inventory.has_items([(i["item_id"], i["quantity"]) for i in recipe["ingredients"]])
            button_color = (0, 150, 0) if can_craft else (100, 100, 100)
            hover_color = (0, 200, 0) if can_craft else (120, 120, 120)
            
            mouse_pos = pygame.mouse.get_pos()
            if self.craft_button_rect.collidepoint(mouse_pos) and can_craft:
                pygame.draw.rect(self.screen, hover_color, self.craft_button_rect)
            else:
                pygame.draw.rect(self.screen, button_color, self.craft_button_rect)
            
            pygame.draw.rect(self.screen, (200, 200, 200), self.craft_button_rect, 2)
            
            button_text = self.font.render("Craft", True, (255, 255, 255))
            text_rect = button_text.get_rect(center=self.craft_button_rect.center)
            self.screen.blit(button_text, text_rect)
            
            # Draw the result item
            if "result" in recipe:
                result_item = recipe["result"]
                if isinstance(result_item, dict):
                    self.draw_item(result_item, result_rect)
                else:
                    self.draw_item({"item": result_item, "quantity": 1}, result_rect)

        # Draw craft button
        pygame.draw.rect(self.screen, (0, 100, 0), self.craft_button_rect)
        pygame.draw.rect(self.screen, (0, 200, 0), self.craft_button_rect, 2)
        
        button_text = self.font.render("Craft", True, (255, 255, 255))
        text_rect = button_text.get_rect(center=self.craft_button_rect.center)
        self.screen.blit(button_text, text_rect)

        # Draw dragged item
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            drag_rect = pygame.Rect(
                mouse_pos[0] - self.slot_size//2,
                mouse_pos[1] - self.slot_size//2,
                self.slot_size,
                self.slot_size
            )
            self.draw_item(self.dragging_item, drag_rect)

        # Draw tooltip if hovering over an item
        if self.hovered_item and not self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            tooltip_text = get_item_tooltip(self.hovered_item)
            self.tooltip.draw(self.screen, tooltip_text, (mouse_pos[0] + 15, mouse_pos[1] + 15))

    def _render_recipe_slot(self, recipe, selected):
        """Create a surface for a recipe slot"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Draw slot background
        color = (70, 70, 70, 200) if selected else (50, 50, 50, 200)
        pygame.draw.rect(surface, color, (0, 0, self.slot_size, self.slot_size))
        border_color = (255, 215, 0, 255) if selected else (100, 100, 100, 255)
        pygame.draw.rect(surface, border_color, (0, 0, self.slot_size, self.slot_size), 2)
        
        # Draw recipe result item
        if recipe and recipe.result:
            item = recipe.result["item"]
            if hasattr(item, 'texture_coords'):
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_texture = self.texture_atlas.subsurface(texture_rect)
                scaled_texture = pygame.transform.scale(item_texture, (self.slot_size-8, self.slot_size-8))
                surface.blit(scaled_texture, (4, 4))
        
        return surface

    # Add similar render methods for ingredients and result slots...

    def draw_item(self, slot, rect):
        """Draw an item in a slot"""
        if slot and slot.get("item"):
            item = slot["item"]
            if hasattr(item, 'texture_coords'):
                tx, ty = item.texture_coords
                texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
                item_img = self.atlas.subsurface(texture_rect)
                scaled_img = pygame.transform.scale(item_img, (self.slot_size-8, self.slot_size-8))
                self.screen.blit(scaled_img, (rect.x + 4, rect.y + 4))
                
                # Draw quantity if more than 1
                quantity = slot.get("quantity", 0)
                if quantity > 1:
                    quantity_text = self.font.render(str(quantity), True, (255, 255, 255))
                    self.screen.blit(quantity_text, (rect.right - 20, rect.bottom - 20))
