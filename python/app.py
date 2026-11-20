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
    command = [blender, "-b", "-P", str(script), "--", "--output", str(output_file)]
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        status = "completed" if result.returncode == 0 and output_file.exists() else "failed"
        JOBS[job_id] = {
            "id": job_id, "episode_id": episode_id, "status": status,
            "video_url": f"/videos/{output_file.name}" if status == "completed" else None,
            "log": (result.stdout + "\n" + result.stderr)[-5000:],
        }
        return jsonify(JOBS[job_id]), (200 if status == "completed" else 500)
    except FileNotFoundError:
        return jsonify({"error": "Blender executable not found. Install Blender or set BLENDER_BIN."}), 503
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Render timed out"}), 504

@app.get("/videos/<path:filename>")
def videos(filename):
    return send_from_directory(OUTPUT, filename)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=False)
