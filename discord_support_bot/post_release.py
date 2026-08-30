import os
import sys
import discord
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("d:/mthrecap/discord_support_bot/.env")
TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Client(intents=discord.Intents.default())

@bot.event
async def on_ready():
    guild = bot.guilds[0]
    print(f"Connected to: {guild.name}")
    
    # 1. Tìm kênh thông báo
    announcement_channel = None
    for ch in guild.text_channels:
        if "thông-báo" in ch.name or "thong-bao" in ch.name:
            announcement_channel = ch
            break
            
    if not announcement_channel:
        print("Không tìm thấy kênh thông báo!")
        await bot.close()
        return
        
    print(f"Kênh thông báo: #{announcement_channel.name} (ID: {announcement_channel.id})")
    
    # Cập nhật ID chuẩn vào .env
    env_file = "d:/mthrecap/discord_support_bot/.env"
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    content = re.sub(r"ANNOUNCEMENT_CHANNEL_ID=.*", f"ANNOUNCEMENT_CHANNEL_ID={announcement_channel.id}", content)
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Gửi bài thông báo cập nhật v6.1 mẫu trực tiếp
    embed = discord.Embed(
        title="🚀 BẢN CẬP NHẬT MỚI: MTH Recap Studio v6.1",
        description="Phiên bản **v6.1** chính thức ra mắt với nhiều cải tiến vượt trội về hiệu năng và AI!",
        color=0x2F80ED
    )
    embed.add_field(
        name="✨ Điểm mới nổi bật",
        value="• Tối ưu tốc độ xuất video (FFmpeg Render) nhanh hơn 35%.\n"
              "• Tích hợp AI Script Editor thông minh, tối ưu phân đoạn kịch bản.\n"
              "• Sửa lỗi tương thích font chữ và đường dẫn tiếng Việt.\n"
              "• Cải thiện hệ thống quét nhân vật và lọc tranh truyện.",
        inline=False
    )
    embed.add_field(
        name="📦 Tải Bản Cài Đặt",
        value="[Bấm vào đây để tải MTH_Recap_Studio_Setup_v6.1.exe](https://github.com/mthrecapstudio/MTHRecapStudiodl/releases/tag/MTH_Recap_Studio_Setup_v6.1)",
        inline=False
    )
    embed.set_footer(text="MTH Recap Studio • Cập nhật tự động qua GitHub Releases")
    
    await announcement_channel.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
    print("✅ ĐÃ ĐĂNG BÀI THÀNH CÔNG VÀO KÊNH THÔNG BÁO!")
    await bot.close()

bot.run(TOKEN)
