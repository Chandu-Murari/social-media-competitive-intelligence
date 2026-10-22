# mbx_research.py — study top content from Instagram pages + YouTube channels
# Output: mbx_research.csv (views, likes, captions, full transcripts)
import csv, os, re, glob, requests
import yt_dlp

APIFY_TOKEN = "PASTE_YOUR_TOKEN_HERE"

# Instagram usernames (no @). Leave [] to skip Instagram.
PAGES = ["ai.cinema021", "naturalhabitatshorts"]

# YouTube channel links (any genre). Leave [] to skip YouTube.
YT_CHANNELS = ["https://www.youtube.com/@fern-tv/videos"]

REELS_PER_PAGE = 10   # Instagram reels scanned per page
TOP_N = 20            # Instagram reels kept (highest views)
YT_SCAN = 40          # latest YouTube videos scanned per channel
YT_TOP = 5            # YouTube videos kept per channel (highest views)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("videos", exist_ok=True)
os.makedirs("subs", exist_ok=True)
rows = []

# ---------------- INSTAGRAM ----------------
if PAGES:
    from apify_client import ApifyClient
    from faster_whisper import WhisperModel
    import subprocess, numpy as np, imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()

    def load_audio(path):
        # decode with ffmpeg (avoids the PyAV version clash)
        raw = subprocess.run([FF, "-nostdin", "-i", path, "-f", "s16le", "-ac", "1",
                              "-ar", "16000", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0

    print("IG 1/3 Scraping reels...")
    client = ApifyClient(APIFY_TOKEN)
    run = client.actor("apify/instagram-reel-scraper").call(
        run_input={"username": PAGES, "resultsLimit": REELS_PER_PAGE})
    ds_id = run["defaultDatasetId"] if isinstance(run, dict) else (
        getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None))
    items = []
    for i in client.dataset(ds_id).iterate_items():
        if not isinstance(i, dict):
            i = i.model_dump() if hasattr(i, "model_dump") else dict(i)
        if i.get("videoUrl"):
            items.append(i)
    views = lambda i: i.get("videoPlayCount") or i.get("videoViewCount") or 0
    items.sort(key=views, reverse=True)
    top = items[:TOP_N]
    print(f"   found {len(items)} reels, keeping top {len(top)}")

    print("IG 2/3 Downloading...")
    for n, it in enumerate(top, 1):
        path = f"videos/ig_{n:02d}.mp4"
        try:
            if not os.path.exists(path):
                r = requests.get(it["videoUrl"], timeout=90)
                with open(path, "wb") as f:
                    f.write(r.content)
            it["file"] = path
        except Exception as e:
            print("   skipped", n, e)
            it["file"] = ""

    print("IG 3/3 Transcribing (slow on laptop, be patient)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    for it in top:
        text = ""
        if it["file"]:
            try:
                segs, _ = model.transcribe(load_audio(it["file"]))
                text = " ".join(s.text.strip() for s in segs) or "(no speech)"
            except Exception as e:
                text = f"(error: {e})"
        rows.append({"platform": "Instagram", "page": it.get("ownerUsername", ""), "title": "",
                     "views": views(it), "likes": it.get("likesCount", ""),
                     "comments": it.get("commentsCount", ""), "url": it.get("url", ""),
                     "caption": (it.get("caption") or "").replace("\n", " "), "transcript": text})

# ---------------- YOUTUBE ----------------
def vtt_to_text(path):
    out, seen = [], set()
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = re.sub(r"<[^>]+>", "", line.strip())
        if (not line or "-->" in line or line.isdigit()
                or line.startswith(("WEBVTT", "Kind:", "Language:"))):
            continue
        if line not in seen:
            seen.add(line)
            out.append(line)
    return " ".join(out)

for ch in YT_CHANNELS:
    print(f"YT Scanning {ch} ...")
    try:
        with yt_dlp.YoutubeDL({"extract_flat": True, "playlistend": YT_SCAN, "quiet": True}) as y:
            info = y.extract_info(ch, download=False)
    except Exception as e:
        print("   channel failed:", e)
        continue
    vids = [e for e in (info.get("entries") or []) if e and e.get("id")]
    vids.sort(key=lambda e: e.get("view_count") or 0, reverse=True)
    print(f"   found {len(vids)} videos, keeping top {min(YT_TOP, len(vids))}")

    for v in vids[:YT_TOP]:
        url = f"https://www.youtube.com/watch?v={v['id']}"
        meta, text = {}, ""
        try:
            opts = {"skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
                    "subtitleslangs": ["en.*"], "subtitlesformat": "vtt",
                    "outtmpl": f"subs/{v['id']}.%(ext)s", "quiet": True}
            with yt_dlp.YoutubeDL(opts) as y:
                meta = y.extract_info(url, download=True) or {}
            files = glob.glob(f"subs/{v['id']}*.vtt")
            text = vtt_to_text(files[0]) if files else "(no subtitles)"
        except Exception as e:
            text = f"(error: {e})"
        print("   got:", (v.get("title") or "")[:60])
        rows.append({"platform": "YouTube", "page": info.get("uploader") or ch,
                     "title": v.get("title", ""), "views": v.get("view_count", ""),
                     "likes": meta.get("like_count", ""), "comments": meta.get("comment_count", ""),
                     "url": url, "caption": (meta.get("description") or "")[:300].replace("\n", " "),
                     "transcript": text})

# ---------------- SAVE ----------------
cols = ["platform", "page", "title", "views", "likes", "comments", "url", "caption", "transcript"]
with open("mbx_research.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print(f"Done -> mbx_research.csv ({len(rows)} rows)")
