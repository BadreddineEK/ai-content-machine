"""file_manager.py - Directory and temp file management."""
from pathlib import Path
import shutil


def prepare_directories() -> None:
    """Create required directories for the pipeline."""
    dirs = ["temp", "output"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)


def cleanup_temp() -> None:
    """Remove all temporary files."""
    temp_dir = Path("temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        temp_dir.mkdir()


def get_output_path(filename: str) -> str:
    """Get full output path for a given filename."""
    return str(Path("output") / filename)


def get_temp_path(filename: str) -> str:
    """Get full temp path for a given filename."""
    return str(Path("temp") / filename)
