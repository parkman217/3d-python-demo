import pygame, sys
from pygame.locals import *



class InputManager:
    def __init__(self):
        pass
    def update(self, data_package):
        for event in data_package['events']:
            if event.type == QUIT:
                data_package['running'] = False
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    data_package['running'] = False
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_UP:
                    data_package['menu_selected'] = (data_package['menu_selected']-1) % 4
                elif event.key == pygame.K_DOWN:
                    data_package['menu_selected'] = (data_package['menu_selected']+1) % 4
                elif event.key == pygame.K_RETURN:
                    if data_package['menu_selected'] == 0:
                        data_package['game_state'] = 'singleplayer'
                    elif data_package['menu_selected'] == 3:
                        data_package['running'] = False
                        pygame.quit()
                        sys.exit()
