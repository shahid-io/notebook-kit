#!/usr/bin/env python3
"""Pull a YouTube lecture (or a whole playlist) into a source pack for writing.

    python3 engine/transcript.py <playlist-or-video-url> [out_dir]

Writes one markdown file per video: front matter, then the auto-captions merged
into ~30 second timestamped paragraphs. Existing files are left alone, so this
is safe to re-run when a playlist grows.

Needs yt-dlp on the path or importable:  pip3 install yt-dlp
Scraping the watch page for `captionTracks` and fetching the `api/timedtext`
baseUrl does NOT work: it returns 200 with an empty body. yt-dlp handles the
tokens YouTube now requires.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

PARA_SECONDS = 30


def run(args):
    return subprocess.run([sys.executable, "-m", "yt_dlp", *args],
                          capture_output=True, text=True).stdout


def slugify(title):
    """'21.1. Backend Scaling: Part-1' -> 'backend-scaling-part-1'."""
    body = re.sub(r"^[\d.]+\s*\.?\s*", "", title)
    return re.sub(r"[^a-z0-9]+", "-", body.lower()).strip("-")[:60]


def paragraphs(path):
    """json3 auto-captions -> [(seconds, text)], rolling duplicates dropped."""
    events = json.load(open(path))["events"]
    lines = []
    for e in events:
        if "segs" not in e or e.get("aAppend"):
            continue
        text = " ".join("".join(s.get("utf8", "") for s in e["segs"]).split())
        if text:
            lines.append((e.get("tStartMs", 0) // 1000, text))
    out, buf, start = [], [], lines[0][0] if lines else 0
    for t, text in lines:
        if t - start >= PARA_SECONDS and buf:
            out.append((start, " ".join(buf)))
            buf, start = [], t
        buf.append(text)
    if buf:
        out.append((start, " ".join(buf)))
    return out


def hms(s):
    return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def fetch(video_id, index, title, duration, out_dir):
    path = os.path.join(out_dir, f"{index:02d}-{slugify(title)}.md")
    if os.path.exists(path):
        print(f"  {index:02d} exists, skipped")
        return
    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmp:
        run(["--skip-download", "--write-auto-sub", "--sub-lang", "en",
             "--sub-format", "json3", "-o", os.path.join(tmp, "s.%(ext)s"), url])
        cap = os.path.join(tmp, "s.en.json3")
        if not os.path.exists(cap):
            print(f"  {index:02d} NO CAPTIONS  {title}")
            return
        paras = paragraphs(cap)
    with open(path, "w") as fh:
        fh.write(f"---\ntitle: {title}\nurl: {url}\n"
                 f"duration: {hms(int(duration or 0))}\n"
                 f"paragraphs: {len(paras)}\n---\n\n")
        for t, text in paras:
            fh.write(f"[{hms(t)}] {text}\n\n")
    print(f"  {index:02d} {len(paras):>4} paras  {os.path.basename(path)}")


def main():
    url = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "sources"
    os.makedirs(out_dir, exist_ok=True)
    rows = run(["--flat-playlist", "--print",
                "%(playlist_index)s|%(id)s|%(duration)s|%(title)s", url])
    for line in rows.strip().split("\n"):
        if not line.strip():
            continue
        index, vid, duration, title = line.split("|", 3)
        fetch(vid, int(index or 1), title,
              float(duration) if duration not in ("", "NA") else 0, out_dir)


if __name__ == "__main__":
    main()
