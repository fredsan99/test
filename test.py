from datetime import datetime
from pathlib import Path
import os
import shutil
import sys
from typing import Optional

from PIL import Image
from PIL.ExifTags import TAGS

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff",
    ".bmp", ".gif", ".cr2", ".nef", ".dng", ".arw", ".rw2"
}


def get_taken_datetime(path: Path) -> Optional[datetime]:
    """Return the capture time from EXIF; fall back to file mtime."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                        try:
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except (ValueError, TypeError):
                            print(f"Unknown date format in EXIF for {path}: {value}")
                            pass
    except Exception:
        print(f"Could not read EXIF data from {path}. Falling back to file modification time.")
        pass

    return datetime.fromtimestamp(path.stat().st_mtime)


def organise(root: Path, move_files: bool) -> None:
    """Create images_sorted structure and copy/move pictures into it."""
    dest_root = root / "images_sorted"
    for file in root.rglob("*"):
        if (
            file.is_file()
            and file.suffix.lower() in IMAGE_EXTS
            and dest_root not in file.parents
        ):
            dt = get_taken_datetime(file)
            dest_dir = dest_root / f"{dt.year:04d}" / f"{dt.month:02d}"
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest_file = dest_dir / file.name
            counter = 1
            while dest_file.exists():
                dest_file = dest_dir / f"{file.stem}_{counter}{file.suffix}"
                counter += 1

            if move_files:
                shutil.move(str(file), dest_file)
            else:
                shutil.copy2(str(file), dest_file)


def ask_parent_folder() -> Path:
    """Prompt until a valid directory is provided."""
    while True:
        folder_str = input("Enter the full path to the folder containing your pictures: ").strip()
        root = Path(folder_str).expanduser().resolve()
        if root.is_dir():
            return root
        print("That path does not exist or is not a directory. Please try again.\n")


def ask_move_or_copy() -> bool:
    """Return True for move, False for copy."""
    while True:
        choice = input("Move files instead of copying? [Y/N]: ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no", ""):
            return False
        print("Please answer y or n.\n")


def main() -> None:
    # clear command line in console
    os.system('cls' if os.name == 'nt' else 'clear')
    root = ask_parent_folder()
    move_files = ask_move_or_copy()

    print("\nStarting … this may take a while for large collections.\n")
    organise(root, move_files)
    print("Done! You will find the sorted photos in:", root / "images_sorted")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled by user.")
