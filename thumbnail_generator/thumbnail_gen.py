import argparse
import subprocess
import sys
from pathlib import Path

OUTER = 20
INNER = 4
WIDTH = 1280
HEIGHT = 720


def run(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Error running ImageMagick command")
        sys.exit(1)


def generate_thumbnail(base, title, part, font, fontsize, color, outdir):
    part_str = f"{part:01d}"
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
        # Part number (bottom right)
        "-gravity",
        "southeast",
        "-pointsize",
        str(fontsize),
        "-annotate",
        "+40+30",
        f"PART {part_str}",
        str(output),
    ]

    run(cmd)
    print(f"Generated: {output}")


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
    parser.add_argument("--part", type=int, help="Single part number")
    parser.add_argument("--range", type=parse_range, help="Part range START-END")

    parser.add_argument("--font", default="DejaVu-Sans-Bold", help="Font name or path")
    parser.add_argument("--fontsize", type=int, default=60, help="Font size")
    parser.add_argument("--color", default="white", help="Font color")
    parser.add_argument("--outdir", type=Path, default=Path("thumbnails"), help="Output directory")

    args = parser.parse_args()

    if not args.part and not args.range:
        parser.error("You must specify --part or --range")

    if args.part and args.range:
        parser.error("Use only one of --part or --range")

    if not args.base.exists():
        print("Base image not found")
        sys.exit(1)

    args.outdir.mkdir(parents=True, exist_ok=True)

    parts = [args.part] if args.part else args.range

    for part in parts:
        generate_thumbnail(
            base=args.base,
            title=args.title,
            part=part,
            font=args.font,
            fontsize=args.fontsize,
            color=args.color,
            outdir=args.outdir,
        )


if __name__ == "__main__":
    exit(main())
