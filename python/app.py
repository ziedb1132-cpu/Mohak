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
    "title": "قطز: السلطان الذي أوقف زحف المغول",
    "status": "جاهز للإنتاج",
    "duration": 180,
    "scenes": [
        {"id": f"scene_{i:02d}", "title": title, "duration": 15, "status": "جاهز للرندر"}
        for i, title in enumerate([
            "عاصفة فوق المشرق", "بدايات مجهولة التفاصيل", "طريق القيادة",
            "سلطان في زمن الخطر", "تهديد المغول", "قرار المواجهة",
            "الاستعداد للحملة", "المسير إلى فلسطين", "لقاء عين جالوت",
            "ساعات الحسم", "نتيجة المعركة", "نهاية السلطان وبقاء الأثر"
        ], 1)
    ],
}]
