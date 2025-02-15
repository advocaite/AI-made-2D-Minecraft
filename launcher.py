import pygame
import sys
from main_menu import MainMenu
from main import main as game_main

def run_launcher():
    pygame.init()
    from config import SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Reriara Clone - Main Menu")
    
    running = True
    while running:
        menu = MainMenu(screen)
        selection = menu.run()
        
        if selection == "start_game":
            result = game_main()
            if result == "quit":
                running = False
            # Continue loop if result is "launcher" to show menu again
        else:
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_launcher()
