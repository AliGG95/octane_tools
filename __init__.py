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
    "name": "Octane Tools",
    "author": "Your Name",
    "description": "Tools for Octane Render in Blender",
    "blender": (4, 0, 0),
    "version": (1, 0),
    "location": "View3D > Sidebar > Octane Tools & Node Editor > Sidebar > Octane Tools",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "3D View"
}

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences

class OctaneToolsPreferences(AddonPreferences):
    bl_idname = __package__

    show_render_overrides: BoolProperty(
        name="Show Render Overrides",
        description="Show render override options in the UI",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "show_render_overrides")

# List of classes for registration
classes = (OctaneToolsPreferences,)

def register():
    # Register preferences first
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Now import and register the tools
    from . import ot_material_tools
    ot_material_tools.register()

def unregister():
    # Import for unregistration
    from . import ot_material_tools
    ot_material_tools.unregister()
    
    # Unregister preferences
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()