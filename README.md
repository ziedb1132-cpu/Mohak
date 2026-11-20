# Crypto Animation Studio

A Python + HTML production workspace for the Crypto Trading Academy 3D animation series.

## Current milestone
- Dark responsive HTML studio dashboard.
- Python Flask API for episodes, scenes and render jobs.
- Blender Python scene generator for a first 3D academy animatic.
- GitHub Actions workflow to render an MP4 and publish it as a workflow artifact.

> The first render is a procedural 3D animatic using placeholder characters and props. Final custom character meshes, Arabic voice acting and lip-sync are subsequent production milestones.

## Run locally
1. Install Blender (3.6+ recommended) and Python 3.10+.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the studio: `python python/app.py`
4. Open http://127.0.0.1:8000

Set `BLENDER_BIN` to your Blender executable if it is not on PATH.

## Render locally
`blender -b -P blender/animation_project.py -- --output output/episode_001.mp4`

## Render on GitHub
Open **Actions → Render Animation Episode → Run workflow**. The generated MP4 is uploaded as an artifact named `crypto-animation-episode`.

GitHub Actions is a render runner, not a permanent video host. Download the artifact or connect a separate hosting/storage service for public playback.


## Arabic dialogue and final audio

The render pipeline now creates three separate Arabic speech WAV files for Adam, Sami, and Leila with eSpeak NG, mixes them with a very quiet generated tonal ambience, animates each character's mouth during their dialogue window, and muxes the audio into the final MP4.

### Local audio prerequisites

Install Blender 4.2+, FFmpeg, and eSpeak NG (with Arabic voice data), then install the Python requirements:

```bash
sudo apt-get install ffmpeg espeak-ng
pip install -r requirements.txt
python python/audio_production.py
python python/app.py
```

Use the **Render Animation Episode** workflow in GitHub Actions to produce the final MP4 artifact. The workflow installs Blender, FFmpeg, and eSpeak NG automatically. The current dialogue is a synthetic Arabic voice preview; final voice casting, expressive acting, phoneme-level lip-sync, and a composed soundtrack are future production upgrades.
