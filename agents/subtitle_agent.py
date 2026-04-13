"""subtitle_agent.py - Node 3b: Subtitle generation via Whisper."""
import os
from pathlib import Path


def generate_subtitles(audio_path: str) -> str:
    """Transcribe audio and generate SRT subtitles using Whisper.

    Returns path to the generated .srt file.
    """
    import whisper
    output_path = "temp/subtitles.srt"

    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="fr", word_timestamps=True)

    srt_content = _segments_to_srt(result["segments"])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path


def _segments_to_srt(segments: list) -> str:
    """Convert Whisper segments to SRT format with max 5 words per line."""
    srt_lines = []
    index = 1

    for segment in segments:
        words = segment["text"].strip().split()
        start = segment["start"]
        end = segment["end"]
        duration = end - start

        # Split into chunks of max 5 words
        chunks = [words[i:i+5] for i in range(0, len(words), 5)]
        if not chunks:
            continue

        chunk_duration = duration / len(chunks)

        for i, chunk in enumerate(chunks):
            chunk_start = start + i * chunk_duration
            chunk_end = start + (i + 1) * chunk_duration
            text = " ".join(chunk)

            srt_lines.append(str(index))
            srt_lines.append(
                f"{_fmt_time(chunk_start)} --> {_fmt_time(chunk_end)}"
            )
            srt_lines.append(text)
            srt_lines.append("")
            index += 1

    return "\n".join(srt_lines)


def _fmt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
