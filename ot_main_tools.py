import bpy
from bpy.app.handlers import persistent
import random

def add_final_render_settings(self, context):
    preferences = context.preferences.addons[__package__].preferences
    if preferences.show_render_overrides:
        layout = self.layout
        col = layout.column()
        col.label(text = "For Final Render Use ...")
        prop_afrs_1 = col.prop(context.scene.otmain_props, "use_cameraimager_render_mode", text = " Camera Imager (Render Mode)")
        prop_afrs_2 = col.prop(context.scene.otmain_props, "use_postprocessing_render_mode", text = " Post Processing (Render Mode)")
        col.separator(factor = 1)

@persistent
def render_start_handler(scene):
    print('Start Rendering')
    scene.otmain_globals.old_cameraimager_preview_setting = scene.octane.use_preview_setting_for_camera_imager
    scene.otmain_globals.old_postprocessing_preview_setting = scene.octane.use_preview_post_process_setting

    if bpy.context.preferences.addons[__package__].preferences.show_render_overrides == False:
        print('OFF')
        return False

    if scene.otmain_props.use_cameraimager_render_mode:
        scene.octane.use_preview_setting_for_camera_imager = False
    if scene.otmain_props.use_postprocessing_render_mode:
        scene.octane.use_preview_post_process_setting = False

@persistent
def render_stop_handler(scene):
    print('Stopped Rendering')
    scene.octane.use_preview_setting_for_camera_imager = scene.otmain_globals.old_cameraimager_preview_setting
    scene.octane.use_preview_post_process_setting = scene.otmain_globals.old_postprocessing_preview_setting

class OCTTOOLS_OT_COPY_OCTANE_OBJECT_COLOR(bpy.types.Operator):
    bl_idname = "octanetools.copy_octane_object_color"
    bl_label = "Copy Octane Object Settings"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        for i in range(len(bpy.context.view_layer.objects.selected)):
            bpy.context.view_layer.objects.selected[i].octane.color = bpy.context.active_object.octane.color

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class OCTTOOLS_OT_SET_RANDOM_COLOR_SEED(bpy.types.Operator):
    bl_idname = "octanetools.set_random_color_seed"
    bl_label = "Set Random Color Seed"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 0, 0) and False:
            cls.poll_message_set()
        return not False

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for iobject in selected_objects:
            iobject.octane.random_color_seed = random.randint(0, 10000)
            iobject.data.update()

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class OCTTOOLS_PT_MAIN_TOOLS(bpy.types.Panel):
    bl_label = 'Main Tools'
    bl_idname = 'OCTTOOLS_PT_main_tools'
    bl_space_type = 'VIEW_3D'
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
        box.separator(factor = 0.2)
        op1 = box.operator('octanetools.set_random_color_seed', text='Randomize Random Color Seed', icon_value=54, emboss=True, depress=False)
        op2 = box.operator('octanetools.copy_octane_object_color', text='Copy Object Color From Active', icon_value=20, emboss=True, depress=False)
        box.separator(factor = 0.2)

class OCTTOOLS_PROP_OTMAIN_PROPERTIES(bpy.types.PropertyGroup):
         
    use_cameraimager_render_mode: bpy.props.BoolProperty(
        name="Use Camera Imager (Render Mode)",
        description="For final rendering use the settins from Camera Imager (Render Mode)",
        default=False,
    ) 

    use_postprocessing_render_mode: bpy.props.BoolProperty(
        name="Use Post Processing (Render Mode)",
        description="For final rendering use the settins from Post Processing (Render Mode)",
        default=False,
    ) 

class OCTTOOLS_PROP_OTMAIN_GLOBALS(bpy.types.PropertyGroup):

    old_cameraimager_preview_setting: bpy.props.BoolProperty(
        name="Old Camera Imager Settings",
        default=False,
    )

    old_postprocessing_preview_setting: bpy.props.BoolProperty(
        name="Old Camera Imager Settings",
        default=False,
    )

classes = (OCTTOOLS_PROP_OTMAIN_PROPERTIES, OCTTOOLS_PROP_OTMAIN_GLOBALS, OCTTOOLS_OT_COPY_OCTANE_OBJECT_COLOR, OCTTOOLS_OT_SET_RANDOM_COLOR_SEED, OCTTOOLS_PT_MAIN_TOOLS)

def main_tools_register():
    from bpy.utils import register_class  
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.render_init.append(render_start_handler)
    bpy.app.handlers.render_complete.append(render_stop_handler)
    bpy.app.handlers.render_cancel.append(render_stop_handler)
    bpy.types.Scene.otmain_props = bpy.props.PointerProperty(type = OCTTOOLS_PROP_OTMAIN_PROPERTIES)
    bpy.types.Scene.otmain_globals = bpy.props.PointerProperty(type = OCTTOOLS_PROP_OTMAIN_GLOBALS)
    bpy.types.OCTANE_VIEW3D_PT_override.prepend(add_final_render_settings)

def main_tools_unregister():
    from bpy.utils import unregister_class  
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.otmain_props
    del bpy.types.Scene.otmain_globals
    bpy.types.OCTANE_VIEW3D_PT_override.remove(add_final_render_settings)
    bpy.app.handlers.render_init.clear()
    bpy.app.handlers.render_complete.clear()
    bpy.app.handlers.render_cancel.clear()