import math
import os
import struct
import ModernGL
import pygame, sys
from pygame.locals import *
import time
import numpy as np
import glm
import copy
import pickle

import m_renderer

class Inventory:
    def __init__(self):
        self.items = {}#type, count
        self.active_items = [None]*9
        #self.bar_vao = None
        self.bar_vaos = []
        self.selected = 0
    def add_item(self, item_type, count):
        if self.contains_item(item_type):
            self.items[item_type] += count
        else:
            self.items[item_type] = count
            if None in self.active_items:
                for a in range(0, len(self.active_items)):
                    if self.active_items[a] == None:
                        self.active_items[a] = item_type
                        break
    def remove_item_from_active_items(self, item_type):
        for a in range(len(self.active_items)):
            if self.active_items[a] == item_type:
                self.active_items[a] = None
    def remove_item(self, item_type, count):
        if self.contains_item(item_type):
            if self.items[item_type] >= count:
                self.items[item_type] -= count
                if self.items[item_type] == 0 and item_type in self.active_items:
                    self.remove_item_from_active_items(item_type)
                return
        print("trying to remove items from inventory when the inventory doesn't have enough")
    def contains_item(self, item_type):
        if item_type in self.items.keys():
            if self.items[item_type] > 0:
                return True
        return False
    def get_item_count(self, item_type):
        if self.contains_item(item_type) == False:
            return 0
        else:
            return self.item[item_type]
    def get_selected(self):
        return self.active_items[self.selected]
    def selected_down(self):
        self.selected = (self.selected+1)%len(self.active_items)
    def selected_up(self):
        self.selected = (self.selected-1)%len(self.active_items)
    def build_bar_vaos(self, data_package):
        '''vert_list = []
        text_list = []
        block_texture_data = data_package['renderer'].block_texture_data
        for a in range(0, len(self.active_items)):
            if self.active_items[a] != None:
                string = block_texture_data[str(self.active_items[a])]['block_name'] + ': '+str(self.items[self.active_items[a]])
            else:string='None'
            vert, text = m_renderer.build_text_vbos(string, data_package['renderer'].font, data_package['renderer'].ctx, 20,
                                                    a*20+20, 20, data_package['renderer'].screenX,
                                                    data_package['renderer'].screenY)
            vert_list.extend(vert)
            text_list.extend(text)
        vertices_vbo = data_package['renderer'].ctx.buffer(vert_list)
        texts_vbo = data_package['renderer'].ctx.buffer(text_list)
        data_package['renderer'].ctx.vertex_array(data_package['renderer'].frame_shader, [(vertices_vbo, '2f', ['in_vert']), (texts_vbo, '2f', ['in_text'])])'''
        self.bar_vaos = []
        renderer = data_package['renderer']
        block_texture_data = renderer.block_texture_data
        for a in range(0, len(self.active_items)):
            if a == self.selected:
                color = (255, 255, 255)
            else:
                color = (255, 0, 0)
            if self.active_items[a] != None:
                string = block_texture_data[str(self.active_items[a])]['block_name'] + ': '+str(self.items[self.active_items[a]])
            else:string = 'None'
            
            vao = m_renderer.build_text_vao(string, renderer.font, renderer.ctx, renderer.frame_shader, 20,
                                            renderer.screenY-(a*20+20), 40, renderer.screenX, renderer.screenY, color=color)
            self.bar_vaos.append(vao)
        
    def render(self):
        for a in self.bar_vaos:
            a[1].use()
            a[0].render()
    









