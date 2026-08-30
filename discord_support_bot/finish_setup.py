import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=True)

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print(f"❌ Không tìm thấy DISCORD_TOKEN trong {env_path}!")
    sys.exit(1)

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("\n❌ Chưa cài đặt thư viện discord.py!")
    sys.exit(1)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"\n🤖 Bot đã đăng nhập: {bot.user.name}")
    
    if not bot.guilds:
        print("❌ Bot chưa vào server nào.")
        await bot.close()
        return

    guild = bot.guilds[0]
    print(f"👉 Đang dọn dẹp và hoàn thiện server: {guild.name}\n")

    # 1. XÓA CÁC KÊNH / CATEGORY CŨ DƯ THỪA
    old_channel_names = ["staff-bugs", "chào-mừng", "chao-mung", "vie-chat", "eng-chat"]
    old_category_names = ["TEXT-CHAT", "Hỗ trợ", "Thông báo", "Nội bộ"]

    print("--- 1. TỰ ĐỘNG DỌN DẸP KÊNH CŨ ---")
    for ch in list(guild.text_channels):
        # Chỉ xóa kênh cũ không thuộc các danh mục mới tạo
        is_in_old_cat = ch.category and ch.category.name in old_category_names
        is_loose_old = ch.category is None and ch.name in old_channel_names
        if (ch.name in old_channel_names and is_in_old_cat) or is_loose_old or ch.name in ["vie-chat", "eng-chat"]:
            try:
                await ch.delete(reason="Dọn dẹp kênh cũ")
                print(f"  🗑️ Đã xóa kênh cũ: #{ch.name}")
            except Exception as e:
                pass

    for cat in list(guild.categories):
        if cat.name in old_category_names:
            try:
                await cat.delete(reason="Dọn dẹp danh mục cũ")
                print(f"  🗑️ Đã xóa danh mục cũ: {cat.name}")
            except Exception as e:
                pass

    # 2. ĐĂNG BÀI GHIM ĐẸP VÀO CÁC KÊNH
    print("\n--- 2. TỰ ĐỘNG ĐĂNG BÀI VÀO CÁC KÊNH CHÍNH ---")
    
    # Kênh Liên Kết
    links_ch = discord.utils.get(guild.text_channels, name="🔗-liên-kết-chính-thức")
    if links_ch:
        embed = discord.Embed(
            title="🔗 LIÊN KẾT CHÍNH THỨC - MTH RECAP STUDIO",
            description="Tất cả các nguồn tải và kênh chính thức của phần mềm **MTH Recap Studio**:",
            color=discord.Color.teal()
        )
        embed.add_field(name="📦 Tải Bản Cập Nhật Mới Nhất", value="[GitHub Releases (Tải App Setup)](https://github.com/mthrecapstudio/MTHRecapStudiodl/releases)", inline=False)
        embed.add_field(name="🌐 Trang Chủ / Mã Nguồn", value="[MTH Recap Studio Repository](https://github.com/mthrecapstudio/MTHRecapStudiodl)", inline=False)
        embed.add_field(name="💬 Kênh Hỗ Trợ Kỹ Thuật", value="Báo sự cố tại kênh #🐛-báo-lỗi hoặc liên hệ Ban Quản Trị.", inline=False)
        embed.set_footer(text="MTH Recap Studio • Luôn tải từ nguồn chính thức để tránh virus")
        await links_ch.send(embed=embed)
        print("  ✓ Đã đăng bài vào #🔗-liên-kết-chính-thức")

    # Kênh FAQ
    faq_ch = discord.utils.get(guild.text_channels, name="❓-faq-hỏi-đáp-nhanh")
    if faq_ch:
        embed = discord.Embed(
            title="❓ CÂU HỎI THƯỜNG GẶP (FAQ)",
            description="Tổng hợp các thắc mắc và cách xử lý lỗi cơ bản khi dùng app:",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="1. App có yêu cầu Card đồ họa (GPU) không?",
            value="MTH Recap tối ưu tốt nhất trên GPU NVIDIA (hỗ trợ CUDA). Nếu dùng CPU hoặc card AMD, hệ thống vẫn chạy được với tốc độ tương ứng.",
            inline=False
        )
        embed.add_field(
            name="2. Bị lỗi render video hoặc không nhận giọng đọc?",
            value="Hãy kiểm tra xem máy tính đã cài đặt đầy đủ gói FFmpeg và model giọng chưa. Xem chi tiết tại kênh hướng dẫn.",
            inline=False
        )
        embed.add_field(
            name="3. Làm sao để nâng cấp bản quyền / tính năng Pro?",
            value="Vui lòng tạo tin nhắn trong kênh #🐛-báo-lỗi hoặc nhắn trực tiếp cho Ban Quản Trị.",
            inline=False
        )
        await faq_ch.send(embed=embed)
        print("  ✓ Đã đăng bài vào #❓-faq-hỏi-đáp-nhanh")

    # Kênh Hướng Dẫn Cài Đặt
    guide_ch = discord.utils.get(guild.text_channels, name="📖-hướng-dẫn-cài-đặt")
    if guide_ch:
        embed = discord.Embed(
            title="📖 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG",
            description="Các bước để bắt đầu sử dụng **MTH Recap Studio** một cách trơn tru nhất:",
            color=discord.Color.green()
        )
        embed.add_field(name="Bước 1: Tải bộ cài", value="Tải file `MTH_Recap_Studio_Setup_v*.exe` từ mục thông báo hoặc kênh liên kết.", inline=False)
        embed.add_field(name="Bước 2: Cài đặt và cấp quyền", value="Chạy file cài đặt với quyền Administrator (Run as Administrator) để tránh lỗi ghi file.", inline=False)
        embed.add_field(name="Bước 3: Khởi động & Tạo dự án", value="Mở app, chọn thư mục lưu trữ và bắt đầu import kịch bản/hình ảnh để dựng video tự động!", inline=False)
        await guide_ch.send(embed=embed)
        print("  ✓ Đã đăng bài vào #📖-hướng-dẫn-cài-đặt")

    # 3. TẠO LINK MỜI VĨNH VIỄN
    print("\n--- 3. TẠO LINK MỜI SERVER VĨNH VIỄN ---")
    invite_ch = discord.utils.get(guild.text_channels, name="📢-thông-báo") or guild.text_channels[0]
    invite = await invite_ch.create_invite(max_age=0, max_uses=0, reason="Link mời vĩnh viễn cho cộng đồng")
    print(f"  🔗 Link mời Discord vĩnh viễn của bạn: {invite.url}")

    # 4. TỰ ĐỘNG CẬP NHẬT CÁC ID VÀO FILE .env
    bug_ch = discord.utils.get(guild.text_channels, name="🐛-báo-lỗi")
    staff_bug_ch = discord.utils.get(guild.text_channels, name="🐛-staff-bugs-dev")
    staff_role = discord.utils.get(guild.roles, name="🛠️ Hỗ Trợ / Staff")

    if bug_ch and env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        import re
        content = re.sub(r"BUG_CHANNEL_ID=.*", f"BUG_CHANNEL_ID={bug_ch.id}", content)
        if staff_bug_ch:
            content = re.sub(r"STAFF_BUG_CHANNEL_ID=.*", f"STAFF_BUG_CHANNEL_ID={staff_bug_ch.id}", content)
        if staff_role:
            content = re.sub(r"SUPPORT_ROLE_ID=.*", f"SUPPORT_ROLE_ID={staff_role.id}", content)
            
        env_path.write_text(content, encoding="utf-8")
        print("  ✓ Đã tự động cập nhật chính xác các ID kênh vào file .env!")

    print("\n=======================================================")
    print("🎉 TẤT CẢ ĐÃ XONG 100%! SERVER CỦA BẠN ĐÃ SẴN SÀNG HOÀN TOÀN.")
    print(f"👉 Link mời người dùng: {invite.url}")
    print("=======================================================\n")
    
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
