import os
import sys
import discord
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("d:/mthrecap/discord_support_bot/.env")
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected: {bot.user.name} ({bot.user.id})")
    guild = bot.guilds[0]
    bot_member = guild.get_member(bot.user.id)
    print(f"Bot roles: {[r.name for r in bot_member.roles]}")
    
    # Kiểm tra quyền gửi tin ở các kênh
    print("\n--- KIỂM TRA QUYỀN GỬI TIN CỦA BOT TẠI CÁC KÊNH ---")
    for ch in guild.text_channels:
        perms = ch.permissions_for(bot_member)
        print(f"#{ch.name}: Send Messages={perms.send_messages}, View Channel={perms.view_channel}")

    # Gán vai trò Quản Trị / Staff cho bot nếu chưa có
    admin_role = discord.utils.get(guild.roles, name="👑 Ban Quản Trị")
    staff_role = discord.utils.get(guild.roles, name="🛠️ Hỗ Trợ / Staff")
    
    roles_to_add = []
    if admin_role and admin_role not in bot_member.roles:
        roles_to_add.append(admin_role)
    if staff_role and staff_role not in bot_member.roles:
        roles_to_add.append(staff_role)
        
    if roles_to_add:
        try:
            await bot_member.add_roles(*roles_to_add)
            print(f"\n✅ Đã tự động cấp vai trò {[r.name for r in roles_to_add]} cho Bot!")
        except Exception as e:
            print(f"\n⚠️ Không thể gán role cho bot: {e}")

    await bot.close()

bot.run(TOKEN)
