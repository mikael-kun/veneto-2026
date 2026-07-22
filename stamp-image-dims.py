#!/usr/bin/env python3
"""
Stamp intrinsic width/height onto every <img> in the journal pages.

Why: images without width/height reserve no space until they load, so the page
grows underneath you and anchor jumps (#d1..#dN) land in the wrong place.
With the attributes present the browser reserves the right box immediately.

Safe to re-run after every batch of new photos: images that already carry both
attributes are left untouched.

Usage, from the repo root (the folder containing journal.html and img/):
    python3 stamp-image-dims.py
    python3 stamp-image-dims.py journal.html notes.html index.html
"""

import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install Pillow")

ROOT = Path(__file__).resolve().parent
DEFAULT_FILES = ["journal.html", "notes.html", "index.html"]

IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
SRC_ATTR = re.compile(r'\bsrc\s*=\s*"([^"]+)"', re.I)
HAS_W = re.compile(r"\bwidth\s*=", re.I)
HAS_H = re.compile(r"\bheight\s*=", re.I)


def stamp(html_path: Path) -> None:
    if not html_path.exists():
        print(f"  skip {html_path.name} (not found)")
        return

    html = html_path.read_text(encoding="utf-8")
    stamped = skipped = missing = external = 0
    missing_paths = []

    def replace(match: re.Match) -> str:
        nonlocal stamped, skipped, missing, external
        tag = match.group(0)

        if HAS_W.search(tag) and HAS_H.search(tag):
            skipped += 1
            return tag

        src_match = SRC_ATTR.search(tag)
        if not src_match:
            return tag

        src = src_match.group(1)
        if src.startswith(("http://", "https://", "data:", "//")):
            external += 1
            return tag

        img_file = (html_path.parent / src).resolve()
        if not img_file.exists():
            missing += 1
            missing_paths.append(src)
            return tag

        try:
            with Image.open(img_file) as im:
                w, h = im.size
        except Exception as exc:  # unreadable / not an image
            missing += 1
            missing_paths.append(f"{src}  ({exc})")
            return tag

        # insert right after "<img" so attribute order stays predictable
        stamped += 1
        return tag[:4] + f' width="{w}" height="{h}"' + tag[4:]

    new_html = IMG_TAG.sub(replace, html)

    if new_html != html:
        html_path.write_text(new_html, encoding="utf-8")

    print(f"  {html_path.name}: {stamped} stamped, {skipped} already had dims, "
          f"{external} external, {missing} missing")
    for m in missing_paths:
        print(f"      MISSING: {m}")


def main() -> None:
    targets = sys.argv[1:] or DEFAULT_FILES
    print("Stamping intrinsic image dimensions…")
    for name in targets:
        stamp(ROOT / name)
    print("Done. Commit the changed HTML alongside the new images.")


if __name__ == "__main__":
    main()
