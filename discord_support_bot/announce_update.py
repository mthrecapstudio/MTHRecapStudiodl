from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
STATE_PATH = ROOT / "data" / "last_announced_version.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Announce a new MTH Recap update to Discord once per version.")
    parser.add_argument("--version", default="", help="Version to announce. Defaults to backend/__init__.py.")
    parser.add_argument("--notes", default="", help="Release notes text or path to a markdown/txt file.")
    parser.add_argument("--url", default="", help="Optional download/changelog URL.")
    parser.add_argument("--force", action="store_true", help="Post even if this version was already announced.")
    return parser.parse_args()


def detect_version() -> str:
    candidates = [
        REPO_ROOT / "backend" / "__init__.py",
        REPO_ROOT / "backend" / "main.py",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"(?:__version__\s*=\s*|version\s*=\s*)[\"']([^\"']+)[\"']", text)
        if match:
            return match.group(1)
    return "unknown"


def load_notes(value: str) -> str:
    if not value:
        return "Bản cập nhật mới đã sẵn sàng. Vui lòng tải bản mới nhất để nhận sửa lỗi và cải thiện ổn định."

    possible_path = Path(value)
    if not possible_path.is_absolute():
        possible_path = REPO_ROOT / possible_path
    if possible_path.exists() and possible_path.is_file():
        return possible_path.read_text(encoding="utf-8", errors="ignore").strip()

    return value.strip()


def already_announced(version: str) -> bool:
    return STATE_PATH.exists() and STATE_PATH.read_text(encoding="utf-8").strip() == version


def mark_announced(version: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(version, encoding="utf-8")


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    webhook_url = os.getenv("DISCORD_ANNOUNCE_WEBHOOK", "").strip()
    if not webhook_url:
        print("Missing DISCORD_ANNOUNCE_WEBHOOK in discord_support_bot/.env", file=sys.stderr)
        return 1

    version = args.version.strip() or detect_version()
    if not args.force and already_announced(version):
        print(f"Version {version} was already announced. Use --force to post again.")
        return 0

    notes = load_notes(args.notes)
    if len(notes) > 3500:
        notes = notes[:3497] + "..."

    fields = []
    if args.url:
        fields.append({"name": "Tải bản mới", "value": args.url, "inline": False})

    response = requests.post(
        webhook_url,
        json={
            "content": "@everyone",
            "allowed_mentions": {"parse": ["everyone"]},
            "embeds": [
                {
                    "title": f"MTH Recap v{version} đã có bản cập nhật",
                    "description": notes,
                    "color": 0x2F80ED,
                    "fields": fields,
                }
            ],
        },
        timeout=20,
    )
    response.raise_for_status()
    mark_announced(version)
    print(f"Announced version {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
