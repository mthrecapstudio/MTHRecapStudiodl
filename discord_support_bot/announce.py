from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a Discord announcement through a webhook.")
    parser.add_argument("--title", required=True, help="Announcement title")
    parser.add_argument("--message", required=True, help="Announcement body")
    parser.add_argument("--url", default="", help="Optional call-to-action URL")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    webhook_url = os.getenv("DISCORD_ANNOUNCE_WEBHOOK", "").strip()
    if not webhook_url:
        print("Missing DISCORD_ANNOUNCE_WEBHOOK in environment or .env", file=sys.stderr)
        return 1

    fields = []
    if args.url:
        fields.append({"name": "Link", "value": args.url, "inline": False})

    response = requests.post(
        webhook_url,
        json={
            "embeds": [
                {
                    "title": args.title,
                    "description": args.message,
                    "color": 0x2F80ED,
                    "fields": fields,
                }
            ]
        },
        timeout=20,
    )
    response.raise_for_status()
    print("Announcement sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
