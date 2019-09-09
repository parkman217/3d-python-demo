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

def BuildShader(ctx):
    prog = ctx.program([
            ctx.vertex_shader('''
                    #version 430

                    in vec4 in_vert;
                    in vec2 in_text;
                    
                    out vec4 v_vert;
                    out vec2 v_text;
                    out vec4 shadow_coord;
                    

                    uniform mat4 MVP;
                    uniform mat4 Depth_MVP;
                    uniform mat4 bias_matrix;

                    
                    void main() {
                        gl_Position = MVP * vec4(in_vert.x, in_vert.y, in_vert.z, 1.0);


                        //mat4 bias_matrix;
                        //bias_matrix[0] = vec4(.5, 0, 0, .5);
                        //bias_matrix[1] = vec4(0, .5, 0, .5);
                        //bias_matrix[2] = vec4(0, 0, .5, .5);
                        //bias_matrix[3] = vec4(0, 0, 0, 1);
                        
                        //bias_matrix[0] = vec4(.5, 0, 0, 0);
                        //bias_matrix[1] = vec4(0, .5, 0, 0);
                        //bias_matrix[2] = vec4(0, 0, .5, 0);
                        //bias_matrix[3] = vec4(.5, .5, .5, 1);
                        
                        shadow_coord = (bias_matrix * Depth_MVP) * vec4(in_vert.x, in_vert.y, in_vert.z, 1.0);
                        //shadow_coord = (Depth_MVP) * vec4(in_vert.x, in_vert.y, in_vert.z, 1.0);

                        v_vert = in_vert;
                        v_text = in_text;
                    }
            '''),
            ctx.fragment_shader('''
                    #version 430

                    in vec4 v_vert;
                    in vec2 v_text;
                    in vec4 shadow_coord;
                    
                    out vec4 color;

                    layout(location = 0) uniform sampler2D Texture;
                    uniform vec3 directional_light;

                    uniform vec3 point_light_pos;
                    uniform vec3 point_light_color;
                    layout(location = 1) uniform sampler2D shadow_map;

                    ivec2 tex_coord;

                    float light_direction;
                    vec3 normal;
                    
                    void main() {
                        light_direction = v_vert.w;//0-6
                        tex_coord = ivec2(int(v_text[0]*32), int(v_text[1]*32));
                        if (light_direction > -0.5 && light_direction < 0.5) {
                            normal = vec3(1, 0, 0);
                        } else if (light_direction > 0.5 && light_direction < 1.5) {
                            normal = vec3(-1, 0, 0);
                        } else if (light_direction > 1.5 && light_direction < 2.5) {
                            normal = vec3(0, 0, 1);
                        } else if (light_direction > 2.5 && light_direction < 3.5) {
                            normal = vec3(0, 0, -1);
                        } else if (light_direction > 3.5 && light_direction < 4.5) {
                            normal = vec3(0, 1, 0);
                        } else if (light_direction > 4.5 && light_direction < 5.5) {
                            normal = vec3(0, -1, 0);
                        } else {
                            vec3 pre_color = (texelFetch(Texture, tex_coord, 0).rgb * 1);
                            color = vec4(pre_color, 0);
                            return;
                        }
                        float light_level = 0.5;//Ambient light level

                        //if (texture(shadow_map, vec2((shadow_coord.x+1)/2, (shadow_coord.y+1)/2)).x < shadow_coord.z) {
                        if (texture(shadow_map, shadow_coord.xy).x > shadow_coord.z-.005) {
                            float directional_light_level = -dot(normal, normalize(directional_light))*0.5;
                            if (directional_light_level < 0){directional_light_level=0;}
                            light_level+=directional_light_level;

                            //color = vec4((texture(shadow_map, vec2((shadow_coord.x+1)/2, (shadow_coord.y+1)/2)).xyz), 1.0)*light_level;
                            //color = vec4((texture(shadow_map, vec2(0.5, 0.4)).xyz), 1.0)*light_level;
                            //return;
                        }
                        
                        float point_light_level = min(1.2, 1/distance(v_vert.xyz, point_light_pos));//linear
                        light_level+=point_light_level;
                        vec3 pre_color = (texelFetch(Texture, tex_coord, 0).rgb * light_level);//(texelFetch(Texture, tex_coord, 0).rgb * light_level);// + (point_light_color*point_light_level);
                        
                        color = vec4(pre_color, 1.0);
                    }
            '''),
    ])
    return prog

def Build_Frame_Shader(ctx):
    prog = ctx.program([
            ctx.vertex_shader('''
                    #version 330

                    in vec2 in_vert;
                    in vec2 in_text;
                    
                    out vec2 v_vert;
                    out vec2 v_text;

                    uniform float z_val;
                    
                    void main() {
                        gl_Position = vec4(in_vert, z_val, 1.0);

                        v_vert = in_vert;
                        v_text = in_text;
                    }
            '''),
            ctx.fragment_shader('''
                    #version 330

                    in vec2 v_vert;
                    in vec2 v_text;
                    
                    out vec4 color;

                    uniform sampler2D Texture;

                    void main() {
                        //vec3 temp_color = texture(Texture, v_text).rgb;
                        //color = vec4(temp_color.x, temp_color.y, temp_color.z, 1);
                        color = texture(Texture, v_text).rgba;
                        //color = vec4(1-temp_color.x, 1-temp_color.y, 1-temp_color.z, 1.0);
                    }
            '''),
    ])
    return prog
        
def Build_Shadow_Shader(ctx):
    prog = ctx.program([
            ctx.vertex_shader('''
                    #version 330 core

                    // Input vertex data, different for all executions of this shader.
                    in vec4 vertexPosition_modelspace;

                    out vec4 pos;

                    // Values that stay constant for the whole mesh.
                    uniform mat4 depthMVP;

                    void main(){
                     gl_Position =  depthMVP * vec4(vertexPosition_modelspace.xyz,1);
                     pos = gl_Position;
                    }
            '''),
            ctx.fragment_shader('''
                    #version 330 core

                    in vec4 pos;
                    
                    // Ouput data
                    
                    //layout(location = 0) out float fragmentdepth;
                    out float fragmentdepth;
                    out vec4 color;

                    void main(){
                        // Not really needed, OpenGL does it anyway
                        //fragmentdepth = gl_FragCoord.z;
                        color = vec4(gl_FragCoord.z, 0, 0, 1.0);
                    }
            '''),
    ])
    return prog
def Build_Button_Shader(ctx):
    prog = ctx.program([
            ctx.vertex_shader('''
                    #version 330

                    in vec2 in_vert;
                    in vec2 in_text;
                    
                    out vec2 v_vert;
                    out vec2 v_text;

                    uniform float z_val;
                    
                    void main() {
                        gl_Position = vec4(in_vert, z_val, 1.0);

                        v_vert = in_vert;
                        v_text = in_text;
                    }
            '''),
            ctx.fragment_shader('''
                    #version 330

                    in vec2 v_vert;
                    in vec2 v_text;
                    
                    out vec4 color;

                    uniform sampler2D Texture;
                    uniform bool selected;

                    void main() {
                        if (selected) {
                            color = texture(Texture, v_text).rgba * 1.75;
                        } else {
                            color = texture(Texture, v_text).rgba;
                        }
                        
                    }
            '''),
    ])
    return prog
