#!/usr/bin/env python3
"""Probe what the YouTube Data API v3 can return for specific video IDs.

This is a discovery utility, not production code. It focuses on the parts that
matter for the curator design:
- metadata enrichment via videos.list
- optional caption-track discovery via captions.list

Notes:
- An API key is enough for videos.list metadata.
- captions.list requires OAuth and only returns caption track metadata.
- captions.download requires permission to edit the video, so it is not a
  general transcript solution for arbitrary third-party videos.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_BASE = "https://www.googleapis.com/youtube/v3"
VIDEO_PARTS = [
    "snippet",
    "contentDetails",
    "statistics",
    "status",
    "topicDetails",
    "recordingDetails",
    "liveStreamingDetails",
]


def build_url(path: str, params: dict[str, Any]) -> str:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{API_BASE}/{path}?{query}"


class ApiError(RuntimeError):
    pass


def fetch_json(url: str, oauth_token: str | None = None) -> dict[str, Any]:
    req = urllib.request.Request(url)
    if oauth_token:
        req.add_header("Authorization", f"Bearer {oauth_token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"HTTP {exc.code} for {url}\n{body}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Request failed for {url}: {exc}") from exc


def fetch_videos(api_key: str, video_ids: list[str]) -> dict[str, Any]:
    return fetch_json(
        build_url(
            "videos",
            {
                "part": ",".join(VIDEO_PARTS),
                "id": ",".join(video_ids),
                "key": api_key,
                "maxResults": len(video_ids),
            },
        )
    )


def fetch_captions(oauth_token: str, video_id: str) -> dict[str, Any]:
    return fetch_json(
        build_url(
            "captions",
            {
                "part": "id,snippet",
                "videoId": video_id,
            },
        ),
        oauth_token=oauth_token,
    )


def summarize_video(item: dict[str, Any]) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})
    statistics = item.get("statistics", {})
    return {
        "video_id": item.get("id"),
        "title": snippet.get("title"),
        "channel_title": snippet.get("channelTitle"),
        "channel_id": snippet.get("channelId"),
        "published_at": snippet.get("publishedAt"),
        "description": snippet.get("description"),
        "tags": snippet.get("tags"),
        "category_id": snippet.get("categoryId"),
        "duration": content_details.get("duration"),
        "definition": content_details.get("definition"),
        "caption_flag": content_details.get("caption"),
        "licensed_content": content_details.get("licensedContent"),
        "view_count": statistics.get("viewCount"),
        "like_count": statistics.get("likeCount"),
        "comment_count": statistics.get("commentCount"),
        "topic_categories": item.get("topicDetails", {}).get("topicCategories"),
        "recording_date": item.get("recordingDetails", {}).get("recordingDate"),
        "privacy_status": item.get("status", {}).get("privacyStatus"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "video_ids",
        nargs="+",
        help="One or more YouTube video IDs to inspect",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("YOUTUBE_API_KEY"),
        help="YouTube Data API key. Defaults to YOUTUBE_API_KEY.",
    )
    parser.add_argument(
        "--oauth-token",
        default=os.getenv("YOUTUBE_OAUTH_TOKEN"),
        help="OAuth bearer token for authenticated endpoints like captions.list.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw API responses instead of the summarized output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print("Missing API key. Set YOUTUBE_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    try:
        videos_response = fetch_videos(args.api_key, args.video_ids)
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    items = videos_response.get("items", [])
    output: dict[str, Any] = {
        "requested_video_ids": args.video_ids,
        "returned_count": len(items),
        "videos": videos_response if args.raw else [summarize_video(item) for item in items],
        "captions": {},
        "notes": [
            "videos.list is suitable for metadata enrichment once you already have video IDs.",
            "YouTube Data API does not expose your personalized signed-in homepage recommendations as a reliable enrichment endpoint.",
            "captions.list only reveals caption track metadata and requires OAuth.",
            "captions.download requires permission to edit the video, so it is not a general transcript path for arbitrary third-party videos.",
        ],
    }

    if args.oauth_token:
        for video_id in args.video_ids:
            try:
                captions = fetch_captions(args.oauth_token, video_id)
                output["captions"][video_id] = captions if args.raw else captions.get("items", [])
            except ApiError as exc:
                output["captions"][video_id] = {"error": str(exc)}
    else:
        output["captions"] = "OAuth token not provided; skipped captions.list probing."

    json.dump(output, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
