#!/usr/bin/env python3
"""Procedural cinematic 3D animatic for the 3-minute Qutuz episode."""
import argparse
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
SCENE_SECONDS = 15
TOTAL_SCENES = 12
END_FRAME = FPS * SCENE_SECONDS * TOTAL_SCENES
ACTIVE_OBJECTS = []

def cli():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="output/episode_001_silent.mp4")
    p.add_argument("--scene-index", type=int, default=0)
    p.add_argument("--resolution-scale", type=int, default=75)
    p.add_argument("--benchmark-frames", type=int, default=0)
    p.add_argument("--eevee-samples", type=int, default=16)
    return p.parse_args(argv)

def mat(name, color, metallic=0.0, rough=0.65, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = rough
    if emission:
        bs.inputs["Emission Color"].default_value = (*color, 1)
        bs.inputs["Emission Strength"].default_value = emission
    return m

def track(obj):
    ACTIVE_OBJECTS.append(obj)
    return obj

def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = track(bpy.context.object)
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new("Soft_Edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return o

def sphere(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc)
    o = track(bpy.context.object)
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    return o

def cone(name, loc, radius, depth, material, vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=0, depth=depth, location=loc)
    o = track(bpy.context.object)
    o.name = name
    o.data.materials.append(material)
    return o

def text_obj(body, loc, size, material, name="Caption"):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    o = track(bpy.context.object)
    o.name = name
    o.data.body = body
    o.data.size = size
    o.data.align_x = "CENTER"
    o.data.extrude = 0.003
    o.data.materials.append(material)
    return o

def humanoid(name, x, y, robe, metal, scale=1.0, helmet=True):
    # Stylized, non-photorealistic historical figure; no claim of portrait accuracy.
    sphere(name+"_Torso", (x,y,1.55*scale), (.48*scale,.30*scale,.72*scale), robe)
    sphere(name+"_Head", (x,y,2.48*scale), (.31*scale,.29*scale,.36*scale), skin)
    if helmet:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=(x,y,2.72*scale))
        h=track(bpy.context.object); h.name=name+"_Helmet"; h.scale=(.34*scale,.32*scale,.20*scale); h.data.materials.append(metal)
        cone(name+"_Helmet_Crest",(x,y,2.98*scale),.09*scale,.42*scale,gold,8)
    else:
        sphere(name+"_Hair",(x,y,2.72*scale),(.33*scale,.30*scale,.16*scale),dark)
    for side in (-1,1):
        sphere(name+"_Arm",(x+side*.49*scale,y,1.75*scale),(.16*scale,.18*scale,.48*scale),robe)
        sphere(name+"_Boot",(x+side*.22*scale,y-.01,.22*scale),(.19*scale,.28*scale,.22*scale),leather)
    return name

def horse(name, x, y, coat):
    sphere(name+"_Body",(x,y,1.0),(.95,.32,.48),coat)
    sphere(name+"_Neck",(x+.62,y,1.48),(.27,.25,.68),coat).rotation_euler[1]=-.42
    sphere(name+"_Head",(x+.86,y,1.9),(.24,.22,.36),coat)
    for dx in (-.55,.45):
        for dy in (-.19,.19):
            cube(name+"_Leg",(x+dx,y+dy,.48),(.13,.14,.88),coat)
    sphere(name+"_Mane",(x+.53,y,1.68),(.13,.26,.5),dark)

def scene_group(index, title, subtitle, style):
    start = (index-1)*SCENE_SECONDS*FPS + 1
    end = index*SCENE_SECONDS*FPS
    before = {obj.name for obj in bpy.data.objects}
    # Stage-specific scenery
    if style == "map":
        cube("Map_Parchment",(0,1,.1),(17,10,.12),sand)
        for x,y in [(-5,1),(0,0),(4,2),(6,-1)]:
            sphere("Map_City",(x,y,.32),(.55,.42,.18),gold)
            cone("Map_Dome",(x,y,.65),.36,.42,ivory)
        text_obj("المشرق الإسلامي · القرن السابع الهجري",(0,-3,1.1),.52,ivory)
        for x in (-6,-3,1,4):
            cube("Route",(x,0,.28),(.08,5,.035),red)
    elif style == "origins":
        cube("Steppe",(0,2,-.2),(18,12,.3),sand)
        for x in (-6,-3,0,3,6):
            cone("Distant_Hill",(x,4,.6),2.5,2.5,ochre,16)
        for x in (-2,0,2):
            cube("Caravan_Crate",(x,0,.65),(.8,.8,.9),leather,.08)
        humanoid("Young_Traveler",0,-1,robe,metal,.8,False)
    elif style == "training":
        cube("Training_Ground",(0,1,-.2),(18,12,.3),sand)
        for x in (-5,-2,2,5):
            humanoid("Mamluk_Trainer_"+str(x),x,0,robe,metal,.9)
            cube("Practice_Target",(x,2,1.3),(.12,.12,2.6),wood)
    elif style == "citadel":
        cube("Citadel_Base",(0,2,1),(12,2,2),stone)
        for x in (-5,-2,2,5):
            cube("Citadel_Tower",(x,2,2.6),(1.4,2.2,4),stone,.12)
            cube("Tower_Crenel",(x,1.9,4.7),(1.7,2.3,.35),gold)
        humanoid("Sultan_Qutuz",0,-1,robe,metal,1.15)
        text_obj("القاهرة · 1259م",(0,-3,1.1),.6,ivory)
    elif style == "invasion":
        cube("Burnished_Plain",(0,2,-.2),(18,12,.3),charcoal)
        for x in (-6,-3,0,3,6):
            cube("Distant_Wall",(x,3,1.2),(2.2,.5,2.4),stone)
        for x in (-5,-2,1,4):
            humanoid("Mongol_Silhouette_"+str(x),x,0,red,metal,.9)
    elif style == "council":
        cube("War_Room_Floor",(0,1,0),(12,9,.25),stone)
        cube("War_Table",(0,0,1.0),(5,2.4,.25),wood)
        cube("Map_Table",(0,-.02,1.16),(4.6,2,.04),sand)
        humanoid("Qutuz_Council",0,-2,robe,metal,1.05)
        for x in (-3,3):
            humanoid("Emir_"+str(x),x,-1,robe,metal,.85)
        text_obj("قرار المواجهة",(0,-3.5,1.1),.65,gold)
    elif style == "forge":
        cube("Forge_Floor",(0,1,-.2),(18,12,.3),charcoal)
        for x in (-4,0,4):
            cube("Anvil",(x,0,.65),(1.3,.8,.5),metal)
            sphere("Forge_Fire",(x,-.1,1.25),(.32,.24,.35),fire)
            humanoid("Armorer_"+str(x),x,-2,robe,metal,.85,False)
    elif style == "march":
        cube("Desert_Road",(0,2,-.3),(20,15,.4),sand)
        for x in (-6,-3,0,3,6):
            cone("Dune_"+str(x),(x,5,.4),3,2,sand,16)
            horse("Mamluk_Horse_"+str(x),x,-1,leather)
            humanoid("Mamluk_Rider_"+str(x),x,-1,robe,metal,.8)
    elif style == "ainjalut":
        cube("Ain_Jalut_Plain",(0,2,-.2),(20,14,.3),sand)
        for x in (-6,-4,-2,2,4,6):
            horse("Mamluk_Cavalry_"+str(x),x,-1,leather)
            humanoid("Mamluk_Rider_"+str(x),x,-1,robe,metal,.75)
        text_obj("عين جالوت · 3 سبتمبر 1260م",(0,-4,1.0),.65,ivory)
    elif style == "battle":
        cube("Battlefield",(0,2,-.2),(20,14,.3),sand)
        for x in (-6,-4,-2,2,4,6):
            horse("Battle_Horse_"+str(x),x,-1,leather)
            humanoid("Battle_Rider_"+str(x),x,-1,robe,metal,.78)
        for x in (-5,-1,3,6):
            cone("Dust_Cloud",(x,1,2.8),1.2,2.4,ochre,12)
    elif style == "victory":
        cube("Victory_Plain",(0,2,-.2),(20,14,.3),sand)
        for x in (-5,-2,2,5):
            cube("Mamluk_Standard",(x,0,3),(.08,.08,3.2),wood)
            cube("Standard_Flag",(x-.45,0,4.2),(.9,.08,.55),gold)
        humanoid("Qutuz_Victory",0,-2,robe,metal,1.1)
        text_obj("انتصار المماليك",(0,-4,1.0),.72,gold)
    elif style == "legacy":
        cube("Sunset_Land",(0,2,-.2),(20,14,.3),sand)
        sphere("Setting_Sun",(5,3,5),(1.3,.35,1.3),fire)
        for x in (-5,-2,2,5):
            cone("Distant_Dome",(x,3,1.2),1.4,2.4,stone,16)
        humanoid("Qutuz_Last_Ride",0,-1,robe,metal,1.0)
        text_obj("قطز · عين جالوت · 658هـ / 1260م",(0,-4,1.0),.58,ivory)

    text_obj(title,(0,-7.0,6.1),.72,gold,"Scene_Title")
    text_obj(subtitle,(0,-7.0,5.45),.36,ivory,"Scene_Subtitle")
    after = {obj.name for obj in bpy.data.objects}
    created = [bpy.data.objects[name] for name in (after-before)]
    for obj in created:
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=1)
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_render", frame=start)
        obj.hide_render = False
        obj.keyframe_insert(data_path="hide_render", frame=end)
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=min(END_FRAME,end+1))
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"

def build(output, scene_index=0, resolution_scale=75, benchmark_frames=0, eevee_samples=16):
    global skin, robe, metal, gold, sand, ochre, stone, ivory, red, charcoal, wood, leather, fire, dark
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    global ACTIVE_OBJECTS
    ACTIVE_OBJECTS=[]
    skin=mat("Skin",(.48,.27,.18))
    robe=mat("Mamluk_Deep_Teal",(.045,.16,.16),.18)
    metal=mat("Aged_Steel",(.28,.34,.38),.72,.28)
    gold=mat("Antique_Gold",(.72,.43,.12),.7,.28)
    sand=mat("Desert_Sand",(.47,.31,.17))
    ochre=mat("Dune_Ochre",(.31,.19,.11))
    stone=mat("Citadel_Stone",(.28,.25,.21))
    ivory=mat("Ivory",(.88,.79,.61),emission=.22)
    red=mat("Mongol_Red",(.32,.055,.035))
    charcoal=mat("Charcoal",(.055,.045,.04))
    wood=mat("Dark_Wood",(.18,.095,.045))
    leather=mat("Horse_Leather",(.20,.09,.045))
    fire=mat("Fire_Glow",(1,.23,.035),emission=1.8)
    dark=mat("Hair",(.035,.025,.02))
    # Ground and lighting remain visible through all twelve scene groups.
    cube("Master_Ground",(0,3,-.65),(30,24,.5),charcoal)
    bpy.ops.object.light_add(type="AREA",location=(-6,-7,12))
    key=bpy.context.object; key.data.energy=1700; key.data.shape="DISK"; key.data.size=9
    key.rotation_euler=(math.radians(25),0,math.radians(-25))
    bpy.ops.object.light_add(type="AREA",location=(7,3,8))
    rim=bpy.context.object; rim.data.energy=1100; rim.data.color=(1,.55,.24); rim.data.size=7
    bpy.ops.object.camera_add(location=(0,-20,8))
    cam=bpy.context.object; cam.data.lens=48
    cam.rotation_euler=(math.radians(76),0,0)
    bpy.context.scene.camera=cam
    scenes=[
      ("عاصفة فوق المشرق","القرن السابع الهجري","map"),
      ("بدايات مجهولة التفاصيل","من أصول خوارزمية إلى عالم المماليك","origins"),
      ("طريق القيادة","التدريب والخبرة العسكرية","training"),
      ("سلطان في زمن الخطر","القاهرة · 1259م","citadel"),
      ("تهديد المغول","الخطر يقترب من مصر والشام","invasion"),
      ("قرار المواجهة","توحيد الصفوف والاستعداد","council"),
      ("الاستعداد للحملة","الفرسان والدروع والخيول","forge"),
      ("المسير إلى فلسطين","جيش المماليك شمالاً","march"),
      ("لقاء عين جالوت","3 سبتمبر 1260م","ainjalut"),
      ("ساعات الحسم","المواجهة بين الجيشين","battle"),
      ("نتيجة المعركة","انتصار المماليك","victory"),
      ("نهاية السلطان وبقاء الأثر","قطز · عين جالوت · 658هـ","legacy"),
    ]
    if scene_index < 0 or scene_index > len(scenes):
        raise ValueError("scene-index must be 0..12")
    selected = range(1, len(scenes)+1) if scene_index == 0 else (scene_index,)
    for i in selected:
        title,sub,style = scenes[i-1]
        scene_group(i,title,sub,style)
        frame=(i-1)*SCENE_SECONDS*FPS+1
        cam.location=(0,-20-(i%3)*1.2,8+(i%2)*.5)
        cam.keyframe_insert(data_path="location",frame=frame)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation="BEZIER"
    scene=bpy.context.scene
    if scene_index:
        scene.frame_start=(scene_index-1)*SCENE_SECONDS*FPS+1
        scene.frame_end=scene_index*SCENE_SECONDS*FPS
    else:
        scene.frame_start=1
        scene.frame_end=END_FRAME
    scene.render.fps=FPS
    scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=max(25,min(100,resolution_scale))
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version >= (4,2,0) else "BLENDER_EEVEE"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples=max(1,eevee_samples)
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing=False
    scene.world.color=(.025,.018,.012)
    scene.view_settings.view_transform="Standard"
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="MEDIUM"
    scene.render.film_transparent=False
    out=Path(output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(out)
    if benchmark_frames > 0:
        if scene_index == 0:
            raise ValueError("benchmark mode requires --scene-index")
        scene.frame_end=min(scene.frame_end,scene.frame_start+benchmark_frames-1)
    expected_frames=scene.frame_end-scene.frame_start+1
    started=time.perf_counter()
    bpy.ops.render.render(animation=True)
    elapsed=time.perf_counter()-started
    if not out.exists() or out.stat().st_size==0:
        raise RuntimeError("Render produced no MP4: "+str(out))
    rendered_frames = scene.frame_end - scene.frame_start + 1
    fps_rendered=rendered_frames/elapsed if elapsed > 0 else 0
    print("QUTUZ_RENDER_METRICS",{"scene":scene_index or "all","frames":rendered_frames,"seconds":round(elapsed,2),"frames_per_second":round(fps_rendered,3),"estimated_360_frame_minutes":round(360/max(fps_rendered,0.001)/60,2),"resolution_percentage":scene.render.resolution_percentage,"eevee_samples":eevee_samples,"benchmark":benchmark_frames>0})
    print("QUTUZ_ANIMATIC_RENDER_COMPLETE",out,out.stat().st_size,"frames",rendered_frames,"scene",scene_index or "all")

if __name__=="__main__":
    args = cli()
    build(args.output, args.scene_index, args.resolution_scale, args.benchmark_frames, args.eevee_samples)
