"""youtube_publisher.py — Upload video to YouTube using YouTube Data API v3."""

import os
import time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle

from utils.logger import get_logger

logger = get_logger("youtube_publisher")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "credentials/youtube_token.pickle"
CLIENT_SECRETS_FILE = "credentials/client_secrets.json"


def get_authenticated_service():
    """Authenticate with YouTube API and return a service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired YouTube credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"Client secrets file not found: {CLIENT_SECRETS_FILE}\n"
                    "Download it from Google Cloud Console and place it in credentials/"
                )
            logger.info("Launching OAuth flow for YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        Path(TOKEN_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
        logger.info("YouTube credentials saved.")

    service = build("youtube", "v3", credentials=creds)
    return service


def build_video_metadata(title: str, description: str, tags: list[str], category_id: str = "22") -> dict:
    """Build the YouTube video metadata body."""
    return {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
            "defaultLanguage": "fr",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: str | None = None,
    category_id: str = "22",
) -> str:
    """Upload a video to YouTube Shorts.

    Args:
        video_path: Path to the final video file.
        title: Video title (max 100 chars).
        description: Video description (max 5000 chars).
        tags: List of tags.
        thumbnail_path: Optional path to thumbnail image.
        category_id: YouTube category ID (default 22 = People & Blogs).

    Returns:
        YouTube video ID.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.info(f"Authenticating with YouTube API...")
    service = get_authenticated_service()

    body = build_video_metadata(title, description, tags, category_id)

    logger.info(f"Uploading video: {video_path}")
    logger.info(f"Title: {title}")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,  # 5MB chunks
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    video_id = None
    response = None
    retry = 0
    max_retries = 5

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")
        except Exception as e:
            if retry < max_retries:
                retry += 1
                wait = 2 ** retry
                logger.warning(f"Upload error (attempt {retry}/{max_retries}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Upload failed after {max_retries} retries: {e}")
                raise

    video_id = response.get("id")
    logger.info(f"Video uploaded successfully! ID: {video_id}")
    logger.info(f"URL: https://www.youtube.com/shorts/{video_id}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            logger.info(f"Uploading thumbnail: {thumbnail_path}")
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path),
            ).execute()
            logger.info("Thumbnail uploaded.")
        except Exception as e:
            logger.warning(f"Thumbnail upload failed (non-critical): {e}")

    return video_id


def build_shorts_description(topic: str, keywords: list[str], niche: str) -> str:
    """Build a YouTube Shorts optimized description."""
    hashtags = " ".join([f"#{kw.replace(' ', '')}" for kw in keywords[:10]])
    description = (
        f"{topic}\n\n"
        f"Dans cette video, on explore ce sujet de maniere claire et engageante.\n\n"
        f"Niche: {niche}\n\n"
        f"{hashtags}\n\n"
        f"#Shorts #YouTube"
    )
    return description
