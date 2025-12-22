import argparse
import json
import httplib2
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from thumbnail_generator.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


# Add HTTP cache
http = httplib2.Http(cache=".cache")


@dataclass
class VideoInfo:
    video_id: str
    title: str


def get_authenticated_service(client_secrets_file: Path):
    """
    Authenticate with OAuth2 and return the YouTube service object.
    """
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_file), SCOPES)
    credentials = flow.run_local_server(port=0)  # Opens a browser for OAuth
    return build("youtube", "v3", credentials=credentials)


def get_video_ids_from_playlist(playlist_id: str, youtube: Any) -> List[VideoInfo]:
    """
    Retrieve all video IDs and titles from a playlist.
    For videos listed as "Private Video", fetch the actual title via videos.list.
    """
    videos: List[VideoInfo] = []
    private_ids: List[str] = []
    next_page_token = None

    while True:
        playlist_request = youtube.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token,
        )
        playlist_response = playlist_request.execute()

        for item in playlist_response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            title = item["snippet"]["title"]
            if title == "Private Video":
                private_ids.append(video_id)
                title = ""  # Placeholder, will fetch later
            videos.append(VideoInfo(video_id=video_id, title=title))

        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    # Fetch real titles for private videos
    for i in range(0, len(private_ids), 50):
        chunk_ids = private_ids[i:i+50]
        videos_request = youtube.videos().list(
            part="snippet",
            id=",".join(chunk_ids),
        )
        videos_response = videos_request.execute()
        for item in videos_response.get("items", []):
            # Find matching VideoInfo
            vid = next((v for v in videos if v.video_id == item["id"]), None)
            if vid:
                vid.title = item["snippet"]["title"]

    return videos


def save_video_ids(videos, filename="video_ids.json"):
    """Save video IDs to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([asdict(video) for video in videos], f, indent=4, ensure_ascii=False)
    logger.info(f"Video IDs saved to {filename} successfully.")


def main():
    parser = argparse.ArgumentParser(description="Retrieve YouTube video IDs from a playlist.")
    parser.add_argument("--client-secrets", type=Path, required=True, help="Path to OAuth client_secrets.json")
    parser.add_argument("--playlist-id", required=True, help="YouTube playlist ID to fetch video IDs from")
    parser.add_argument(
        "--output",
        default="video_ids.json",
        help="Path to save the JSON file containing video IDs (default: video_ids.json)",
    )
    args = parser.parse_args()

    # Authenticate
    youtube = get_authenticated_service(args.client_secrets)

    try:
        video_ids = get_video_ids_from_playlist(args.playlist_id, youtube)
        logger.info(f"Retrieved {len(video_ids)} video IDs.")
        save_video_ids(video_ids, args.output)
    except Exception as e:
        logger.error(f"Error retrieving video IDs: {e}")


if __name__ == "__main__":
    setup_logging()
    exit(main())
