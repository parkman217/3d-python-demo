import math
import os
import struct
import ModernGL
import pygame, sys
from pygame.locals import *
import time
import numpy as np
from pyrr import matrix44, vector3, quaternion
from numpy import linalg as LA
import glm


def tex_pos_to_coords(tx, ty):
    #texture_atlas_size = 8192#pixels width and height
    #half_pixel_length = 1/(texture_atlas_size*2)
    texture_width = 4#/texture_atlas_size#number of squares
    start_x = texture_width * tx
    start_y = texture_width * ty

    x0 = start_x# + half_pixel_length
    x1 = start_x + texture_width# - half_pixel_length

    y0 = start_y# + half_pixel_length
    y1 = start_y + texture_width# - half_pixel_length

    return x0, x1, y0, y1

def BuildForwardFace(x, y, z, block_type, block_texture_data):#texture done
    if block_type == 0:
        return [], []
    vbo = [ x-0.5, y-0.5, z+0.5, 2.0
         , x+0.5, y+0.5, z+0.5, 2.0
         , x-0.5, y+0.5, z+0.5, 2.0
         , x-0.5, y-0.5, z+0.5, 2.0
         , x+0.5, y-0.5, z+0.5, 2.0
         , x+0.5, y+0.5, z+0.5, 2.0]
    tx = block_texture_data[str(block_type)]['forward_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['forward_texture']['texture_y']

    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x0, y0,
                x1, y1,
                x0, y1,
                x0, y0,
                x1, y0,
                x1, y1]
    return vbo, texture_coords

def BuildBackwardFace(x, y, z, block_type, block_texture_data):#texture done
    if block_type == 0:
        return [], []
    vbo = [ x-0.5, y-0.5, z-0.5, 3.0
         , x-0.5, y+0.5, z-0.5, 3.0
         , x+0.5, y+0.5, z-0.5, 3.0
         , x-0.5, y-0.5, z-0.5, 3.0
         , x+0.5, y+0.5, z-0.5, 3.0
         , x+0.5, y-0.5, z-0.5, 3.0]
    
    tx = block_texture_data[str(block_type)]['backward_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['backward_texture']['texture_y']
    
    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x1, y0,
                    x1, y1,
                    x0, y1,
                    x1, y0,
                    x0, y1,
                    x0, y0]
    return vbo, texture_coords
def BuildRightFace(x, y, z, block_type, block_texture_data):#texture done
    if block_type == 0:
        return [], []
    vbo =[ x+0.5, y-0.5, z-0.5, 0.0
         , x+0.5, y+0.5, z+0.5, 0.0
         , x+0.5, y-0.5, z+0.5, 0.0
         , x+0.5, y-0.5, z-0.5, 0.0
         , x+0.5, y+0.5, z-0.5, 0.0
         , x+0.5, y+0.5, z+0.5, 0.0]
    
    tx = block_texture_data[str(block_type)]['right_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['right_texture']['texture_y']
    
    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x1, y0,
                x0, y1,
                x0, y0,
                x1, y0,
                x1, y1,
                x0, y1]
    return vbo, texture_coords
def BuildLeftFace(x, y, z, block_type, block_texture_data):#texture done
    if block_type == 0:
        return [], []
    vbo =[ x-0.5, y-0.5, z-0.5, 1.0
         , x-0.5, y-0.5, z+0.5, 1.0
         , x-0.5, y+0.5, z+0.5, 1.0
         , x-0.5, y-0.5, z-0.5, 1.0
         , x-0.5, y+0.5, z+0.5, 1.0
         , x-0.5, y+0.5, z-0.5, 1.0]
    
    tx = block_texture_data[str(block_type)]['left_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['left_texture']['texture_y']
    
    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x0, y0,
                    x1, y0,
                    x1, y1,
                    x0, y0,
                    x1, y1,
                    x0, y1]
    return vbo, texture_coords
def BuildBottomFace(x, y, z, block_type, block_texture_data):
    if block_type == 0:
        return [], []
    vbo =[ x+0.5, y-0.5, z-0.5, 5.0
         , x+0.5, y-0.5, z+0.5, 5.0
         , x-0.5, y-0.5, z-0.5, 5.0
         , x-0.5, y-0.5, z-0.5, 5.0
         , x+0.5, y-0.5, z+0.5, 5.0
         , x-0.5, y-0.5, z+0.5, 5.0]
    
    tx = block_texture_data[str(block_type)]['bottom_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['bottom_texture']['texture_y']
    
    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x1, y0,
                    x1, y1,
                    x0, y0,
                    x0, y0,
                    x1, y1,
                    x0, y1]
    return vbo, texture_coords

def BuildTopFace(x, y, z, block_type, block_texture_data):#fixed texture
    if block_type == 0:
        return [], []
    vbo =[ x+0.5, y+0.5, z-0.5, 4.0
         , x-0.5, y+0.5, z-0.5, 4.0
         , x+0.5, y+0.5, z+0.5, 4.0
         , x-0.5, y+0.5, z-0.5, 4.0
         , x-0.5, y+0.5, z+0.5, 4.0
         , x+0.5, y+0.5, z+0.5, 4.0]
    
    tx = block_texture_data[str(block_type)]['top_texture']['texture_x']
    ty = block_texture_data[str(block_type)]['top_texture']['texture_y']
    
    x0, x1, y0, y1 = tex_pos_to_coords(tx, ty)
    texture_coords = [x1, y0,
                    x0, y0,
                    x1, y1,
                    x0, y0,
                    x0, y1,
                    x1, y1]
    return vbo, texture_coords

def build_chunk(ctx, prog, chunk, world_, player_, block_texture_data):
    vertices = []
    colors = []

    world_width = world_.world_circumferance
    x_delta = chunk.chunk_x*16

    chunk_player_in = player_.pos[0]//world_width
    world_loop_in = player_.pos[0]//(world_width*16)#how many world overlaps aka times gone around the world

    region_chunk_in = chunk.chunk_x // (world_width//3+1)#need to add the one due to rounding
    region_player_in = chunk_player_in // (world_width//3+1)#need to add the one due to rounding

    if chunk_player_in % world_width < world_width/3:#in first region
        if region_chunk_in == 2:#put it on the left
            x_delta+=(world_loop_in-1)*world_width*16
        else:#put in on the right / middle
            x_delta+=(world_loop_in)*world_width*16
    elif chunk_player_in % world_width < 2*world_width/3:#in second region
        x_delta+=(world_loop_in)*world_width*16#things go where they are supposed to
    else:#in third region
        if region_chunk_in == 0:#go to the right
            x_delta+=(world_loop_in+1)*world_width*16
        else:
            x_delta+=(world_loop_in)*world_width*16
    
    for elem in chunk.get_visable_faces():
        x, y, z = elem[0]
        direction = elem[1]
        block_type = chunk.get_block_at(x,y,z)

        x+=x_delta#making sure the blocks have the right render coords
        z+=chunk.chunk_z*16
        
        if direction == 2:
            vbo1, color1 = BuildForwardFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
        elif direction == 3:#correct
            vbo1, color1 = BuildBackwardFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
        elif direction == 1:
            vbo1, color1 = BuildLeftFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
        elif direction == 0:
            vbo1, color1 = BuildRightFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
        elif direction == 4:
            vbo1, color1 = BuildTopFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
        elif direction == 5:
            vbo1, color1 = BuildBottomFace(x,y,z, block_type, block_texture_data)
            vertices.extend(vbo1)
            colors.extend(color1)
    return vertices, colors
def build_faces_from_broken_block(x, y, z, world_, block_texture_data):
    block0 = world_.get_block_at(x+1, y, z)
    block1 = world_.get_block_at(x-1, y, z)
    block2 = world_.get_block_at(x, y+1, z)
    block3 = world_.get_block_at(x, y-1, z)
    block4 = world_.get_block_at(x, y, z+1)
    block5 = world_.get_block_at(x, y, z-1)

    vertices = []
    colors = []
    block_data = []

    if block0 != None and block0 != 0:
        vbo1, color1 = BuildLeftFace(x+1,y,z,block0, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x+1,y,z), len(block_data)])
    if block1 != None and block1 != 0:
        vbo1, color1 = BuildRightFace(x-1,y,z,block1, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x-1,y,z), len(block_data)])
    if block2 != None and block2 != 0:
        vbo1, color1 = BuildBottomFace(x,y+1,z,block2, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y+1,z), len(block_data)])
    if block3 != None and block3 != 0:
        vbo1, color1 = BuildTopFace(x,y-1,z,block3, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y-1,z), len(block_data)])
    if block4 != None and block4 != 0:
        vbo1, color1 = BuildBackwardFace(x,y,z+1,block4, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z+1), len(block_data)])
    if block5 != None and block5 != 0:
        vbo1, color1 = BuildForwardFace(x,y,z-1,block5, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z-1), len(block_data)])
    return vertices, colors, block_data#actually vertices and texture data


def build_faces_from_placed_block(x, y, z, block_type, world_, block_texture_data):
    block0 = world_.get_block_at(x+1, y, z)
    block1 = world_.get_block_at(x-1, y, z)
    block2 = world_.get_block_at(x, y+1, z)
    block3 = world_.get_block_at(x, y-1, z)
    block4 = world_.get_block_at(x, y, z+1)
    block5 = world_.get_block_at(x, y, z-1)

    vertices = []
    colors = []
    block_data = []

    if block0 != None and block0 == 0:
        vbo1, color1 = BuildRightFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    if block1 != None and block1 == 0:
        vbo1, color1 = BuildLeftFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    if block2 != None and block2 == 0:
        vbo1, color1 = BuildTopFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    if block3 != None and block3 == 0:
        vbo1, color1 = BuildBottomFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    if block4 != None and block4 == 0:
        vbo1, color1 = BuildForwardFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    if block5 != None and block5 == 0:
        vbo1, color1 = BuildBackwardFace(x,y,z,block_type, block_texture_data)
        vertices.extend(vbo1)
        colors.extend(color1)
        block_data.append([(x,y,z), len(block_data)])
    return vertices, colors, block_data#actually vertices and texture data




