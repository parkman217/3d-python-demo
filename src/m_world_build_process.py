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

import m_chunk

def thread_print(string):
    debug = False
    if debug == True:
        file = open("process_dump.txt", 'a')
        file.write(str(string)+'\n')
        file.close()


def gen_chunk(x, y, world_seed, spawn_rates_list, chunk_defaults):
    '''Used to generate new chunks given the givens for the rebuild_faces_process'''
    try:
        seed = world_seed + ','+str(x)+','+str(y)
        random.seed(seed)
        num = random.randint(0,chunk_defaults['total_weight'])
        curr_total = 0
        file_name = 'empty.p'
        for a in spawn_rates_list:
            curr_total += a['spawn_rate_weight']
            if num < curr_total:
                file_name = a['file_name']
                break
        block_list = copy.deepcopy(chunk_defaults[file_name])
        c = m_chunk.Chunk(x, y, world_seed, block_list = block_list)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        thread_print(str((exc_type, fname, exc_tb.tb_lineno)))
    return c
    
def rebuild_faces_process(pipe_b, world_circumferance, universe_height, world_seed, universe_save_name):    
    try:
        universe_path = '../saves/'+universe_save_name
        if not os.path.exists(universe_path):
            os.makedirs(universe_path)
            f = open(universe_path+'/universe.conf', 'w+')
            f.writelines('universe_seed_here')
            f.close()
        world_path = universe_path+'/'+world_seed
        if not os.path.exists(world_path):
            os.makedirs(world_path)
            f = open(world_path+'/world.conf','w+')
            f.writelines(world_seed)
            f.close()

        chunk_list = []
        for a in range(0, world_circumferance):
            column = []
            for b in range(0, universe_height):
                column.append([None, None])
            chunk_list.append(column)
        #chunk_list = [[[None, None]]*universe_height for a in range(0, world_circumferance)]#empty until chunks are loaded or generated

        f = open('../chunk_defaults/spawn_rates.json', 'r')
        text = f.read()
        f.close()
        chunk_spawn_rates = json.loads(text)
        
        chunk_defaults = {}
        chunk_defaults['total_weight'] = 0
        for a in chunk_spawn_rates:
            chunk_defaults['total_weight']+=a['spawn_rate_weight']
            block_list = pickle.load(open('../chunk_defaults/'+a['file_name'], 'rb'))
            chunk_defaults[a['file_name']] = block_list
            
        running = True
        loaded_chunk_indices = []
        while running:
            in_data = pipe_b.recv()
            if in_data == "Stop":
                #pickle.dump(chunk_list, open(world_path+'/world.p', 'wb'))#saving the chunk data
                running = False
                for a in range(0, len(chunk_list)):
                    for b in range(0, len(chunk_list[a])):
                        if chunk_list[a][b][1] != None:
                            chunk_path = world_path+'/'+str(a)+','+str(b)+'.dat'
                            pickle.dump(chunk_list[a][b][1], open(chunk_path, 'wb'))
                break
            
            #3 types of inbound messages
            #break block
            #place block
            #enter new chunk
            if in_data[0] == "Break":
                x = in_data[1]
                y = in_data[2]
                z = in_data[3]
                chunk_x = x//16
                chunk_z = z//16
                if chunk_z >= universe_height:
                    continue#skip because this isn't right
                if chunk_x >= world_circumferance or chunk_x < 0:
                    chunk_x = chunk_x % world_circumferance
                chunk = chunk_list[chunk_x][chunk_z][0]
                x = x%16
                z = z%16
                chunk.set_block_at(x, y, z, 0)
                chunk_list[chunk_x][chunk_z][1][(x%16, y, z%16)] = 0
                if chunk_z+1 < universe_height and z == 15:#setting the adjacent chunk to edited so the visable faces updates when reloaded
                    if chunk_list[chunk_x][chunk_z+1][0] != None:
                        chunk_list[chunk_x][chunk_z+1][0].edited = True
                if chunk_z-1 >= 0 and z == 0:#setting the adjacent chunk to edited so the visable faces updates when reloaded
                    if chunk_list[chunk_x][chunk_z-1][0] != None:
                        chunk_list[chunk_x][chunk_z-1][0].edited = True
                if x == 15:#setting the adjacent chunk to edited so the visable faces updates when reloaded
                    if chunk_list[(chunk_x+1)%world_circumferance][chunk_z][0] != None:
                        chunk_list[(chunk_x+1)%world_circumferance][chunk_z][0].edited = True
                if x == 0:#setting the adjacent chunk to edited so the visable faces updates when reloaded
                    if chunk_list[(chunk_x-1)%world_circumferance][chunk_z][0] != None:
                        chunk_list[(chunk_x-1)%world_circumferance][chunk_z][0].edited = True

            elif in_data[0] == "Place":
                x = in_data[1]
                y = in_data[2]
                z = in_data[3]
                block_type = in_data[4]
                chunk_x = x//16
                chunk_z = z//16
                if chunk_z >= universe_height:
                    continue#skip because this isn't right
                if chunk_x >= world_circumferance or chunk_x < 0:
                    chunk_x = chunk_x % world_circumferance
                chunk = chunk_list[chunk_x][chunk_z][0]
                chunk.set_block_at(x%16, y, z%16, block_type)
                chunk_list[chunk_x][chunk_z][1][(x%16, y, z%16)] = block_type
                
            elif in_data[0] == "Enter":
                chunk_x = in_data[1][0]
                chunk_z = in_data[1][1]
                if chunk_z >= universe_height:
                    continue#skip because this isn't right
                player_pos = in_data[2]
                render_distance = in_data[3]

                return_data = [[], []]#updated, loaded/generated, unloaded indices

                chunks_that_should_be_rendered = []
                position = (chunk_x-render_distance, chunk_z-render_distance)
                for x in range(render_distance*2+1):
                    for y in range(render_distance*2+1):
                        if (position[1]+y) < universe_height:
                            chunks_that_should_be_rendered.append(((position[0]+x)%world_circumferance, (position[1]+y)))

                reload_list = []
                #get a list of chunks that werent rendered last time
                for c in chunks_that_should_be_rendered:
                    if c not in loaded_chunk_indices:
                        reload_list.append(c)
                for c in range(0, len(loaded_chunk_indices)):
                    if loaded_chunk_indices[c] not in chunks_that_should_be_rendered:
                        pos = loaded_chunk_indices[c]
                        if pos[0] >= world_circumferance or pos[0] < 0:
                            pos = (pos[0] % world_circumferance, pos[1])
                        return_data[1].append(pos)#the chunks that should be removed from the render list aka unloading chunks
                        
                already_set_for_loading = []
                for pos in chunks_that_should_be_rendered:#loading stuff loop
                    pos_original = pos
                    if pos[0] >= world_circumferance or pos[0] < 0:
                        pos = (pos[0] % world_circumferance, pos[1])
                    if pos[1] < universe_height and pos[1] >= 0:
                        if chunk_list[pos[0]][pos[1]][0] == None:#if have not generated them before in this go
                            #c = Chunk(pos[0], pos[1], world_seed)
                            '''        else:#load the world pickle data
                            if not os.path.isfile(world_path+'/world.p'):
                                chunk_list = [[[None]]*universe_height for a in range(0, world_circumferance)]
                            else:
                                chunk_list = pickle.load(open(world_path+'/world.p', 'rb'))
                            '''
                            c = gen_chunk(pos[0], pos[1], world_seed, chunk_spawn_rates, chunk_defaults)
                            chunk_path = world_path+'/'+str(pos[0])+','+str(pos[1])+'.dat'
                            edit_map = {}
                            if os.path.isfile(chunk_path):
                                #chunk edit map saved before
                                edit_map = pickle.load(open(chunk_path, 'rb'))
                                for key in edit_map.keys():
                                    x, y, z = key
                                    c.set_block_at(x, y, z, edit_map[key])
                            chunk_list[pos[0]][pos[1]][0] = c
                            chunk_list[pos[0]][pos[1]][1] = edit_map#setting the chunk_list second element to the edit_map
                        elif pos_original in reload_list:#Generated but they were unloaded at some point
                            return_data[0].append(chunk_list[pos[0]][pos[1]][0])
                            already_set_for_loading.append((pos[0],pos[1]))
                for pos in chunks_that_should_be_rendered: #rendering stuff loop
                    plus_x = chunk_list[(pos[0]+1)%world_circumferance][pos[1]][0]
                    minus_x = chunk_list[(pos[0]-1)%world_circumferance][pos[1]][0]
                    if pos[1]+1 < universe_height:
                        plus_z = chunk_list[pos[0]%world_circumferance][pos[1]+1][0]
                    else:
                        plus_z = None
                    if pos[1]-1 >= 0:
                        minus_z = chunk_list[pos[0]%world_circumferance][pos[1]-1][0]
                    else:
                        minus_z = None
                    if pos[0] >= world_circumferance or pos[0] < 0:
                        pos = (pos[0] % world_circumferance, pos[1])
                    if pos[1] < universe_height and pos[1] >= 0:
                        #thread_print(chunk_list[pos[0]][pos[1]][0])
                        if chunk_list[pos[0]][pos[1]][0].calculate_visable_faces(plus_x, minus_x, plus_z, minus_z) == True:#if they were updated or generated or loaded
                            if pos not in already_set_for_loading:#make sure not from the unloaded chunks
                                return_data[0].append(chunk_list[pos[0]][pos[1]][0])
                
                loaded_chunk_indices = chunks_that_should_be_rendered#setting the loaded chunks to the newly loaded chunks
                
                if len(return_data[0]) == 0 and len(return_data[1]) == 0:
                    pipe_b.send("Done")
                else:
                    pipe_b.send(return_data)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        thread_print(str((exc_type, fname, exc_tb.tb_lineno)))
