# utils/extractor.py
import zipfile
import py7zr
from pathlib import Path

# Only these formats are supported
SUPPORTED_ARCHIVES = (".zip", ".7z")

def extract_archive(archive_path: str, output_dir: Path):
    """
    Extract a .zip or .7z archive into the output directory.
    """
    archive = Path(archive_path)
    ext = archive.suffix.lower()

    if ext == ".zip":
        with zipfile.ZipFile(archive, "r") as z:
            z.extractall(output_dir)

    elif ext == ".7z":
        with py7zr.SevenZipFile(archive, mode="r") as z:
            z.extractall(path=output_dir)

    else:
        raise ValueError(f"Unsupported archive format: {ext}")