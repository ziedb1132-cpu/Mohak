import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

def args_after_dashes():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/episode_001.mp4")
    return parser.parse_args(argv)

def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    return mat

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()

def add_character(name, x, coat, skin, hair, scale=1.0):
    coat_mat, skin_mat, hair_mat = coat, skin, hair
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(x, 0, 1.15*scale))
    body = bpy.context.object; body.name = name + "_Body"; body.scale = (0.42*scale, 0.27*scale, 0.65*scale); body.data.materials.append(coat_mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(x, -0.01, 2.05*scale))
    head = bpy.context.object; head.name = name + "_Head"; head.scale = (0.34*scale, 0.31*scale, 0.38*scale); head.data.materials.append(skin_mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=(x, 0.02, 2.34*scale))
    hair_obj = bpy.context.object; hair_obj.name = name + "_Hair"; hair_obj.scale = (0.35*scale, 0.31*scale, 0.19*scale); hair_obj.data.materials.append(hair_mat)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, location=(x+side*0.12*scale, -0.294*scale, 2.08*scale))
        eye=bpy.context.object; eye.name=name+"_Eye"; eye.scale=(0.035*scale,0.025*scale,0.05*scale); eye.data.materials.append(material("EyeWhite", (0.95,0.95,0.9)))
    return body

def build_scene(output):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    navy=material("Academy Navy",(0.025,0.055,0.12),0.25)
    blue=material("Adam Blue Suit",(0.035,0.12,0.32),0.1)
    black=material("Sami Dark Outfit",(0.035,0.045,0.065))
    purple=material("Leila Suit",(0.16,0.07,0.22))
    skin=material("Warm Skin",(0.72,0.43,0.29))
    hair=material("Dark Hair",(0.025,0.018,0.02))
    gold=material("Bitcoin Gold",(0.95,0.55,0.08),0.75,0.22)
    floor_mat=material("Floor",(0.012,0.02,0.045),0.35)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,0)); bpy.context.object.data.materials.append(floor_mat)
    # Main holographic display
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,2.0,3.1)); screen=bpy.context.object; screen.name="Market_Display"; screen.scale=(5.8,0.12,2.35); screen.data.materials.append(navy)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0,1.78,3.25)); coin=bpy.context.object; coin.name="Bitcoin_Hologram"; coin.scale=(0.78,0.12,0.78); coin.data.materials.append(gold)
    # Three stylized placeholder presenters
    add_character("Adam", -2.2, blue, skin, hair, 1.05)
    add_character("Sami", 0.0, black, skin, hair, 0.95)
    add_character("Leila", 2.2, purple, skin, hair, 1.0)
    # Accent lights
    for loc, color, power, size in [((-4,-3,6),(0.12,0.35,1),1300,5),((4,1,5),(1,0.55,0.18),1100,4),((0,-1,7),(0.55,0.7,1),900,5)]:
        bpy.ops.object.light_add(type="AREA", location=loc); light=bpy.context.object; light.data.energy=power; light.data.shape="DISK"; light.data.size=size; light.data.color=color; aim(light,(0,0,1.5))
    bpy.ops.object.camera_add(location=(0,-10,3.5)); cam=bpy.context.object; aim(cam,(0,0.6,1.7)); cam.data.lens=42; bpy.context.scene.camera=cam
    # Gentle camera push-in
    cam.location=(0,-12,3.8); cam.keyframe_insert(data_path="location",frame=1)
    cam.location=(0,-10,3.5); cam.keyframe_insert(data_path="location",frame=192)
    coin.rotation_euler[1]=0; coin.keyframe_insert(data_path="rotation_euler",frame=1)
    coin.rotation_euler[1]=math.tau; coin.keyframe_insert(data_path="rotation_euler",frame=192)
    scene=bpy.context.scene; scene.frame_start=1; scene.frame_end=192; scene.render.fps=24
    scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.world.color=(0.025,0.025,0.04)
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    out=Path(output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(out)
    bpy.ops.render.render(animation=True)
    print("ANIMATION_RENDER_COMPLETE", out)

if __name__ == "__main__":
    opts=args_after_dashes()
    build_scene(opts.output)
