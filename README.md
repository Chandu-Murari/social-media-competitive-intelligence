# Social Media Competitive Intelligence Pipeline

An automated Python pipeline that collects public performance data from Instagram and YouTube, transcribes the videos, and turns it into a clean dataset for analysis in Power BI.

## Why
Content teams spend money producing videos without knowing which formats, hooks and topics actually win. This pipeline studies top-performing competitors first, so production budget goes into proven patterns.

## How it works
```
Apify API (Instagram) ─┐
                       ├─> Download ─> Speech-to-text (Whisper) ─> CSV ─> Power BI
yt-dlp (YouTube) ──────┘                      (YouTube captions)
```

| Step | Tool |
|---|---|
| Extract public post data (views, likes, comments, captions) | Apify API, yt-dlp |
| Transcribe video audio | faster-whisper (OpenAI Whisper), ffmpeg |
| Clean and enrich (engagement rate, hook text, sponsor flag) | Python (csv, regex) |
| Visualise | Power BI |

## Files
- `mbx_research.py` — main pipeline (scrape → download → transcribe → CSV)
- `fill_transcripts.py` — re-runs transcription on downloaded videos only
- `content_performance_clean.csv` — cleaned, analysis-ready dataset

## Sample findings (15 top posts, 2 channels, 50M+ combined views)
- **Short-form animal comedy** (1.2M–14.4M views): every top reel uses a familiar human scene (a fight, a coach, a cop show, a couple) voiced over real animal footage, with the educational fact kept in the caption. Like rate 5–9% of views.
- **Long-form animated documentary** (8.4M–11M views): every top video opens mid-scene in present tense ("A shooter is taking aim…") and puts stakes before context. 5/5 top videos carried a sponsor.
- A sponsor integrated as dialogue still reached 2.5M views — ads written into the story did not hurt reach.

## Data & compliance
- Public data only, collected through official tools/APIs.
- No personal data about viewers is collected or stored.
- Built with Canadian privacy expectations (PIPEDA) in mind.

## Run it
```
pip install apify-client faster-whisper yt-dlp imageio-ffmpeg requests
python mbx_research.py
```
Add your own Apify token and target pages/channels at the top of the script.
