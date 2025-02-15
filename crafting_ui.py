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
