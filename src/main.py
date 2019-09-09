import math
import os
import struct
import ModernGL
import pygame, sys
from pygame.locals import *
import time
import numpy as np
import glm
import datetime as dt
import copy
import traceback
from multiprocessing import freeze_support

import m_shaders
import m_player
import m_renderer
import m_world
import m_input_manager

class Game:
    def __init__(self):
        self.data_package = {}#used for the event loops and holds player, world, etc
        self.data_package['renderer'] = m_renderer.Renderer(960, 540)#creates a render object

        self.data_package['running'] = True

        self.data_package['input_manager'] = m_input_manager.InputManager()        

        self.ingame_update_list = ['player', 'world', 'renderer']#things to call update on each frame
        self.ingame_tick_list = ['renderer']

        self.menus_update_list = ['renderer', 'input_manager']
        self.menus_tick_list = ['renderer']

        self.data_package['world'] = None
        self.data_package['player'] = None

        self.data_package['fps'] = 0
        self.data_package['universe_seed'] = 'test_universe_seed2'

        self.tick_rate = 2#how many times per second
        self.last_tick_time = time.time()

        self.game_state = 'menus'#menus, singleplayer, multiplayer
        self.data_package['game_state'] = self.game_state
        self.data_package['menu_selected'] = 0

        self.last_frame_time = time.time()
        self.frame_count = 0
        self.data_package['fps_counter'] = True
        self.debug_frame_latency = False
        self.last_second_time = time.time()
    def start_single_player(self):
        sector_x, sector_z = 0, 0
        world_seed = self.data_package['universe_seed'] + ','+str(sector_x)+','+str(sector_z)
        self.data_package['world'] = m_world.World(16, 8, world_seed)
        self.data_package['player'] = m_player.Player(self.data_package)
    def add_event_handler(self, func):#used to add event handler functions to be called
        self.event_handlers.append(func)
    def get_dt(self):
        t = time.time()
        dt = t - self.last_frame_time
        self.last_frame_time = t
        if dt > .01 and self.debug_frame_latency == True:
            print(dt)
        self.frame_count+=1
        if t - self.last_second_time > 1:
            self.data_package['fps'] = self.frame_count
            self.frame_count = 1
            self.last_second_time = t
                
        return dt
    def run(self):
        while self.data_package['running']:
            self.data_package['dt'] = self.get_dt()
            self.data_package['events'] = pygame.event.get()

            t = time.time()#ticks only once per tick time
            tick = False
            if t - self.last_tick_time > (1.0/self.tick_rate):
                self.last_tick_time = t
                tick = True
            if self.data_package['game_state'] == 'singleplayer':
                if self.data_package['world'] == None or self.data_package['player'] == None:
                    self.start_single_player()
                for obj in self.ingame_update_list:#updates each frame
                    self.data_package[obj].update(self.data_package)
                if tick == True:
                    for obj in self.ingame_tick_list:
                        self.data_package[obj].tick(self.data_package)
            
            elif self.data_package['game_state'] == 'menus':
                if self.data_package['world'] != None or self.data_package['player'] != None:
                    self.data_package['world'] = None
                    self.data_package['player'] = None
                for obj in self.menus_update_list:
                    self.data_package[obj].update(self.data_package)
                if tick == True:
                    for obj in self.menus_tick_list:
                        self.data_package[obj].tick(self.data_package)


if __name__ == '__main__':
    freeze_support()
    g = Game()
    g.run()
    
