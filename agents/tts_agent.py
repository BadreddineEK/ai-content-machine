"""tts_agent.py - Node 3a: Text-to-Speech using edge-tts."""
import asyncio
import os
from pathlib import Path
from typing import Tuple
import edge_tts


def generate_tts(script: dict, config: dict) -> Tuple[str, float]:
    """Generate voice-over audio from script using edge-tts.

    Returns (audio_path, duration_in_seconds).
    """
    voice = config.get("voix", "fr-FR-HenriNeural")
    text = f"{script['hook']} {script['corps']} {script['cta']}"
    output_path = "temp/voice.mp3"

    asyncio.run(_generate_audio(text, voice, output_path))
    duration = _get_audio_duration(output_path)
    return output_path, duration


async def _generate_audio(text: str, voice: str, output_path: str) -> None:
    """Async function to generate audio using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def _get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file using ffprobe."""
    import subprocess
    import json
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", audio_path
            ],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        for stream in streams:
            if "duration" in stream:
                return float(stream["duration"])
    except Exception:
        pass
    # Fallback: estimate from file size (rough approximation)
    size = os.path.getsize(audio_path)
    return size / (128 * 1024 / 8)  # Assume 128kbps
