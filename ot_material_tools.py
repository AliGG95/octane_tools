# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Octane Material Tools",
    "author": "Your Name",
    "description": "Tools for converting materials to Octane format",
    "blender": (4, 0, 0),
    "version": (1, 0),
    "location": "Node Editor > Sidebar > Octane Tools",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Material"
}

import bpy
from bpy.props import (StringProperty, CollectionProperty, PointerProperty)
from bpy.types import PropertyGroup
from bpy_extras.io_utils import ImportHelper
from os import path
import random
from mathutils import Vector
from math import degrees

# Import all the module files
from . import ot_material_tools
from . import ot_main_tools
from octane.utils import utility, consts


classes = []

group_solo = {'temp_groupsocket': None, }
solo_mode = {'old_input': None, 'inside_group': False, 'group_socket': None, }

def findfromsocket(inp_tosocket):
    if inp_tosocket.is_linked == False:
        return None
    
    for i in range(len(bpy.context.view_layer.objects.active.active_material.node_tree.links)):
        if (bpy.context.view_layer.objects.active.active_material.node_tree.links[i].to_socket == inp_tosocket):
            return bpy.context.view_layer.objects.active.active_material.node_tree.links[i].from_socket
    #Continue
    
def findtosocket(inp_fromsocket):
    if inp_fromsocket.is_linked == False:
        return None
    
    for i in range(len(bpy.context.view_layer.objects.active.active_material.node_tree.links)):
        if (bpy.context.view_layer.objects.active.active_material.node_tree.links[i].from_socket == inp_fromsocket):
            return bpy.context.view_layer.objects.active.active_material.node_tree.links[i].to_socket
    #Continue  
    
def getlink(inp_tosocket):
    for i in range(len(bpy.context.view_layer.objects.active.active_material.node_tree.links)):
        if (bpy.context.view_layer.objects.active.active_material.node_tree.links[i].to_socket == inp_tosocket):
            return bpy.context.view_layer.objects.active.active_material.node_tree.links[i]
    #Continue 
    
def findsocketname(inp_sockets, inp_name):
    is_found = False
    for socket in inp_sockets:
        if socket.name == inp_name:
            is_found = True
            break
    return is_found

def get_group_interface_node(node_type, node_tree=None, verify_connections=False):
    """
    Enhanced group interface node handler.
    
    Args:
        node_type (str): Type of node ('GROUP_INPUT' or 'GROUP_OUTPUT')
        node_tree: Target node tree
        verify_connections (bool): Verify and return connection info
    
    Returns:
        tuple: (node, existed, connections)
    """
    if node_tree is None:
        try:
            node_tree = bpy.context.active_node.id_data
        except (AttributeError, ReferenceError):
            return None, False, {}

    # Szukamy istniejącego węzła
    existing_node = None
    for node in node_tree.nodes:
        if node.type == node_type:
            existing_node = node
            break

    if existing_node:
        node = existing_node
        existed = True
    else:
        # Poprawka: Prawidłowe nazwy typów węzłów
        type_mapping = {
            'GROUP_INPUT': 'NodeGroupInput',
            'GROUP_OUTPUT': 'NodeGroupOutput'
        }
        
        locations = {'GROUP_INPUT': (-500, 0), 'GROUP_OUTPUT': (500, 0)}
        
        try:
            node = node_tree.nodes.new(type=type_mapping[node_type])
            node.location = locations[node_type]
            existed = False
        except Exception as e:
            print(f"Error creating node: {str(e)}")
            return None, False, {}

    # Reszta funkcji pozostaje bez zmian...
    connections = {}
    if verify_connections and node:
        if node_type == 'GROUP_INPUT':
            for output in node.outputs:
                links_data = []
                for link in output.links:
                    links_data.append({
                        'to_node': link.to_node.name,
                        'to_socket': link.to_socket.name,
                        'socket_type': link.to_socket.type
                    })
                if links_data:
                    connections[output.name] = {
                        'links': links_data,
                        'type': output.type
                    }
        else:  # GROUP_OUTPUT
            for input in node.inputs:
                links_data = []
                for link in input.links:
                    links_data.append({
                        'from_node': link.from_node.name,
                        'from_socket': link.from_socket.name,
                        'socket_type': link.from_socket.type
                    })
                if links_data:
                    connections[input.name] = {
                        'links': links_data,
                        'type': input.type
                    }

    return node, existed, connections

def rgba2rgb(inp_rgba):
    return (inp_rgba[0], inp_rgba[1], inp_rgba[2])

def float2rgb(inp_float):
    return (inp_rgba[inp_float], inp_rgba[inp_float], inp_rgba[inp_float])




#RANGE
def convert_map_range(inp_node):
    oct_range_node = bpy.context.material.node_tree.nodes.new(type='OctaneOperatorRange')
    oct_range_node.name = 'OCT_' + inp_node.name
    
    # Mapowanie typów interpolacji z Cycles na Octane
    interpolation_map = {
        'LINEAR': 'Linear',
        'STEPPED': 'Steps',
        'SMOOTH': 'Smoothstep',
        'SMOOTHSTEP': 'Smoothstep',
        'SMOOTHERSTEP': 'Smootherstep'
    }
    
    # Ustawienie wartości domyślnych tylko jeśli socket nie jest podłączony
    if not inp_node.inputs['Value'].is_linked:
        oct_range_node.inputs['Value'].default_value = inp_node.inputs['Value'].default_value
    if not inp_node.inputs['From Min'].is_linked:
        oct_range_node.inputs['Input min'].default_value = inp_node.inputs['From Min'].default_value
    if not inp_node.inputs['From Max'].is_linked:
        oct_range_node.inputs['Input max'].default_value = inp_node.inputs['From Max'].default_value
    if not inp_node.inputs['To Min'].is_linked:
        oct_range_node.inputs['Output min'].default_value = inp_node.inputs['To Min'].default_value
    if not inp_node.inputs['To Max'].is_linked:
        oct_range_node.inputs['Output max'].default_value = inp_node.inputs['To Max'].default_value
    
    # Ustawienie typu interpolacji
    if hasattr(inp_node, "interpolation_type"):
        if inp_node.interpolation_type in interpolation_map:
            oct_range_node.inputs['Interpolation'].default_value = interpolation_map[inp_node.interpolation_type]
    
    # Ustawienie ilości kroków dla trybu stepped
    if hasattr(inp_node, "steps"):
        oct_range_node.inputs['Levels'].default_value = inp_node.steps
    
    # Ustawienie clamp
    if hasattr(inp_node, "clamp"):
        oct_range_node.inputs['Clamp'].default_value = inp_node.clamp
        
    oct_range_node.parent = inp_node.parent
    oct_range_node.location = inp_node.location
    
    return True



#VECTOR MATH
def convert_vector_math(inp_node):
    oct_vector_math_node = bpy.context.material.node_tree.nodes.new(type='OctaneCyclesNodeVectorMathNodeWrapper')
    oct_vector_math_node.name = 'OCT_' + inp_node.name
    
    # Mapowanie operacji z Cycles na Octane
    operation_map = {
        'ADD': 'Add',
        'SUBTRACT': 'Subtract',
        'MULTIPLY': 'Multiply',
        'DIVIDE': 'Divide',
        'MULTIPLY_ADD': 'Multiply Add',
        'CROSS_PRODUCT': 'Cross Product',
        'PROJECT': 'Project',
        'REFLECT': 'Reflect',
        'REFRACT': 'Refract',
        'FACEFORWARD': 'Faceforward',
        'DOT_PRODUCT': 'Dot Product', 
        'DISTANCE': 'Distance',
        'LENGTH': 'Length',
        'SCALE': 'Scale',
        'NORMALIZE': 'Normalize',
        'ABSOLUTE': 'Absolute',
        'MINIMUM': 'Minimum',
        'MAXIMUM': 'Maximum',
        'FLOOR': 'Floor',
        'CEIL': 'Ceil',
        'FRACTION': 'Fraction',
        'MODULO': 'Modulo',
        'WRAP': 'Wrap',
        'SNAP': 'Snap',
        'SINE': 'Sine',
        'COSINE': 'Cosine',
        'TANGENT': 'Tangent'
    }

    # Ustawienie typu operacji
    if inp_node.operation in operation_map:
        oct_vector_math_node.inputs[0].default_value = operation_map[inp_node.operation]

    # Kopiowanie wartości domyślnych wektorów wejściowych
    input_mapping = {
        'Vector': 1,
        'Vector_001': 2,
        'Vector_002': 3,
        'Scale': 4
    }

    for input_name, socket_index in input_mapping.items():
        if input_name in inp_node.inputs and not inp_node.inputs[input_name].is_linked:
            if hasattr(inp_node.inputs[input_name], 'default_value'):
                oct_vector_math_node.inputs[socket_index].default_value = inp_node.inputs[input_name].default_value

    # Zachowanie lokalizacji i rodzica
    oct_vector_math_node.parent = inp_node.parent
    oct_vector_math_node.location = inp_node.location

    return True



#Math Node
def convert_math(inp_node):
    oct_mathnode = bpy.context.material.node_tree.nodes.new(type='OctaneCyclesNodeMathNodeWrapper')
    oct_mathnode.name = 'OCT_' + inp_node.name
    
    # Convert operation type using the converter dictionary from node_math.py
    operation_map = {
        "ADD": "Add",
        "SUBTRACT": "Subtract", 
        "MULTIPLY": "Multiply",
        "DIVIDE": "Divide",
        "MULTIPLY_ADD": "Multiply Add",
        "POWER": "Power",
        "LOGARITHM": "Logarithm",
        "SQRT": "Square Root",
        "INV_SQRT": "Inverse Square Root",
        "ABSOLUTE": "Absolute",
        "EXPONENT": "Exponent",
        "MINIMUM": "Minimum", 
        "MAXIMUM": "Maximum",
        "LESS_THAN": "Less Than",
        "GREATER_THAN": "Greater Than",
        "SIGN": "Sign",
        "COMPARE": "Compare",
        "SMOOTH_MIN": "Smooth min",
        "SMOOTH_MAX": "Smooth max",
        "ROUND": "Round",
        "FLOOR": "Floor", 
        "CEIL": "Ceil",
        "TRUNC": "Truncate",
        "FRACT": "Fraction",
        "MODULO": "Truncated Modulo",
        "FLOORED_MODULO": "Floored Modulo",
        "WRAP": "Wrap",
        "SNAP": "Snap",
        "PINGPONG": "Pingpong",
        "SINE": "Sine",
        "COSINE": "Cosine", 
        "TANGENT": "Tangent",
        "ARCSINE": "Arcsine",
        "ARCCOSINE": "Arccosine",
        "ARCTANGENT": "Arctangent", 
        "ARCTAN2": "Arctan2",
        "SINH": "Hyperbolic Sine",
        "COSH": "Hyperbolic Cosine",
        "TANH": "Hyperbolic Tangent",
        "RADIANS": "Radians",
        "DEGREES": "Degrees"
    }

    # Set the operation type
    if inp_node.operation in operation_map:
        oct_mathnode.inputs[0].default_value = operation_map[inp_node.operation]
    
    # Handle inputs
    # Value1 input
    if inp_node.inputs[0].is_linked:
        pass  # Links will be handled by relink_nodes()
    else:
        oct_mathnode.inputs[3].default_value = inp_node.inputs[0].default_value
        
    # Value2 input
    if inp_node.inputs[1].is_linked:
        pass  # Links will be handled by relink_nodes()
    else:
        oct_mathnode.inputs[4].default_value = inp_node.inputs[1].default_value
        
    # Value3 input (for operations that use it like Multiply Add)
    if len(inp_node.inputs) > 2:
        if inp_node.inputs[2].is_linked:
            pass  # Links will be handled by relink_nodes()
        else:
            oct_mathnode.inputs[5].default_value = inp_node.inputs[2].default_value

    # Set clamp if available in the original node
    if hasattr(inp_node, "use_clamp"):
        oct_mathnode.inputs[1].default_value = 1 if inp_node.use_clamp else 0
        oct_mathnode.inputs[2].default_value = inp_node.use_clamp

    # Copy node location and other common properties
    oct_mathnode.parent = inp_node.parent
    oct_mathnode.location = inp_node.location

    return True

#PRINCIPLED BSDF TO UM
def convert_principledbsdf2um(inp_node):
    
    list_inputs = (('Base Color', 'Albedo', 'COLOR'), ('Metallic', 'Metallic', 'FLOAT'), ('Roughness', 'Roughness', 'FLOAT'), ('IOR', 'Dielectric IOR', 'FLOAT'), ('Alpha', 'Opacity', 'FLOAT'), 
    ('Specular Anisotropy', 'Anisotropy', 'FLOAT'), ('Anisotropic Rotation', 'Rotation', 'FLOAT'), ('Coat Weight', 'Coating', 'FLOAT2COLOR'), ('Coat Roughness', 'Coating roughness', 'FLOAT'), ('Coat IOR', 'Coating IOR', 'FLOAT'), 
    ('Sheen Weight', 'Sheen', 'FLOAT2COLOR'), ('Sheen Roughness', 'Sheen roughness', 'FLOAT'), )
    
    oct_um_node = bpy.context.material.node_tree.nodes.new(type='OctaneUniversalMaterial', )
    oct_um_node.name = 'OCT_' + inp_node.name
    
    for inp in list_inputs:
        try:
            if inp[2] == 'FLOAT' or inp[2] == 'VECTOR':
                oct_um_node.inputs[inp[1]].default_value = inp_node.inputs[inp[0]].default_value   
            elif inp[2] == 'COLOR':
                 oct_um_node.inputs[inp[1]].default_value = rgba2rgb(inp_node.inputs[inp[0]].default_value)
            elif inp[2] == 'FLOAT2COLOR':
                    oct_um_node.inputs[inp[1]].default_value = float2rgb(inp_node.inputs[inp[0]].default_value)  
        except:
            pass
                
    oct_um_node.parent = inp_node.parent        
    oct_um_node.location = inp_node.location
    oct_um_node.inputs['BSDF model'].default_value = 'GGX (energy preserving)'
    oct_um_node.inputs['[OctaneGroupTitle]Transmission Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Base Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Specular Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Roughness'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]IOR'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Coating Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Thin Film Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Sheen Layer'].show_group_sockets = False
    oct_um_node.inputs['[OctaneGroupTitle]Transmission Properties'].show_group_sockets = False
    
    #oct_um_node.inputs['[OctaneGroupTitle]Geometry Properties'].show_group_sockets = False
    
    return True

#PRINCIPLED BSDF TO SSM
def convert_principledbsdf2ssm(inp_node):
    
    list_inputs = (('Base Color', 'Base color', 'COLOR'), ('Metallic', 'Metalness', 'FLOAT'), ('Roughness', 'Specular roughness', 'FLOAT'), ('IOR', 'Specular IOR', 'FLOAT'), ('Alpha', 'Opacity', 'FLOAT'), ('Subsurface Weight', 'Subsurface weight', 'FLOAT'), 
    ('Subsurface Radius', 'Subsurface radius', 'VECTOR'), ('Subsurface Scale', 'Subsurface scale', 'FLOAT'), ('Subsurface Anisotropy', 'Subsurface anisotropy', 'FLOAT'), ('Specular IOR Level', 'Specular weight', 'MISC'), ('Specular Tint', 'Specular color', 'COLOR'), ('Specular Anisotropy', 'Specular anisotropy', 'FLOAT'), 
    ('Anisotropic Rotation', 'Specular rotation', 'FLOAT'), ('Transmission Weight', 'Transmission weight', 'FLOAT'), ('Coat Weight', 'Coating weight', 'FLOAT'), ('Coat Roughness', 'Coating roughness', 'FLOAT'), ('Coat IOR', 'Coating IOR', 'FLOAT'), 
    ('Coat Tint', 'Coating color', 'COLOR'), ('Sheen Weight', 'Sheen weight', 'FLOAT'), ('Sheen Roughness', 'Sheen roughness', 'FLOAT'), ('Sheen Tint', 'Sheen color', 'COLOR'), ('Emission Color', 'Emission color', 'COLOR'), ('Emission Strength', 'Emission weight', 'FLOAT'), )
    
    oct_ssm_node = bpy.context.material.node_tree.nodes.new(type='OctaneStandardSurfaceMaterial', )
    oct_ssm_node.name = 'OCT_' + inp_node.name
    
    for inp in list_inputs:
        try:
            if inp[2] == 'FLOAT' or inp[2] == 'VECTOR':
                oct_ssm_node.inputs[inp[1]].default_value = inp_node.inputs[inp[0]].default_value   
            elif inp[2] == 'COLOR':
                 oct_ssm_node.inputs[inp[1]].default_value = rgba2rgb(inp_node.inputs[inp[0]].default_value)
            else:
                if inp[0] == 'Specular IOR Level':
                    oct_ssm_node.inputs[inp[1]].default_value = inp_node.inputs[inp[0]].default_value * 2  
        except:
            pass
                
    oct_ssm_node.parent = inp_node.parent        
    oct_ssm_node.location = inp_node.location
    oct_ssm_node.inputs['Base weight'].default_value = 1
    oct_ssm_node.inputs['[OctaneGroupTitle]Base Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Specular Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Transmission Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Subsurface'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Medium'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Coating Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Sheen Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Emission Layer'].show_group_sockets = False
    oct_ssm_node.inputs['[OctaneGroupTitle]Thin Film Layer'].show_group_sockets = False
    
    return True

#RGB Color
def convert_rgb_color(inp_node):
    oct_rgb_color_node = bpy.context.material.node_tree.nodes.new(type='OctaneRGBColor')
    oct_rgb_color_node.name = 'OCT_' + inp_node.name
    
    oct_rgb_color_node.a_value = inp_node.outputs[0].default_value[:3]
    
    oct_rgb_color_node.parent = inp_node.parent
    oct_rgb_color_node.location = inp_node.location
    
    return True
    
# IMAGE TEXTURE    
def convert_imagetexture(inp_node):
    oct_rgbimage_node = bpy.context.material.node_tree.nodes.new(type='OctaneRGBImage', )
    oct_rgbimage_node.name = 'OCT_' + inp_node.name
    oct_rgbimage_node.image = inp_node.image
    try:
        if (inp_node.image.colorspace_settings.name == 'Non-Color'):
            oct_rgbimage_node.inputs['Legacy gamma'].default_value = 1.0
    except:
        pass
    oct_rgbimage_node.parent = inp_node.parent
    oct_rgbimage_node.location = inp_node.location
    
    return True   
    
# DISPLACEMENT
def convert_displacement(inp_node):
    oct_texdisplacement_node = bpy.context.material.node_tree.nodes.new(type='OctaneTextureDisplacement', )
    oct_texdisplacement_node.name = 'OCT_' + inp_node.name
    oct_texdisplacement_node.inputs['Mid level'].default_value = inp_node.inputs['Midlevel'].default_value
    oct_texdisplacement_node.inputs['Height'].default_value = inp_node.inputs['Scale'].default_value
    oct_texdisplacement_node.parent = inp_node.parent
    oct_texdisplacement_node.location = inp_node.location
    
    return True

# VECTOR DISPLACEMENT
def convert_vectordisplacement(inp_node):
    oct_vectordisplacement_node = bpy.context.material.node_tree.nodes.new(type='OctaneTextureDisplacement', )
    oct_vectordisplacement_node.name = 'OCT_' + inp_node.name
    oct_vectordisplacement_node.inputs['Mid level'].default_value = inp_node.inputs['Midlevel'].default_value
    oct_vectordisplacement_node.inputs['Height'].default_value = inp_node.inputs['Scale'].default_value
    oct_vectordisplacement_node.parent = inp_node.parent
    oct_vectordisplacement_node.location = inp_node.location
    
    return True
    
# HSV
def convert_hsv(inp_node):
    oct_colorcorrection_node = bpy.context.material.node_tree.nodes.new(type='OctaneColorCorrection', )
    oct_colorcorrection_node.name = 'OCT_' + inp_node.name
    oct_colorcorrection_node.inputs['Hue'].default_value = inp_node.inputs['Hue'].default_value * 2 - 1
    oct_colorcorrection_node.inputs['Saturation'].default_value = inp_node.inputs['Saturation'].default_value * 100
    oct_colorcorrection_node.inputs['Mask'].default_value = inp_node.inputs['Fac'].default_value
    oct_colorcorrection_node.parent = inp_node.parent
    oct_colorcorrection_node.location = inp_node.location
    
    return True
    
# BRIGHTNESS/CONTRAST
def convert_brightcontrast(inp_node):
    oct_colorcorrection_node = bpy.context.material.node_tree.nodes.new(type='OctaneColorCorrection', )
    oct_colorcorrection_node.name = 'OCT_' + inp_node.name
    oct_colorcorrection_node.inputs['Brightness'].default_value = abs(inp_node.inputs['Bright'].default_value)
    oct_colorcorrection_node.inputs['Contrast'].default_value = inp_node.inputs['Contrast'].default_value
    oct_colorcorrection_node.parent = inp_node.parent
    oct_colorcorrection_node.location = inp_node.location 
    
    return True

# MAPPING
def convert_mapping(inp_node):
    oct_mapping_node = bpy.context.material.node_tree.nodes.new(type='Octane3DTransformation', )
    oct_mapping_node.name = 'OCT_' + inp_node.name
    oct_mapping_node.inputs['Rotation'].default_value[0] = degrees(inp_node.inputs['Rotation'].default_value[0])
    oct_mapping_node.inputs['Rotation'].default_value[1] = degrees(inp_node.inputs['Rotation'].default_value[1])
    oct_mapping_node.inputs['Rotation'].default_value[2] = degrees(inp_node.inputs['Rotation'].default_value[2])
    
    oct_mapping_node.inputs['Scale'].default_value[0] = 1 / inp_node.inputs['Scale'].default_value[0] if inp_node.inputs['Scale'].default_value[0] != 0 else 1
    oct_mapping_node.inputs['Scale'].default_value[1] = 1 / inp_node.inputs['Scale'].default_value[1] if inp_node.inputs['Scale'].default_value[1] != 0 else 1
    oct_mapping_node.inputs['Scale'].default_value[2] = 1 / inp_node.inputs['Scale'].default_value[2] if inp_node.inputs['Scale'].default_value[2] != 0 else 1
    
    oct_mapping_node.inputs['Translation'].default_value[0] = inp_node.inputs['Location'].default_value[0]
    oct_mapping_node.inputs['Translation'].default_value[1] = inp_node.inputs['Location'].default_value[1]
    oct_mapping_node.inputs['Translation'].default_value[2] = inp_node.inputs['Location'].default_value[2] 
    
    oct_mapping_node.parent = inp_node.parent
    oct_mapping_node.location = inp_node.location
    
    return True

# COLOR RAMP
def convert_colorramp(inp_node):
    oct_gradientmap_node = bpy.context.material.node_tree.nodes.new(type='OctaneGradientMap', )
    oct_gradientmap_node.name = 'OCT_' + inp_node.name
    
    temp_node = utility.get_octane_helper_node(oct_gradientmap_node.name)
    if temp_node == None:
        oct_gradientmap_node.init_color_ramp_helper_node()
        oct_gradientmap_node.loads_color_ramp_data()
        oct_gradientmap_node.update_value_sockets()
        oct_gradientmap_node.dumps_color_ramp_data()
        
    new_color_ramp = utility.get_octane_helper_node(oct_gradientmap_node.color_ramp_name).color_ramp
    
    for i in range(len(inp_node.color_ramp.elements)):
        if i <= len(new_color_ramp.elements) - 1:
            new_color_ramp.elements[i].color = inp_node.color_ramp.elements[i].color
            new_color_ramp.elements[i].position = inp_node.color_ramp.elements[i].position
            pass
        else:
           new_element = new_color_ramp.elements.new(inp_node.color_ramp.elements[i].position)
           new_element.color = inp_node.color_ramp.elements[i].color
    
    oct_gradientmap_node.parent = inp_node.parent
    oct_gradientmap_node.location = inp_node.location 
    
    return True

# INVERT COLOR
def convert_invertcolor(inp_node):
    oct_inverttexture_node = bpy.context.material.node_tree.nodes.new(type='OctaneInvertTexture', )
    oct_inverttexture_node.name = 'OCT_' + inp_node.name
    oct_inverttexture_node.parent = inp_node.parent
    oct_inverttexture_node.location = inp_node.location 
    
    return True

# VORONOI
def convert_voronoi(inp_node):
    oct_voronoi_node = bpy.context.material.node_tree.nodes.new(type='OctaneNoiseTexture', )
    oct_voronoi_node.name = 'OCT_' + inp_node.name
    oct_voronoi_node.inputs[1].default_value = 'Voronoi'
    oct_voronoi_node.inputs['Octaves'].default_value = int(inp_node.inputs['Detail'].default_value)
    oct_voronoi_node.parent = inp_node.parent
    oct_voronoi_node.location = inp_node.location 
    
    return True

# NOISE
def convert_noise(inp_node):
    oct_noise_node = bpy.context.material.node_tree.nodes.new(type='OctaneNoiseTexture', )
    oct_noise_node.name = 'OCT_' + inp_node.name
    oct_noise_node.inputs['Octaves'].default_value = int(inp_node.inputs['Detail'].default_value)
    oct_noise_node.parent = inp_node.parent
    oct_noise_node.location = inp_node.location 
    
    return True

# MIX SHADER
def convert_mixshader(inp_node):
    oct_mixmaterial_node = bpy.context.material.node_tree.nodes.new(type='OctaneMixMaterial', )
    oct_mixmaterial_node.name = 'OCT_' + inp_node.name
    oct_mixmaterial_node.inputs['Amount'].default_value = inp_node.inputs['Fac'].default_value
    oct_mixmaterial_node.parent = inp_node.parent
    oct_mixmaterial_node.location = inp_node.location 
    
    return True

# TRANSPARENT BSDF
def convert_transparentbsdf(inp_node):
    oct_specularmaterial_node = bpy.context.material.node_tree.nodes.new(type='OctaneSpecularMaterial', )
    oct_specularmaterial_node.name = 'OCT_' + inp_node.name
    oct_specularmaterial_node.inputs['Transmission'].default_value = rgba2rgb(inp_node.inputs['Color'].default_value)
    oct_specularmaterial_node.inputs['Index of refraction'].default_value = 1
    oct_specularmaterial_node.inputs['[OctaneGroupTitle]Roughness'].show_group_sockets = False
    oct_specularmaterial_node.inputs['[OctaneGroupTitle]IOR'].show_group_sockets = False
    oct_specularmaterial_node.inputs['[OctaneGroupTitle]Thin Film Layer'].show_group_sockets = False
    oct_specularmaterial_node.inputs['[OctaneGroupTitle]Transmission Properties'].show_group_sockets = False
    oct_specularmaterial_node.parent = inp_node.parent
    oct_specularmaterial_node.location = inp_node.location 
    
    return True
    
# OUTPUT MATERIAL
def convert_outputmaterial(inp_node):
    oct_outputmaterial_node = bpy.context.material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    oct_outputmaterial_node.name = 'OCT_' + inp_node.name
    
    # Sprawdzamy dostępność opcji "octane" w enumie target
    try:
        if 'octane' in oct_outputmaterial_node.bl_rna.properties['target'].enum_items:
            oct_outputmaterial_node.target = 'octane'
        else:
            oct_outputmaterial_node.target = 'ALL'
            print("Warning: 'octane' target not available for output node. Using 'ALL' instead.")
    except Exception as e:
        oct_outputmaterial_node.target = 'ALL'
        print(f"Warning: Error checking 'octane' target availability. Using 'ALL' instead. Error: {str(e)}")
    
    oct_outputmaterial_node.parent = inp_node.parent
    oct_outputmaterial_node.location = inp_node.location 
    
    return True




# Octane Mix Wrapper
def convert_mix_color(inp_node):
    oct_mix_node = bpy.context.material.node_tree.nodes.new(type='OctaneCyclesMixColorNodeWrapper')
    oct_mix_node.name = 'OCT_' + inp_node.name
    
    # Mapowanie typów mieszania z Cycles na Octane
    blend_type_map = {
        'MIX': 'Mix',
        'DARKEN': 'Darken',
        'MULTIPLY': 'Multiply', 
        'BURN': 'Burn',
        'LIGHTEN': 'Lighten',
        'SCREEN': 'Screen',
        'DODGE': 'Dodge',
        'ADD': 'Add',
        'OVERLAY': 'Overlay',
        'SOFT_LIGHT': 'Soft Light',
        'LINEAR_LIGHT': 'Linear Light',
        'DIFFERENCE': 'Difference',
        'EXCLUSION': 'Exclusion',
        'SUBTRACT': 'Subtract',
        'DIVIDE': 'Divide',
        'HUE': 'Hue',
        'SATURATION': 'Saturation',
        'COLOR': 'Color',
        'VALUE': 'Value'
    }

    # Ustaw typ mieszania
    if inp_node.blend_type in blend_type_map:
        oct_mix_node.inputs[0].default_value = blend_type_map[inp_node.blend_type]

    # Ustaw wartości domyślne dla Factor
    if inp_node.inputs[0].is_linked == False:  # Factor/Fac input
        oct_mix_node.inputs['Factor'].default_value = inp_node.inputs[0].default_value
    
    # Ustaw domyślne wartości dla Clamp - w nowym nodzie Mix nie ma tych opcji,
    # więc ustawiamy na False
    oct_mix_node.inputs['Clamp Factor'].default_value = True
    oct_mix_node.inputs['Clamp Result'].default_value = False

    # Ustaw wartości domyślne dla kolorów wejściowych jeśli nie są podłączone
    if not inp_node.inputs[6].is_linked:  # Color1
        oct_mix_node.inputs['A'].default_value = inp_node.inputs[6].default_value[:3]
    if not inp_node.inputs[7].is_linked:  # Color2
        oct_mix_node.inputs['B'].default_value = inp_node.inputs[7].default_value[:3]

    # Skopiuj położenie i rodzica
    oct_mix_node.parent = inp_node.parent
    oct_mix_node.location = inp_node.location

    return True




    
# MIX TEXTURE TO COMPOSITE NODE
def convert_mixtexture2comptexture(inp_node):
    
    blendmodes = {'MIX' : 'Mix|Normal', 'DARKEN' : 'Photometric|Darken', 'MULTIPLY' : 'Blend|Multiply', 'BURN' : 'Photometric|Color burn', 
    'LIGHTEN' : 'Photometric|Lighten', 'SCREEN' : 'Photometric|Screen', 'DODGE' : 'Photometric|Color dodge', 'ADD' : 'Blend|Add',
    'OVERLAY' : 'Translucent|Overlay', 'SOFT_LIGHT' : 'Translucent|Soft light', 'LINEAR_LIGHT' : 'Translucent|Linear light', 'DIFFERENCE' : 'Arithmetic|Difference', 
    'EXCLUSION' : 'Arithmetic|Exclusion', 'SUBTRACT' : 'Arithmetic|Subtract', 'DIVIDE' : 'Arithmetic|Divide', 'HUE' : 'Spectral|Hue', 'SATURATION' : 'Spectral|Saturation', 
    'COLOR' : 'Spectral|Color', 'VALUE' : 'Spectral|Value'}
    
    ctgroup_exists = False
    for group in bpy.data.node_groups:
        if group.name == ".OCT_COMPTEXGROUP" + inp_node.blend_type:
            ctgroup_exists = True
            break
        
    if ctgroup_exists == False:
        comptex_group = bpy.data.node_groups.new(".OCT_COMPTEXGROUP" + inp_node.blend_type, type='ShaderNodeTree')
        nodes = comptex_group.nodes
        links = comptex_group.links

        input_node = nodes.new(type='NodeGroupInput')
        input_node.location = (-500,0)
        output_node = nodes.new(type='NodeGroupOutput')
        output_node.location = (250,0)

        comptex_node = nodes.new(type='OctaneCompositeTexture')
        comptex_node.inputs[0].default_value = False #CLAMP
        comptexlayer1_node = nodes.new(type='OctaneTexLayerTexture')
        comptexlayer1_node.location = (-250,-100)
        comptexlayer2_node = nodes.new(type='OctaneTexLayerTexture')
        comptexlayer2_node.location = (-250,100)
        
        links.new(comptexlayer2_node.outputs[0], comptex_node.inputs[2])
        links.new(comptexlayer1_node.outputs[0], comptex_node.inputs[3])

        Input_1 = comptex_group.interface.new_socket(name='Opacity', in_out='INPUT', socket_type='NodeSocketFloat')
        Input_2 = comptex_group.interface.new_socket(name='Top Layer', in_out='INPUT', socket_type='NodeSocketColor')
        Input_3 = comptex_group.interface.new_socket(name='Base Layer', in_out='INPUT', socket_type='NodeSocketColor')
        Output_1 = comptex_group.interface.new_socket(name='Texture Out', in_out='OUTPUT', )

        links.new(input_node.outputs[0], comptexlayer2_node.inputs[2])
        links.new(input_node.outputs[1], comptexlayer2_node.inputs[1])
        links.new(input_node.outputs[2], comptexlayer1_node.inputs[1])
        links.new(output_node.inputs[0], comptex_node.outputs[0])
        
    oct_comptex_node = bpy.context.material.node_tree.nodes.new('ShaderNodeGroup')
    oct_comptex_node.node_tree = bpy.data.node_groups[".OCT_COMPTEXGROUP" + inp_node.blend_type].copy()
    oct_comptex_node.name = '.OCT_' + inp_node.name
    oct_comptex_node.label = oct_comptex_node.name
    oct_comptex_node.inputs[0].default_value = inp_node.inputs[0].default_value
    oct_comptex_node.inputs[1].default_value = inp_node.inputs[7].default_value
    oct_comptex_node.inputs[2].default_value = inp_node.inputs[6].default_value
    oct_comptex_node.node_tree.nodes[4].inputs[3].default_value = blendmodes[inp_node.blend_type]
    oct_comptex_node.parent = inp_node.parent
    oct_comptex_node.location = inp_node.location
    
    return True

def is_node_group(node):
    """
    Checks if the node is a group node that can be converted.
    
    Args:
        node: Node to check
        
    Returns:
        bool: True if node is a convertible group node
    """
    return (node.type == 'GROUP' and 
            node.node_tree is not None and 
            not node.node_tree.is_embedded_data)
            
            
            
def reconnect_external_group_connections(node_group_node, new_group):
    """
    Reconnects external connections for a converted node group.
    
    Args:
        node_group_node: The node group instance in the material
        new_group: The newly converted Octane node group
    """
    def map_socket_name(socket_name, is_output=False):
        """Maps Cycles socket names to their Octane equivalents"""
        if is_output:
            # Mapping dla output socketów
            output_mapping = {
                'BSDF': 'Material out',
                'Shader': 'Material out',
                'Color': 'Color',
                'Value': 'Value',
                'Vector': 'Vector'
            }
            return output_mapping.get(socket_name, socket_name)
        else:
            # Mapping dla input socketów
            input_mapping = {
                'BSDF': 'Material',
                'Shader': 'Material',
                'Color': 'Color',
                'Value': 'Value',
                'Vector': 'Vector'
            }
            return input_mapping.get(socket_name, socket_name)

    # Pobierz node tree, w którym znajduje się node group
    parent_tree = node_group_node.id_data

    # Zachowaj wszystkie istniejące połączenia
    input_connections = []
    output_connections = []

    # Zbierz połączenia wejściowe
    for input in node_group_node.inputs:
        if input.is_linked:
            for link in input.links:
                input_connections.append({
                    'from_socket': link.from_socket,
                    'to_socket_name': input.name,
                    'to_socket_type': input.type
                })

    # Zbierz połączenia wyjściowe
    for output in node_group_node.outputs:
        if output.is_linked:
            for link in output.links:
                output_connections.append({
                    'to_socket': link.to_socket,
                    'from_socket_name': output.name,
                    'from_socket_type': output.type
                })

    # Zamień grupę na nową
    node_group_node.node_tree = new_group

    # Odtwórz połączenia wejściowe
    for conn in input_connections:
        try:
            mapped_name = map_socket_name(conn['to_socket_name'])
            if mapped_name in node_group_node.inputs:
                parent_tree.links.new(
                    conn['from_socket'],
                    node_group_node.inputs[mapped_name]
                )
        except Exception as e:
            print(f"Error reconnecting input {conn['to_socket_name']}: {str(e)}")

    # Odtwórz połączenia wyjściowe
    for conn in output_connections:
        try:
            mapped_name = map_socket_name(conn['from_socket_name'], is_output=True)
            if mapped_name in node_group_node.outputs:
                parent_tree.links.new(
                    node_group_node.outputs[mapped_name],
                    conn['to_socket']
                )
        except Exception as e:
            print(f"Error reconnecting output {conn['from_socket_name']}: {str(e)}")

    return True


def convert_node_group(context, node_group):
    """
    Converts Cycles node group to Octane equivalent.
    Creates new node group with converted nodes maintaining original connections.
    """
    # Sprawdzenie czy grupa istnieje i ma węzły
    if not node_group or not node_group.nodes:
        return False
        
    # Helper function dla mapowania nazw socketów
    def map_socket_name(from_socket_name, to_node_type):
        # Mapowanie dla Vector -> UV transform
        if from_socket_name.lower() in ['vector', 'uv', 'uv_map']:
            if to_node_type == 'OctaneRGBImage':
                return 'UV transform'
        
        # Mapowanie dla Universal Material
        if to_node_type == 'OctaneUniversalMaterial':
            socket_mapping = {
                'Base Color': 'Albedo',
                'Metallic': 'Metallic',
                'Roughness': 'Roughness',
                'IOR': 'Dielectric IOR',
                'Alpha': 'Opacity',
                'Normal': 'Normal',
                'Specular Anisotropy': 'Anisotropy',
                'Anisotropic Rotation': 'Rotation',
                'Transmission Weight': 'Transmission',
                'Coat Weight': 'Coating',
                'Coat Roughness': 'Coating roughness',
                'Coat IOR': 'Coating IOR',
                'Coat Normal': 'Coating normal',
                'Sheen Weight': 'Sheen',
                'Sheen Roughness': 'Sheen roughness',
                'Emission Color': 'Emission'
            }
            return socket_mapping.get(from_socket_name, from_socket_name)

        # Mapowanie dla Standard Surface Material
        if to_node_type == 'OctaneStandardSurfaceMaterial':
            socket_mapping = {
                'Base Color': 'Base color',
                'Metallic': 'Metalness',
                'Roughness': 'Specular roughness',
                'IOR': 'Specular IOR',
                'Alpha': 'Opacity',
                'Normal': 'Normal',
                'Subsurface Weight': 'Subsurface weight',
                'Subsurface Radius': 'Subsurface radius',
                'Subsurface Scale': 'Subsurface scale',
                'Subsurface Anisotropy': 'Subsurface anisotropy',
                'Specular IOR Level': 'Specular weight',
                'Specular Tint': 'Specular color',
                'Specular Anisotropy': 'Specular anisotropy',
                'Anisotropic Rotation': 'Specular rotation',
                'Transmission Weight': 'Transmission weight',
                'Coat Weight': 'Coating weight',
                'Coat Roughness': 'Coating roughness',
                'Coat IOR': 'Coating IOR',
                'Coat Tint': 'Coating color',
                'Coat Normal': 'Coating normal',
                'Sheen Weight': 'Sheen weight',
                'Sheen Roughness': 'Sheen roughness',
                'Sheen Tint': 'Sheen color',
                'Emission Color': 'Emission color',
                'Emission Strength': 'Emission weight'
            }
            return socket_mapping.get(from_socket_name, from_socket_name)
            
        return from_socket_name

    # Znajdź najwyższy istniejący numer OCT_GROUP
    highest_num = 0
    for group in bpy.data.node_groups:
        if group.name.startswith("OCT_GROUP."):
            try:
                num = int(group.name.split(".")[-1])
                highest_num = max(highest_num, num)
            except:
                pass
    
    # Utwórz nową grupę
    new_group_name = f"OCT_GROUP.{highest_num + 1:03d}"
    oct_group = bpy.data.node_groups.new(new_group_name, type='ShaderNodeTree')

    # Pobierz informacje o oryginalnych połączeniach
    orig_input_node, _, input_connections = get_group_interface_node('GROUP_INPUT', 
                                                                   node_group, 
                                                                   verify_connections=True)
    orig_output_node, _, output_connections = get_group_interface_node('GROUP_OUTPUT', 
                                                                     node_group, 
                                                                     verify_connections=True)

    # Utwórz węzły interfejsu w nowej grupie
    new_input_node, _, _ = get_group_interface_node('GROUP_INPUT', oct_group)
    new_output_node, _, _ = get_group_interface_node('GROUP_OUTPUT', oct_group)

    # Zachowaj oryginalne sockety interfejsu jako referencje
    original_inputs = {}
    original_outputs = {}
    
    # Skopiuj interfejs z zachowaniem typów socketów
    for socket in node_group.interface.items_tree:
        socket_type = socket.bl_socket_idname
        if socket_type == 'NodeSocketShader':
            socket_type = 'NodeSocketColor'  # Konwersja shader socket na color dla Octane
            
        if socket.in_out == 'INPUT':
            new_socket = oct_group.interface.new_socket(
                name=socket.name,
                in_out='INPUT',
                socket_type=socket_type
            )
            original_inputs[socket.identifier] = new_socket
            
        elif socket.in_out == 'OUTPUT':
            new_socket = oct_group.interface.new_socket(
                name=socket.name,
                in_out='OUTPUT',
                socket_type=socket_type
            )
            original_outputs[socket.identifier] = new_socket

    # Słownik do mapowania starych węzłów na nowe
    node_mapping = {}
    
    # Konwertuj wszystkie węzły w grupie
    for node in node_group.nodes:
        if node.type not in {'GROUP_INPUT', 'GROUP_OUTPUT', 'FRAME', 'REROUTE'}:
            try:
                new_node = None
                # Mix node
                if node.bl_idname == 'ShaderNodeMix':
                    if context.scene.otm_props.use_mix_node_wrapper:
                        new_node = oct_group.nodes.new(type='OctaneCyclesMixColorNodeWrapper')
                        if new_node:
                            # Ustawienia dla Mix node
                            blend_type_map = {
                                'MIX': 'Mix',
                                'DARKEN': 'Darken',
                                'MULTIPLY': 'Multiply',
                                'BURN': 'Burn',
                                'LIGHTEN': 'Lighten',
                                'SCREEN': 'Screen',
                                'DODGE': 'Dodge',
                                'ADD': 'Add',
                                'OVERLAY': 'Overlay',
                                'SOFT_LIGHT': 'Soft Light',
                                'LINEAR_LIGHT': 'Linear Light',
                                'DIFFERENCE': 'Difference',
                                'EXCLUSION': 'Exclusion',
                                'SUBTRACT': 'Subtract',
                                'DIVIDE': 'Divide',
                                'HUE': 'Hue',
                                'SATURATION': 'Saturation',
                                'COLOR': 'Color',
                                'VALUE': 'Value'
                            }
                            if node.blend_type in blend_type_map:
                                new_node.inputs[0].default_value = blend_type_map[node.blend_type]
                
                # Principled BSDF
                elif node.bl_idname == 'ShaderNodeBsdfPrincipled':
                    if context.scene.otm_props.main_material == 'UM':
                        new_node = oct_group.nodes.new(type='OctaneUniversalMaterial')
                        if new_node:
                            new_node.inputs['BSDF model'].default_value = 'GGX (energy preserving)'
                    else:
                        new_node = oct_group.nodes.new(type='OctaneStandardSurfaceMaterial')
                        if new_node:
                            new_node.inputs['Base weight'].default_value = 1
                
                # Image Texture
                elif node.bl_idname == 'ShaderNodeTexImage':
                    new_node = oct_group.nodes.new(type='OctaneRGBImage')
                    if new_node:
                        new_node.image = node.image
                        if node.image and node.image.colorspace_settings.name == 'Non-Color':
                            new_node.inputs['Legacy gamma'].default_value = 1.0
                
                # Math nodes
                elif node.bl_idname == 'ShaderNodeMath':
                    new_node = oct_group.nodes.new(type='OctaneCyclesNodeMathNodeWrapper')
                elif node.bl_idname == 'ShaderNodeVectorMath':
                    new_node = oct_group.nodes.new(type='OctaneCyclesNodeVectorMathNodeWrapper')
                elif node.bl_idname == 'ShaderNodeMapRange':
                    new_node = oct_group.nodes.new(type='OctaneOperatorRange')
                
                # Color nodes
                elif node.bl_idname == 'ShaderNodeRGB':
                    new_node = oct_group.nodes.new(type='OctaneRGBColor')
                    if new_node and hasattr(node.outputs[0], 'default_value'):
                        new_node.a_value = node.outputs[0].default_value[:3]
                
                # Texture nodes
                elif node.bl_idname == 'ShaderNodeTexVoronoi':
                    new_node = oct_group.nodes.new(type='OctaneNoiseTexture')
                    if new_node:
                        new_node.inputs[1].default_value = 'Voronoi'
                        new_node.inputs['Octaves'].default_value = int(node.inputs['Detail'].default_value)
                elif node.bl_idname == 'ShaderNodeTexNoise':
                    new_node = oct_group.nodes.new(type='OctaneNoiseTexture')
                    if new_node:
                        new_node.inputs['Octaves'].default_value = int(node.inputs['Detail'].default_value)
                
                # Other shader nodes
                elif node.bl_idname == 'ShaderNodeMixShader':
                    new_node = oct_group.nodes.new(type='OctaneMixMaterial')
                elif node.bl_idname == 'ShaderNodeBsdfTransparent':
                    new_node = oct_group.nodes.new(type='OctaneSpecularMaterial')
                    if new_node:
                        if hasattr(node.inputs['Color'], 'default_value'):
                            new_node.inputs['Transmission'].default_value = node.inputs['Color'].default_value[:3]
                        new_node.inputs['Index of refraction'].default_value = 1
                
                # Color correction nodes
                elif node.bl_idname == 'ShaderNodeBrightContrast':
                    new_node = oct_group.nodes.new(type='OctaneColorCorrection')
                elif node.bl_idname == 'ShaderNodeHueSaturation':
                    new_node = oct_group.nodes.new(type='OctaneColorCorrection')
                elif node.bl_idname == 'ShaderNodeValToRGB':
                    new_node = oct_group.nodes.new(type='OctaneGradientMap')
                elif node.bl_idname == 'ShaderNodeInvert':
                    new_node = oct_group.nodes.new(type='OctaneInvertTexture')
                
                if new_node:
                    new_node.name = 'OCT_' + node.name
                    new_node.location = node.location
                    new_node.label = node.label
                    new_node.hide = node.hide
                    new_node.mute = node.mute
                    
                    # Kopiuj wartości domyślne dla socketów
                    for input in node.inputs:
                        if not input.is_linked and input.name in new_node.inputs:
                            if hasattr(input, 'default_value'):
                                try:
                                    new_node.inputs[input.name].default_value = input.default_value
                                except:
                                    pass
                    
                    node_mapping[node] = new_node
                    
            except Exception as e:
                print(f"Error converting node {node.name}: {str(e)}")
                continue

    # Odtwórz połączenia
    for old_node, new_node in node_mapping.items():
        # Połącz inputy
        for input_socket in old_node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                from_node = from_socket.node
                
                if from_node.type == 'GROUP_INPUT':
                    for original_socket in node_group.interface.items_tree:
                        if original_socket.in_out == 'INPUT' and original_socket.identifier in original_inputs:
                            if original_socket.name == from_socket.name:
                                try:
                                    mapped_input_name = map_socket_name(input_socket.name, new_node.bl_idname)
                                    if mapped_input_name in new_node.inputs:
                                        oct_group.links.new(new_input_node.outputs[original_socket.name], 
                                                         new_node.inputs[mapped_input_name])
                                except Exception as e:
                                    print(f"Failed to connect group input: {original_socket.name} to {mapped_input_name}: {str(e)}")
                                    
                elif from_node in node_mapping:
                    from_oct_node = node_mapping[from_node]
                    if len(from_oct_node.outputs) > 0:
                        try:
                            mapped_input_name = map_socket_name(input_socket.name, new_node.bl_idname)
                            if mapped_input_name in new_node.inputs:
                                oct_group.links.new(from_oct_node.outputs[0], 
                                                 new_node.inputs[mapped_input_name])
                        except Exception as e:
                            print(f"Failed to connect nodes: {from_oct_node.name} to {new_node.name}: {str(e)}")

        # Połącz outputy
        for output_socket in old_node.outputs:
            if output_socket.is_linked:
                for link in output_socket.links:
                    to_socket = link.to_socket
                    to_node = to_socket.node
                    
                    if to_node.type == 'GROUP_OUTPUT':
                        for original_socket in node_group.interface.items_tree:
                            if original_socket.in_out == 'OUTPUT' and original_socket.identifier in original_outputs:
                                if original_socket.name == to_socket.name:
                                    try:
                                        oct_group.links.new(new_node.outputs[0], 
                                                         new_output_node.inputs[original_socket.name])
                                    except Exception as e:
                                        print(f"Failed to connect group output: {new_node.name} to {original_socket.name}: {str(e)}")
                                        
                    elif to_node in node_mapping:
                        to_oct_node = node_mapping[to_node]
                        try:
                            mapped_input_name = map_socket_name(to_socket.name, to_oct_node.bl_idname)
                            if mapped_input_name in to_oct_node.inputs:
                                oct_group.links.new(new_node.outputs[0], 
                                                 to_oct_node.inputs[mapped_input_name])
                        except Exception as e:
                            print(f"Failed to connect nodes: {new_node.name} to {to_oct_node.name}: {str(e)}")
        for material in bpy.data.materials:
                if material.use_nodes:
                    for node in material.node_tree.nodes:
                        if (node.type == 'GROUP' and 
                            node.node_tree and 
                            node.node_tree.name == node_group.name):
                            # Odtwórz połączenia zewnętrzne dla każdej instancji grupy
                            reconnect_external_group_connections(node, oct_group)

    return oct_group

# CONVERT MATERIAL
def convert_material(context, inp_material):
    convertednodes = []
    oldnodes = []
    
    try:
        for oldnode in inp_material.node_tree.nodes:
            oldnodes.append(oldnode)
    except:
        pass
        
    # Najpierw konwertuj grupy nodów
    for node in oldnodes:
        if is_node_group(node):
            # Konwertuj grupę i utwórz nową grupę Octane
            converted_group = convert_node_group(context, node.node_tree)
            if converted_group:
                # Podmień node group na nową wersję
                node.node_tree = converted_group
    
    #WAVE 1         
    for wavenode in oldnodes:
        was_converted = False

        # Najpierw sprawdzamy nod Mix
        if wavenode.bl_idname == 'ShaderNodeMix':
            if context.scene.otm_props.use_mix_node_wrapper:
                was_converted = convert_mix_color(wavenode)
            elif context.scene.otm_props.use_composite_nodes:
                was_converted = convert_mixtexture2comptexture(wavenode)
        # Pozostałe przypadki sprawdzamy tylko jeśli wasn_converted jest nadal False
        elif wavenode.bl_idname == 'ShaderNodeBsdfPrincipled':
            if context.scene.otm_props.main_material == 'UM':
                was_converted = convert_principledbsdf2um(wavenode)          
            else:
                was_converted = convert_principledbsdf2ssm(wavenode)          
        elif wavenode.bl_idname == 'ShaderNodeTexImage':
            was_converted = convert_imagetexture(wavenode) 
        elif wavenode.bl_idname == 'ShaderNodeDisplacement':
            was_converted = convert_displacement(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeHueSaturation':
            was_converted = convert_hsv(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeBrightContrast':
            was_converted = convert_brightcontrast(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeMapping':
            was_converted = convert_mapping(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeValToRGB':
            was_converted = convert_colorramp(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeRGB':
            was_converted = convert_rgb_color(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeInvert':
            was_converted = convert_invertcolor(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeMixShader':
            was_converted = convert_mixshader(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeBsdfTransparent':
            was_converted = convert_transparentbsdf(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeVectorDisplacement':
            was_converted = convert_vectordisplacement(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeTexVoronoi':
            was_converted = convert_voronoi(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeTexNoise':
            was_converted = convert_noise(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeOutputMaterial':
            was_converted = convert_outputmaterial(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeMath':
            was_converted = convert_math(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeVectorMath':
            was_converted = convert_vector_math(wavenode)
        elif wavenode.bl_idname == 'ShaderNodeMapRange':
            was_converted = convert_map_range(wavenode)
            
        if was_converted:
            convertednodes.append(wavenode)
     
    inp_material.node_tree.update_tag()
    
    if len(convertednodes) > 0:
        relink_nodes(context, inp_material)
    
    for oldnode in oldnodes:
        try:
            if oldnode.type != 'GROUP' and convertednodes.index(oldnode) >= 0:
                inp_material.node_tree.nodes.remove(oldnode)
                pass
        except:
            if oldnode.bl_idname == 'NodeFrame' or oldnode.bl_idname == 'NodeReroute':
                pass
            else:
                oldnode.color = (0.6,0.2,0.2)
                oldnode.use_custom_color = True
            pass
        
        
        
def relink_nodes(context, inp_material):
    first_inputs = ('ShaderNodeDisplacement', 'ShaderNodeVectorDisplacement', )
    first_outputs = ('ShaderNodeTexImage', 'ShaderNodeBsdfPrincipled', 'ShaderNodeMix', 'ShaderNodeDisplacement', 'ShaderNodeHueSaturation',
    'ShaderNodeBrightContrast', 'ShaderNodeMapping', 'ShaderNodeValToRGB', 'ShaderNodeInvert', 'ShaderNodeMixShader', 
    'ShaderNodeBsdfTransparent', 'ShaderNodeVectorDisplacement', 'ShaderNodeTexVoronoi', 'ShaderNodeTexNoise', 'ShaderNodeRGB', 
    'ShaderNodeMath', 'ShaderNodeVectorMath', 'ShaderNodeMapRange')
    
    # Mapping słownik dla socketów "Fac" na "Amount"
    fac_to_amount_mapping = {
        'ShaderNodeMix': {'Factor': 'Factor'},
        'ShaderNodeMixShader': {'Fac': 'Amount'},
        'ShaderNodeValToRGB': {'Fac': 'Amount'},
        
    }

    principledbsdf_to_ssm = {'Base Color' : 'Base color', 'Metallic' : 'Metalness', 'Roughness' : 'Specular roughness', 'IOR' : 'Specular IOR',
    'Alpha' : 'Opacity', 'Normal' : 'Normal', 'Subsurface Weight' : 'Subsurface weight', 'Subsurface Radius' : 'Subsurface radius', 'Subsurface Scale' : 'Subsurface scale',
    'Subsurface Anisotropy' : 'Subsurface anisotropy', 'Specular IOR Level' : 'Specular weight', 'Specular Tint' : 'Specular color', 'Specular Anisotropy' : 'Specular anisotropy',
    'Anisotropic Rotation' : 'Specular rotation', 'Transmission Weight' : 'Transmission weight', 'Coat Weight' : 'Coating weight', 'Coat Roughness' : 'Coating roughness',
    'Coat IOR' : 'Coating IOR', 'Coat Tint' : 'Coating color', 'Coat Normal' : 'Coating normal', 'Sheen Weight' : 'Sheen weight', 'Sheen Roughness' : 'Sheen roughness',
    'Sheen Tint' : 'Sheen color', 'Emission Color' : 'Emission color', 'Emission Strength' : 'Emission weight'}
    
    principledbsdf_to_um = {'Base Color' : 'Albedo', 'Specular IOR Level' : 'Specular', 'Metallic' : 'Metallic', 'Roughness' : 'Roughness', 'IOR' : 'Dielectric IOR',
    'Alpha' : 'Opacity', 'Normal' : 'Normal', 'Specular Anisotropy' : 'Anisotropy', 'Anisotropic Rotation' : 'Rotation', 'Transmission Weight' : 'Transmission', 'Coat Weight' : 'Coating', 'Coat Roughness' : 'Coating roughness',
    'Coat IOR' : 'Coating IOR', 'Coat Normal' : 'Coating normal', 'Sheen Weight' : 'Sheen', 'Sheen Roughness' : 'Sheen roughness', 'Emission Color' : 'Emission'}

    relinkedlinks = []
    oldlinks = []
    for oldlink in inp_material.node_tree.links:
        oldlinks.append(oldlink)
    
    for link in oldlinks:    
        from_node = link.from_socket.node
        to_node = link.to_socket.node
        
        # Ustalamy prefiksy w zależności od typu węzła i ustawień
        if from_node.bl_idname == 'ShaderNodeMix' or to_node.bl_idname == 'ShaderNodeMix':
            if context.scene.otm_props.use_composite_nodes:
                # Dla Composite Nodes
                from_node_prefix = '.OCT_' if from_node.bl_idname == 'ShaderNodeMix' else 'OCT_'
                to_node_prefix = '.OCT_' if to_node.bl_idname == 'ShaderNodeMix' else 'OCT_'
            else:
                # Dla Mix Node Wrapper lub standardowego przypadku
                from_node_prefix = 'OCT_'
                to_node_prefix = 'OCT_'
        else:
            from_node_prefix = 'OCT_'
            to_node_prefix = 'OCT_'

        # FROM SOCKETS
        newlink_fromsocket = link.from_socket
        try:
            if first_outputs.index(from_node.bl_idname) >= 0:
                newlink_fromsocket = inp_material.node_tree.nodes[from_node_prefix + from_node.name].outputs[0]
        except:
            newlink_fromsocket = link.from_socket
            pass
        
        if from_node.bl_idname == 'NodeReroute':
            newlink_fromsocket = link.from_socket
                    
        # TO SOCKETS
        newlink_tosocket = link.to_socket
        
        # Obsługa socketów dla nodów Mix
        if to_node.bl_idname == 'ShaderNodeMix':
            if context.scene.otm_props.use_mix_node_wrapper:
                # Mapowanie dla Mix Node Wrapper
                if link.to_socket.name == 'Factor':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[5]
                elif link.to_socket.name == 'A':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[6]
                elif link.to_socket.name == 'B':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[7]
            elif context.scene.otm_props.use_composite_nodes:
                # Mapowanie dla Composite Nodes
                if link.to_socket.name == 'Factor':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[0]
                elif link.to_socket.name == 'A':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[2]
                elif link.to_socket.name == 'B':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[1]

        # Reszta oryginalnej logiki łączenia
        try:
            if first_inputs.index(to_node.bl_idname) >= 0:
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[0]
        except:
            pass

        # Math node jako odbiorca
        if to_node.bl_idname == 'ShaderNodeMath':
            try:
                converted_node = inp_material.node_tree.nodes[to_node_prefix + to_node.name]
                if link.to_socket == to_node.inputs[0]:  # Value1
                    newlink_tosocket = converted_node.inputs['Value1']
                elif link.to_socket == to_node.inputs[1]:  # Value2
                    newlink_tosocket = converted_node.inputs['Value2']
                elif len(to_node.inputs) > 2 and link.to_socket == to_node.inputs[2]:  # Value3
                    newlink_tosocket = converted_node.inputs['Value3']
            except:
                pass

        # Vector Math node jako odbiorca
        elif to_node.bl_idname == 'ShaderNodeVectorMath':
            try:
                converted_node = inp_material.node_tree.nodes[to_node_prefix + to_node.name]
                input_map = {
                    0: 'Vector1',
                    1: 'Vector2',
                    2: 'Vector3'
                }
                if link.to_socket.identifier in input_map:
                    socket_index = int(link.to_socket.identifier.split('_')[1])
                    newlink_tosocket = converted_node.inputs[input_map[socket_index]]
                elif link.to_socket.name == 'Scale':
                    newlink_tosocket = converted_node.inputs['Scale']
            except:
                pass
            
            
        elif to_node.bl_idname == 'ShaderNodeMapRange':
            try:
                converted_node = inp_material.node_tree.nodes[to_node_prefix + to_node.name]
                input_map = {
                    'Value': 'Value',
                    'From Min': 'Input min',
                    'From Max': 'Input max',
                    'To Min': 'Output min',
                    'To Max': 'Output max'
                }
                
                if link.to_socket.name in input_map:
                    newlink_tosocket = converted_node.inputs[input_map[link.to_socket.name]]
            except:
                pass

        elif to_node.bl_idname == 'ShaderNodeBsdfPrincipled':
            try:
                if context.scene.otm_props.main_material == 'UM':
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[principledbsdf_to_um[link.to_socket.name]]
                else:
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[principledbsdf_to_ssm[link.to_socket.name]]
            except:
                pass
            
        if to_node.bl_idname == 'ShaderNodeTexImage':
            try:
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs['UV transform']
            except:
                pass
                    
        if to_node.bl_idname == 'ShaderNodeOutputMaterial':
            if link.to_socket.name == 'Surface':
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[0]
            elif link.to_socket.name == 'Displacement':
                if to_node.inputs[0].is_linked:
                    try:
                        old_from_node = findfromsocket(to_node.inputs[0]).node
                        new_from_node = inp_material.node_tree.nodes[to_node_prefix + old_from_node.name]
                        newlink_tosocket = new_from_node.inputs['Displacement']
                    except:
                        pass
        
        if from_node.bl_idname == 'ShaderNodeRGB':
            newlink_fromsocket = inp_material.node_tree.nodes[from_node_prefix + from_node.name].outputs[0]
                    
                                
        if to_node.bl_idname == 'ShaderNodeBump':
            if to_node.outputs[0].is_linked:
                try:
                    target_node = findtosocket(to_node.outputs[0]).node
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + target_node.name].inputs['Bump']
                    
                    if from_node.bl_idname == 'ShaderNodeTexImage':
                        oct_rgb_node = inp_material.node_tree.nodes.get('OCT_' + from_node.name)
                        if oct_rgb_node:
                            oct_rgb_node.inputs['Power'].default_value = to_node.inputs['Strength'].default_value
                except:
                    pass
                
        if to_node.bl_idname == 'ShaderNodeNormalMap':
            if to_node.outputs[0].is_linked:
                try:
                    target_node = findtosocket(to_node.outputs[0]).node
                    if target_node.bl_idname == 'ShaderNodeBump':
                        target_node = findtosocket(target_node.outputs[0]).node
                    newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + target_node.name].inputs['Normal']
                    
                    if from_node.bl_idname == 'ShaderNodeTexImage':
                        oct_rgb_node = inp_material.node_tree.nodes.get('OCT_' + from_node.name)
                        if oct_rgb_node:
                            oct_rgb_node.inputs['Power'].default_value = to_node.inputs['Strength'].default_value
                except:
                    pass
                
        if to_node.bl_idname == 'ShaderNodeHueSaturation':
            link_map = {'Hue' : 3, 'Saturation' : 4, 'Value' : 1, 'Fac' : 9, 'Color': 0}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]
            
        if to_node.bl_idname == 'ShaderNodeBrightContrast':
            link_map = {'Color' : 0, 'Bright' : 1, 'Contrast' : 6}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]
            
        if to_node.bl_idname == 'ShaderNodeValToRGB':
            link_map = {'Fac' : 2}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]
            
        if to_node.bl_idname == 'ShaderNodeInvert':
            link_map = {'Color' : 0}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]   
        
        if to_node.bl_idname == 'ShaderNodeMixShader':
            if link.to_socket == to_node.inputs[1]:
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[1]
            if link.to_socket == to_node.inputs[2]:
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[2]
            if link.to_socket.name in fac_to_amount_mapping['ShaderNodeMixShader']:
                newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[fac_to_amount_mapping['ShaderNodeMixShader'][link.to_socket.name]]
                             
                
        if to_node.bl_idname == 'ShaderNodeBsdfTransparent':
            link_map = {'Color' : 1}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]
            
        if to_node.bl_idname == 'ShaderNodeTexVoronoi':
            link_map = {'Vector' : 4}
            newlink_tosocket = inp_material.node_tree.nodes[to_node_prefix + to_node.name].inputs[link_map[link.to_socket.name]]
        
        try:
            if newlink_fromsocket.node.bl_idname != 'ShaderNodeNormalMap':
                bpy.context.material.node_tree.links.new(input=newlink_fromsocket, output=newlink_tosocket)
                relinkedlinks.append(link)
        except:
            pass

    for ilink in relinkedlinks:
        try:
            bpy.context.material.node_tree.links.remove(ilink)
        except:
            pass


class OCTTOOLS_OP_CONVERT_TO_OCTANE_MATERIAL(bpy.types.Operator):
    bl_idname = "octanetools.convert_to_octane_material"
    bl_label = "Convert To Octane Material"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        is_octanematerial = False
        
        for inode in bpy.context.object.active_material.node_tree.nodes:
            if inode.bl_idname == 'OctaneUniversalMaterial' or inode.bl_idname == 'OctaneStandardSurfaceMaterial':
                is_octanematerial = True
                break
        
        if is_octanematerial == False:
            convert_material(context, bpy.context.object.active_material)
            
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)  
    
    

    
class OCTTOOLS_OP_REMOVE_MARKED_NODES(bpy.types.Operator):
    bl_idname = "octanetools.remove_marked_nodes"
    bl_label = "Remove Market Nodes"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        for loopnode in bpy.context.material.node_tree.nodes:
            if round(loopnode.color[0], 1) == 0.6 and round(loopnode.color[1], 1) == 0.2 and round(loopnode.color[2], 1) == 0.2:
                bpy.context.material.node_tree.nodes.remove(loopnode)  
            
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)
    
class OCTTOOLS_OP_CREATEIMAGENODE(bpy.types.Operator):
    bl_idname = "octanetools.createimagenode"
    bl_label = "Create Image Node"
    bl_description = "Create a Cycles image node based on the active RGB Image node."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if ((bpy.context.active_node.bl_idname == 'OctaneRGBImage') or 
            (bpy.context.active_node.bl_idname == 'OctaneGreyscaleImage') or 
            (bpy.context.active_node.bl_idname == 'OctaneAlphaImage')):
            temp_node = bpy.context.material.node_tree.nodes.new(type='ShaderNodeTexImage', )
            temp_node.location = tuple(Vector(bpy.context.active_node.location) - Vector((350, 0)))
            temp_node.image = bpy.context.active_node.image

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)
    
class OCTTOOLS_OP_DISSOLVENODE(bpy.types.Operator):
    bl_idname = "octanetools.dissolvenode"
    bl_label = "Dissolve Node"
    bl_description = "Dissolves a node while trying to relink it."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (bpy.context.area.type != 'NODE_EDITOR') or (bpy.context.area.ui_type != 'ShaderNodeTree'):
            return False
        active_node = bpy.context.active_node
        if (active_node != None) and (active_node.bl_idname != 'ShaderNodeOutputMaterial'):
            if active_node.outputs[0].is_linked:
                to_socket = findtosocket(active_node.outputs[0])
                for socket in active_node.inputs:
                    if (socket.is_linked):
                        from_socket = findfromsocket(socket)
                        if from_socket.octane_pin_type == to_socket.octane_pin_type:
                            active_node.id_data.links.new(input = from_socket, output = to_socket, )
                            break
            bpy.context.active_object.active_material.node_tree.nodes.remove(active_node)

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)
    
class OCTTOOLS_OP_SOLO_MODE(bpy.types.Operator):
    bl_idname = "octanetools.solo_mode"
    bl_label = "Solo Mode"
    bl_description = "Solo Octane Texture Node"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if (bpy.context.active_node != None):
            active_node_tree = bpy.context.view_layer.objects.active.active_material.node_tree 
            if 'O_SM_DIFF' in active_node_tree.nodes:
                active_node_tree.nodes.remove(active_node_tree.nodes['O_SM_DIFF'], )
                active_node_tree.nodes.remove(active_node_tree.nodes['O_SM_EM'], )
                if solo_mode['inside_group']:
                    bpy.context.active_node.id_data.interface.remove(item=solo_mode['group_socket'], )
                if (solo_mode['old_input'] != None):
                    temp_link = active_node_tree.links.new(input = active_node_tree.nodes['Material Output'].inputs['Surface'], output = solo_mode['old_input'], )
            elif len(bpy.context.active_node.outputs) > 0:
                if (bpy.context.active_node.outputs[0].bl_idname == 'OctaneTextureOutSocket'):
                    diffuse_node = active_node_tree.nodes.new(type='OctaneDiffuseMaterial', )
                    diffuse_node.name = 'O_SM_DIFF'
                    diffuse_node.location = (1000, 1000)
                    diffuse_node.inputs['Diffuse'].default_value = (0.0, 0.0, 0.0)
                    emission_node = bpy.context.view_layer.objects.active.active_material.node_tree.nodes.new(type='OctaneTextureEmission', )
                    emission_node.name = 'O_SM_EM'
                    emission_node.location = (700, 1000)
                    emission_node.inputs['Power'].default_value = 1.0
                    emission_node.inputs['Visible on diffuse'].default_value = False
                    emission_node.inputs['Visible on specular'].default_value = False
                    emission_node.inputs['Visible on scattering volumes'].default_value = False
                    emission_node.inputs['Cast shadows'].default_value = False
                    emission_node.inputs['Surface brightness'].default_value = True

                    temp_link = active_node_tree.links.new(input = diffuse_node.inputs['Emission'], output = emission_node.outputs['Emission out'], )
                    solo_mode['old_input'] = findfromsocket(active_node_tree.nodes['Material Output'].inputs['Surface'])
                    temp_link = active_node_tree.links.new(input = active_node_tree.nodes['Material Output'].inputs['Surface'], output = active_node_tree.nodes['O_SM_DIFF'].outputs['Material out'], )

                    group_output_node = get_group_interface_node('GROUP_OUTPUT')
                    solo_mode['inside_group'] = False

                    if (group_output_node != None):
                        solo_mode['inside_group'] = True
                        solo_mode['group_socket'] = bpy.context.active_node.id_data.interface.new_socket(name='SM_GROUPOUT', in_out='OUTPUT', )
                        temp_link = bpy.context.active_node.id_data.links.new(input = bpy.context.active_node.outputs['Texture out'], output = group_output_node.inputs['SM_GROUPOUT'], )
                        temp_link = bpy.context.view_layer.objects.active.active_material.node_tree.links.new(input=bpy.context.material.node_tree.nodes.active.outputs['SM_GROUPOUT'], output=bpy.context.view_layer.objects.active.active_material.node_tree.nodes['O_SM_EM'].inputs['Texture'], )
                    else:
                        temp_link = active_node_tree.links.new(input = active_node_tree.nodes['O_SM_EM'].inputs['Texture'], output = active_node_tree.nodes.active.outputs[0], )
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)
    
class OCTTOOLS_OP_CREATE_PBR_SETUP(bpy.types.Operator, ImportHelper):
    bl_idname = "octanetools.create_pbr_setup"
    bl_label = "Create PBR Setup"
    bl_description = "Open files and create a PBR node setup."
    bl_options = {"REGISTER", "UNDO"}

    directory: StringProperty(
        name='Directory',
        subtype='DIR_PATH',
        default='',
        description='Folder containing images'
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        if len(self.files) > 0:

            um_sockets = {'DIFFUSE' : 'Albedo', 'METALLIC' : 'Metallic', 'ROUGHNESS' : 'Roughness', 'EMISSION' : 'Emission', 'BUMP' : 'Bump', 'NORMAL' : 'Normal', 'DISPLACEMENT' : 'Displacement'}
            ssm_sockets = {'DIFFUSE' : 'Base color', 'METALLIC' : 'Metallness', 'ROUGHNESS' : 'Specular roughness', 'EMISSION' : 'Emission', 'BUMP' : 'Bump', 'NORMAL' : 'Normal', 'DISPLACEMENT' : 'Displacement'}

            ao_strings = ['Ambient', 'ambient','AO', 'ao']
            diffuse_strings = ['Diffuse', 'diffuse','Diff', 'diff', 'Albedo', 'albedo', 'Base', 'base', 'Color', 'color']
            metallic_strings = ['Metallness', 'metalness', 'Metal', 'metal', 'Metallic', 'metallic']
            roughness_strings = ['Roughness', 'roughness', 'Rough', 'rough']
            emission_strings = ['Emission', 'emission', 'Emit', 'emit']
            bump_strings = ['Bump', 'bump']
            normal_strings = ['Normal', 'normal']
            displacement_strings = ['Displacement', 'displacement', 'Displace', 'displace', 'Height', 'height', 'Disp', 'disp']

            # CREATE MATERIAL
            new_material = bpy.data.materials.new('Octane PBR Material')
            new_material.use_nodes = True
            if context.scene.otm_props.pbr_new_slot:
                bpy.context.object.data.materials.append(new_material)
                bpy.context.object.active_material_index = len(bpy.context.object.material_slots) - 1
            else:
                bpy.context.object.active_material = new_material
            
            output_node = [node for node in new_material.node_tree.nodes if node.bl_idname == 'ShaderNodeOutputMaterial'][0]
            old_material_node = findfromsocket(output_node.inputs[0]).node

            if context.scene.otm_props.pbr_material == 'UM':
                material_node = new_material.node_tree.nodes.new(type = 'OctaneUniversalMaterial')
                used_sockets = um_sockets
            else:
                material_node = new_material.node_tree.nodes.new(type = 'OctaneStandardSurfaceMaterial')
                material_node.inputs['Base weight'].default_value = 1
                used_sockets = ssm_sockets

            material_node.location = (0,300)
            new_material.node_tree.links.new(input = output_node.inputs[0], output = material_node.outputs[0])
            new_material.node_tree.nodes.remove(old_material_node)
            transform_node = new_material.node_tree.nodes.new(type = 'Octane3DTransformation')
            transform_node.location = tuple(Vector(material_node.location) - Vector((1050, 0)))

            for file in self.files:
                temp_node = new_material.node_tree.nodes.new(type = 'OctaneRGBImage')
                temp_node.location = tuple(Vector(material_node.location) - Vector((700, 0)))  
                new_material.node_tree.links.new(input = transform_node.outputs[0], output = temp_node.inputs[5])

                temp_img = bpy.data.images.load(path.join(self.directory, file.name))      
                temp_node.image = temp_img

                # SET GAMMA
                if any(x in file.name for x in diffuse_strings) == False:
                    temp_node.inputs[2].default_value = 1

                # DIFFUSE NODE
                if any(x in file.name for x in diffuse_strings):
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = material_node.inputs[used_sockets['DIFFUSE']])
                # METALLIC NODE
                if any(x in file.name for x in metallic_strings):
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = material_node.inputs[used_sockets['METALLIC']])
                # ROUGHNESS NODE
                if any(x in file.name for x in roughness_strings):
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = material_node.inputs[used_sockets['ROUGHNESS']])
                # EMISSION NODE
                if any(x in file.name for x in emission_strings):
                    temp_emission_node = new_material.node_tree.nodes.new(type = 'OctaneTextureEmission')
                    temp_emission_node.location = tuple(Vector(material_node.location) - Vector((350, 0)))
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = temp_emission_node.inputs[0])
                    new_material.node_tree.links.new(input = temp_emission_node.outputs[0], output = material_node.inputs[used_sockets['EMISSION']])
                # BUMP NODE
                if any(x in file.name for x in bump_strings):
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = material_node.inputs[used_sockets['BUMP']])
                # NORMAL NODE
                if any(x in file.name for x in normal_strings):
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = material_node.inputs[used_sockets['NORMAL']])
                # DISPLACEMENT NODE
                if any(x in file.name for x in displacement_strings):
                    temp_displacement_node = new_material.node_tree.nodes.new(type = 'OctaneTextureDisplacement')
                    temp_displacement_node.location = tuple(Vector(material_node.location) - Vector((350, 0)))
                    temp_displacement_node.inputs[1].default_value = 0.5
                    temp_displacement_node.inputs[2].default_value = "2048x2048"
                    temp_displacement_node.inputs[3].default_value = 0.1
                    temp_displacement_node.inputs[4].default_value = 'Follow smoothed normal'
                    new_material.node_tree.links.new(input = temp_node.outputs[0], output = temp_displacement_node.inputs[0])
                    new_material.node_tree.links.new(input = temp_displacement_node.outputs[0], output = material_node.inputs[used_sockets['DISPLACEMENT']])

            # POSITION LINKED NODES
            vertical_offset = material_node.location.y
            for socket in material_node.inputs:
                if socket.is_linked:
                    from_socket = findfromsocket(socket)
                    if socket.name == used_sockets['EMISSION']:
                        from_socket.node.location.y = vertical_offset
                        findfromsocket(from_socket.node.inputs[0]).node.location.y = vertical_offset
                    elif socket.name == used_sockets['DISPLACEMENT']:
                        from_socket.node.location.y = vertical_offset - 130
                        findfromsocket(from_socket.node.inputs[0]).node.location.y = vertical_offset
                    else:
                        from_socket.node.location.y = vertical_offset
                    vertical_offset -= 370

            # POSITION UNLINKED NODES
            vertical_offset = material_node.location.y + 370
            for node in new_material.node_tree.nodes:
                if node.bl_idname == 'OctaneRGBImage':
                    if node.outputs[0].is_linked == False:
                        node.location.y = vertical_offset
                        vertical_offset += 370      

        return {"FINISHED"}
    
class OCTTOOLS_PROP_OTMATERIALS_PROPERTIES(bpy.types.PropertyGroup):

    main_material : bpy.props.EnumProperty(
        name = "Main Material",
        description = "Select Main Material",
        items = [
            ('UM', "Universal Material", ""),
            ('SSM', "Standard Surface Material", "")
        ]
    )    
        
    use_composite_nodes: bpy.props.BoolProperty(
        name="Always use Composite Nodes",
        description="Use Composite Texture nodes instead of Mix/Add/Multiply Texture nodes",
        default=False,
        update=lambda self, context: self._update_exclusive_checkboxes('use_composite_nodes')
    ) 

    use_mix_node_wrapper: bpy.props.BoolProperty(
        name="Use Octane Mix Node Wrapper",
        description="Use Octane Mix Node Wrapper for mixing textures",
        default=True,
        update=lambda self, context: self._update_exclusive_checkboxes('use_mix_node_wrapper')
    )

    use_clamp: bpy.props.BoolProperty(
        name="Clamp Factor",
        description="Clamp the Factor input value between 0 and 1",
        default=True
    )

    use_clamp_result: bpy.props.BoolProperty(
        name="Clamp Result",
        description="Clamp the result of the mix operation between 0 and 1",
        default=False
    )

    def _update_exclusive_checkboxes(self, prop_name):
        if prop_name == 'use_composite_nodes' and self.use_composite_nodes:
            self.use_mix_node_wrapper = False
        elif prop_name == 'use_mix_node_wrapper' and self.use_mix_node_wrapper:
            self.use_composite_nodes = False

    pbr_material : bpy.props.EnumProperty(
        name = "PBR Material",
        description = "Select PBR Material",
        items = [
            ('UM', "Universal Material", ""),
            ('SSM', "Standard Surface Material", "")
        ]
    )

    pbr_new_slot: bpy.props.BoolProperty(
        name="Create New Material Slot",
        description="Create a new material slot for the PBR material.",
        default=False,
    ) 

class OCTTOOLS_PT_MATERIAL_CONVERSION(bpy.types.Panel):
    bl_label = 'Material Tools'
    bl_idname = 'OCTTOOLS_PT_material_conversion'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Octane Tools'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        if bpy.data.scenes["Scene"].render.engine != 'octane':
            return False
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        col = box.column(align = False)
        col.separator(factor = 1)
        op1 = col.operator('octanetools.convert_to_octane_material', text=' Convert To Octane Material', icon_value=127, emboss=True, depress=False)
        col.separator(factor = 1)
        col.separator(factor = 2)
        col.label(text = "Convert Principled BSDF to:")
        col.prop(context.scene.otm_props, "main_material", text = "")
        col.separator(factor = 0.5)
        col.prop(context.scene.otm_props, "use_composite_nodes", text = " Use Composite Nodes")
        col.prop(context.scene.otm_props, "use_mix_node_wrapper", text = " Use Octane Mix Node Wrapper") 
        col.separator(factor = 2)
        op3 = col.operator('octanetools.remove_marked_nodes', text=' Remove Marked Nodes', icon="TRASH", emboss=True, depress=False)
        col.separator(factor = 1)

        box = layout.box()
        col = box.column(align = False)
        col.separator(factor = 1)
        op4 = col.operator('octanetools.create_pbr_setup', text=' Create PBR Setup', icon_value=127, emboss=True, depress=False)
        col.separator(factor = 2)
        col.prop(context.scene.otm_props, "pbr_material", text = "")
        col.separator(factor = 1)
        col.prop(context.scene.otm_props, "pbr_new_slot", text = "Add New Material Slot")
        col.separator(factor = 1)

        col = layout.column(align = False)
        col.separator(factor = 1)
        col.label(text='Shortcuts:')
        col.label(text='I > Create Blender Image Node')
        col.label(text='CTRL-ALT-LMB > Solo Texture Node')
        col.label(text='SHIFT X > Dissolve Node')

classes = (OCTTOOLS_PROP_OTMATERIALS_PROPERTIES, OCTTOOLS_PT_MATERIAL_CONVERSION, OCTTOOLS_OP_CONVERT_TO_OCTANE_MATERIAL, OCTTOOLS_OP_REMOVE_MARKED_NODES, OCTTOOLS_OP_SOLO_MODE, OCTTOOLS_OP_CREATEIMAGENODE, OCTTOOLS_OP_DISSOLVENODE, OCTTOOLS_OP_CREATE_PBR_SETUP)
addon_keymaps = []

def register():
    # Register all classes
    from . import ot_main_tools
    
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties
    bpy.types.Scene.otm_props = PointerProperty(type=OCTTOOLS_PROP_OTMATERIALS_PROPERTIES)
    
    # Register keymaps
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new('octanetools.solo_mode', 'LEFTMOUSE', 'PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new('octanetools.solo_mode', 'S', 'PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new('octanetools.createimagenode', 'I', 'PRESS')
        addon_keymaps.append((km, kmi))
        
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new('octanetools.dissolvenode', 'X', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

    # Register main tools
    ot_main_tools.main_tools_register()

def unregister():
    # Unregister all classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    # Unregister properties
    del bpy.types.Scene.otm_props
    
    # Unregister main tools
    ot_main_tools.main_tools_unregister()

if __name__ == "__main__":
    register()