import argparse
import subprocess
import sys
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
from typing import List, Optional

from .logging_config import setup_logging, get_logger

logger = get_logger(__name__)

OUTER = 20
INNER = 4
WIDTH = 1280
HEIGHT = 720


def run(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        logger.error("Error running ImageMagick command")
        sys.exit(1)


def generate_thumbnail(base, title, part: Optional[int], font, fontsize, color, outdir, no_part_label: bool = False):
    # part may be None when --no-part-label is used; in that case omit part text
    part_str = f"{part:01d}" if part is not None else ""
    # When no_part_label is requested, do not include the part number in the filename
    if no_part_label:
        output = outdir / "thumbnail.png"
    else:
        output = outdir / f"thumbnail_part_{part_str}.png"

    cmd = [
        "magick",
        str(base),
        "-resize",
        f"{WIDTH}x{HEIGHT}^",
        "-gravity",
        "center",
        "-extent",
        f"{WIDTH}x{HEIGHT}",
        # Add thick outline around image
        "-bordercolor",
        "none",
        "-border",
        str(OUTER),
        # Outer black stroke
        "-stroke",
        "black",
        "-strokewidth",
        str(OUTER),
        "-fill",
        "none",
        "-draw",
        f"rectangle {OUTER / 2},{OUTER / 2} {WIDTH + OUTER * 1.5},{HEIGHT + OUTER * 1.5}",
        # Inner white stroke
        "-stroke",
        "white",
        "-strokewidth",
        str(INNER),
        "-fill",
        "none",
        "-draw",
        f"rectangle {OUTER},{OUTER} {WIDTH + OUTER},{HEIGHT + OUTER}",
        # Title (top center)
        "-gravity",
        "north",
        "-font",
        font,
        "-pointsize",
        str(fontsize),
        "-fill",
        color,
        "-stroke",
        "black",
        "-strokewidth",
        "3",
        "-background",
        "none",
        "-size",
        "1200x200",
        "caption:" + title,
        "-geometry",
        "+0+40",
        "-composite",
    ]

    # Optionally add part number (bottom right) onto the image.
    if not no_part_label:
        cmd.extend([
            "-gravity",
            "southeast",
            "-pointsize",
            str(fontsize),
            "-annotate",
            "+40+30",
            f"PART {part_str}",
        ])

    # Output filename (always appended last)
    cmd.append(str(output))

    run(cmd)

    return output.as_posix()


def parse_range(r):
    try:
        start, end = r.split("-")
        return range(int(start), int(end) + 1)
    except Exception:
        raise argparse.ArgumentTypeError("Range must be in form START-END")


def main():
    parser = argparse.ArgumentParser(description="Generate numbered video thumbnails using ImageMagick")

    parser.add_argument("--base", required=True, type=Path, help="Base thumbnail image")
    parser.add_argument("--title", required=True, help="Title text")
    # Make --part, --range and --no-part-label mutually exclusive and require one of them.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--part", type=int, help="Single part number")
    group.add_argument("--range", type=parse_range, help="Part range START-END")
    group.add_argument("--no-part-label", action="store_true", help="Do not draw the 'PART N' label on the image and omit the part from filenames")
    parser.add_argument("--font", default="DejaVu-Sans-Bold", help="Font name or path")
    parser.add_argument("--fontsize", type=int, default=60, help="Font size")
    parser.add_argument("--color", default="white", help="Font color")
    parser.add_argument("--outdir", type=Path, default=Path("thumbnails"), help="Output directory")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads (set 1 to disable parallelism)")
    

    args = parser.parse_args()

    if not args.base.exists():
        logger.error("Base image not found")
        sys.exit(1)

    args.outdir.mkdir(parents=True, exist_ok=True)

    if args.no_part_label:
        parts = [None]
    else:
        parts = list([args.part] if args.part else args.range)

    # Collect (part, path) so we can preserve ordering when printing results.
    outputs: List[tuple] = []

    # If workers == 1 or only a single part, run sequentially to preserve ordering and simplicity.
    if args.workers <= 1 or len(parts) <= 1:
        for part in tqdm(parts):
            outputs.append(
                (part, generate_thumbnail(
                    base=args.base,
                    title=args.title,
                    part=part,
                    font=args.font,
                    fontsize=args.fontsize,
                    color=args.color,
                    outdir=args.outdir,
                    no_part_label=args.no_part_label,
                ))
            )
    else:
        # Parallel execution using a thread pool. ImageMagick subprocess calls are I/O/OS-bound,
        # so threads are a reasonable approach and avoid pickling overhead of processes.
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            future_to_part = {
                ex.submit(
                    generate_thumbnail,
                    args.base,
                    args.title,
                    part,
                    args.font,
                    args.fontsize,
                    args.color,
                    args.outdir,
                    args.no_part_label,
                ): part
                for part in parts
            }

            for fut in tqdm(concurrent.futures.as_completed(future_to_part), total=len(future_to_part)):
                part = future_to_part[fut]
                try:
                    outputs.append((part, fut.result()))
                except Exception as e:
                    logger.error(f"Error generating thumbnail for part {part}: {e}")
                    sys.exit(1)
    # Sort outputs by part number to preserve deterministic ordering
    outputs.sort(key=lambda p: (p[0] is None, p[0] or 0))
    paths = [p for _, p in outputs]

    logger.info("Generated thumbnails:")
    for path in paths:
        logger.info(path)


if __name__ == "__main__":
    setup_logging()
    exit(main())
