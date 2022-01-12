from typing import List

import bpy

import bmesh

from .bmesh import bm_yield_loose_parts


def obj_mesh_copy(obj: bpy.types.Object):
    bm = bmesh.new(use_operators=False)
    bm.from_mesh(obj.data)
    new_mesh = bpy.data.meshes.new(obj.name + "_copy")
    bm.to_mesh(new_mesh)
    new_mesh.update()
    new_obj = bpy.data.objects.new(obj.name + "_copy", new_mesh)
    new_obj.use_fake_user = True
    return new_obj


def obj_get_loose_parts(obj: bpy.types.Object):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    loose_parts = [region.to_obj(obj.name) for region in bm_yield_loose_parts(bm)]
    bm.free()
    return loose_parts


def obj_join_mesh_objects(objs: List[bpy.types.Object]):
    bm = bmesh.new(use_operators=False)

    for obj in objs:
        if obj.type != "MESH":
            bm.free()
            raise RuntimeError("Only mesh objects can be joined together")
        bm.from_mesh(obj.data)

    joined_mesh = bpy.data.meshes.new("Joined Mesh Object")
    joined_obj = bpy.data.objects.new(joined_mesh.name, joined_mesh)
    joined_obj.use_fake_user = True
    bm.to_mesh(joined_mesh)
    joined_mesh.update()
    bm.free()

    return joined_obj


# workaround annoying issue where sometimes view3d poll fails
def view_selected_all_regions(context: bpy.types.Context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for region in area.regions:
                if region.type != "WINDOW":
                    continue
                bpy.ops.view3d.view_selected({"region": region, "area": area})


def focus_viewport(context: bpy.types.Context, target_objs: List[bpy.types.Object]):
    """Hide all other objects, show the targets and focus viewport on them"""
    obj: bpy.types.Object
    for obj in context.view_layer.objects:
        obj.hide_set(True, view_layer=context.view_layer)

    for obj in target_objs:
        obj.hide_set(False, view_layer=context.view_layer)
        obj.select_set(True, view_layer=context.view_layer)

    view_selected_all_regions(context)


def ensure_object_mode(context: bpy.types.Context):
    ctx = context.copy()
    if bpy.ops.object.mode_set.poll(ctx):
        bpy.ops.object.mode_set(ctx, mode="OBJECT")

    if context.mode != "OBJECT":
        raise RuntimeError("Failed to ensure Object mode")


def select_object(context: bpy.types.Context, obj: bpy.types.Object):
    if obj is None:
        return
    # objects cannot be selected if they are not linked to a collection in the active view layer
    if obj.name not in context.view_layer.objects:
        context.scene.collection.objects.link(obj)
    obj.hide_set(False)  # objects cannot be selected if they are hidden
    obj.select_set(True)


def activate_object(context: bpy.types.Context, obj: bpy.types.Object):
    select_object(context, obj)  # objects cannot be active if they are not selected
    context.view_layer.objects.active = obj
