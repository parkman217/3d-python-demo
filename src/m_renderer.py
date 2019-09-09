import math
import os
import struct
import ModernGL
import pygame, sys
from pygame.locals import *
from PIL import Image
import time
import numpy as np
import glm
import json

import m_shaders

def local(*path):
    return os.path.join(os.path.dirname(__file__), *path)

def calculate_2d_vertices_square(pos_x, pos_y, screen_x, screen_y, size):
    '''Calculates the vertices for a location centered on pos_x and pos_y with size as the percent of the screen

    pos_x is the position on the x axis 0 = left side of screen 1 = right side
    pos_y is the position on the y axis 0 = botom of screen 1 = top of screen
    screen_x is the width of the screen
    screen_y is the height of the screen
    size is the size of the square of vertices relitive to the window width

    returns bytes'''
    aspect_ratio = screen_x / screen_y
    delta_x = size / 2
    delta_y = delta_x * aspect_ratio
    pts = [pos_x - delta_x,pos_y - delta_y, pos_x + delta_x,pos_y - delta_y, pos_x + delta_x,pos_y + delta_y,
            pos_x - delta_x,pos_y - delta_y, pos_x + delta_x,pos_y + delta_y, pos_x - delta_x,pos_y + delta_y]
    return np.array(pts).astype('f4').tobytes()
'''def build_text_vbo_bytes(string, font, ctx, start_x, start_y, height, screen_x, screen_y):
    start_x*=2
    start_y*=2
    text = pygame.transform.flip(font.render(string, True, (255, 255, 255)), False, True)
    text_texture = ctx.texture(text.get_size(), 4, pygame.image.tostring(text, 'RGBA'))

    width = height*len(string) * .75
    pts = np.array([(start_x)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y + height)/screen_y-1.0,
           (start_x)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y + height)/screen_y-1.0,
           (start_x)/screen_x-1.0, (start_y + height)/screen_y-1.0])
    return pts.astype('f4').tobytes(), np.array([0,0, 1,0, 1,1, 0,0, 1,1, 0,1]).astype('f4').tobytes()

def build_text_vao(string, font, ctx, frame_shader, start_x, start_y, height, screen_x, screen_y):
    vertices_data, texts_data = build_text_vbo_bytes(string, font, ctx, start_x, start_y, height, screen_x, screen_y)
    vertices_vbo = ctx.buffer(vertices_data)
    texts_vbo = ctx.buffer(texts_data)
    return ctx.vertex_array(frame_shader, [(vertices_vbo, '2f', ['in_vert']), (texts_vbo, '2f', ['in_text'])]), text_texture
'''

def build_text_vao(string, font, ctx, frame_shader, start_x, start_y, height, screen_x, screen_y, color = (255,255,255)):
    start_x*=2
    start_y*=2
    text = pygame.transform.flip(font.render(string, True, color), False, True)
    text_texture = ctx.texture(text.get_size(), 4, pygame.image.tostring(text, 'RGBA'))

    width = height*len(string) * .75
    pts = np.array([(start_x)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y + height)/screen_y-1.0,
           (start_x)/screen_x-1.0, (start_y)/screen_y-1.0,
           (start_x + width)/screen_x-1.0, (start_y + height)/screen_y-1.0,
           (start_x)/screen_x-1.0, (start_y + height)/screen_y-1.0])    
    vertices_vbo = ctx.buffer(pts.astype('f4').tobytes())
    texts_vbo = ctx.buffer(np.array([0,0, 1,0, 1,1, 0,0, 1,1, 0,1]).astype('f4').tobytes())
    return ctx.vertex_array(frame_shader, [(vertices_vbo, '2f', ['in_vert']), (texts_vbo, '2f', ['in_text'])]), text_texture

def normalize(vec):
    total = 0
    for a in vec: total+=a**2
    total = math.sqrt(total)
    ret = []
    for a in vec:ret.append(a/total)
    return ret

def build_button_vao(ctx, self, shader, offset, x, y, width, height):
    
    pts = np.array([x/self.screenX-1.0, y/self.screenY-1.0,  (x+width)/self.screenX-1.0, y/self.screenY-1.0,  (x+width)/self.screenX-1.0, (y+height)/self.screenY-1.0,
                    x/self.screenX-1.0, y/self.screenY-1.0,  (x+width)/self.screenX-1.0, (y+height)/self.screenY-1.0,  x/self.screenX-1.0, (y+height)/self.screenY-1.0])
    texture_height = .25
    vertices_vbo = ctx.buffer(pts.astype('f4').tobytes())
    texts_pts = np.array([0,offset, 1,offset, 1,offset+texture_height, 0,offset, 1,offset+texture_height, 0,offset+texture_height])
    texts_vbo = ctx.buffer(texts_pts.astype('f4').tobytes())
    return ctx.vertex_array(shader, [(vertices_vbo, '2f', ['in_vert']), (texts_vbo, '2f', ['in_text'])])

def build_menu_buttons(self, ctx):
    img = Image.open('../res/buttons.png').transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
    self.button_texture = ctx.texture(img.size, 3, img.tobytes())
    self.button_shader = m_shaders.Build_Button_Shader(ctx)

    self.button_selected_uniform = self.button_shader.uniforms['selected']
    self.button_selected_uniform.value = False

    button_width = 400
    button_height = 75
    button_x_buffer = 100
    button_y_buffer = 175
    button_offset = 100

    self.menu_button_list = [build_button_vao(ctx, self, self.button_shader, .75, button_x_buffer, self.screenY*2-(button_y_buffer+button_offset*0), button_width, button_height),
                             build_button_vao(ctx, self, self.button_shader, .5, button_x_buffer, self.screenY*2-(button_y_buffer+button_offset*1), button_width, button_height),
                             build_button_vao(ctx, self, self.button_shader, .25, button_x_buffer, self.screenY*2-(button_y_buffer+button_offset*2), button_width, button_height),
                             build_button_vao(ctx, self, self.button_shader, 0, button_x_buffer, self.screenY*2-(button_y_buffer+button_offset*3), button_width, button_height)]
    
def renderer_init(self, screenX, screenY):
    self.screenX = screenX
    self.screenY = screenY

    position = (25, 25)
    #os.environ['SDL_VIDEO_WINDOW_POS'] = str(position[0]) + "," + str(position[1])

    self.aspect_ratio = self.screenX / self.screenY
    self.resolution_scale = 100
    
    self.shadow_detail_level = 4# 1, 2, 3, 4, ...

    self.shadow_resolution = int(512*self.shadow_detail_level)#should be tied in with render distance

    self.resolution_x = int(self.screenX * self.resolution_scale / 100)
    self.resolution_y = int(self.screenY * self.resolution_scale / 100)
    
    pygame.init()
    #self.screen = pygame.display.set_mode((screenX, screenY), DOUBLEBUF | OPENGL | FULLSCREEN)
    self.screen = pygame.display.set_mode((screenX, screenY), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Game Caption")
    self.ctx = ModernGL.create_context()

    self.sun_angle = 45

    f = open('../options/block_texture_data.json', 'r')
    text = f.read()
    f.close()
    self.block_texture_data = json.loads(text)

    build_menu_buttons(self, self.ctx)
    
    self.prog = m_shaders.BuildShader(self.ctx)
    self.mvp_uniform = self.prog.uniforms['MVP']
    self.directional_light_uniform = self.prog.uniforms['directional_light']
    self.set_light_direction()
    self.point_light_pos = self.prog.uniforms['point_light_pos']
    self.point_light_pos.value = (0,0,0)
    self.prog_depth_mvp = self.prog.uniforms['Depth_MVP']
    self.prog.uniforms['Texture'].value = 0
    self.prog.uniforms['shadow_map'].value = 1
    self.prog.uniforms['bias_matrix'].value = tuple(np.array(glm.mat4(0.5, 0.0, 0.0, 0.0,0.0, 0.5, 0.0, 0.0,0.0, 0.0, 0.5, 0.0,0.5, 0.5, 0.5, 1.0).value).reshape((1,16))[0])
    
    self.frame_shader = m_shaders.Build_Frame_Shader(self.ctx)#used for rendering the world to the screen
    self.texture_to_render_to = self.ctx.texture((self.resolution_x,self.resolution_y),3)
    self.depth_buffer = self.ctx.depth_renderbuffer((self.resolution_x,self.resolution_y))
    self.frame_buffer = self.ctx.framebuffer(self.texture_to_render_to, self.depth_buffer)#thing
    self.frame_vertices_vbo = self.ctx.buffer(np.array([-1,-1, 1,-1, 1,1, -1,-1, 1,1, -1,1]).astype('f4').tobytes())
    self.frame_texts_vbo = self.ctx.buffer(np.array([0,0, 1,0, 1,1, 0,0, 1,1, 0,1]).astype('f4').tobytes())
    self.frame_vao = self.ctx.vertex_array(self.frame_shader, [(self.frame_vertices_vbo, '2f', ['in_vert']), (self.frame_texts_vbo, '2f', ['in_text'])])

    self.shadow_shader = m_shaders.Build_Shadow_Shader(self.ctx)
    self.shadow_texture = self.ctx.texture((self.shadow_resolution, self.shadow_resolution), 3)
    self.shadow_depth_buffer = self.ctx.depth_renderbuffer((self.shadow_resolution, self.shadow_resolution))
    self.shadow_frame_buffer = self.ctx.framebuffer(self.shadow_texture, self.shadow_depth_buffer)
    self.shadow_mvp = self.shadow_shader.uniforms['depthMVP']

    self.font = pygame.font.Font("../res/font.ttf", 72)
    self.fps_vao, self.fps_texture = build_text_vao("100", self.font, self.ctx, self.frame_shader, 0, 0, 30, self.screenX, self.screenY)

    img_cross = Image.open('../res/cross.png').transpose(Image.FLIP_TOP_BOTTOM).convert('RGBA')
    self.cross_texture = self.ctx.texture(img_cross.size, 4, img_cross.tobytes())
    self.cross_vertices_vbo = self.ctx.buffer(calculate_2d_vertices_square(0.0, 0.0, self.screenX, self.screenY, .03))
    self.cross_texts_vbo = self.ctx.buffer(np.array([0,0, 1,0, 1,1, 0,0, 1,1, 0,1]).astype('f4').tobytes())
    self.cross_vao = self.ctx.vertex_array(self.frame_shader, [(self.cross_vertices_vbo, '2f', ['in_vert']), (self.cross_texts_vbo, '2f', ['in_text'])])

    self.frame_z_val_uniform = self.frame_shader.uniforms['z_val']
    self.frame_z_val_uniform.value = -0.9

    '''These matricies will be accessed by different rendering methods'''
    self.projection = None #The projection matrix
    self.view = None #The view matrix

    img = Image.open('../res/texture.png').transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
    self.texture = self.ctx.texture(img.size, 3, img.tobytes())
    self.texture.build_mipmaps()

    self.shadow_vert_vao_1 = None
    self.shadow_vert_vao_2 = None

class Renderer:
    def set_light_direction(self):
        rads = math.radians(self.sun_angle)
        x = -math.cos(rads)
        if x == 0:
            x+=.00001
        y = -math.sin(rads)
        self.directional_light_uniform.value = (x, y, 0)
    def __init__(self, screenX, screenY):
        renderer_init(self, screenX, screenY)
    def render_ingame(self, data_package):
        local_player = data_package['player']
        world_ = data_package['world']

        self.ctx.enable(ModernGL.DEPTH_TEST)
        self.ctx.enable(ModernGL.BLEND)
        self.ctx.enable(ModernGL.CULL_FACE)

        self.ctx.screen.use()#rendering the main framebuffer to the screen
        self.ctx.viewport = (0, 0, self.screenX, self.screenY)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        self.ctx.wireframe = False
        self.projection, self.view = local_player.build_projection_view(self)
        
        if type(world_ )!= type(None):
            if world_.rebuild_shadows == True:#only rebuild shadows when place / break / generate
                world_.rebuild_shadows = False
                vertices_vbo, second_vertices_vbo = world_.get_vbos()#render the world and return the vertex information for both vbos
                if type(vertices_vbo) != type(None):
                    self.shadow_vert_vao_1 = self.ctx.vertex_array(self.shadow_shader, [(vertices_vbo, '4f', ['vertexPosition_modelspace'])])#update the buffers with the vertex data
                if type(second_vertices_vbo) != type(None):
                    self.shadow_vert_vao_2 = self.ctx.vertex_array(self.shadow_shader, [(second_vertices_vbo, '4f', ['vertexPosition_modelspace'])])#update the buffers with the vertex data
            
            self.shadow_frame_buffer.use()#render to the frame buffer
            self.shadow_frame_buffer.clear(0,0,0,1)
            self.ctx.viewport = (0, 0, self.shadow_resolution, self.shadow_resolution)
            shadow_mvp = tuple(np.array(self.build_shadow_mvp(local_player).value).reshape((1,16))[0])#still need to update the mvp each frame
            self.shadow_mvp.value = shadow_mvp
            self.prog_depth_mvp.value = shadow_mvp
            if type(self.shadow_vert_vao_1) != type(None):
                self.shadow_vert_vao_1.render()
            if type(self.shadow_vert_vao_2) != type(None):
                self.shadow_vert_vao_2.render()
                
            model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(0.5, 0.5, 0.5));#world model matrix
            self.set_MVP_from_model(model_matrix)
            self.frame_buffer.use()#render to the frame buffer
            self.texture.use(0)#use the main texture atlas
            self.shadow_texture.use(1)#use the shadow texture

            self.frame_buffer.clear(0,0,0,1)
            self.ctx.viewport = (0, 0, self.resolution_x, self.resolution_y)
            world_.render()

        self.ctx.screen.use()#rendering the main framebuffer to the screen
        self.ctx.viewport = (0, 0, self.screenX, self.screenY)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.texture_to_render_to.use()#rendering the worldframe
        self.frame_z_val_uniform.value = -0.8
        self.frame_vao.render()

        self.cross_texture.use()#rendering the cross
        self.frame_z_val_uniform.value = -0.9
        self.cross_vao.render()

        local_player.inventory.render()

        if data_package['fps_counter'] == True:
            self.fps_texture.use()#render the fps counter
            self.fps_vao.render()
        
        pygame.display.flip()
    def render_menus(self, data_package):
        self.ctx.enable(ModernGL.DEPTH_TEST)
        self.ctx.enable(ModernGL.BLEND)
        self.ctx.enable(ModernGL.CULL_FACE)

        self.ctx.screen.use()#rendering the main framebuffer to the screen
        self.ctx.viewport = (0, 0, self.screenX, self.screenY)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        if data_package['fps_counter']==True:
            self.fps_texture.use()#render the fps counter
            self.fps_vao.render()

        self.button_texture.use()#rendering the buttons
        for a in range(len(self.menu_button_list)):
            if data_package['menu_selected'] == a:
                self.button_selected_uniform.value = True
                self.menu_button_list[a].render()
                self.button_selected_uniform.value = False
            else:
                self.menu_button_list[a].render()
        
        pygame.display.flip()#showing the screen
        
    def update(self, data_package):
        if data_package['game_state'] == 'singleplayer' or data_package['game_state'] == 'multiplayer':
            self.render_ingame(data_package)
        elif data_package['game_state'] == 'menus':
            self.render_menus(data_package)
        
    def tick(self, data_package):
        fps_str = str(data_package['fps'])
        self.fps_vao, self.fps_texture = build_text_vao(fps_str, self.font, self.ctx, self.frame_shader, self.screenX-50, self.screenY-15, 30, self.screenX, self.screenY)
    def build_shadow_mvp(self, local_player):
        lookX, lookY, lookZ = normalize(self.directional_light_uniform.value)
        render_distance = local_player.render_distance
        
        #left, right, bottom, top, near, far
        proj = glm.ortho(-(render_distance+2)*16,
                         (render_distance+2)*16,
                         -(render_distance+2)*16,
                         (render_distance+2)*16,
                         -10,
                         (render_distance*2+2)*16)#last one is render distance
        pos = (-lookX*(render_distance+1)*16+local_player.pos[0], 64, local_player.pos[2])
        
        view = glm.lookAt(glm.vec3(pos[0], pos[1], pos[2]),
                          glm.vec3(pos[0]+lookX, pos[1]+lookY, pos[2]+lookZ),
                          glm.vec3(0,1,0))
        return proj * view
        
    def set_MVP_from_model(self, model_matrix):
        mvp = self.projection * self.view * model_matrix
        self.mvp_uniform.value = tuple(np.array(mvp.value).reshape((1,16))[0])
    def set_point_light_pos(self, pos):
        self.point_light_pos.value = pos
    
        
