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

import m_inventory


class Player:
    def __init__(self, data_package):
        self.pos = [8.1,34.1,8.1]
        self.horizontalRotation = 0
        self.verticalRotation = 0
        self.speed = 30.0
        self.sensitivity = 180

        self.mouse_sensitivity = 14.0
        self.dt = .1
        
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.forward = False
        self.backward = False
        self.rotLeft = False
        self.rotRight = False
        self.rotUp = False
        self.rotDown = False

        self.world = data_package['world']
        self.renderer = data_package['renderer']

        self.falling = True
        self.fall_speed = 0.0
        self.fall_acceleration = 30.0

        self.flying = True

        self.inventory_open = False
        pygame.mouse.set_visible(self.inventory_open)

        self.inventory = m_inventory.Inventory()
        self.inventory.build_bar_vaos(data_package)

        self.chunk_in = [-1, -1]#set to an invalid chunk to force the chunk vao generating process
        self.render_distance = 3

        self.sun_move_speed = 15
        self.block_to_place = 1
        self.infinite_blocks = False
        
    def player_input(self, data_package):
        eventList = data_package['events']
        for event in eventList:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if data_package['world'] != None:
                        data_package['world'].exit_world()
                    data_package['game_state'] = 'menus'
                elif event.key == pygame.K_p:
                    print(self.pos)
                elif event.key == pygame.K_w:
                    self.forward = True
                elif event.key == pygame.K_s:
                    self.backward = True
                elif event.key == pygame.K_a:
                    self.left = True
                elif event.key == pygame.K_d:
                    self.right = True
                elif event.key == pygame.K_k:
                    self.renderer.set_point_light_pos(tuple(self.pos))
                elif event.key == pygame.K_m:
                    print("Saving chunk 0,0 as new_chunk_template.p")
                    pickle.dump(self.world.chunk_list[0][0].block_list, open('../chunk_defaults/new_chunk_template.p', 'wb'))
                elif event.key == pygame.K_i:
                    self.infinite_blocks = self.infinite_blocks == False
                elif event.key == pygame.K_SPACE:
                    if self.flying:
                        self.up = True
                    else:
                        self.falling = True
                        self.fall_speed = 10
                elif event.key == pygame.K_LSHIFT:
                    self.down = True
                elif event.key == pygame.K_LEFT:
                    self.rotLeft=True
                elif event.key == pygame.K_RIGHT:
                    self.rotRight=True
                elif event.key == pygame.K_UP:
                    self.rotUp=True
                elif event.key == pygame.K_DOWN:
                    self.rotDown=True
                elif event.key == pygame.K_e:
                    self.inventory_open = self.inventory_open == False
                    pygame.mouse.set_visible(self.inventory_open)
                elif event.key == pygame.K_f:
                    self.flying = self.flying == False
                    self.fall_speed = 0
            elif event.type == KEYUP:
                if event.key == pygame.K_w:
                    self.forward = False
                elif event.key == pygame.K_s:
                    self.backward = False
                elif event.key == pygame.K_a:
                    self.left = False
                elif event.key == pygame.K_d:
                    self.right = False
                elif event.key == pygame.K_SPACE:
                    self.up = False
                elif event.key == pygame.K_LSHIFT:
                    self.down = False
                elif event.key == pygame.K_LEFT:
                    self.rotLeft=False
                elif event.key == pygame.K_RIGHT:
                    self.rotRight=False
                elif event.key == pygame.K_UP:
                    self.rotUp=False
                elif event.key == pygame.K_DOWN:
                    self.rotDown=False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    #player left clicked
                    if self.inventory_open == False:
                        x,y,z=self.world.get_block_looking_at(20, self.pos, self.horizontalRotation, self.verticalRotation)
                        block_type = self.world.get_block_at(x,y,z)
                        if self.world.break_block(x,y,z, self.renderer) == True:
                            self.inventory.add_item(block_type, 1)
                            self.inventory.build_bar_vaos(data_package)
                elif event.button == 3:
                    #player right clicked
                    if self.inventory_open == False:
                        coords = self.world.get_empty_block_looking_at(20, self.pos, self.horizontalRotation, self.verticalRotation)
                        if coords == None:
                            print("Cant place a block when you are in a block")
                        else:
                            x,y,z = coords
                            if self.infinite_blocks == True:
                                self.world.place_block(x,y,z, self.block_to_place, self.renderer)
                            else:
                                selected = self.inventory.get_selected()
                                if selected != None:
                                    self.inventory.remove_item(selected, 1)
                                    self.world.place_block(x,y,z, selected, self.renderer)
                                    self.inventory.build_bar_vaos(data_package)
                elif event.button == 2:
                    #player middle clicked
                    if self.inventory_open == False:
                        x,y,z=self.world.get_block_looking_at(20, self.pos, self.horizontalRotation, self.verticalRotation)
                        self.block_to_place = self.world.get_block_at(x,y,z)
                elif event.button == 4:
                    self.inventory.selected_up()
                    self.inventory.build_bar_vaos(data_package)
                elif event.button == 5:
                    self.inventory.selected_down()
                    self.inventory.build_bar_vaos(data_package)
            elif event.type == MOUSEMOTION:
                if self.inventory_open == False:
                    pos = event.pos
                    dx = self.renderer.screenX/2 - pos[0]
                    dy = self.renderer.screenY/2 - pos[1]
                    self.horizontalRotation += self.mouse_sensitivity*dx*.01#*self.dt
                    self.verticalRotation += self.mouse_sensitivity*dy*.01#*self.dt

                    if self.verticalRotation > 89:
                        self.verticalRotation = 89
                    if self.verticalRotation < -89:
                        self.verticalRotation = -89
                    pygame.mouse.set_pos((self.renderer.screenX/2), int(self.renderer.screenY/2))
    def chunk_in_update(self, new_chunk_in): #called when the player enters a new chunk
        self.chunk_in = new_chunk_in
        self.world.enter_new_chunk(self.chunk_in, self)
    def update(self, data_package):

        #handle input
        self.player_input(data_package)
        
        dt = data_package['dt']
        lookX = math.sin(math.radians(self.horizontalRotation))#*math.fabs(math.cos(math.radians(self.verticalRotation)))
        lookZ = math.cos(math.radians(self.horizontalRotation))#*math.fabs(math.cos(math.radians(self.verticalRotation)))
        lookY = math.sin(math.radians(self.verticalRotation))
        self.dt = dt

        if self.rotRight == True:
            self.renderer.sun_angle+=self.sun_move_speed * dt
            self.renderer.set_light_direction()
        elif self.rotLeft == True:
            self.renderer.sun_angle-=self.sun_move_speed * dt
            self.renderer.set_light_direction()
        

        if self.flying == False:
            if self.falling == True:
                #print(self.fall_speed)
                block_type = self.world.get_block_at(self.pos[0]-.5, self.pos[1]-1.75, self.pos[2])
                if (block_type != 0 and block_type != None) and self.fall_speed < 0:#blocks are below and going down
                    self.falling = False
                    self.pos[1] = int(self.pos[1])+.75
                    self.fall_speed = 0
                else:#if no blocks below
                    self.pos[1]+=self.fall_speed*self.dt
                    self.fall_speed-=self.fall_acceleration*self.dt
            elif self.world.get_block_at(self.pos[0], self.pos[1]-1.8, self.pos[2]) == 0:
                self.falling = True

        if self.flying:
            if self.up:
                self.pos[1]+=self.speed*dt
            elif self.down:
                self.pos[1]-=self.speed*dt
        if self.left:
            self.pos[0]+=self.speed*lookZ*dt
            self.pos[2]-=self.speed*lookX*dt
        elif self.right:
            self.pos[0]-=self.speed*lookZ*dt
            self.pos[2]+=self.speed*lookX*dt
        if self.forward:
            self.pos[0]+=self.speed*lookX*dt
            self.pos[2]+=self.speed*lookZ*dt
        elif self.backward:
            self.pos[0]-=self.speed*lookX*dt
            self.pos[2]-=self.speed*lookZ*dt
        if self.rotLeft:
            pass
            #self.horizontalRotation += self.sensitivity*dt
        elif self.rotRight:
            pass
            #self.horizontalRotation -= self.sensitivity*dt
        if self.rotUp and self.verticalRotation < 85:
            self.verticalRotation+=self.sensitivity*dt
        elif self.rotDown and self.verticalRotation > -85:
            self.verticalRotation-=self.sensitivity*dt

        #making sure the player doesn't go out of bounds
        if self.pos[2] < 0:
            self.pos[2] = 0
        elif self.pos[2] >= self.world.universe_height*16:
            self.pos[2] = self.world.universe_height*16-.001

        calculated_chunk_in = [math.floor(self.pos[0])//16, math.floor(self.pos[2])//16]
        if calculated_chunk_in[0] < 0:#need to make sure that the chunk in wraps around
            calculated_chunk_in[0] += self.world.world_height
        elif calculated_chunk_in[0] > self.world.world_height:
            calculated_chunk_in[0] -= self.world.world_height
        if self.chunk_in != calculated_chunk_in:
            self.chunk_in_update(calculated_chunk_in)
    def build_projection_view(self, renderer):
        lookX = math.sin(math.radians(self.horizontalRotation))*math.fabs(math.cos(math.radians(self.verticalRotation)))
        lookZ = math.cos(math.radians(self.horizontalRotation))*math.fabs(math.cos(math.radians(self.verticalRotation)))
        lookY = math.sin(math.radians(self.verticalRotation))
        projection = glm.perspective(1.5, renderer.screenX/renderer.screenY, .1, 1000)
        view = glm.lookAt(glm.vec3(self.pos[0], self.pos[1], self.pos[2]),
                          glm.vec3(self.pos[0]+lookX, self.pos[1]+lookY, self.pos[2]+lookZ),
                          glm.vec3(0,1,0))            
        return projection, view





