import pygame
import config as c
from crafting import Crafting
from scrollable_list import ScrollableList
from item import Item

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
        self.screen.fill((50, 50, 50))
        title = self.font.render("Crafting", True, (255,255,255))
        self.screen.blit(title, (c.SCREEN_WIDTH//2 - title.get_width()//2, 20))

        self.recipe_list.draw(self.screen, self.font, self.selected_recipe)

        button_rect = pygame.Rect(c.SCREEN_WIDTH//2 - 40, c.SCREEN_HEIGHT - 80, 80, 40)
        pygame.draw.rect(self.screen, (0,200,0), button_rect)
        btn_text = self.font.render("Craft", True, (0,0,0))
        self.screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2,
                                    button_rect.centery - btn_text.get_height()//2))

        # Draw inventory section
        rows = 4
        cols = 8
        for i in range(len(self.inventory.main)):
            row = i // cols
            col = i % cols
            x = self.inventory_x + col * (self.slot_size + self.slot_padding)
            y = self.inventory_y + row * (self.slot_size + self.slot_padding)
            
            # Draw slot background
            rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            # Draw item if present
            slot = self.inventory.main[i]
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

        # Draw dragged item
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            item = self.dragging_item["item"]
            tx, ty = item.texture_coords
            texture_rect = pygame.Rect(tx * c.BLOCK_SIZE, ty * c.BLOCK_SIZE, c.BLOCK_SIZE, c.BLOCK_SIZE)
            item_img = self.atlas.subsurface(texture_rect)
            item_img = pygame.transform.scale(item_img, (self.slot_size, self.slot_size))
            self.screen.blit(item_img, (mx - self.slot_size//2, my - self.slot_size//2))

        # Save previous clip and set clip to scrollable area
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(self.scroll_rect)
        
        # Draw crafting items inside this rectangle
        for recipe in self.recipes:
            # ...existing drawing code for each recipe item...
            pass  # Replace with your drawing logic

        # Reset clip region
        self.screen.set_clip(previous_clip)
