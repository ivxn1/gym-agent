import os
import logging
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Fallback curated links when API is unavailable or quota exceeded
FALLBACK_LINKS: dict[str, str] = {
    "jumping jacks": "https://youtu.be/c4DAnQ6DtF8",
    "burpees": "https://youtu.be/dZgVxmf6jkA",
    "mountain climbers": "https://youtu.be/nmwgirgXLYM",
    "high knees": "https://youtu.be/ZZZoCNMU48U",
    "squat": "https://youtu.be/aclHkVaku9U",
    "push up": "https://youtu.be/_l3ySVKYVJ8",
    "plank": "https://youtu.be/pSHjTRCQxIw",
    "lunge": "https://youtu.be/QOVaHwm-Q6U",
    "hip thrust": "https://youtu.be/xDmFkJxPzeM",
    "resistance band row": "https://youtu.be/GZbfZ033f74",
    "resistance band curl": "https://youtu.be/QC3vqlhBL4E",
    "resistance band press": "https://youtu.be/3EFl9xZ3KYo",
    "jump rope": "https://youtu.be/FJmRQ5iTXKE",
    "russian twist": "https://youtu.be/wkD8rjkodUI",
    "leg raise": "https://youtu.be/JB2oyawG9KI",
    "crunches": "https://youtu.be/Xyd_fa5zoEU",
    "glute bridge": "https://youtu.be/wPM8icPu6H8",
    "dead bug": "https://youtu.be/4XLEnwUr1d8",
    "bird dog": "https://youtu.be/wiFNA3sqjCA",
    "inchworm": "https://youtu.be/7kgZnJGDNMU",
    "world's greatest stretch": "https://youtu.be/Tz8s0SMLefY",
    "hip circles": "https://youtu.be/XoVKpKcV3g8",
    "foam rolling": "https://youtu.be/SaD1YXLUVIY",
}


async def search_youtube(exercise_name: str) -> str:
    """Return a YouTube URL for the exercise. Uses API if key present, else fallback."""
    # Check fallback first (fast path)
    lower = exercise_name.lower()
    for key, url in FALLBACK_LINKS.items():
        if key in lower:
            return url

    if not YOUTUBE_API_KEY:
        return _build_search_url(exercise_name)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(YOUTUBE_SEARCH_URL, params={
                "part": "snippet",
                "q": f"{exercise_name} how to exercise tutorial",
                "maxResults": 1,
                "type": "video",
                "key": YOUTUBE_API_KEY,
                "relevanceLanguage": "en",
                "videoDuration": "short",
            })
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if items:
                video_id = items[0]["id"]["videoId"]
                return f"https://youtu.be/{video_id}"
    except Exception as e:
        logger.warning("YouTube API error for '%s': %s", exercise_name, e)

    return _build_search_url(exercise_name)


def _build_search_url(exercise_name: str) -> str:
    query = exercise_name.replace(" ", "+") + "+exercise+tutorial"
    return f"https://www.youtube.com/results?search_query={query}"
