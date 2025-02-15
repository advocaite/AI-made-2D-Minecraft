import pygame
import config as c
from crafting import Crafting

class CraftingUI:
    def __init__(self, screen, inventory, atlas):
        self.screen = screen
        self.inventory = inventory
        self.atlas = atlas
        self.crafting = Crafting()
        self.font = pygame.font.SysFont(None, 24)
        self.running = True
        self.recipes = list(self.crafting.recipes.keys())
        self.selected_recipe = 0
        self.recipe_rects = []  # will hold clickable areas for each recipe

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
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pos = event.pos
                        # Check if any recipe was clicked.
                        for idx, rect in enumerate(self.recipe_rects):
                            if rect.collidepoint(pos):
                                self.selected_recipe = idx
                        # Also check if craft button was clicked.
                        button_rect = pygame.Rect(c.SCREEN_WIDTH//2 - 40, c.SCREEN_HEIGHT - 80, 80, 40)
                        if button_rect.collidepoint(pos):
                            recipe_key = self.recipes[self.selected_recipe]
                            crafted = self.crafting.craft_item(self.inventory, recipe_key)
                            if crafted:
                                self.inventory.add_item(crafted)
            self.draw()
            pygame.display.flip()

    def draw(self):
        self.screen.fill((50, 50, 50))
        self.recipe_rects = []  # reset clickable areas each frame
        title = self.font.render("Crafting", True, (255,255,255))
        self.screen.blit(title, (c.SCREEN_WIDTH//2 - title.get_width()//2, 20))
        # Display list of recipes:
        for idx, key in enumerate(self.recipes):
            color = (255,215,0) if idx == self.selected_recipe else (255,255,255)
            recipe_text = self.font.render(key.capitalize(), True, color)
            text_pos = (50, 60 + idx * 60)
            self.screen.blit(recipe_text, text_pos)
            # Render the result image from texture atlas with transparency.
            recipe = self.crafting.recipes[key]
            tx, ty = recipe["result"]["texture_coords"]
            block_size = c.BLOCK_SIZE
            texture_rect = pygame.Rect(tx * block_size, ty * block_size, block_size, block_size)
            img = self.atlas.subsurface(texture_rect).convert_alpha()
            # Scale image (e.g., to 48x48) and ensure smooth scaling.
            img = pygame.transform.smoothscale(img, (48, 48))
            img_pos = (c.SCREEN_WIDTH - 100, 60 + idx * 60)
            self.screen.blit(img, img_pos)
            # Save recipe text clickable region.
            recipe_rect = pygame.Rect(text_pos[0], text_pos[1], recipe_text.get_width(), recipe_text.get_height())
            self.recipe_rects.append(recipe_rect)
        # Draw craft button.
        button_rect = pygame.Rect(c.SCREEN_WIDTH//2 - 40, c.SCREEN_HEIGHT - 80, 80, 40)
        pygame.draw.rect(self.screen, (0,200,0), button_rect)
        btn_text = self.font.render("Craft", True, (0,0,0))
        self.screen.blit(btn_text, (button_rect.centerx - btn_text.get_width()//2,
                                    button_rect.centery - btn_text.get_height()//2))
