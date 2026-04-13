"""visual_agent.py - Node 4: Fetch video clips from Pexels API."""
import os
import requests
from pathlib import Path
from typing import List

PEXELS_API_URL = "https://api.pexels.com/videos/search"


def fetch_video_clips(keywords: List[str], config: dict) -> List[str]:
    """Fetch and download stock video clips from Pexels API.

    Returns list of local file paths for downloaded clips.
    """
    api_key = os.environ.get("PEXELS_API_KEY", "")
    nb_clips = config.get("nb_clips_visuels", 6)
    clips_per_keyword = max(1, nb_clips // len(keywords)) if keywords else nb_clips
    downloaded = []

    for keyword in keywords:
        if len(downloaded) >= nb_clips:
            break
        clips = _search_clips(keyword, api_key, clips_per_keyword)
        for clip in clips:
            if len(downloaded) >= nb_clips:
                break
            path = _download_clip(clip, len(downloaded))
            if path:
                downloaded.append(path)

    # Fallback if not enough clips
    while len(downloaded) < nb_clips:
        fallback_path = _create_fallback_clip(len(downloaded))
        downloaded.append(fallback_path)

    return downloaded[:nb_clips]


def _search_clips(keyword: str, api_key: str, per_page: int = 3) -> list:
    """Search Pexels for video clips matching keyword."""
    if not api_key:
        return []
    headers = {"Authorization": api_key}
    params = {
        "query": keyword,
        "per_page": per_page,
        "orientation": "portrait",
        "size": "medium",
    }
    try:
        r = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        # Fallback to landscape if no portrait results
        if not videos:
            params["orientation"] = "landscape"
            r = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=20)
            r.raise_for_status()
            videos = r.json().get("videos", [])
        return videos
    except Exception:
        return []


def _download_clip(video: dict, index: int) -> str:
    """Download a single video clip from Pexels."""
    try:
        # Select best quality video file
        video_files = sorted(
            video.get("video_files", []),
            key=lambda x: x.get("width", 0),
            reverse=True
        )
        # Prefer HD or higher
        for vf in video_files:
            if vf.get("width", 0) >= 720:
                url = vf["link"]
                break
        else:
            url = video_files[0]["link"] if video_files else None

        if not url:
            return None

        output_path = f"temp/clip_{index:02d}.mp4"
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path
    except Exception:
        return None


def _create_fallback_clip(index: int) -> str:
    """Create a solid color fallback clip using FFmpeg."""
    output_path = f"temp/clip_{index:02d}.mp4"
    import subprocess
    colors = ["black", "navy", "darkblue", "midnightblue", "darkslateblue", "indigo"]
    color = colors[index % len(colors)]
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                f"-i", f"color=c={color}:size=1080x1920:rate=30",
                "-t", "10", "-c:v", "libx264", output_path
            ],
            capture_output=True, timeout=30
        )
    except Exception:
        # Ultra fallback: create empty file
        Path(output_path).touch()
    return output_path
