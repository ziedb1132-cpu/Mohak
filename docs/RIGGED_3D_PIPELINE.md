# Mohak Rigged 3D Animation Pilot

This workflow renders a real-time 3D scene in Blender on GitHub-hosted runners. It does not use a slideshow or pan/zoom over still images.

## Run it

1. Open the repository's **Actions** tab.
2. Select **Mohak - Rigged 3D Animation Pilot**.
3. Press **Run workflow**.
4. Choose 720p (recommended) and start the run.
5. When the workflow finishes, open its run page and download the **mohak-rigged-3d-pilot** artifact.

## What this first pilot proves

- Blender creates two 3D characters with armature skeletons.
- Character body parts are attached to named bones.
- Bone rotations are keyframed across 360 frames (15 seconds at 24 fps).
- The camera has its own animated push-in and drift.
- The courtyard environment uses 3D geometry and cinematic lighting.
- The result is encoded as an MP4 artifact.

## Important production boundary

This is a technical animation pilot, not yet a finished broadcast-quality series. The first characters are stylized procedural stand-ins. The next production stage is to replace them with approved, detailed character meshes and proper deformation rigs, add facial controls and Arabic phoneme-based lip sync, record/produce character-specific voices, and build reusable scene assets. GitHub Actions can run all of those steps, but rendering time and artifact size depend on the scene complexity and available runner resources.

The workflow is manual so a long render is never launched unexpectedly on every commit. GitHub-hosted runners have finite execution limits; this job is capped below six hours.
