import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=True)

TOKEN = os.getenv("DISCORD_TOKEN")

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("❌ Chưa cài đặt discord.py")
    sys.exit(1)

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

VALID_CATEGORIES = [
    "📢 ── THÔNG TIN CHÍNH THỨC ──",
    "💬 ── THẢO LUẬN & GIAO LƯU ──",
    "🛠️ ── HỖ TRỢ KỸ THUẬT ──",
    "🔒 ── BAN QUẢN TRỊ (STAFF ONLY) ──"
]

@bot.event
async def on_ready():
    print(f"🤖 Đã kết nối: {bot.user.name}")
    guild = bot.guilds[0]
    print(f"Server: {guild.name}")
    
    print("\n--- ĐANG XÓA TOÀN BỘ KÊNH CŨ NGOÀI DANH MỤC CHUẨN ---")
    
    # 1. Xóa tất cả các kênh text không nằm trong VALID_CATEGORIES
    for ch in list(guild.text_channels):
        if not ch.category or ch.category.name not in VALID_CATEGORIES:
            try:
                await ch.delete(reason="Xóa kênh cũ dư thừa")
                print(f"  🗑️ Đã xóa kênh cũ: {ch.name}")
            except Exception as e:
                print(f"  ❌ Không thể xóa kênh {ch.name}: {e}")

    # 2. Xóa các Category không nằm trong VALID_CATEGORIES
    for cat in list(guild.categories):
        if cat.name not in VALID_CATEGORIES:
            try:
                await cat.delete(reason="Xóa danh mục cũ dư thừa")
                print(f"  🗑️ Đã xóa danh mục cũ: {cat.name}")
            except Exception as e:
                print(f"  ❌ Không thể xóa danh mục {cat.name}: {e}")

    print("\n✅ ĐÃ DỌN SẠCH 100% CÁC KÊNH THỪA!")
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
