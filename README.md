# Thumbnail Generator

A Python package for generating custom YouTube video thumbnails from a base image and automatically uploading them to your YouTube videos.

## Features

- 🎨 **Generate Custom Thumbnails** - Create visually appealing thumbnails from a base image using ImageMagick with customizable text, fonts, and colors
- 📺 **YouTube Integration** - Retrieve video information from YouTube playlists using the official YouTube API
- 📤 **Auto-Upload** - Automatically upload generated thumbnails to your YouTube videos
- 🔄 **Batch Processing** - Handle multiple videos with concurrent thumbnail generation and uploads
- 📝 **Detailed Logging** - Comprehensive logging of all operations for debugging and monitoring

## Requirements

- Python 3.12 or higher
- Poetry 2.2.1
- [ImageMagick](https://imagemagick.org/#gsc.tab=0) installed and available in your PATH
- [YouTube API](https://developers.google.com/youtube/v3/docs) credentials (OAuth2)

## Installation

1. Install Poetry 2.2.1:
```bash
pip install poetry==2.2.1
```

2. Clone the repository:
```bash
git clone <repository-url>
cd thumbnail_generator
```

3. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies using Poetry:
```bash
poetry install
```

5. Install ImageMagick:
- **macOS**: `brew install imagemagick`
- **Windows**: Download from [ImageMagick.org](https://imagemagick.org/script/download.php)
- **Linux**: `sudo apt-get install imagemagick`

## Setup

### YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials as JSON and save as `client_secrets.json` in the project root

## Usage

### 1. Get Video IDs from a YouTube Playlist

```bash
python -m thumbnail_generator.get_youtube_video_ids \
  --playlist-id <PLAYLIST_ID> \
  --client-secrets client_secrets.json \
  --output video_ids.json
```

**Arguments:**
- `--client-secrets` (required): Path to OAuth `client_secrets.json` file
- `--playlist-id` (required): YouTube playlist ID to fetch video IDs from
- `--output` (optional): Path to save the JSON file containing video IDs (default: `video_ids.json`)

**Output:**
- Creates a JSON file with an array of objects containing `video_id` and `title` for each video in the playlist

### 2. Generate Thumbnails

```bash
python -m thumbnail_generator.thumbnail_gen \
  --base path/to/base_image.png \
  --title "My Video Title" \
  --part 1 \
  --outdir ./thumbnails
```

**Required Arguments:**
- `--base` (required): Path to the base thumbnail image
- `--title` (required): Title text to display on the thumbnail
- One of the following mutually exclusive options (required):
  - `--part <NUMBER>`: Generate a single thumbnail for the specified part number
  - `--range <START-END>`: Generate thumbnails for a range of parts (e.g., `1-5`)
  - `--no-part-label`: Generate a single thumbnail without part number label

**Optional Arguments:**
- `--font` (optional): Font name or path (default: `DejaVu-Sans-Bold`)
- `--fontsize` (optional): Font size in pixels (default: `60`)
- `--color` (optional): Font color (default: `white`)
- `--outdir` (optional): Output directory for generated thumbnails (default: `thumbnails`)
- `--workers` (optional): Number of worker threads for parallel generation (default: `4`). Set to `1` to disable parallelism

**Output:**
- Generates thumbnail images in the specified output directory
- For `--part` or `--range`: Files named `thumbnail_part_<N>.png`
- For `--no-part-label`: File named `thumbnail.png`

### 3. Update YouTube Video Thumbnails

```bash
python -m thumbnail_generator.update_youtube_videos \
  --client-secrets client_secrets.json \
  --videos-json video_ids.json \
  --thumbnails-folder ./thumbnails \
  --update
```

**Required Arguments:**
- `--client-secrets` (required): Path to OAuth `client_secrets.json` file
- `--videos-json` (required): Path to JSON file with video information (from step 1)
- `--thumbnails-folder` (required): Folder containing the generated thumbnail images

**Optional Arguments:**
- `--min-part` (optional): Minimum part number to update (filters videos with part >= specified value)
- `--part-range` (optional): Range of part numbers to update in format `START-END` (e.g., `1-10`)
- `--update` (optional): If set, uploads thumbnails to YouTube. Without this flag, only matches thumbnails to videos (dry-run)
- `--max-retries` (optional): Maximum number of upload retries for failed uploads (default: `3`)

**Output:**
- Matches thumbnails to videos based on part numbers in filenames and video titles
- Creates a new JSON file `<original_filename>_with_thumbnails.json` showing the thumbnail assignments
- If `--update` is set, uploads the thumbnails to the corresponding YouTube videos

## Project Structure

```
thumbnail_generator/
├── __init__.py
├── __pycache__/
├── get_youtube_video_ids.py    # Fetch videos from playlists
├── thumbnail_gen.py            # Generate thumbnails with ImageMagick
├── update_youtube_videos.py    # Upload thumbnails to YouTube
└── logging_config.py           # Logging configuration
```

## Example Workflow

```bash
# Step 1: Get videos from your playlist
python -m thumbnail_generator.get_youtube_video_ids \
  --playlist-id "PLxxxxxxxxxxxx" \
  --client-secrets client_secrets.json \
  --output video_ids.json

# Step 2: Generate thumbnails for parts 1-5
python -m thumbnail_generator.thumbnail_gen \
  --base base_image.png \
  --title "Video Title" \
  --range 1-5 \
  --outdir ./thumbnails

# Step 3: Upload all generated thumbnails (matching by part number)
python -m thumbnail_generator.update_youtube_videos \
  --client-secrets client_secrets.json \
  --videos-json video_ids.json \
  --thumbnails-folder ./thumbnails \
  --update
```

## Configuration

Environment variables can be set in a `.env` file:

```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/client_secrets.json
```

## License

[MIT](LICENSE.md)
