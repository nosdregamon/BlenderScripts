#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  ***** END GPL LICENSE BLOCK *****
#
#
#  ***** NOTE *****
#
# This is a modified version (for my own use) of Level buddy by Matt Lucas.
# You can find the original script here : https://matt-lucas.itch.io/level-buddy
# This version is a test for Blender 2.92 and doesn't work well because of the new boolean solvers (I may be wrong)


bl_info = {
    "name": "Level Buddy Ormusto",
    "author": "Matt Lucas, Matthieu Gouby",
    "version": (1, 0),
    "blender": (2, 92, 0),
    "location": "View3D > Tools",
    "description": "A set of workflow tools based on concepts from Doom and Unreal level mapping.",
    "warning": "still under development and lacks documentation.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
}

import bpy
import bmesh

# MY MATERIALS
MyMaterials = {
    'EXTCEILING':(0.5,0.0,0.5,1.0),
    'EXTWALL':(0.5,0.0,0.5,1.0),
    'EXTFLOOR':(0.5,0.0,0.5,1.0),
    'EXT2CEILING':(0.1,0.0,0.1,1.0),
    'EXT2WALL':(0.1,0.0,0.1,1.0),
    'EXT2FLOOR':(0.1,0.0,0.1,1.0),
    'HUBCEILING':(0.0,0.5,0.0,1.0),
    'HUBWALL':(0.0,0.5,0.0,1.0),
    'HUBFLOOR':(0.0,0.5,0.0,1.0),
    'HUBCEILINGDARK':(0.0,0.1,0.0,1.0),
    'HUBWALLDARK':(0.0,0.1,0.0,1.0),
    'HUBFLOORDARK':(0.0,0.1,0.0,1.0),
    'ROOM1CEILING':(0.5,0.0,0.0,1.0),
    'ROOM1WALL':(0.5,0.0,0.0,1.0),
    'ROOM1FLOOR':(0.5,0.0,0.0,1.0),  
    'ROOM1CEILINGDARK':(0.1,0.0,0.0,1.0),
    'ROOM1WALLDARK':(0.1,0.0,0.0,1.0),
    'ROOM1FLOORDARK':(0.1,0.0,0.0,1.0),    
    'ROOM2CEILING':(0.5,0.5,0.0,1.0),
    'ROOM2WALL':(0.5,0.5,0.0,1.0),
    'ROOM2FLOOR':(0.5,0.5,0.0,1.0),  
    'ROOM2CEILINGDARK':(0.1,0.1,0.0,1.0),
    'ROOM2WALLDARK':(0.1,0.1,0.0,1.0),
    'ROOM2FLOORDARK':(0.1,0.1,0.0,1.0),  
    'ROOM3CEILING':(0.0,0.0,0.5,1.0),
    'ROOM3WALL':(0.0,0.0,0.5,1.0),
    'ROOM3FLOOR':(0.0,0.0,0.5,1.0),  
    'ROOM3CEILINGDARK':(0.0,0.0,0.1,1.0),
    'ROOM3WALLDARK':(0.0,0.0,0.1,1.0),
    'ROOM3FLOORDARK':(0.0,0.0,0.1,1.0), 
    'BRUSH':(0.5,0.5,0.5,1.0)            
}

# TEXTURE PROPERTIES
bpy.types.Scene.texel_density = bpy.props.IntProperty(name="Texel Density", default=128, step=128, min=8, max=512)
bpy.types.Scene.offset_x = bpy.props.FloatProperty(name="Offset X", default=0)
bpy.types.Scene.offset_y = bpy.props.FloatProperty(name="Offset Y", default=0)
bpy.types.Scene.nudge_amount = bpy.props.FloatProperty(name="Nudge Amount", default=0.125)

def export_level_map():
    scn = bpy.context.scene
    if scn.map_export_path is not "":
        bpy.data.objects[scn.map_name].hide_select = False
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_pattern(pattern=scn.map_name)
        bpy.data.objects[scn.map_name].select_set(True)
        bpy.ops.export_scene.fbx(
            bake_space_transform=True,
            axis_forward="Z",
            use_selection=1,
            filepath=bpy.path.abspath(scn.map_export_path) + scn.map_name.lower() + ".fbx"
        )

def update_location_precision(ob):
    ob.location.x = round(ob.location.x, 1)
    ob.location.y = round(ob.location.y, 1)
    ob.location.z = round(ob.location.z, 1)
    cleanup_vertex_precision(ob)

def freeze_transforms(ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=ob.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')

def update_sector(self, context):
    ob = bpy.context.active_object  
    if ob is not None:
        if ob.type == 'MESH' and ob.sector_type == 'PLANE':
            update_location_precision(ob)
            if not ob.is_sector_mesh:
                update_sector_plane_modifier(ob)
        if ob.type != 'NONE' or ob.sector_type != 'PLANE':
            update_sector_plane_modifier(ob)
            update_location_precision(ob)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_pattern(pattern=ob.name)
        bpy.context.view_layer.objects.active = ob

def update_sector_plane_modifier(ob):
    if ob.modifiers:
        mod = ob.modifiers[0]
        if mod.type == "SOLIDIFY":
            if ob.floor_height > 0:
                mod.thickness = ob.ceiling_height - ob.floor_height
            else:
                mod.thickness = ob.ceiling_height - ob.floor_height
            mod.material_offset = 1
            mod.material_offset_rim = 2                    

#GET OR CREATE MATERIAL
def update_sector_plane_materials(ob):
    if not "Texture" in bpy.data.images:   
        tex_image = bpy.ops.image.new(name='Texture', width=1024, height=1024, color=[0.0, 0.0, 0.0, 1.0], alpha=True, generated_type='BLANK', float=False, use_stereo_3d=False, tiled=False)
    
    for mat, color in MyMaterials.items():
        mat2 = bpy.data.materials.get(mat)
        if mat2 is None:
            mat = bpy.data.materials.new(name=mat)
            mat.shadow_method = 'NONE'
            mat.diffuse_color = color
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images['Texture']
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex.outputs['Color']) 
            mat = ""

#ASSIGN TEXTURESET
class ADDON_OT_TextureSet(bpy.types.Operator):
    bl_idname = "scene.textureset"
    bl_label = "textureset"

    CeilingTexture : bpy.props.StringProperty(name="CeilingTexture")
    FloorTexture : bpy.props.StringProperty(name="FloorTexture")
    WallTexture : bpy.props.StringProperty(name="WallTexture")
    
    def execute(self, context):      
        if bpy.context.selected_objects != []:   
            for ob in bpy.context.selected_objects:
                if ob is not None: 
                    if ob.type == 'MESH':
                        if ob.sector_type == 'PLANE':
                            update_sector_plane_materials(ob)
                            bpy.context.view_layer.objects.active = ob     
                            for x in bpy.context.object.material_slots:
                                bpy.context.object.active_material_index = 0
                                bpy.ops.object.material_slot_remove()
                            bpy.ops.object.material_slot_add()    
                            bpy.ops.object.material_slot_add()  
                            bpy.ops.object.material_slot_add()                              
                            ob.data.materials[0] = bpy.data.materials.get(self.CeilingTexture)                        
                            ob.data.materials[1] = bpy.data.materials.get(self.FloorTexture) 
                            ob.data.materials[2] = bpy.data.materials.get(self.WallTexture)  
                        else:
                            update_sector_plane_materials(ob)                        
                            bpy.context.view_layer.objects.active = ob     
                            for x in bpy.context.object.material_slots:
                                bpy.context.object.active_material_index = 0
                                bpy.ops.object.material_slot_remove()
                            bpy.ops.object.material_slot_add()   
                            ob.data.materials[0] = bpy.data.materials.get("BRUSH")                                                             
        return {"FINISHED"}  

def cleanup_vertex_precision(ob):
    p = bpy.context.scene.map_precision
    if ob.type == 'MESH':
        for v in ob.data.vertices:
            if ob.modifiers:
                mod = ob.modifiers[0]
                if mod.type == "SOLIDIFY":
                    v.co.z = ob.floor_height
            v.co.x = round(v.co.x, p)
            v.co.y = round(v.co.y, p)
            v.co.z = round(v.co.z, p)

def apply_boolean(obj_active, x, bool_op):
    scn = bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')    
    obj_active.select_set(True) 
    ob_bool = bpy.data.objects[x]   
    cleanup_vertex_precision(ob_bool)
    copy_materials(obj_active, bpy.data.objects[x])
    mod = obj_active.modifiers.new(name=x, type='BOOLEAN')
    mod.object = ob_bool
    mod.operation = bool_op
    if scn.bool_solver == 'FAST':
        mod.solver = 'FAST'
    else: 
        mod.solver = 'EXACT'    
    bpy.ops.object.modifier_apply(modifier=x, report=True)

def create_new_boolean_object(scn, name):
    old_map = None
    if bpy.data.meshes.get(name + "_MESH") is not None:
        old_map = bpy.data.meshes[name + "_MESH"]
        old_map.name = "map_old"
    me = bpy.data.meshes.new(name + "_MESH")
    if bpy.data.objects.get(name) is None:
        ob = bpy.data.objects.new(name, me)
        col = bpy.data.collections.get("Collection 1")
        if col:
            col.name = "Collection"
        bpy.data.collections['Collection'].objects.link(ob)
    else:
        ob = bpy.data.objects[name]
        ob.data = me
    if old_map is not None:
        bpy.data.meshes.remove(old_map)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob  

def auto_texture(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.texture_buddy_uv()
    bpy.ops.object.editmode_toggle()

def copy_materials(a, b):
    for m in b.data.materials:
        has_material = False
        for mat in a.data.materials:
            if mat is not None and m is not None:
                if mat.name == m.name:
                    has_material = True
        if not has_material:
            a.data.materials.append(m)

def recalculate_normals_inside(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=True)
    bpy.ops.object.editmode_toggle()

bpy.types.Scene.map_export_path = bpy.props.StringProperty(
    name="Export Path",
    default="",
    subtype="DIR_PATH"
)
bpy.types.Scene.map_precision = bpy.props.IntProperty(
    name="Map Precision",
    default=1,
    min=0,
    max=4,
    description='Controls the rounding level of vertex precisions.  Lower numbers round to higher values.  A level of "1" would round 1.234 to 1.2 and a level of "2" would round to 1.23'
)
bpy.types.Object.ceiling_height = bpy.props.FloatProperty(
    name="Ceiling Height",
    default=4,
    step=50,
    precision=1,
    update=update_sector
)
bpy.types.Object.floor_height = bpy.props.FloatProperty(
    name="Floor Height",
    default=0,
    step=50,
    precision=1,
    update=update_sector
)
bpy.types.Object.sector_group = bpy.props.EnumProperty(
    items=[
        ("A", "A", "the first group to combine"),
        ("B", "B", "the second group to combine")
    ],
    name="Group",
    description="the combining group this object belongs to.  A is combined before B",
    default="A",
    update=update_sector
)
bpy.types.Object.is_sector = bpy.props.BoolProperty(
    name="Is Sector",
    default=False
)
bpy.types.Object.sector_type = bpy.props.EnumProperty(
    items=[
        ("PLANE", "2D Sector", "is a 2d sector plane"),
        ("NONE", "None", "marks the objet as not a sector") 
    ],
    name="Sector Type",
    description="the sector type",
    default='NONE'
)
bpy.types.Scene.bool_solver = bpy.props.EnumProperty(
    items=[
        ("FAST", "Fast", "Use Fast Solver"),
        ("EXACT", "Exact", "Use Exact Solver")     
    ],
    name="Boolean Solver",
    description="the solver",
    default='FAST'
)
bpy.types.Scene.map_name = bpy.props.StringProperty(
    name="Map Name",
    default="Map"
)
bpy.types.Scene.brush_material = bpy.props.StringProperty(
    name="Active Material",
    default=""
)

class ADDON_PT_LevelBuddyPanel(bpy.types.Panel):
    bl_label = "Level Buddy"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Buddy Tools"

    def draw(self, context):
        ob = context.active_object
        scn = bpy.context.scene
        layout = self.layout
        col = layout.column(align=True)
        col.label(icon="WORLD", text="Map Settings")
        col.prop(scn, "map_name", text="Name")     
        layout.separator()
        col = layout.column(align=True)
        col.label(icon="FILE_FOLDER", text="FBX Export Settings")
        col.prop(scn, "map_export_path", text="")
        col.operator("scene.level_buddy_build_map", text="Build & Export Map", icon="MOD_BUILD").map_export = True
        layout.separator()
        col = layout.column(align=True)
        col.label(icon="MODIFIER_ON", text="Toolbox")
        col.operator("scene.cut_all_sectors", text="Cut All Sector", icon="MOD_EXPLODE")        
        col.operator("scene.cut_sector", text="Cut Sector", icon="MOD_EXPLODE")
        layout.separator()
        col = layout.column(align=True)
        col.label(icon="MOD_BOOLEAN", text="Boolean Solver")
        col.prop(scn, "bool_solver", text="Solver")        
        layout.separator()
        col = layout.column(align=True)
        col.label(icon="SNAP_PEEL_OBJECT", text="New Sector")
        col.operator("scene.level_new_sector", text="New Sector", icon="SURFACE_NCURVE")
        layout.separator()
        col = layout.column(align=True)
        col.operator("scene.level_buddy_cleanup", icon="ERROR")
        col.operator("scene.level_buddy_empty_trash", icon="ERROR")
        layout.separator()
        col = layout.column(align=True)
        if ob is not None:
            col.label(icon="FORCE_LENNARDJONES", text="Sector Settings")
            col.prop(ob, "sector_type", text="Type")
            col.prop(ob, "sector_group", text="Group")
            layout.separator()
            col = layout.column(align=True)               
            if ob is not None and len(bpy.context.selected_objects) > 0:
                if ob.sector_type != 'NONE':
                    if ob.modifiers:
                        mod = ob.modifiers[0]
                        if mod.type == "SOLIDIFY":
                            col.label(icon="MOD_ARRAY", text="Sector Heights")
                            col.prop(ob, "ceiling_height")
                            col.prop(ob, "floor_height")
                            layout.separator()
                            col = layout.column(align=True)
                            col.label(icon="MATERIAL", text="Sector Materials")                                                   
                            op = col.operator("scene.textureset", text="Hub", icon="MATERIAL")
                            op.CeilingTexture="HUBCEILING"
                            op.FloorTexture="HUBFLOOR"
                            op.WallTexture="HUBWALL"
                            op = col.operator("scene.textureset", text="Hub Dark", icon="MATERIAL") 
                            op.CeilingTexture="HUBCEILINGDARK"
                            op.FloorTexture="HUBFLOORDARK"
                            op.WallTexture="HUBWALLDARK"                            
                            op = col.operator("scene.textureset", text="Room Red", icon="MATERIAL") 
                            op.CeilingTexture="ROOM1CEILING"
                            op.FloorTexture="ROOM1FLOOR"
                            op.WallTexture="ROOM1WALL"                              
                            op = col.operator("scene.textureset", text="Room Red Dark", icon="MATERIAL") 
                            op.CeilingTexture="ROOM1CEILINGDARK"
                            op.FloorTexture="ROOM1FLOORDARK"
                            op.WallTexture="ROOM1WALLDARK"                                
                            op = col.operator("scene.textureset", text="Room Yellow", icon="MATERIAL") 
                            op.CeilingTexture="ROOM2CEILING"
                            op.FloorTexture="ROOM2FLOOR"
                            op.WallTexture="ROOM2WALL"                            
                            op = col.operator("scene.textureset", text="Room Yellow Dark", icon="MATERIAL")    
                            op.CeilingTexture="ROOM2CEILINGDARK"
                            op.FloorTexture="ROOM2FLOORDARK"
                            op.WallTexture="ROOM2WALLDARK"                                
                            op = col.operator("scene.textureset", text="Room Blue", icon="MATERIAL") 
                            op.CeilingTexture="ROOM3CEILING"
                            op.FloorTexture="ROOM3FLOOR"
                            op.WallTexture="ROOM3WALL"                            
                            op = col.operator("scene.textureset", text="Room Blue Dark", icon="MATERIAL")
                            op.CeilingTexture="ROOM3CEILINGDARK"
                            op.FloorTexture="ROOM3FLOORDARK"
                            op.WallTexture="ROOM3WALLDARK"                                 
                            op = col.operator("scene.textureset", text="Exterior", icon="MATERIAL") 
                            op.CeilingTexture="EXTCEILING"
                            op.FloorTexture="EXTFLOOR"
                            op.WallTexture="EXTWALL"                            
                            op = col.operator("scene.textureset", text="Exterior 2", icon="MATERIAL")
                            op.CeilingTexture="EXT2CEILING"
                            op.FloorTexture="EXT2FLOOR"
                            op.WallTexture="EXT2WALL"                               

class ADDON_OT_CutAllSectors(bpy.types.Operator):
    bl_idname = "scene.cut_all_sectors"
    bl_label = "Cut All Sector"

    def execute(self, context): 
        bpy.ops.object.select_all(action='DESELECT') 
        bpy.ops.object.select_all(action='SELECT')  
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY') 
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.edge_split(type='EDGE')
        bpy.ops.mesh.separate(type='LOOSE')  
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')              
        return {"FINISHED"}

class ADDON_OT_CutSector(bpy.types.Operator):
    bl_idname = "scene.cut_sector"
    bl_label = "Cut Sector"

    def execute(self, context):           
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.edge_split(type='EDGE')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')
        return {"FINISHED"}
  
class ADDON_OT_LevelNewSector(bpy.types.Operator):
    bl_idname = "scene.level_new_sector"
    bl_label = "Level New Sector"

    def execute(self, context):
        scn = bpy.context.scene
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_plane_add(size=1,
                                         align='WORLD',
                                         calc_uvs=True,
                                         enter_editmode=False,
                                         location=(0, 0, 0)
                                         )
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].offset = 1
        bpy.context.object.modifiers["Solidify"].use_even_offset = True
        bpy.context.object.modifiers["Solidify"].use_quality_normals = True
        ob = bpy.context.active_object
        ob.name = "sector"
        ob.data.name = "sector"
        ob.ceiling_height = 4
        ob.floor_height = 0
        ob.sector_type = 'PLANE'
        ob.display_type = 'WIRE'
        bpy.context.object.hide_render = True
        update_sector_plane_materials(ob)
        bpy.ops.scene.textureset(CeilingTexture="HUBCEILING",FloorTexture="HUBFLOOR",WallTexture="HUBWALL")
        bpy.context.view_layer.objects.active = ob      
        bpy.ops.object.level_update_sector()
        return {"FINISHED"}

class ADDON_OT_LevelUpdateSector(bpy.types.Operator):
    bl_idname = "object.level_update_sector"
    bl_label = "Level Update Sector"

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            update_sector_plane_modifier(ob)
        return {"FINISHED"}

class ADDON_OT_LevelCleanupPrecision(bpy.types.Operator):
    bl_idname = "scene.level_buddy_cleanup"
    bl_label = "Level Cleanup Precision"

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for ob in selected_objects:
            update_location_precision(ob)
        return {"FINISHED"}

class ADDON_OT_LevelEmptyTrash(bpy.types.Operator):
    bl_idname = "scene.level_buddy_empty_trash"
    bl_label = "Level Empty Trash"

    def execute(self, context):
        for o in bpy.data.objects:
            if o.users == 0:
                bpy.data.objects.remove(o)
        for m in bpy.data.meshes:
            if m.users == 0:
                bpy.data.meshes.remove(m)
        return {"FINISHED"}

class ADDON_OT_LevelBuddyBuildMap(bpy.types.Operator):
    bl_idname = "scene.level_buddy_build_map"
    bl_label = "Level Buddy Build Map"

    bool_op : bpy.props.StringProperty(
        name="bool_op",
        default="UNION"
    )
    map_export : bpy.props.BoolProperty(
        name="map_export",
        default=False
    )

    def execute(self, context):
        scn = bpy.context.scene
        edit_mode = False
        edit_mode_object = None
        if bpy.context.active_object is not None:
            edit_mode_object = bpy.context.active_object.name
        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.object.editmode_toggle()
            edit_mode = True
        if self.bool_op == 'EXPORT':
            export_level_map()
        else:
            sector_list = []
            sector_list_b = []
            level_map = create_new_boolean_object(scn, scn.map_name)
            visible_objects = bpy.context.visible_objects
            for ob in visible_objects:
                if ob.type == 'MESH' and ob.sector_type != 'NONE' and ob != level_map:
                    if ob.sector_type == 'PLANE':
                        sector_list.append(ob.name)
            # sector A
            for x in sector_list:
                apply_boolean(level_map, x, 'UNION')                            
            # sector B
            for x in sector_list_b:
                apply_boolean(level_map, x, 'UNION')                           
            recalculate_normals_inside(level_map)    
            auto_texture(level_map)            
            # for x in range(10):
            if self.map_export:                
                export_level_map()
            level_map.hide_select = True
            bpy.ops.object.select_all(action='DESELECT')
            if edit_mode_object is not None:
                bpy.data.objects[edit_mode_object].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[edit_mode_object]
                if edit_mode:
                    bpy.ops.object.editmode_toggle()
        self.map_export = False
        return {"FINISHED"}

# TEXTURE BUDDY UV OPERATOR CLASS        
class ADDON_OT_TextureBuddyUV(bpy.types.Operator):
    bl_idname = "object.texture_buddy_uv"
    bl_label = "Texture Buddy UV"

    axis : bpy.props.StringProperty(name="Axis", default="AUTO")

    # EXECUTE OPERATOR
    def execute(self, context):
        obj = context.active_object
        me = obj.data
        objectLocation = context.active_object.location
        objectScale = context.active_object.scale
        texelDensity = context.scene.texel_density
        textureWidth = 64
        textureHeight = 64
        if bpy.context.mode == 'EDIT_MESH' or bpy.context.mode == 'OBJECT':
            was_obj_mode = False
            if bpy.context.mode == 'OBJECT':
                was_obj_mode = True
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')
            bm = bmesh.from_edit_mesh(me)
            uv_layer = bm.loops.layers.uv.verify()
            for f in bm.faces:
                if f.select:
                    bpy.ops.uv.select_all(action='SELECT')
                    matIndex = f.material_index
                    if len(obj.data.materials) > matIndex:
                        if obj.data.materials[matIndex] is not None:
                            nX = f.normal.x
                            nY = f.normal.y
                            nZ = f.normal.z
                            if nX < 0:
                                nX = nX * -1
                            if nY < 0:
                                nY = nY * -1
                            if nZ < 0:
                                nZ = nZ * -1
                            faceNormalLargest = nX
                            faceDirection = "x"
                            if faceNormalLargest < nY:
                                faceNormalLargest = nY
                                faceDirection = "y"
                            if faceNormalLargest < nZ:
                                faceNormalLargest = nZ
                                faceDirection = "z"
                            if faceDirection == "x":
                                if f.normal.x < 0:
                                    faceDirection = "-x"
                            if faceDirection == "y":
                                if f.normal.y < 0:
                                    faceDirection = "-y"
                            if faceDirection == "z":
                                if f.normal.z < 0:
                                    faceDirection = "-z"
                            if self.axis == "X":
                                faceDirection = "x"
                            if self.axis == "Y":
                                faceDirection = "y"
                            if self.axis == "Z":
                                faceDirection = "z"
                            if self.axis == "-X":
                                faceDirection = "-x"
                            if self.axis == "-Y":
                                faceDirection = "-y"
                            if self.axis == "-Z":
                                faceDirection = "-z"
                            for l in f.loops:
                                luv = l[uv_layer]
                                if luv.select and l[uv_layer].pin_uv is not True:
                                    if faceDirection == "x":
                                        luv.uv.x = ((l.vert.co.y * objectScale[1]) + objectLocation[
                                            1]) * texelDensity / textureWidth
                                        luv.uv.y = ((l.vert.co.z * objectScale[2]) + objectLocation[
                                            2]) * texelDensity / textureWidth
                                    if faceDirection == "-x":
                                        luv.uv.x = (((l.vert.co.y * objectScale[1]) + objectLocation[
                                            1]) * texelDensity / textureWidth) * -1
                                        luv.uv.y = ((l.vert.co.z * objectScale[2]) + objectLocation[
                                            2]) * texelDensity / textureWidth
                                    if faceDirection == "y":
                                        luv.uv.x = (((l.vert.co.x * objectScale[0]) + objectLocation[
                                            0]) * texelDensity / textureWidth) * -1
                                        luv.uv.y = ((l.vert.co.z * objectScale[2]) + objectLocation[
                                            2]) * texelDensity / textureWidth
                                    if faceDirection == "-y":
                                        luv.uv.x = ((l.vert.co.x * objectScale[0]) + objectLocation[
                                            0]) * texelDensity / textureWidth
                                        luv.uv.y = ((l.vert.co.z * objectScale[2]) + objectLocation[
                                            2]) * texelDensity / textureWidth
                                    if faceDirection == "z":
                                        luv.uv.x = ((l.vert.co.x * objectScale[0]) + objectLocation[
                                            0]) * texelDensity / textureWidth
                                        luv.uv.y = ((l.vert.co.y * objectScale[1]) + objectLocation[
                                            1]) * texelDensity / textureWidth
                                    if faceDirection == "-z":
                                        luv.uv.x = (((l.vert.co.x * objectScale[0]) + objectLocation[
                                            0]) * texelDensity / textureWidth) * 1
                                        luv.uv.y = (((l.vert.co.y * objectScale[1]) + objectLocation[
                                            1]) * texelDensity / textureWidth) * -1
                                    luv.uv.x = luv.uv.x - context.scene.offset_x
                                    luv.uv.y = luv.uv.y - context.scene.offset_y
            bmesh.update_edit_mesh(me)
            if was_obj_mode:
                bpy.ops.object.editmode_toggle()
        return {"FINISHED"}

classes = (
    ADDON_PT_LevelBuddyPanel,
    ADDON_OT_LevelBuddyBuildMap,
    ADDON_OT_CutAllSectors,
    ADDON_OT_CutSector,
    ADDON_OT_LevelNewSector,
    ADDON_OT_LevelUpdateSector,
    ADDON_OT_LevelCleanupPrecision,
    ADDON_OT_LevelEmptyTrash,
    ADDON_OT_TextureSet,
    ADDON_OT_TextureBuddyUV
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()