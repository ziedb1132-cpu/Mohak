#!/usr/bin/env python3
"""Create original Arabic character dialogue and a subtle synthetic music bed."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FFMPEG = shutil.which("ffmpeg")
ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")
if not FFMPEG or not ESPEAK:
    raise SystemExit("Missing audio tools: install ffmpeg and espeak-ng")

lines = [
    ("adam", "مرحباً بكم في أكاديمية تداول العملات الرقمية.", 145, 48, 1000),
    ("sami", "أريد أن أفهم كيف يعمل هذا السوق.", 158, 62, 4200),
    ("leila", "سنبدأ من الأساسيات ونتعلم خطوة بخطوة.", 135, 38, 7300),
]
tracks = []
for speaker, text, speed, pitch, delay in lines:
    wav = OUT / f"voice_{speaker}.wav"
    subprocess.run([ESPEAK, "-v", "ar", "-s", str(speed), "-p", str(pitch), "-a", "170", "-w", str(wav), text], check=True)
    tracks.append((wav, delay, speaker))

# Mix independent character voices at their timeline positions, plus a quiet generated tonal bed.
inputs = []
filters = []
for i, (wav, delay, speaker) in enumerate(tracks):
    inputs += ["-i", str(wav)]
    filters.append(f"[{i}:a]adelay={delay}|{delay},volume=1.0[v{i}]")
inputs += ["-f", "lavfi", "-t", "12", "-i", "sine=frequency=110:sample_rate=44100"]
filters.append(f"[{len(tracks)}:a]volume=0.018,lowpass=f=220[music]")
mix_inputs = "".join(f"[v{i}]" for i in range(len(tracks))) + "[music]"
filters.append(f"{mix_inputs}amix=inputs={len(tracks)+1}:duration=longest:normalize=0,alimiter=limit=0.92[aout]")
final = OUT / "episode_001_audio.wav"
cmd = [FFMPEG, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[aout]", "-t", "12", "-ar", "44100", "-ac", "2", str(final)]
subprocess.run(cmd, check=True)
print("AUDIO_RENDER_COMPLETE", final, final.stat().st_size)
