import math
import os
import struct
import ModernGL
import pygame, sys
from pygame.locals import *
import time
import numpy as np
import glm
import threading
import random
from multiprocessing import Process, Pipe
import copy
import pickle
import json



class Chunk:
    def __init__(self, chunk_x, chunk_z, world_seed, height = 64, block_list = None):
        self.chunk_x = chunk_x #chunk x coord
        self.chunk_z = chunk_z #chunk z coord
        self.height = height
        self.seed = str(chunk_x) + ":" + str(chunk_z) + ":" + str(world_seed)
        self.edited = False

        if block_list == None:
            self.block_list = []
            for x in range(0, 16):
                y_list = []
                for y in range(0, self.height):
                    z_list = []
                    for z in range(0, 16):
                        if y < 28:
                            z_list.append(1)
                        elif y < 31:
                            z_list.append(2)
                        elif y < 32:
                            z_list.append(3)
                        else:
                            z_list.append(0)
                    y_list.append(z_list)
                self.block_list.append(y_list)
        else:
            self.block_list = block_list
        self.visable_faces = None
        self.render_vao_start_offset = None
    def get_block_at(self, x, y, z):
        x = math.floor(x)
        y = math.floor(y)
        z = math.floor(z)
        if x < 0 or x > 15 or y >= self.height or y < 0 or z > 15 or z < 0:
            return None
        return self.block_list[x][y][z]
    def set_block_at(self, x, y, z, block_type):
        self.edited = True
        self.block_list[x][y][z] = block_type
    def calculate_visable_faces(self, plus_x, minus_x, plus_z, minus_z):
        #doesn't need to recalculate if it wasn't edited since last calculation
        invisable_block_types = [0]
        if self.visable_faces == None or self.edited == True:
            self.edited = False
            self.visable_faces = [] #each element of this list will be a tuple containing the index and the face direction
            # 0 = +x
            # 1 = -x
            # 2 = +z
            # 3 = -z
            # 4 = +y
            # 5 = -y

            for x in range(0, len(self.block_list)):
                for y in range(0, len(self.block_list[x])):
                    for z in range(0, len(self.block_list[x][y])):
                        a = (x,y,z)
                        if self.block_list[x][y][z] not in invisable_block_types:
                            if x == 0:
                                if minus_x != None:
                                    if minus_x.get_block_at(15, y, z) in invisable_block_types:
                                        self.visable_faces.append((a, 1, len(self.visable_faces)))
                            elif self.get_block_at(x-1, y, z) in invisable_block_types:
                                self.visable_faces.append((a, 1, len(self.visable_faces)))
                                
                            if x == 15:
                                if plus_x != None:
                                    if plus_x.get_block_at(0, y, z) in invisable_block_types:
                                        self.visable_faces.append((a, 0, len(self.visable_faces)))
                            elif self.get_block_at(x+1, y, z) in invisable_block_types:
                                self.visable_faces.append((a, 0, len(self.visable_faces)))
                                
                            if y == 0:
                                pass
                            elif self.get_block_at(x, y-1, z) in invisable_block_types:
                                self.visable_faces.append((a, 5, len(self.visable_faces)))
                                
                            if y == self.height-1:
                                self.visable_faces.append((a, 4, len(self.visable_faces)))
                            elif self.get_block_at(x, y+1, z) in invisable_block_types:
                                self.visable_faces.append((a, 4, len(self.visable_faces)))
                                
                            if z == 0:
                                if minus_z != None:
                                    if minus_z.get_block_at(x, y, 15) in invisable_block_types:
                                        self.visable_faces.append((a, 3, len(self.visable_faces)))
                            elif self.get_block_at(x, y, z-1) in invisable_block_types:
                                self.visable_faces.append((a, 3, len(self.visable_faces)))
                            if z == 15:
                                if plus_z != None:
                                    if plus_z.get_block_at(x, y, 0) in invisable_block_types:
                                        self.visable_faces.append((a, 2, len(self.visable_faces)))
                            elif self.get_block_at(x, y, z+1) in invisable_block_types:
                                self.visable_faces.append((a, 2, len(self.visable_faces)))
            return True#return true if needed to recalculate
        else:
            return False#return false if didn't need to recalculate
                        
    def get_visable_faces(self):
        if self.visable_faces == None:
            self.calculate_visable_faces()
            return self.visable_faces
        else:
            return self.visable_faces
