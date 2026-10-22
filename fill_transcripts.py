# fill_transcripts.py — transcribe the Instagram reels already downloaded in videos/
# and write the transcripts into mbx_research.csv. No re-scraping, no Apify cost.
import csv, os, subprocess
import numpy as np
import imageio_ffmpeg
from faster_whisper import WhisperModel

os.chdir(os.path.dirname(os.path.abspath(__file__)))
FF = imageio_ffmpeg.get_ffmpeg_exe()

def load_audio(path):
    # decode with ffmpeg (avoids the PyAV version clash)
    raw = subprocess.run([FF, "-nostdin", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0

with open("mbx_research.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("Loading Whisper model...")
model = WhisperModel("small", device="cpu", compute_type="int8")

n = 0
for r in rows:
    if r["platform"] != "Instagram":
        continue
    n += 1
    path = f"videos/ig_{n:02d}.mp4"
    if not os.path.exists(path):
        r["transcript"] = "(no video file)"
        continue
    try:
        audio = load_audio(path)
        if audio.size == 0:
            r["transcript"] = "(no audio)"
        else:
            segs, _ = model.transcribe(audio)
            r["transcript"] = " ".join(s.text.strip() for s in segs) or "(no speech)"
    except Exception as e:
        r["transcript"] = f"(error: {e})"
    print(f"{n:02d}", r["transcript"][:70])

with open("mbx_research.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("Done -> mbx_research.csv updated")
