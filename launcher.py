import pygame
import sys
from main_menu import MainMenu
from main import main as game_main

def run_launcher():
    pygame.init()
    from config import SCREEN_WIDTH, SCREEN_HEIGHT
    # Create a fullscreen window.
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Reriara Clone - Main Menu")
    
    menu = MainMenu(screen)
    selection = menu.run()
    
    if selection == "start_game":
        game_main()
    else:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    run_launcher()
