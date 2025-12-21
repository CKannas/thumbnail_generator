import argparse
import json
import time
import re
import httplib2
from dataclasses import asdict, dataclass
from pathlib import Path
from tqdm import tqdm
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .logging_config import setup_logging, get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Add HTTP cache
http = httplib2.Http(cache=".cache")

@dataclass
class Video:
    video_id: str
    title: str
    thumbnail_path: Optional[str] = None  # Optional, will be set after matching


def get_authenticated_service(client_secrets_file: Path):
    """
    Authenticate with OAuth2 and return the YouTube service object.
    """
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_file), SCOPES)
    credentials = flow.run_local_server(port=0)  # Opens a browser for OAuth
    return build("youtube", "v3", credentials=credentials)


def match_thumbnails_to_videos(videos, thumbnails_folder: Path):
    """
    Match thumbnails based on Part number in video title and file names.
    """
    thumb_pattern = re.compile(r"thumbnail_part_(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)
    thumbnail_map = {}
    for f in thumbnails_folder.iterdir():
        match = thumb_pattern.match(f.name)
        if match:
            part_number = int(match.group(1))
            thumbnail_map[part_number] = f

    video_pattern = re.compile(r"Part (\d+)$", re.IGNORECASE)
    for video in videos:
        match = video_pattern.search(video.title)
        if match:
            part_number = int(match.group(1))
            video.thumbnail_path = str(thumbnail_map.get(part_number)) if thumbnail_map.get(part_number) else None
            if video.thumbnail_path is None:
                logger.warning(f"No thumbnail found for '{video.title}'")
        else:
            video.thumbnail_path = None
            logger.warning(f"Video title '{video.title}' does not contain a part number")

    return videos


def filter_videos_by_min_part(videos, min_part: int):
    pattern = re.compile(r"Part (\d+)$", re.IGNORECASE)
    filtered = []
    for video in videos:
        match = pattern.search(video.title)
        if match and int(match.group(1)) >= min_part:
            filtered.append(video)
    return filtered


def filter_videos_by_part_range(videos, part_range: tuple[int, int]):
    pattern = re.compile(r"Part (\d+)$", re.IGNORECASE)
    filtered = []
    for video in videos:
        match = pattern.search(video.title)
        if match:
            part_number = int(match.group(1))
            if part_range[0] <= part_number <= part_range[1]:
                filtered.append(video)
    return filtered


def update_video_thumbnail(youtube, video_id, thumbnail_path, max_retries=3, retry_delay=2):
    """Update thumbnail with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            media = MediaFileUpload(thumbnail_path)
            youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
            return True
        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise e


def parse_part_range(range_str: str) -> tuple[int, int]:
    try:
        start, end = map(int, range_str.split("-"))
        if start > end:
            raise ValueError
        return start, end
    except Exception:
        raise argparse.ArgumentTypeError(f"Invalid part range: '{range_str}'. Use format start-end, e.g., 130-145.")


def main():
    parser = argparse.ArgumentParser(description="Match thumbnails and optionally update YouTube videos.")
    parser.add_argument("--client-secrets", type=Path, required=True, help="Path to OAuth client_secrets.json")
    parser.add_argument("--videos-json", required=True, type=Path, help="Path to JSON with videos info")
    parser.add_argument("--thumbnails-folder", required=True, type=Path, help="Folder containing thumbnails")
    parser.add_argument("--min-part", type=int, help="Minimum Part number to update")
    parser.add_argument("--part-range", type=parse_part_range, help="Range of Part numbers to update, format: start-end")
    parser.add_argument("--update", action="store_true", help="Upload thumbnails to YouTube if set")
    args = parser.parse_args()

    # Validate paths
    if not args.videos_json.is_file():
        raise ValueError(f"Videos JSON file not found: {args.videos_json}")
    if not args.thumbnails_folder.is_dir():
        raise ValueError(f"Thumbnails folder not found: {args.thumbnails_folder}")

    # Load videos JSON
    with args.videos_json.open("r", encoding="utf-8") as f:
        videos = [Video(**v) for v in json.load(f)]

    # Apply filters
    if args.min_part:
        videos = filter_videos_by_min_part(videos, args.min_part)
    elif args.part_range:
        videos = filter_videos_by_part_range(videos, args.part_range)

    logger.info(f"{len(videos)} videos selected for processing after filtering.")

    # Always match thumbnails
    videos = match_thumbnails_to_videos(videos, args.thumbnails_folder)

    # Save updated JSON
    updated_json_path = args.videos_json.with_name(args.videos_json.stem + "_with_thumbnails.json")
    with updated_json_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(v) for v in videos], f, indent=4, ensure_ascii=False)
    logger.info(f"Updated JSON with thumbnails saved to {updated_json_path}")

    if args.update:
        # Authenticate
        youtube = get_authenticated_service(args.client_secrets)
        # Sequential upload with progress bar
        log_msgs = []
        for video in tqdm(videos, desc="Uploading thumbnails"):
            if video.thumbnail_path:
                try:
                    update_video_thumbnail(youtube, video.video_id, video.thumbnail_path)
                    log_msgs.append(f"✅ '{video.title}' updated")
                except Exception as e:
                    log_msgs.append(f"❌ Failed '{video.title}': {e}")
            else:
                log_msgs.append(f"⚠️ Skipped '{video.title}': No thumbnail assigned")
        for msg in log_msgs:
            logger.info(msg)
    else:
        logger.info("Update flag not set. Thumbnails were matched but not uploaded to YouTube.")


if __name__ == "__main__":
    setup_logging()
    exit(main())
