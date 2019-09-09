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

import m_mesh_builder
import m_chunk
import m_world_build_process


            
class World:
    '''Worlds have a circumference that represents the number of chunks around they are and they also have a universe height which is how many chunks tall the world and the universe are'''

    def __init__(self, world_circumferance, universe_height, seed, universe_save_name = "Universe"):
        self.world_circumferance = world_circumferance
        self.universe_height = universe_height
        self.chunk_list = [[None]*self.universe_height for a in range(0, self.world_circumferance)]
        self.world_height = 64
        self.world_seed = seed

        self.verticesVBO = None
        self.world_vao = None

        self.indices_to_ignore = []

        self.chunk_render_list = []
        self.vertex_data = None

        self.second_vao = None
        self.second_vertex_data = []
        self.second_texture_data = []
        self.second_face_index_data = []# ((x,y,z), idx)
        self.second_verticesVBO = None

        self.thread_status = "Waiting"

        self.process_comm, b = Pipe()
        self.building_process = Process(target=m_world_build_process.rebuild_faces_process, args=(b,self.world_circumferance, self.universe_height, seed, universe_save_name,))
        self.building_process.start()

        self.need_to_rebuild_vao = False
        self.rebuild_queue = None
        self.rebuild_shadows = True

        self.break_wait_list = []
        self.place_wait_list = []
    def update(self, data_package):#used in the main thread once a frame
        renderer_ = data_package['renderer']
        player_ = data_package['player']
        if self.rebuild_queue != None and self.thread_status == "Waiting":
            self.thread_status = "Working"
            self.process_comm.send(["Enter", self.rebuild_queue[0], self.rebuild_queue[1].pos, self.rebuild_queue[1].render_distance])#message, chunk_coords, player.pos, render_distance
            self.rebuild_queue = None

        if self.process_comm.poll() == True:#ready to read an object
            ret_data = self.process_comm.recv()
            if ret_data == "Done":#Don't need to update the chunks
                self.thread_status = "Waiting"
                return
            for c in ret_data[0]:#updating the chunks that were updated
                x = c.chunk_x
                z = c.chunk_z
                self.chunk_list[x][z] = c
                found = False
                for a in range(0, len(self.chunk_render_list)):#aaaahhhh this is slow!!!!!!!
                    if self.chunk_render_list[a].chunk_x == x and self.chunk_render_list[a].chunk_z == z:
                        self.chunk_render_list[a] = c
                        found = True
                        break
                if found == False:
                    self.chunk_render_list.append(c)
            for c in ret_data[1]:#chunks that need to be unloaded
                x = c[0]
                z = c[1]
                for a in range(0, len(self.chunk_render_list)):#aaaahhhh this is slow!!!!!!!
                    if a >= len(self.chunk_render_list):
                        break
                    if self.chunk_render_list[a].chunk_x == x and self.chunk_render_list[a].chunk_z == z:
                        self.chunk_render_list.pop(a)
                        a-=1
            self.thread_status = "Start_Building_VAO"
            
        elif self.thread_status == "Start_Building_VAO":
            self.working_vertices_bytes = bytearray()
            self.working_textures_bytes = bytearray()
            self.working_total_offset = 0
            self.working_chunk_on = 0
            self.thread_status = "Adding_Chunks"
        elif self.thread_status == "Adding_Chunks":
            if self.working_chunk_on == len(self.chunk_render_list):
                self.thread_status = "Building_Vertex_VBO"
            else:
                c = self.chunk_render_list[self.working_chunk_on]
                self.chunk_render_list[self.working_chunk_on].render_vao_start_offset = self.working_total_offset
                self.working_total_offset+=len(c.visable_faces)
                vertices1, textures1 = m_mesh_builder.build_chunk(renderer_.ctx, renderer_.prog, c, self, player_, renderer_.block_texture_data)
                self.working_vertices_bytes.extend(struct.pack(str(len(vertices1))+'f', *vertices1))
                self.working_textures_bytes.extend(struct.pack(str(len(textures1))+'f', *textures1))
                self.working_chunk_on += 1
        elif self.thread_status == "Building_Vertex_VBO":
            self.verticesVBO = renderer_.ctx.buffer(self.working_vertices_bytes)            
            self.thread_status = "Building_Texture_VBO"
        elif self.thread_status == "Building_Texture_VBO":
            self.texturesVBO = renderer_.ctx.buffer(self.working_textures_bytes)
            self.world_vao = renderer_.ctx.vertex_array(renderer_.prog, [(self.verticesVBO, '4f', ['in_vert']),
                                      (self.texturesVBO, '2f', ['in_text'])])
            self.indices_to_ignore = []
            self.second_vao = None
            self.second_vertex_data = []
            self.second_texture_data = []
            self.second_face_index_data = []# ((x,y,z), idx)
            self.second_verticesVBO = None
            self.thread_status = "Waiting"
            self.rebuild_shadows = True
            while len(self.place_wait_list) > 0:#placing the blocks that were placed while rebuilding the vao
                x,y,z,block_type = self.place_wait_list[0]
                self.place_block(x,y,z,block_type,renderer_)
                self.place_wait_list.pop(0)
    def get_chunk_at(self, chunk_x, chunk_z):
        if chunk_x >= self.world_circumferance or chunk_x < 0:
            chunk_x = chunk_x % self.world_circumferance
        if chunk_z >= self.universe_height or chunk_z < 0:
            chunk_z = chunk_z % self.universe_height
        try:
            return self.chunk_list[chunk_x][chunk_z]
        except:
            print(chunk_x)
            print(chunk_z)
    def does_chunk_exist_at(self, chunk_x, chunk_z):
        if chunk_x >= self.world_circumferance or chunk_x < 0:
            chunk_x = chunk_x % self.world_circumferance
        if chunk_z >= self.universe_height or chunk_z < 0:
            return False
        return self.chunk_list[chunk_x][chunk_z] != None
    def generate_chunk_at(self, chunk_x, chunk_z):
        
        if chunk_x >= self.world_circumferance or chunk_x < 0:
            chunk_x = chunk_x % self.world_circumferance
        if chunk_z >= self.universe_height or chunk_z < 0:
            chunk_z = chunk_z % self.universe_height

        if self.does_chunk_exist_at(chunk_x, chunk_z)== False:
            chunk = Chunk(chunk_x, chunk_z, 64)
            self.chunk_list[chunk_x][chunk_z] = chunk
            return chunk
        else:
            return self.get_chunk_at(chunk_x, chunk_z)
    def render(self):
        if type(self.world_vao) != type(None):
            self.world_vao.render()
        if type(self.second_vao) != type(None):
            self.second_vao.render()
    def get_vbos(self):
        return self.verticesVBO, self.second_verticesVBO
    def break_block(self, x, y, z, renderer_):
        if self.thread_status == "Waiting":#only break or place blocks if thread not running for now            
            chunk_x = x//16
            chunk_z = z//16
            if self.does_chunk_exist_at(chunk_x, chunk_z) == False:
                print("Trying to break a block where one does not exist")
                return False
            chunk = self.get_chunk_at(chunk_x, chunk_z)
            block_type = chunk.get_block_at(x%16, y, z%16)
            if block_type == 0 or block_type == None:#returning if trying to break air or nothing
                return False
            
            chunk.set_block_at(x%16, y, z%16, 0)#setting the block to 0
            if chunk.render_vao_start_offset == None:
                return False

            if self.thread_status == "Waiting":#send to the process if not working on something right now
                self.process_comm.send(["Break", x, y, z])
            else:
                print("appendinating")
                self.break_wait_list.append((x,y,z))
                
            self.rebuild_shadows = True
            '''Setting the visable faces in the main vao to be invisable for the block that was broken'''
            chunk_visable_faces = chunk.get_visable_faces()
            for a in range(0, len(chunk_visable_faces)):
                if chunk_visable_faces[a][0][0] == x%16 and chunk_visable_faces[a][0][1] == y and chunk_visable_faces[a][0][2] == z%16:
                    start = (chunk.render_vao_start_offset + chunk_visable_faces[a][2])*96#in byte offsets so 24*4
                    zeros = [0]*24
                    zero_data = struct.pack(str(len(zeros))+'f', *zeros)
                    self.verticesVBO.write(zero_data, offset = start)
                    self.world_vao = renderer_.ctx.vertex_array(renderer_.prog, [(self.verticesVBO, '4f', ['in_vert']),
                                              (self.texturesVBO, '2f', ['in_text'])])


            '''Deleting data from the second vao buffers if it was for a block that was just deleted'''
            for a in range(0, len(self.second_face_index_data)):
                if a >= len(self.second_face_index_data):
                    break
                if self.second_face_index_data[a][0] == (x,y,z):
                    idx = self.second_face_index_data[a][1]
                    self.second_vertex_data[(idx+0)*24:(idx+1)*24] = [0]*24 #setting the bad data to zeros

            '''Adding render data to the second vao for the faces around the block that was just broken'''
            vertices, text_data, block_data = m_mesh_builder.build_faces_from_broken_block(x, y, z, self, renderer_.block_texture_data)
            count = len(self.second_face_index_data)
            for a in block_data:
                self.second_face_index_data.append([a[0], a[1]+count])
            self.second_vertex_data.extend(vertices)
            self.second_texture_data.extend(text_data)
            if len(self.second_vertex_data) > 0 and len(self.second_texture_data) > 0:
                self.second_verticesVBO = renderer_.ctx.buffer(struct.pack(str(len(self.second_vertex_data))+'f', *self.second_vertex_data))
                texturesVBO = renderer_.ctx.buffer(struct.pack(str(len(self.second_texture_data))+'f', *self.second_texture_data))
                self.second_vao = renderer_.ctx.vertex_array(renderer_.prog, [(self.second_verticesVBO, '4f', ['in_vert']),
                                      (texturesVBO, '2f', ['in_text'])])
            return True
        return False #if the block breaking was not sucessful return false

    def place_block(self, x, y, z, block_type, renderer_):
        chunk_x = x//16
        chunk_z = z//16
        
        if self.does_chunk_exist_at(chunk_x, chunk_z) == False:
            print("Trying to place a block where you can't")
            return None
        chunk = self.get_chunk_at(chunk_x, chunk_z)
        if block_type == 0 or block_type == None:#returning if trying to place nothing or air
            return None
        
        chunk.set_block_at(x%16, y, z%16, block_type)#setting the block to the block type
        if self.thread_status == "Waiting":
            self.process_comm.send(["Place", x, y, z, block_type])
        else:
            self.place_wait_list.append((x,y,z,block_type))

        self.rebuild_shadows = True
        vertices, text_data, block_data = m_mesh_builder.build_faces_from_placed_block(x, y, z, block_type, self, renderer_.block_texture_data)
        count = len(self.second_face_index_data)
        for a in block_data:
            self.second_face_index_data.append([a[0], a[1]+count])
        self.second_vertex_data.extend(vertices)
        self.second_texture_data.extend(text_data)
        self.second_verticesVBO = renderer_.ctx.buffer(struct.pack(str(len(self.second_vertex_data))+'f', *self.second_vertex_data))
        texturesVBO = renderer_.ctx.buffer(struct.pack(str(len(self.second_texture_data))+'f', *self.second_texture_data))
        self.second_vao = renderer_.ctx.vertex_array(renderer_.prog, [(self.second_verticesVBO, '4f', ['in_vert']),
                                  (texturesVBO, '2f', ['in_text'])])
        
    def get_block_at(self, x, y, z):
        x = int(x)
        y = int(y)
        z = int(z)
        chunk_x = x//16
        chunk_z = z//16
        if self.does_chunk_exist_at(chunk_x, chunk_z) == True:
            chunk = self.get_chunk_at(chunk_x, chunk_z)
            return chunk.get_block_at(x%16, y, z%16)
        else:
            return None
    def exit_world(self):
        #called when the player leaves the world or leaves the game after being on this world
         self.process_comm.send("Stop")#kill the process and save the world data

    def enter_new_chunk(self, chunk_pos, player_, force_update=False):# used when the player enters a new chunk and the world vao needs to update
        self.rebuild_queue = [chunk_pos, player_]
    def get_distance(self, pos_1, pos_2):
        return ((pos_1[0]-pos_2[0])**2+(pos_1[1]-pos_2[1])**2+(pos_1[2]-pos_2[2])**2)**.5
    def get_empty_block_looking_at(self, look_distance, start_pos, horizontal_rotation, verticle_rotation):#returns x, y, z coords
        look_dir = [math.sin(math.radians(horizontal_rotation))*math.fabs(math.cos(math.radians(verticle_rotation))),
                    math.sin(math.radians(verticle_rotation)),
                    math.cos(math.radians(horizontal_rotation))*math.fabs(math.cos(math.radians(verticle_rotation)))]
        end_pos = copy.copy(start_pos)
        current_block_type = self.get_block_at(math.floor(end_pos[0]), math.floor(end_pos[1]), math.floor(end_pos[2]))
        last_end_pos = None
        while self.get_distance(start_pos, end_pos) < look_distance and current_block_type == 0:
            last_end_pos = end_pos
            end_pos = self.block_ray_cast(end_pos, look_dir)
            current_block_type = self.get_block_at(math.floor(end_pos[0]), math.floor(end_pos[1]), math.floor(end_pos[2]))
        if last_end_pos == None or self.get_distance(start_pos, end_pos) >= look_distance:
            return None
        return math.floor(last_end_pos[0]), math.floor(last_end_pos[1]), math.floor(last_end_pos[2])

    def get_block_looking_at(self, look_distance, start_pos, horizontal_rotation, verticle_rotation):#returns x, y, z coords
        look_dir = [math.sin(math.radians(horizontal_rotation))*math.fabs(math.cos(math.radians(verticle_rotation))),
                    math.sin(math.radians(verticle_rotation)),
                    math.cos(math.radians(horizontal_rotation))*math.fabs(math.cos(math.radians(verticle_rotation)))]
        end_pos = copy.copy(start_pos)
        current_block_type = self.get_block_at(math.floor(end_pos[0]), math.floor(end_pos[1]), math.floor(end_pos[2]))
        while self.get_distance(start_pos, end_pos) < look_distance and current_block_type == 0:
            end_pos = self.block_ray_cast(end_pos, look_dir)
            current_block_type = self.get_block_at(math.floor(end_pos[0]), math.floor(end_pos[1]), math.floor(end_pos[2]))
        return math.floor(end_pos[0]), math.floor(end_pos[1]), math.floor(end_pos[2])

    def block_ray_cast(self, start_pos, look_dir):#look_dir needs to be normalized
        neg_x = False
        neg_y = False
        neg_z = False
        start_pos = copy.copy(start_pos)
        if look_dir[0] > 0:#looking in the positive x direction
            distance = math.ceil(start_pos[0])-start_pos[0]
            if look_dir[0] == 0:
                x_time = 100
            else:
                x_time = math.fabs(distance/look_dir[0])
        else:#looking in the negative x direction
            distance = start_pos[0]-math.floor(start_pos[0])
            neg_x = True
            if look_dir[0] == 0:
                x_time = 100
            else:
                x_time = math.fabs(distance/look_dir[0])
        if look_dir[1] > 0:#looking in the positive y direction
            distance = math.ceil(start_pos[1])-start_pos[1]
            if look_dir[1] == 0:
                y_time = 100
            else:
                y_time = math.fabs(distance/look_dir[1])
        else:#looking in the negative y direction
            distance = start_pos[1]-math.floor(start_pos[1])
            neg_y=True
            if look_dir[1] == 0:
                y_time = 100
            else:
                y_time = math.fabs(distance/look_dir[1])
        if look_dir[2] > 0:#looking in the positive z direction
            distance = math.ceil(start_pos[2])-start_pos[2]
            if look_dir[2] == 0:
                z_time = 100
            else:
                z_time = math.fabs(distance/look_dir[2])
        else:#looking in the negative z direction
            distance = start_pos[2]-math.floor(start_pos[2])
            neg_z = True
            if look_dir[2] == 0:
                z_time = 100
            else:
                z_time = math.fabs(distance/look_dir[2])

        if x_time < y_time and x_time < z_time:
            #x is the closest
            d_time = x_time
            end_pos = [start_pos[0]+look_dir[0]*d_time,start_pos[1]+look_dir[1]*d_time,start_pos[2]+look_dir[2]*d_time]
            if neg_x:
                end_pos[0]-=0.0001
            else:
                end_pos[0]+=0.0001
        elif y_time < x_time and y_time < z_time:
            #y is the closest
            d_time = y_time
            end_pos = [start_pos[0]+look_dir[0]*d_time,start_pos[1]+look_dir[1]*d_time,start_pos[2]+look_dir[2]*d_time]
            if neg_y:
                end_pos[1]-=0.0001
            else:
                end_pos[1]+=0.0001
        else:
            #z is the closest
            d_time = z_time
            end_pos = [start_pos[0]+look_dir[0]*d_time,start_pos[1]+look_dir[1]*d_time,start_pos[2]+look_dir[2]*d_time]
            if neg_z:
                end_pos[2]-=0.0001
            else:
                end_pos[2]+=0.0001
        return end_pos

        
        
        
