#!/usr/bin/env python3
"""Generate a 180-second Arabic narration track for the Qutuz historical episode."""
from pathlib import Path
import shutil
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
FFMPEG = shutil.which("ffmpeg")
ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")
if not FFMPEG or not ESPEAK:
    raise SystemExit("Missing audio tools: install ffmpeg and espeak-ng")

NARRATION = [
    "في القرن السابع الهجري، اجتاح المغول مدناً كبرى في المشرق، وسقطت بغداد، وامتد الخطر إلى بلاد الشام. وكان السؤال: هل يصل الزحف إلى مصر؟",
    "كان قطز من أصول خوارزمية، وجاء إلى عالم المماليك في زمن مضطرب. لا تحفظ لنا المصادر تفاصيل مؤكدة عن كل سنوات نشأته، لكنها تحفظ لنا صعوده قائداً.",
    "في دولة المماليك، كانت المكانة تُبنى بالخبرة العسكرية والولاء والقدرة على القيادة. وتدرّج قطز حتى أصبح من أصحاب النفوذ في الحكم والجيش.",
    "وفي سنة ألف ومئتين وتسع وخمسين للميلاد، تولّى قطز سلطنة مصر. لم يكن أمامه وقت طويل للاستقرار؛ فالخطر المغولي كان يقترب، والدولة تحتاج إلى قرار حاسم.",
    "بعد سقوط بغداد، تعرضت مدن في الشام للهجوم، وتقدمت القوات المغولية بقيادة هولاكو. صار الدفاع عن مصر وبلاد الشام مسألة مصير.",
    "واجه قطز التهديد ورفض الخضوع له. عمل على جمع الأمراء وتعبئة القوات، واختار أن يخرج بالجيش لملاقاة المغول بدلاً من انتظار وصولهم إلى مصر.",
    "استعد الجيش المملوكي للحملة، وشارك بيبرس في القيادة العسكرية. كان على الفرسان أن يواجهوا قوة اشتهرت بسرعة الحركة والرماية على ظهور الخيل.",
    "تحرك قطز بجيشه شمالاً نحو فلسطين. لم تكن الرحلة مجرد انتقال عسكري؛ بل كانت استعداداً لمواجهة قد تحدد مستقبل مصر والشام لسنوات طويلة.",
    "في الثالث من سبتمبر سنة ألف ومئتين وستين للميلاد، التقى الجيش المملوكي بالقوة المغولية قرب عين جالوت في فلسطين. وكان قطز يقود جيش السلطنة، وبيبرس من أبرز قادته.",
    "اشتد القتال، وتعرضت قوات المماليك لضغط شديد. ثم استعادت زمام المبادرة، وأسهمت القيادة والتكتيكات العسكرية في تحويل مسار المعركة.",
    "انتهت المواجهة بانتصار المماليك ومقتل قائد المغول كتبغا وفق عدد من الروايات. وأوقف الانتصار التقدم المغولي غرباً نحو مصر، وغيّر ميزان القوى في المنطقة.",
    "لكن قطز لم يعش طويلاً بعد النصر؛ فقد قُتل في طريق عودته إلى مصر في أواخر سنة ألف ومئتين وستين للميلاد، وتختلف الروايات في بعض تفاصيل مقتله. بقي اسمه مرتبطاً بعين جالوت."
]

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

parts = []
for i, text in enumerate(NARRATION, 1):
    wav = OUT / f"qutuz_narration_{i:02d}.wav"
    run([ESPEAK, "-v", "ar", "-s", "142", "-p", "38", "-a", "175", "-w", str(wav), text])
    with wave.open(str(wav), "rb") as f:
        duration = f.getnframes() / float(f.getframerate())
    # Preserve a little breathing room at the end of each 15-second chapter.
    if duration > 14.4:
        fitted = OUT / f"qutuz_narration_{i:02d}_fit.wav"
        tempo = min(1.35, duration / 14.4)
        run([FFMPEG, "-y", "-i", str(wav), "-af", f"atempo={tempo:.4f}", "-t", "14.4", str(fitted)])
        wav = fitted
        duration = 14.4
    parts.append((wav, (i - 1) * 15_000, i))

inputs = []
filters = []
for idx, (wav, delay, scene) in enumerate(parts):
    inputs += ["-i", str(wav)]
    filters.append(f"[{idx}:a]adelay={delay}|{delay},volume=1.0[v{idx}]")
# Original atmospheric tonal bed, kept very quiet under the narration.
inputs += ["-f", "lavfi", "-t", "180", "-i", "anoisesrc=color=pink:amplitude=0.012:sample_rate=44100"]
filters.append(f"[{len(parts)}:a]lowpass=f=700,volume=0.10[amb]")
mix = "".join(f"[v{i}]" for i in range(len(parts))) + "[amb]"
filters.append(f"{mix}amix=inputs={len(parts)+1}:duration=longest:normalize=0,alimiter=limit=0.92,apad=whole_dur=180,atrim=0:180[aout]")
final = OUT / "episode_001_audio.wav"
run([FFMPEG, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[aout]", "-t", "180", "-ar", "44100", "-ac", "2", str(final)])
print("QUTUZ_AUDIO_COMPLETE", final, final.stat().st_size)
