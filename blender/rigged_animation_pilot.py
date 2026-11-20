#!/usr/bin/env python3
"""Create a 15-second rigged 3D animation pilot for Mohak (Blender 4.5+)."""
import argparse, math, os, sys
from pathlib import Path
import bpy
from mathutils import Vector

FPS = 24
DURATION = 15
FRAMES = FPS * DURATION

def args():
    av = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="output/mohak_pilot_001.mp4")
    p.add_argument("--resolution", type=int, default=720)
    p.add_argument("--samples", type=int, default=24)
    return p.parse_args(av)

def material(name, color, metallic=0.0, roughness=0.55):
    m = bpy.data.materials.new(name); m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    return m

def sphere(name, location, scale, mat, parent=None, bone=None, bevel=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
    if parent and bone:
        world = o.matrix_world.copy()
        o.parent = parent; o.parent_type = "BONE"; o.parent_bone = bone
        o.matrix_world = world
    return o

def cylinder_between(name, a, b, radius, mat, parent=None, bone=None):
    mid = (Vector(a)+Vector(b))/2
    vec = Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=vec.length, location=mid)
    o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"
    o.rotation_quaternion=vec.to_track_quat("Z","Y")
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
    bevel=o.modifiers.new("Soft silhouette","BEVEL"); bevel.width=radius*.22; bevel.segments=3
    if parent and bone:
        world=o.matrix_world.copy(); o.parent=parent; o.parent_type="BONE"; o.parent_bone=bone; o.matrix_world=world
    return o

def make_character(name, x, palette, with_cape=False):
    skin, cloth, trim, metal, hair, leather = palette
    arm_data=bpy.data.armatures.new(name+"_Skeleton")
    arm=bpy.data.objects.new(name+"_Rig",arm_data); bpy.context.collection.objects.link(arm)
    arm.location=(x,0,0); arm.show_in_front=True
    bpy.context.view_layer.objects.active=arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones={}
    def bone(n, head, tail, parent=None):
        b=arm_data.edit_bones.new(n); b.head=head; b.tail=tail
        if parent: b.parent=arm_data.edit_bones[parent]
        bones[n]=b
    bone("root",(0,0,.12),(0,0,.55))
    bone("spine",(0,0,.55),(0,0,1.55),"root")
    bone("head",(0,0,1.55),(0,0,2.15),"spine")
    for side,sgn in (("L",-1),("R",1)):
        bone("upper_arm."+side,(sgn*.28,0,1.42),(sgn*.62,0,1.05),"spine")
        bone("forearm."+side,(sgn*.62,0,1.05),(sgn*.72,0,.72),"upper_arm."+side)
        bone("thigh."+side,(sgn*.16,0,.58),(sgn*.20,0,.30),"root")
        bone("shin."+side,(sgn*.20,0,.30),(sgn*.20,-.02,.08),"thigh."+side)
    bpy.ops.object.mode_set(mode="OBJECT"); arm.select_set(False)
    # All visible pieces are attached to actual deform rig bones, not animated still images.
    sphere(name+"_Torso",(x,0,1.05),(.43,.27,.62),cloth,arm,"spine")
    sphere(name+"_Chest",(x,-.015,1.40),(.39,.27,.25),trim,arm,"spine")
    sphere(name+"_Head",(x,0,1.83),(.27,.25,.32),skin,arm,"head")
    sphere(name+"_Hair",(x,0,2.02),(.28,.26,.17),hair,arm,"head")
    sphere(name+"_Helmet",(x,0,2.08),(.29,.27,.15),metal,arm,"head")
    sphere(name+"_Belt",(x,-.01,.72),(.40,.28,.09),trim,arm,"spine")
    for side,sgn in (("L",-1),("R",1)):
        cylinder_between(name+"_UpperArm_"+side,(x+sgn*.32,0,1.38),(x+sgn*.60,0,1.06),.13,cloth,arm,"upper_arm."+side)
        sphere(name+"_Elbow_"+side,(x+sgn*.60,0,1.06),(.14,.14,.14),trim,arm,"forearm."+side)
        cylinder_between(name+"_Forearm_"+side,(x+sgn*.60,0,1.06),(x+sgn*.71,0,.76),.105,metal,arm,"forearm."+side)
        sphere(name+"_Hand_"+side,(x+sgn*.72,0,.72),(.11,.10,.13),skin,arm,"forearm."+side)
        cylinder_between(name+"_Thigh_"+side,(x+sgn*.16,0,.58),(x+sgn*.20,0,.30),.16,cloth,arm,"thigh."+side)
        cylinder_between(name+"_Shin_"+side,(x+sgn*.20,0,.30),(x+sgn*.20,-.02,.08),.105,leather,arm,"shin."+side)
        sphere(name+"_Boot_"+side,(x+sgn*.20,-.10,.09),(.15,.25,.11),leather,arm,"shin."+side)
    if with_cape:
        sphere(name+"_Cape",(x,.20,1.05),(.46,.12,.64),cloth,arm,"spine")
    arm["rig_type"]="Mohak_Humanoid_v1"
    return arm

def key_pose(arm, frame, action):
    bpy.context.view_layer.objects.active=arm
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_mode="XYZ"
        pb.rotation_euler=(0,0,0)
    if action=="walk":
        phase=(frame/FPS)*math.tau*1.25
        for side,sgn in (("L",1),("R",-1)):
            arm.pose.bones["thigh."+side].rotation_euler[0]=math.sin(phase)*.42*sgn
            arm.pose.bones["shin."+side].rotation_euler[0]=max(0,-math.sin(phase)*.48)
            arm.pose.bones["upper_arm."+side].rotation_euler[0]=-math.sin(phase)*.30*sgn
        arm.pose.bones["spine"].rotation_euler[1]=math.sin(phase)*.035
    elif action=="address":
        arm.pose.bones["upper_arm.R"].rotation_euler[1]=-.95
        arm.pose.bones["forearm.R"].rotation_euler[1]=-.35
        arm.pose.bones["head"].rotation_euler[1]=-.08
        arm.pose.bones["spine"].rotation_euler[1]=.04
    elif action=="listen":
        arm.pose.bones["head"].rotation_euler[1]=.12
        arm.pose.bones["upper_arm.L"].rotation_euler[1]=-.22
    for pb in arm.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler",frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")

def main():
    a=args(); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    skin=material("Warm skin",(.48,.25,.16)); teal=material("Qutuz deep teal",(.025,.12,.13))
    gold=material("Antique gold",(.68,.43,.13),.65,.3); steel=material("Aged steel",(.25,.31,.35),.75,.28)
    hair=material("Dark hair",(.035,.022,.016)); leather=material("Leather",(.16,.065,.03))
    stone=material("Citadel sandstone",(.29,.22,.15)); ground=material("Courtyard",(.105,.09,.075))
    sky=material("Backdrop",(.018,.035,.06))
    # Environment: courtyard, walls, arches and warm practical lights.
    sphere("Distant moon",(5,5,7),(1.2,.25,1.2),gold)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,0))
    floor=bpy.context.object; floor.name="Courtyard floor"; floor.data.materials.append(ground)
    for xx in (-7,7):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(xx,3,3))
        wall=bpy.context.object; wall.name="Citadel wall"; wall.dimensions=(.5,12,6); wall.data.materials.append(stone)
        bevel=wall.modifiers.new("Worn edges","BEVEL"); bevel.width=.12; bevel.segments=3
    for xx in (-5,-2.5,2.5,5):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(xx,3,5.2))
        tower=bpy.context.object; tower.name="Battlement"; tower.dimensions=(1.1,1.1,1.4); tower.data.materials.append(stone)
    qutuz=make_character("Qutuz",-1.35,(skin,teal,gold,steel,hair,leather),True)
    guard=make_character("Mamluk_guard",1.35,(skin,steel,gold,teal,hair,leather),False)
    # Grounded movement and clear acting beats: approach, turn, address, reaction.
    for frame in (1,36,72,108,144,180,216,252,288,324,360):
        t=(frame-1)/(FRAMES-1)
        qutuz.location.x=-2.2+0.45*math.sin(t*math.pi)
        qutuz.keyframe_insert(data_path="location",frame=frame)
        guard.location.x=1.65-0.25*math.sin(t*math.pi)
        guard.keyframe_insert(data_path="location",frame=frame)
    for f in range(1,FRAMES+1,12):
        key_pose(qutuz,f,"walk" if f<84 else ("address" if f<250 else "listen"))
        key_pose(guard,f,"listen" if f<190 else "address")
    # A separate animated camera rig; slow push-in and slight lateral drift.
    bpy.ops.object.camera_add(location=(0,-10,3.2)); cam=bpy.context.object
    cam.data.lens=48; target=Vector((0,0,1.15))
    direction=target-Vector(cam.location); cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    bpy.context.scene.camera=cam
    for f,loc in ((1,(0,-10,3.2)),(180,(-.35,-8.8,3.0)),(360,(.25,-7.6,2.8))):
        cam.location=loc; cam.keyframe_insert(data_path="location",frame=f)
        direction=target-Vector(loc); cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
        cam.keyframe_insert(data_path="rotation_euler",frame=f)
    # Cinematic lighting.
    bpy.ops.object.light_add(type="AREA",location=(-4,-5,8)); key=bpy.context.object
    key.data.energy=1500; key.data.shape="DISK"; key.data.size=6
    key.rotation_euler=(math.radians(25),0,math.radians(-20))
    bpy.ops.object.light_add(type="AREA",location=(4,2,6)); rim=bpy.context.object
    rim.data.energy=1900; rim.data.color=(1,.55,.24); rim.data.size=4
    rim.rotation_euler=(math.radians(20),0,math.radians(150))
    scene=bpy.context.scene; scene.frame_start=1; scene.frame_end=FRAMES; scene.render.fps=FPS
    scene.render.resolution_x=1280; scene.render.resolution_y=720
    scene.render.resolution_percentage=100 if a.resolution>=720 else 75
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="GOOD"
    scene.render.filepath=str(out.resolve()); scene.render.use_file_extension=True
    scene.render.image_settings.color_mode="RGB"
    scene.view_settings.view_transform="AgX"
    scene.render.film_transparent=False
    scene.world.color=(.025,.025,.025)
    # Smooth motion interpolation.
    for obj in (qutuz,guard,cam):
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation="BEZIER"
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)
    if not out.exists() or out.stat().st_size<100000:
        raise RuntimeError("Render output missing or unexpectedly small")
    print(f"MOHAK_RIGGED_PILOT_OK path={out} frames={FRAMES} fps={FPS} seconds={DURATION}")
    print("RIG_CHECK",qutuz.get("rig_type"),guard.get("rig_type"))

if __name__=="__main__": main()
