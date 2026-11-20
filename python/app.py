from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)
app = Flask(__name__, static_folder="../web", static_url_path="")
JOBS: dict[str, dict] = {}

EPISODES = [{
    "id": "episode_001",
    "title": "اكتشف عالم العملات الرقمية",
    "status": "جاهز للتحضير",
    "scenes": [
        {"id": "scene_001", "title": "افتتاحية أكاديمية التداول", "duration": 8, "status": "مخطط"},
        {"id": "scene_002", "title": "سؤال سامي", "duration": 8, "status": "مخطط"},
        {"id": "scene_003", "title": "إجابة الأستاذ آدم", "duration": 8, "status": "مخطط"},
    ],
}]

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Crypto Animation Studio"})

@app.get("/api/episodes")
def episodes():
    return jsonify(EPISODES)

@app.get("/api/jobs")
def jobs():
    return jsonify(list(JOBS.values()))

@app.post("/api/render")
def render():
    payload = request.get_json(silent=True) or {}
    episode_id = payload.get("episode_id", "episode_001")
    if episode_id != "episode_001":
        return jsonify({"error": "Unknown episode"}), 404

    blender = os.environ.get("BLENDER_BIN", "blender")
    script = ROOT / "blender" / "animation_project.py"
    output_file = OUTPUT / f"{episode_id}.mp4"
    job_id = str(uuid.uuid4())[:8]
    silent_file = OUTPUT / f"{episode_id}_silent.mp4"
    audio_script = ROOT / "python" / "audio_production.py"
    audio_file = OUTPUT / "episode_001_audio.wav"
    command = [blender, "-b", "-P", str(script), "--", "--output", str(silent_file)]
    try:
        audio_result = subprocess.run(["python", str(audio_script)], cwd=ROOT, capture_output=True, text=True, timeout=300)
        if audio_result.returncode != 0:
            raise RuntimeError("Audio generation failed: " + audio_result.stderr[-1500:])
        render_result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        if render_result.returncode != 0:
            raise RuntimeError("Blender render failed: " + render_result.stderr[-2500:])
        mux_result = subprocess.run(["ffmpeg", "-y", "-i", str(silent_file), "-i", str(audio_file), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output_file)], cwd=ROOT, capture_output=True, text=True, timeout=300)
        result = mux_result
        status = "completed" if mux_result.returncode == 0 and output_file.exists() else "failed"
        JOBS[job_id] = {
            "id": job_id, "episode_id": episode_id, "status": status,
            "video_url": f"/videos/{output_file.name}" if status == "completed" else None,
            "log": (audio_result.stdout + "\n" + render_result.stdout + "\n" + result.stderr)[-5000:],
        }
        return jsonify(JOBS[job_id]), (200 if status == "completed" else 500)
    except FileNotFoundError:
        return jsonify({"error": "Required executable not found. Install Blender, ffmpeg and espeak-ng."}), 503
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Render timed out"}), 504

@app.get("/videos/<path:filename>")
def videos(filename):
    return send_from_directory(OUTPUT, filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=False)
