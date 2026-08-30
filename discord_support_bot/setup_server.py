import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Tải biến môi trường từ .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("\n❌ Chưa cài đặt thư viện discord.py!")
    print("👉 Hãy chạy lệnh: pip install discord.py python-dotenv\n")
    sys.exit(1)

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN or TOKEN.strip() == "":
    print("\n⚠️ CHƯA CÓ BOT TOKEN!")
    print(f"👉 Vui lòng mở file '{env_path}' và điền DISCORD_TOKEN=bot_token_cua_ban")
    print("   Hoặc nhập trực tiếp tại đây:")
    TOKEN = input("Nhập Discord Bot Token: ").strip()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"\n=======================================================")
    print(f"🤖 Bot đã đăng nhập thành công: {bot.user.name} ({bot.user.id})")
    print(f"=======================================================")
    
    guilds = list(bot.guilds)
    if not guilds:
        print("\n❌ Bot chưa tham gia server nào!")
        print("👉 Hãy mời bot vào server Discord của bạn trước bằng link OAuth2.")
        await bot.close()
        return

    print("\n📋 Danh sách server bot đang tham gia:")
    for idx, g in enumerate(guilds, start=1):
        print(f"  [{idx}] {g.name} (ID: {g.id})")

    if len(guilds) == 1:
        target_guild = guilds[0]
        print(f"\n👉 Tự động chọn server duy nhất: **{target_guild.name}**")
    else:
        choice = input(f"\nNhập số thứ tự server muốn setup (1-{len(guilds)}): ").strip()
        try:
            target_guild = guilds[int(choice) - 1]
        except Exception:
            target_guild = guilds[0]

    print(f"\n🚀 Đang tiến hành tạo cấu trúc Kênh & Phân quyền cho server: {target_guild.name}...")
    
    try:
        await build_discord_structure(target_guild)
    except Exception as e:
        print(f"\n❌ Có lỗi xảy ra trong quá trình setup: {e}")
    finally:
        print("\n🎉 Hoàn thành! Đang ngắt kết nối bot...")
        await bot.close()

async def build_discord_structure(guild: discord.Guild):
    everyone = guild.default_role

    print("\n--- 1. TẠO VAI TRÒ (ROLES) ---")
    roles_created = {}

    # Danh sách Role chuẩn
    role_definitions = [
        {"name": "👑 Ban Quản Trị", "color": discord.Color.red(), "admin": True, "hoist": True},
        {"name": "🛠️ Hỗ Trợ / Staff", "color": discord.Color.blue(), "admin": False, "hoist": True},
        {"name": "⭐ VIP Member", "color": discord.Color.gold(), "admin": False, "hoist": True},
        {"name": "✅ Thành Viên", "color": discord.Color.green(), "admin": False, "hoist": False},
        {"name": "🔇 Muted", "color": discord.Color.dark_grey(), "admin": False, "hoist": False},
    ]

    existing_roles = {r.name: r for r in guild.roles}

    for r_def in role_definitions:
        r_name = r_def["name"]
        if r_name in existing_roles:
            print(f"  ✓ Role đã tồn tại: {r_name}")
            roles_created[r_name] = existing_roles[r_name]
        else:
            perms = discord.Permissions.all() if r_def["admin"] else discord.Permissions.none()
            new_role = await guild.create_role(
                name=r_name,
                colour=r_def["color"],
                permissions=perms,
                hoist=r_def["hoist"],
                reason="MTH Recap Auto Server Setup"
            )
            print(f"  + Đã tạo Role: {r_name}")
            roles_created[r_name] = new_role

    admin_role = roles_created.get("👑 Ban Quản Trị")
    staff_role = roles_created.get("🛠️ Hỗ Trợ / Staff")

    print("\n--- 2. TẠO DANH MỤC & KÊNH (CATEGORIES & CHANNELS) ---")
    
    # Cấu hình danh mục và các kênh
    categories_layout = [
        {
            "name": "📢 ── THÔNG TIN CHÍNH THỨC ──",
            "channels": [
                {
                    "name": "📢-thông-báo",
                    "topic": "Thông báo cập nhật bản phát hành, tính năng mới của MTH Recap Studio",
                    "read_only": True
                },
                {
                    "name": "📜-nội-quy",
                    "topic": "Nội quy văn hóa cộng đồng MTH Recap",
                    "read_only": True
                },
                {
                    "name": "🔗-liên-kết-chính-thức",
                    "topic": "Tải phần mềm, Website, GitHub & Tài liệu chính thức",
                    "read_only": True
                },
                {
                    "name": "❓-faq-hỏi-đáp-nhanh",
                    "topic": "Tổng hợp các câu hỏi và lỗi thường gặp nhất",
                    "read_only": True
                }
            ]
        },
        {
            "name": "💬 ── THẢO LUẬN & GIAO LƯU ──",
            "channels": [
                {
                    "name": "🇻🇳-thảo-luận-chung",
                    "topic": "Kênh giao lưu, trò chuyện tiếng Việt cho anh em sáng tạo nội dung",
                    "read_only": False
                },
                {
                    "name": "🇺🇸-general-chat",
                    "topic": "International English community chat for MTH Recap Studio",
                    "read_only": False
                },
                {
                    "name": "💡-góp-ý-tính-năng",
                    "topic": "Đóng góp ý tưởng, yêu cầu thêm tính năng mới cho app",
                    "read_only": False
                },
                {
                    "name": "🌟-khoe-thành-quả",
                    "topic": "Nơi chia sẻ video, hình ảnh và sản phẩm hoàn thiện từ MTH Recap",
                    "read_only": False
                }
            ]
        },
        {
            "name": "🛠️ ── HỖ TRỢ KỸ THUẬT ──",
            "channels": [
                {
                    "name": "📖-hướng-dẫn-cài-đặt",
                    "topic": "Hướng dẫn cài đặt, kích hoạt bản quyền và cấu hình GPU/Torch",
                    "read_only": True
                },
                {
                    "name": "🐛-báo-lỗi",
                    "topic": "Gửi báo lỗi phần mềm tại đây. Bot AI sẽ tự động hỗ trợ và tạo thread riêng!",
                    "read_only": False
                },
                {
                    "name": "🎫-yêu-cầu-hỗ-trợ",
                    "topic": "Kênh liên hệ hỗ trợ riêng tư về bản quyền hoặc sự cố",
                    "read_only": False
                }
            ]
        },
        {
            "name": "🔒 ── BAN QUẢN TRỊ (STAFF ONLY) ──",
            "staff_only": True,
            "channels": [
                {
                    "name": "💬-staff-chat",
                    "topic": "Thảo luận nội bộ đội ngũ hỗ trợ",
                    "read_only": False
                },
                {
                    "name": "🐛-staff-bugs-dev",
                    "topic": "Kênh nhận thông báo lỗi tự động đẩy về cho Lập trình viên",
                    "read_only": False
                }
            ]
        }
    ]

    saved_channel_ids = {}

    for cat_data in categories_layout:
        cat_name = cat_data["name"]
        
        # Thiết lập quyền cho Category
        overwrites = {
            everyone: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        if cat_data.get("staff_only"):
            # Ẩn hoàn toàn với @everyone, chỉ Staff và Admin xem được
            overwrites[everyone] = discord.PermissionOverwrite(read_messages=False)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Kiểm tra xem danh mục đã có chưa
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            category = await guild.create_category(cat_name, overwrites=overwrites)
            print(f"\n📁 Đã tạo Danh mục: {cat_name}")
        else:
            print(f"\n📁 Danh mục đã có: {cat_name}")

        # Tạo các kênh con
        for ch_data in cat_data["channels"]:
            ch_name = ch_data["name"]
            existing_ch = discord.utils.get(guild.text_channels, name=ch_name, category=category)
            
            ch_overwrites = dict(overwrites)
            if ch_data.get("read_only"):
                # Mọi người chỉ đọc, không gửi tin nhắn
                ch_overwrites[everyone] = discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=False,
                    add_reactions=True
                )
                if admin_role:
                    ch_overwrites[admin_role] = discord.PermissionOverwrite(send_messages=True)
                if staff_role:
                    ch_overwrites[staff_role] = discord.PermissionOverwrite(send_messages=True)

            if not existing_ch:
                channel = await guild.create_text_channel(
                    name=ch_name,
                    category=category,
                    topic=ch_data["topic"],
                    overwrites=ch_overwrites
                )
                print(f"  + Đã tạo kênh: #{ch_name}")
            else:
                channel = existing_ch
                print(f"  ✓ Kênh đã có: #{ch_name}")

            saved_channel_ids[ch_name] = channel.id

    print("\n--- 3. GỬI TIN NHẮN MẪU BAN ĐẦU ---")
    
    # 1. Gửi tin nhắn nội quy
    rules_ch = discord.utils.get(guild.text_channels, name="📜-nội-quy")
    if rules_ch:
        messages = [msg async for msg in rules_ch.history(limit=5)]
        if not messages:
            rules_embed = discord.Embed(
                title="📜 NỘI QUY CỘNG ĐỒNG MTH RECAP STUDIO",
                description="Chào mừng bạn đến với cộng đồng người dùng **MTH Recap Studio**. Vui lòng tuân thủ các quy tắc sau để giữ gìn môi trường văn minh:",
                color=discord.Color.blue()
            )
            rules_embed.add_field(name="1. Tôn trọng lẫn nhau", value="Không dùng từ ngữ xúc phạm, phân biệt đối xử, quấy rối hoặc gây hấn.", inline=False)
            rules_embed.add_field(name="2. Không spam / quảng cáo", value="Không đăng link độc, virus, quảng cáo dịch vụ trái phép hoặc spam tin nhắn.", inline=False)
            rules_embed.add_field(name="3. Đúng kênh đúng chủ đề", value="Báo lỗi vào đúng kênh `🐛-báo-lỗi`, giao lưu vào `🇻🇳-thảo-luận-chung`.", inline=False)
            rules_embed.add_field(name="4. Bảo mật thông tin", value="Không chia sẻ Key bản quyền, thông tin cá nhân lên các kênh công khai.", inline=False)
            rules_embed.set_footer(text="Chúc các bạn có trải nghiệm tuyệt vời cùng MTH Recap Studio!")
            await rules_ch.send(embed=rules_embed)
            print("  ✓ Đã gửi nội quy mẫu vào #📜-nội-quy")

    # 2. Gửi hướng dẫn báo lỗi mẫu
    bug_ch = discord.utils.get(guild.text_channels, name="🐛-báo-lỗi")
    if bug_ch:
        messages = [msg async for msg in bug_ch.history(limit=5)]
        if not messages:
            bug_embed = discord.Embed(
                title="🐛 HƯỚNG DẪN BÁO LỖI PHẦN MỀM",
                description="Để team kỹ thuật hỗ trợ bạn nhanh nhất, vui lòng gửi tin nhắn báo lỗi theo mẫu bên dưới:\n\n"
                            "```text\n"
                            "• Phiên bản App: (Ví dụ: v5.4 hoặc v6.0)\n"
                            "• Mô tả lỗi: (Lỗi xảy ra ở bước nào? Lỗi gì?)\n"
                            "• Ảnh chụp màn hình lỗi / Log: (Đính kèm kèm theo)\n"
                            "```\n"
                            "💡 *Bot hỗ trợ AI sẽ tự động phân tích và tạo Thread riêng để xử lý cho bạn.*",
                color=discord.Color.orange()
            )
            await bug_ch.send(embed=bug_embed)
            print("  ✓ Đã gửi bảng hướng dẫn mẫu vào #🐛-báo-lỗi")

    print("\n=======================================================")
    print("✅ ĐÃ THIẾT LẬP HOÀN TẤT SERVER DISCORD!")
    print("=======================================================")
    print("📌 CÁC THÔNG SỐ CẤU HÌNH CHO FILE .env CỦA BOT:")
    print(f"BUG_CHANNEL_ID={saved_channel_ids.get('🐛-báo-lỗi', '')}")
    print(f"STAFF_BUG_CHANNEL_ID={saved_channel_ids.get('🐛-staff-bugs-dev', '')}")
    print(f"ANNOUNCEMENT_CHANNEL_ID={saved_channel_ids.get('📢-thông-báo', '')}")
    if staff_role:
        print(f"SUPPORT_ROLE_ID={staff_role.id}")
    print("=======================================================\n")

if __name__ == "__main__":
    bot.run(TOKEN)
