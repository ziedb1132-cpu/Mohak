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

SCENE_TITLES = [
    "عاصفة فوق المشرق", "بدايات مجهولة التفاصيل", "طريق القيادة",
    "سلطان في زمن الخطر", "تهديد المغول", "قرار المواجهة",
    "الاستعداد للحملة", "المسير إلى فلسطين", "لقاء عين جالوت",
    "ساعات الحسم", "نتيجة المعركة", "نهاية السلطان وبقاء الأثر"
]
EPISODES = [{
    "id": "episode_001",
    "title": "قطز: السلطان الذي أوقف زحف المغول",
    "status": "جاهز للإنتاج",
    "duration": 180,
    "scenes": [
        {"id": f"scene_{i:02d}", "title": title, "duration": 15, "status": "جاهز للرندر"}
        for i, title in enumerate(SCENE_TITLES, 1)
    ],
}]


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Mohak Historical Animation Studio"})


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
    script = ROOT / "blender" / "qutuz_episode.py"
    output_file = OUTPUT / "qutuz_episode_001.mp4"
    silent_file = OUTPUT / "episode_001_silent.mp4"
    audio_script = ROOT / "python" / "qutuz_audio.py"
    audio_file = OUTPUT / "episode_001_audio.wav"
    job_id = str(uuid.uuid4())[:8]
    try:
        audio_result = subprocess.run(
            ["python3", str(audio_script)], cwd=ROOT,
            capture_output=True, text=True, timeout=600
        )
        if audio_result.returncode != 0:
            raise RuntimeError("Audio generation failed: " + audio_result.stderr[-2000:])

        render_result = subprocess.run(
            [blender, "-b", "-P", str(script), "--", "--output", str(silent_file)],
            cwd=ROOT, capture_output=True, text=True, timeout=21600
        )
        if render_result.returncode != 0:
            raise RuntimeError("Blender render failed: " + render_result.stderr[-3000:])

        mux_result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(silent_file), "-i", str(audio_file),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-t", "180", "-movflags",
             "+faststart", str(output_file)],
            cwd=ROOT, capture_output=True, text=True, timeout=600
        )
        if mux_result.returncode != 0 or not output_file.exists() or output_file.stat().st_size == 0:
            raise RuntimeError("Audio/video mux failed: " + mux_result.stderr[-2000:])

        JOBS[job_id] = {
            "id": job_id, "episode_id": episode_id, "status": "completed",
            "video_url": f"/videos/{output_file.name}",
            "log": (audio_result.stdout + "\n" + render_result.stdout + "\n" + mux_result.stderr)[-5000:],
        }
        return jsonify(JOBS[job_id])
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
