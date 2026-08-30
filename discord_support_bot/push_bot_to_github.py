import os
import sys
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO", "mthrecapstudio/MTHRecapStudiodl")

if not TOKEN:
    print("❌ Không tìm thấy GITHUB_TOKEN trong .env!")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "mth-discord-bot-uploader"
}

files_to_upload = [
    ("discord_support_bot/bot.py", Path("d:/mthrecap/discord_support_bot/bot.py")),
    ("discord_support_bot/requirements.txt", Path("d:/mthrecap/discord_support_bot/requirements.txt")),
    ("discord_support_bot/responses.json", Path("d:/mthrecap/discord_support_bot/responses.json")),
    ("discord_support_bot/knowledge_base.md", Path("d:/mthrecap/discord_support_bot/knowledge_base.md")),
    ("discord_support_bot/README.md", Path("d:/mthrecap/discord_support_bot/README.md")),
    ("discord_support_bot/documents/bang_gia_va_tinh_nang.md", Path("d:/mthrecap/discord_support_bot/documents/bang_gia_va_tinh_nang.md")),
    ("discord_support_bot/documents/cam_nang_khac_phuc_su_co.md", Path("d:/mthrecap/discord_support_bot/documents/cam_nang_khac_phuc_su_co.md")),
    ("discord_support_bot/documents/huong_dan_su_dung_toan_tap.md", Path("d:/mthrecap/discord_support_bot/documents/huong_dan_su_dung_toan_tap.md")),
    ("render.yaml", Path("d:/mthrecap/render.yaml")),
]

print(f"🚀 Đang tải toàn bộ code bot lên GitHub repo: {REPO}...\n")

for repo_path, local_path in files_to_upload:
    if not local_path.exists():
        print(f"⚠️ Bỏ qua {repo_path} (file không tồn tại trên máy)")
        continue

    content = local_path.read_bytes()
    encoded_content = base64.b64encode(content).decode("utf-8")

    # Kiểm tra xem file đã tồn tại trên repo chưa để lấy SHA
    url = f"https://api.github.com/repos/{REPO}/contents/{repo_path}"
    get_res = requests.get(url, headers=headers)
    
    sha = None
    if get_res.status_code == 200:
        sha = get_res.json().get("sha")

    payload = {
        "message": f"Deploy: add/update {repo_path} for Render",
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        print(f"  ✅ Đã tải lên GitHub: {repo_path}")
    else:
        print(f"  ❌ Lỗi tải lên {repo_path}: {put_res.status_code} - {put_res.text}")

print("\n🎉 ĐÃ TẢI TOÀN BỘ CODE BOT LÊN GITHUB THÀNH CÔNG!")
