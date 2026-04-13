"""video_agent.py - Node 5: Video assembly using FFmpeg."""
import subprocess
import os
from pathlib import Path
from typing import List


def assemble_video(
    clips: List[str],
    audio_path: str,
    srt_path: str,
    output_name: str,
    config: dict,
) -> str:
    """Assemble final 9:16 vertical video using FFmpeg.

    Pipeline: concat clips -> crop/scale 9:16 -> overlay audio -> burn subtitles.
    Returns path to final video.
    """
    output_path = f"output/{output_name}"
    temp_concat = "temp/concat.mp4"
    temp_scaled = "temp/scaled.mp4"

    # Step 1: Concat clips
    _concat_clips(clips, temp_concat)

    # Step 2: Scale and crop to 9:16 (1080x1920)
    _scale_to_vertical(temp_concat, temp_scaled)

    # Step 3: Overlay audio and burn subtitles
    _add_audio_and_subtitles(temp_scaled, audio_path, srt_path, output_path)

    return output_path


def _concat_clips(clips: List[str], output: str) -> None:
    """Concatenate multiple video clips using FFmpeg concat demuxer."""
    # Write concat list file
    concat_list = "temp/concat_list.txt"
    with open(concat_list, "w") as f:
        for clip in clips:
            abs_path = os.path.abspath(clip)
            f.write(f"file '{abs_path}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy", output
        ],
        check=True, capture_output=True, timeout=120
    )


def _scale_to_vertical(input_path: str, output_path: str) -> None:
    """Scale and crop video to 1080x1920 (9:16 portrait format)."""
    # Scale to fill 1080x1920, then crop if needed
    vf = (
        "scale=w=1080:h=1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", vf,
            "-r", "30",
            "-c:v", "libx264", "-preset", "fast",
            "-crf", "23", "-an", output_path
        ],
        check=True, capture_output=True, timeout=300
    )


def _add_audio_and_subtitles(
    video_path: str, audio_path: str, srt_path: str, output_path: str
) -> None:
    """Add audio track and burn subtitles into the final video."""
    abs_srt = os.path.abspath(srt_path).replace("\\", "/")
    # Subtitle style: white, bold, centered at bottom
    subtitle_style = (
        "FontName=Arial,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=80"
    )
    vf = f"subtitles='{abs_srt}':force_style='{subtitle_style}'"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-map", "0:v:0", "-map", "1:a:0",
            output_path
        ],
        check=True, capture_output=True, timeout=600
    )
