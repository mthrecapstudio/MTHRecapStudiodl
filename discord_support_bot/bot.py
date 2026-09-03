from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import discord
import requests
from discord import app_commands
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


load_dotenv()

ROOT = Path(__file__).resolve().parent
RESPONSES_PATH = ROOT / "responses.json"
KNOWLEDGE_BASE_PATH = ROOT / "knowledge_base.md"


@dataclass(frozen=True)
class Settings:
    token: str
    bug_channel_id: int | None
    support_role_id: int | None
    staff_bug_channel_id: int | None
    bug_log_path: Path
    bot_status: str
    gemini_api_key: str
    gemini_model: str
    gemini_fallback_models: list[str]
    discord_announce_webhook: str
    announcement_channel_id: int | None
    github_repo: str
    github_token: str
    github_poll_seconds: int
    github_state_path: Path
    github_announce_on_start: bool
    bot_api_url: str = "https://mthrecapstudio.fun/bot_api"
    bot_api_secret: str = "mth_discord_bot_secret_2026_9x8a"
    welcome_channel_id: int | None = None


def parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    return int(value) if value else None


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing DISCORD_TOKEN in .env")

    log_path = Path(os.getenv("BUG_LOG_PATH", "data/bug_reports.jsonl"))
    if not log_path.is_absolute():
        log_path = ROOT / log_path

    github_state_path = Path(os.getenv("GITHUB_RELEASE_STATE_PATH", "data/last_github_release.txt"))
    if not github_state_path.is_absolute():
        github_state_path = ROOT / github_state_path

    fallback_models = [
        model.strip()
        for model in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-lite").split(",")
        if model.strip()
    ]

    return Settings(
        token=token,
        bug_channel_id=parse_optional_int(os.getenv("BUG_CHANNEL_ID")),
        support_role_id=parse_optional_int(os.getenv("SUPPORT_ROLE_ID")),
        staff_bug_channel_id=parse_optional_int(os.getenv("STAFF_BUG_CHANNEL_ID")),
        bug_log_path=log_path,
        bot_status=os.getenv("BOT_STATUS", "Listening for bug reports").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        gemini_fallback_models=fallback_models,
        discord_announce_webhook=os.getenv("DISCORD_ANNOUNCE_WEBHOOK", "").strip(),
        announcement_channel_id=parse_optional_int(os.getenv("ANNOUNCEMENT_CHANNEL_ID")),
        github_repo=os.getenv("GITHUB_REPO", "").strip(),
        github_token=os.getenv("GITHUB_TOKEN", "").strip(),
        github_poll_seconds=max(60, int(os.getenv("GITHUB_POLL_SECONDS", "300"))),
        github_state_path=github_state_path,
        github_announce_on_start=os.getenv("GITHUB_ANNOUNCE_ON_START", "").strip().lower() in {"1", "true", "yes"},
        bot_api_url=os.getenv("BOT_API_URL", "https://mthrecapstudio.fun/bot_api").strip(),
        bot_api_secret=os.getenv("BOT_API_SECRET", "mth_discord_bot_secret_2026_9x8a").strip(),
        welcome_channel_id=parse_optional_int(os.getenv("WELCOME_CHANNEL_ID")),
    )


def load_response_rules() -> dict[str, Any]:
    with RESPONSES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)

DOCS_DIR = ROOT / "documents"

def load_knowledge_base() -> str:
    parts = []
    if KNOWLEDGE_BASE_PATH.exists():
        parts.append(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8").strip())
    
    if DOCS_DIR.exists():
        for doc_file in DOCS_DIR.glob("**/*"):
            if doc_file.is_file() and doc_file.suffix.lower() in [".md", ".txt", ".json"]:
                try:
                    content = doc_file.read_text(encoding="utf-8").strip()
                    if content:
                        parts.append(f"\n--- Tài liệu: {doc_file.name} ---\n{content}")
                except Exception as e:
                    print(f"Không thể đọc tài liệu {doc_file.name}: {e}")
                    
    return "\n\n".join(parts)


def classify_report(content: str, rules: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    normalized = content.lower()
    for key, rule in rules.items():
        if key == "default":
            continue
        if any(keyword.lower() in normalized for keyword in rule.get("keywords", [])):
            return key, rule
    return "default", rules["default"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_text(value: str, limit: int = 80) -> str:
    value = " ".join(value.strip().split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def is_bug_thread(channel: Any, bug_channel_id: int | None) -> bool:
    return isinstance(channel, discord.Thread) and bug_channel_id is not None and channel.parent_id == bug_channel_id


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)



def _sync_request_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    import requests
    resp = requests.post(url, data=payload, headers=headers, timeout=12)
    if resp.status_code == 403:
        return {"status": "error", "message": "Sai khóa bảo mật kết nối với web hosting."}
    if resp.status_code != 200:
        return {"status": "error", "message": f"Máy chủ web phản hồi mã lỗi {resp.status_code}."}
    return resp.json()


async def call_web_api(settings: Settings, action: str, data: dict[str, Any]) -> dict[str, Any]:
    url = settings.bot_api_url
    headers = {
        "X-Bot-Secret": settings.bot_api_secret,
        "User-Agent": "MTH-Discord-Bot/6.2.0"
    }
    payload = {"action": action, **data}
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_request_post, url, payload, headers)
    except Exception as e:
        return {"status": "error", "message": f"Không thể kết nối đến máy chủ web: {e}"}


class SupportBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(intents=intents)
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.rules = load_response_rules()
        self.knowledge_base = load_knowledge_base()
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key) if genai and settings.gemini_api_key else None
        self.github_monitor_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        @self.tree.command(name="bug", description="Báo lỗi cho team hỗ trợ")
        @app_commands.describe(
            mo_ta="Mô tả lỗi, các bước tạo lại lỗi, và thông báo lỗi nếu có"
        )
        async def bug_command(interaction: discord.Interaction, mo_ta: str) -> None:
            if not interaction.channel or not isinstance(interaction.channel, discord.abc.Messageable):
                await interaction.response.send_message(
                    "Không thể tạo báo lỗi ở vị trí này.",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)
            pseudo_message = await interaction.channel.send(
                f"Bug report từ {interaction.user.mention}: {mo_ta}",
                allowed_mentions=discord.AllowedMentions(users=False),
            )
            await self.handle_bug_report(pseudo_message, mo_ta, reporter=interaction.user)
            await interaction.followup.send(
                "Đã ghi nhận báo lỗi và tạo thread hỗ trợ.",
                ephemeral=True,
            )

        
        # ---- LOGIC DÙNG CHUNG CHO NHẬN QUÀ TÂN THỦ ----
        async def _execute_claim(interaction: discord.Interaction, user_input: str) -> None:
            try:
                await interaction.response.defer(ephemeral=False)
                clean_username = user_input.strip()
                
                res = await call_web_api(self.settings, "claim_welcome", {
                    "discord_id": str(interaction.user.id),
                    "discord_name": interaction.user.name,
                    "username": clean_username,
                    "amount": 20000
                })
                
                if res.get("status") == "success":
                    embed = discord.Embed(
                        title="🎉 NHẬN QUÀ TÂN THỦ THÀNH CÔNG!",
                        description=f"Chúc mừng {interaction.user.mention} đã nhận thành công quà tặng gia nhập cộng đồng Discord!",
                        color=0x7C5CFF
                    )
                    embed.add_field(name="👤 Tài khoản MTH", value=f"`{res.get('username')}`", inline=True)
                    embed.add_field(name="🎁 Phần thưởng", value="`+20.000 Credits`", inline=True)
                    embed.add_field(name="💰 Số dư mới", value=f"**{res.get('new_balance', 0):,}** Credits", inline=True)
                    embed.set_footer(text="MTH AI Studio • Mở app để kiểm tra và bắt đầu tạo video recap ngay!")
                    await interaction.followup.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ KHÔNG THỂ NHẬN QUÀ",
                        description=res.get("message", "Đã có lỗi xảy ra."),
                        color=0xFF4D4D
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                print(f"Lỗi khi xử lý claim: {e}")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Đã xảy ra lỗi: {e}", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ Đã xảy ra lỗi: {e}", ephemeral=True)
                except Exception:
                    pass

        @self.tree.command(name="nhanqua", description="🎁 Nhận ngay 20.000 Credits quà tân thủ Discord vào tài khoản MTH AI Studio!")
        @app_commands.describe(ten_tai_khoan="Tên đăng nhập tài khoản của bạn trên app MTH AI Studio")
        async def nhanqua_command(interaction: discord.Interaction, ten_tai_khoan: str) -> None:
            await _execute_claim(interaction, ten_tai_khoan)

        @self.tree.command(name="claim", description="🎁 Claim 20,000 Free Credits for your MTH AI Studio account!")
        @app_commands.describe(username="Your MTH AI Studio app username")
        async def claim_command(interaction: discord.Interaction, username: str) -> None:
            await _execute_claim(interaction, username)

        # ---- COMMAND: KIỂM TRA TÀI KHOẢN ----
        @self.tree.command(name="taikhoan", description="📊 Kiểm tra số dư Credits và thời hạn gói trên app MTH AI Studio")
        @app_commands.describe(ten_tai_khoan="Tên đăng nhập tài khoản MTH của bạn")
        async def taikhoan_command(interaction: discord.Interaction, ten_tai_khoan: str) -> None:
            try:
                await interaction.response.defer(ephemeral=True)
                res = await call_web_api(self.settings, "check_user", {"username": ten_tai_khoan.strip()})
                
                if res.get("status") == "success":
                    embed = discord.Embed(
                        title=f"📊 THÔNG TIN TÀI KHOẢN: {res.get('username')}",
                        color=0x06B6D4
                    )
                    embed.add_field(name="💰 Số dư Credits", value=f"**{res.get('credits', 0):,}**", inline=True)
                    embed.add_field(name="👑 Gói dịch vụ", value=f"**{res.get('plan', 'FREE')}**", inline=True)
                    embed.add_field(name="⏳ Hạn sử dụng", value=f"{res.get('expires_at')}", inline=False)
                    embed.set_footer(text="MTH AI Studio • Nạp thêm credit tại mthrecapstudio.fun")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ {res.get('message', 'Không tìm thấy tài khoản.')}", ephemeral=True)
            except Exception as e:
                print(f"Lỗi lệnh /taikhoan: {e}")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Lỗi: {e}", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ Lỗi: {e}", ephemeral=True)
                except Exception:
                    pass

        # ---- COMMAND: ADMIN TRAO THƯỞNG / TẶNG CREDIT (CHỈ DÀNH CHO ADMIN) ----
        @self.tree.command(name="tangqua", description="👑 [ADMIN] Tặng Credits hoặc cộng ngày dùng cho thành viên trúng giải")
        @app_commands.describe(
            ten_tai_khoan="Tên tài khoản MTH được nhận quà",
            so_credits="Số Credits cần cộng thêm (ví dụ: 50000)",
            so_ngay="Số ngày sử dụng PRO cần cộng thêm (để 0 nếu không cộng ngày)",
            ly_do="Lý do trao thưởng (ví dụ: Thắng minigame đố vui)"
        )
        async def tangqua_command(
            interaction: discord.Interaction, 
            ten_tai_khoan: str, 
            so_credits: int = 0, 
            so_ngay: int = 0,
            ly_do: str = "Phần thưởng sự kiện Discord"
        ) -> None:
            # Kiểm tra quyền: Phải là Admin server hoặc có role Support
            is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False
            if not is_admin and self.settings.support_role_id and interaction.guild:
                member = interaction.guild.get_member(interaction.user.id)
                if member and any(r.id == self.settings.support_role_id for r in member.roles):
                    is_admin = True
                    
            if not is_admin:
                await interaction.response.send_message("❌ Bạn không có quyền thực hiện lệnh này!", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=False)
            res = await call_web_api(self.settings, "admin_reward", {
                "admin_id": f"{interaction.user.name} ({interaction.user.id})",
                "username": ten_tai_khoan.strip(),
                "credits": so_credits,
                "days": so_ngay,
                "reason": ly_do
            })

            if res.get("status") == "success":
                embed = discord.Embed(
                    title="🎁 PHẦN THƯỞNG ĐÃ ĐƯỢC TRAO!",
                    description=f"Admin {interaction.user.mention} đã trao thưởng cho tài khoản `{ten_tai_khoan}`!\n**Lý do:** {ly_do}",
                    color=0xF59E0B
                )
                if so_credits > 0:
                    embed.add_field(name="💰 Credits cộng thêm", value=f"+{so_credits:,}", inline=True)
                if so_ngay > 0:
                    embed.add_field(name="⏳ Ngày dùng cộng thêm", value=f"+{so_ngay} ngày PRO", inline=True)
                embed.add_field(name="📊 Số dư mới", value=f"**{res.get('new_balance', 0):,}** Credits", inline=True)
                embed.set_footer(text="MTH AI Studio • Chúc mừng người chiến thắng!")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ {res.get('message', 'Không thể trao thưởng.')}", ephemeral=True)

        # ---- COMMAND: GỢI Ý TIÊU ĐỀ VIDEO YOUTUBE / TIKTOK RECAP ----
        @self.tree.command(name="tieude", description="💡 AI gợi ý 5 tiêu đề video YouTube/TikTok giật gân, chuẩn SEO cho truyện")
        @app_commands.describe(ten_truyen="Tên bộ truyện hoặc bối cảnh diễn biến chính")
        async def tieude_command(interaction: discord.Interaction, ten_truyen: str) -> None:
            await interaction.response.defer(ephemeral=False)
            prompt = f"Hãy gợi ý 5 tiêu đề video YouTube và TikTok giật gân, cuốn hút, kích thích tò mò chuẩn SEO dành cho kênh recap bộ truyện: '{ten_truyen}'. Trình bày ngắn gọn, kèm emoji sinh động."
            reply = await self.generate_general_ai_reply(prompt, interaction.user.display_name)
            embed = discord.Embed(
                title=f"🎬 GỢI Ý TIÊU ĐỀ RECAP: {ten_truyen}",
                description=reply,
                color=0xEC4899
            )
            embed.set_footer(text="MTH AI Studio Creative Advisor • Dùng cho YouTube Shorts / TikTok / Long video")
            await interaction.followup.send(embed=embed)

        # ---- COMMAND: GỢI Ý CÂU HOOK MỞ ĐẦU VIDEO ----
        @self.tree.command(name="hook", description="⚡ AI viết 3 câu Hook mở đầu video siêu bánh cuốn giữ chân người xem 5 giây đầu")
        @app_commands.describe(noi_dung="Tên truyện hoặc khoảnh khắc kịch tính muốn làm mở đầu")
        async def hook_command(interaction: discord.Interaction, noi_dung: str) -> None:
            await interaction.response.defer(ephemeral=False)
            prompt = f"Hãy viết 3 mẫu câu Hook mở đầu video (5 giây đầu tiên) cực kỳ kích tính, gây sốc, giữ chân người xem không lướt qua dành cho recap truyện: '{noi_dung}'. Giọng điệu hào hùng hoặc bí ẩn."
            reply = await self.generate_general_ai_reply(prompt, interaction.user.display_name)
            embed = discord.Embed(
                title=f"⚡ CÂU HOOK MỞ ĐẦU VIDEO: {noi_dung}",
                description=reply,
                color=0x8B5CF6
            )
            embed.set_footer(text="MTH AI Studio • Đọc câu hook này trong 3-5 giây đầu của video recap!")
            await interaction.followup.send(embed=embed)

        await self.tree.sync()
        if self.settings.github_repo and (self.settings.discord_announce_webhook or self.settings.announcement_channel_id):
            self.github_monitor_task = self.loop.create_task(self.monitor_github_releases())

    async def on_ready(self) -> None:
        activity = discord.Activity(type=discord.ActivityType.listening, name=self.settings.bot_status)
        await self.change_presence(activity=activity)
        print(f"🤖 Bot đang hoạt động: {self.user} (ID: {self.user.id if self.user else 'unknown'})")
        print("💡 Đang sẵn sàng nhận câu hỏi và hỗ trợ người dùng 24/7...")

        # Đồng bộ lệnh Slash ngay lập tức cho các Server (Instant Guild Sync - Hiện lệnh trong 1 giây)
        try:
            for guild in self.guilds:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"⚡ [INSTANT SYNC] Đã đồng bộ lệnh Slash tức thì cho Server: {guild.name} ({guild.id})")
        except Exception as e:
            print(f"⚠️ Không thể đồng bộ lệnh guild tức thì: {e}")

    
    async def on_member_join(self, member: discord.Member) -> None:
        """Tự động chào đón thành viên mới và hướng dẫn nhận quà tân thủ."""
        try:
            # Ưu tiên gửi vào kênh welcome nếu có cấu hình
            channel = None
            if self.settings.welcome_channel_id:
                channel = member.guild.get_channel(self.settings.welcome_channel_id)
            if not channel:
                # Tìm kênh chat chung hoặc system_channel
                channel = member.guild.system_channel
                if not channel:
                    for ch in member.guild.text_channels:
                        if ch.name in {"general", "chat-chung", "thao-luan", "nhan-qua", "chao-mung"}:
                            channel = ch
                            break
            if channel:
                embed = discord.Embed(
                    title=f"🎉 CHÀO MỪNG {member.display_name.upper()} GIA NHẬP MTH AI STUDIO!",
                    description=(
                        f"Chào mừng {member.mention} đã đến với cộng đồng sáng tạo video recap manga/anime! 🎬\n\n"
                        f"🎁 **QUÀ TÂN THỦ DÀNH CHO BẠN:**\n"
                        f"Hãy gõ ngay lệnh: **`/nhanqua ten_tai_khoan: [tên_app_của_bạn]`**\n"
                        f"để nhận ngay **20.000 Credits miễn phí** vào tài khoản MTH AI Studio nhé!\n\n"
                        f"💡 Cần hỗ trợ kỹ thuật hoặc mẹo làm video? Hãy thoải mái đặt câu hỏi trong kênh chat nhé!"
                    ),
                    color=0x7C5CFF
                )
                if member.display_avatar:
                    embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="MTH AI Studio • Chúc bạn tạo nên những video triệu view!")
                await channel.send(content=member.mention, embed=embed)
        except Exception as e:
            print(f"Lỗi khi gửi lời chào thành viên mới: {e}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        ch_name = getattr(message.channel, "name", "direct_message")
        print(f"\n📩 Nhận tin nhắn mới tại [#{ch_name}] từ {message.author.name}: {message.content}")

        if is_bug_thread(message.channel, self.settings.bug_channel_id):
            content = message.content.strip()
            should_analyze = (
                content.lower() in {"!analyze", "!phan tich", "phan tich", "phân tích"}
                or bool(message.attachments)
                or len(content) >= 3
            )
            if should_analyze:
                await self.analyze_thread(message.channel, message)
            return

        # ---- HỖ TRỢ LỆNH DẤU CHẤM THAN (PREFIX COMMANDS) CHỐNG LỖI TÍCH HỢP DISCORD ----
        raw_text = message.content.strip()
        lower_text = raw_text.lower()
        
        if lower_text.startswith(("!nhanqua", "!claim", "!taikhoan", "!tk", "!hook", "!tieude")):
            parts = raw_text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in {"!nhanqua", "!claim"}:
                if not arg:
                    await message.reply("⚠️ Vui lòng nhập tên tài khoản. Ví dụ: `!nhanqua HatDauNhoBe` hoặc `!claim HatDauNhoBe`", allowed_mentions=discord.AllowedMentions.none())
                    return
                async with message.channel.typing():
                    res = await call_web_api(self.settings, "claim_welcome", {
                        "discord_id": str(message.author.id),
                        "discord_name": message.author.name,
                        "username": arg,
                        "amount": 20000
                    })
                    if res.get("status") == "success":
                        embed = discord.Embed(
                            title="🎉 NHẬN QUÀ TÂN THỦ THÀNH CÔNG!",
                            description=f"Chúc mừng {message.author.mention} đã nhận thành công quà tặng gia nhập cộng đồng Discord!",
                            color=0x7C5CFF
                        )
                        embed.add_field(name="👤 Tài khoản MTH", value=f"`{res.get('username')}`", inline=True)
                        embed.add_field(name="🎁 Phần thưởng", value="`+20.000 Credits`", inline=True)
                        embed.add_field(name="💰 Số dư mới", value=f"**{res.get('new_balance', 0):,}** Credits", inline=True)
                        embed.set_footer(text="MTH AI Studio • Mở app để kiểm tra và bắt đầu tạo video recap ngay!")
                        await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                    else:
                        embed = discord.Embed(
                            title="❌ KHÔNG THỂ NHẬN QUÀ",
                            description=res.get("message", "Đã có lỗi xảy ra."),
                            color=0xFF4D4D
                        )
                        await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                return

            elif cmd in {"!taikhoan", "!tk"}:
                if not arg:
                    await message.reply("⚠️ Vui lòng nhập tên tài khoản. Ví dụ: `!taikhoan HatDauNhoBe`", allowed_mentions=discord.AllowedMentions.none())
                    return
                async with message.channel.typing():
                    res = await call_web_api(self.settings, "check_user", {"username": arg})
                    if res.get("status") == "success":
                        embed = discord.Embed(
                            title=f"📊 THÔNG TIN TÀI KHOẢN: {res.get('username')}",
                            color=0x06B6D4
                        )
                        embed.add_field(name="💰 Số dư Credits", value=f"**{res.get('credits', 0):,}**", inline=True)
                        embed.add_field(name="👑 Gói dịch vụ", value=f"**{res.get('plan', 'FREE')}**", inline=True)
                        embed.add_field(name="⏳ Hạn sử dụng", value=f"{res.get('expires_at')}", inline=False)
                        embed.set_footer(text="MTH AI Studio • Nạp thêm credit tại mthrecapstudio.fun")
                        await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                    else:
                        await message.reply(f"❌ {res.get('message', 'Không tìm thấy tài khoản.')}", allowed_mentions=discord.AllowedMentions.none())
                return

            elif cmd == "!tieude":
                if not arg:
                    await message.reply("⚠️ Vui lòng nhập tên truyện. Ví dụ: `!tieude Solo Leveling`", allowed_mentions=discord.AllowedMentions.none())
                    return
                async with message.channel.typing():
                    prompt = f"Hãy gợi ý 5 tiêu đề video YouTube và TikTok giật gân, cuốn hút, kích thích tò mò chuẩn SEO dành cho kênh recap bộ truyện: '{arg}'. Trình bày ngắn gọn, kèm emoji sinh động."
                    reply = await self.generate_general_ai_reply(prompt, message.author.display_name)
                    embed = discord.Embed(
                        title=f"🎬 GỢI Ý TIÊU ĐỀ RECAP: {arg}",
                        description=reply,
                        color=0xEC4899
                    )
                    embed.set_footer(text="MTH AI Studio Creative Advisor • Dùng cho YouTube Shorts / TikTok / Long video")
                    await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                return

            elif cmd == "!hook":
                if not arg:
                    await message.reply("⚠️ Vui lòng nhập nội dung hoặc tên truyện. Ví dụ: `!hook Trọng sinh thành ma vương`", allowed_mentions=discord.AllowedMentions.none())
                    return
                async with message.channel.typing():
                    prompt = f"Hãy viết 3 mẫu câu Hook mở đầu video (5 giây đầu tiên) cực kỳ kích tính, gây sốc, giữ chân người xem không lướt qua dành cho recap truyện: '{arg}'. Giọng điệu hào hùng hoặc bí ẩn."
                    reply = await self.generate_general_ai_reply(prompt, message.author.display_name)
                    embed = discord.Embed(
                        title=f"⚡ CÂU HOOK MỞ ĐẦU VIDEO: {arg}",
                        description=reply,
                        color=0x8B5CF6
                    )
                    embed.set_footer(text="MTH AI Studio • Đọc câu hook này trong 3-5 giây đầu của video recap!")
                    await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                return

        # Tự động tiếp chuyện trong các kênh chat AI riêng mà không cần @mention
        ai_channels = {"tro-chuyen-cung-ai", "hoi-dap-ai", "ai-chat", "chat-bot", "tam-su-ai"}
        is_in_ai_channel = ch_name.lower() in ai_channels

        # Kiểm tra xem tin nhắn có nhắc đến Bot (User mention, Role mention, hoặc gọi tên bot)
        is_mentioned = is_in_ai_channel
        if self.user:
            # 1. Tag user bot trực tiếp
            if self.user in message.mentions or any(m.id == self.user.id for m in message.mentions) or str(self.user.id) in message.content:
                is_mentioned = True
            # 2. Tag role của bot (Role mention)
            elif message.guild and message.role_mentions:
                bot_member = message.guild.get_member(self.user.id)
                if bot_member:
                    bot_role_ids = {r.id for r in bot_member.roles if r.name != "@everyone"}
                    if any(rm.id in bot_role_ids for rm in message.role_mentions):
                        is_mentioned = True
            # 3. Chứa tên bot trong nội dung
            elif "mth support bot" in message.content.lower():
                is_mentioned = True

        if is_mentioned and not message.mention_everyone:
            print(f"🤖 [Gemini AI] Đang xử lý câu hỏi từ {message.author.name}...")
            # Lọc bỏ các tag mention thừa để lấy nội dung câu hỏi sạch
            clean_prompt = message.clean_content
            for r in message.role_mentions:
                clean_prompt = clean_prompt.replace(f"@{r.name}", "")
            clean_prompt = clean_prompt.replace(f"@{self.user.name}", "").replace(f"@{self.user.display_name}", "").strip()
            
            import re
            clean_prompt = re.sub(r"<@&?\d+>", "", clean_prompt).strip()
            
            if not clean_prompt:
                clean_prompt = "Xin chào, bạn có thể hỗ trợ gì cho tôi về MTH Recap Studio?"
            
            async with message.channel.typing():
                try:
                    image_parts = await self.extract_image_parts(message)
                    reply_text = await self.generate_general_ai_reply(clean_prompt, message.author.display_name, image_parts=image_parts)
                    if reply_text:
                        # Chia nhỏ tin nhắn nếu dài hơn 1950 ký tự để không bị Discord chặn
                        if len(reply_text) <= 1950:
                            await message.reply(reply_text, allowed_mentions=discord.AllowedMentions.none())
                        else:
                            # Cắt theo từng đoạn vừa vặn
                            chunks = []
                            curr = ""
                            for line in reply_text.splitlines(keepends=True):
                                if len(curr) + len(line) > 1900:
                                    chunks.append(curr)
                                    curr = line
                                else:
                                    curr += line
                            if curr:
                                chunks.append(curr)

                            for idx, chunk in enumerate(chunks):
                                if idx == 0:
                                    await message.reply(chunk.strip(), allowed_mentions=discord.AllowedMentions.none())
                                else:
                                    await message.channel.send(chunk.strip(), allowed_mentions=discord.AllowedMentions.none())
                        print(f"✅ [Gemini AI] Đã gửi câu trả lời thành công cho {message.author.name}!")
                        return
                except Exception as e:
                    print(f"❌ Lỗi gửi tin nhắn AI: {e}")
                    await message.reply(f"Đã có lỗi xảy ra khi xử lý phản hồi: {e}", allowed_mentions=discord.AllowedMentions.none())
                    return

        if self.settings.bug_channel_id and message.channel.id != self.settings.bug_channel_id:
            if not message.content.lower().startswith("!bug "):
                return

        if message.content.lower().startswith("!bug "):
            content = message.content[5:].strip()
        else:
            content = message.content.strip()

        if not content:
            return

        await self.handle_bug_report(message, content)

    async def extract_image_parts(self, message: discord.Message) -> list[Any]:
        parts = []
        if not types or not message.attachments:
            return parts
        for attachment in message.attachments:
            mime = attachment.content_type or ""
            if mime.startswith("image/") or attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                try:
                    img_data = await attachment.read()
                    if img_data:
                        parts.append(types.Part.from_bytes(data=img_data, mime_type=mime or "image/png"))
                        print(f"📸 Đã tải ảnh đính kèm từ user: {attachment.filename} ({len(img_data)} bytes)")
                except Exception as e:
                    print(f"❌ Không thể đọc ảnh {attachment.filename}: {e}")
        return parts

    async def generate_general_ai_reply(self, prompt: str, user_name: str, image_parts: list[Any] | None = None) -> str | None:
        if not self.gemini_client:
            return "Chào bạn! Tôi là bot hỗ trợ MTH Recap Studio. Bạn cần hỗ trợ kỹ thuật hãy nhắn tại kênh #🐛-báo-lỗi nhé!"

        # Tải lại toàn bộ dữ liệu tài liệu mới nhất theo thời gian thực
        current_knowledge = load_knowledge_base()

        system_prompt = (
            f"Bạn là trợ lý ảo AI chính thức của phần mềm MTH Recap Studio (MTH AI Studio) - công cụ sản xuất video review manga/anime tự động trên Windows.\n"
            f"Bạn có khả năng nhìn và đọc hình ảnh chụp màn hình (Multimodal Vision) rất rõ ràng.\n"
            f"Hãy trả lời người dùng '{user_name}' bằng tiếng Việt một cách chính xác, chi tiết, chuyên nghiệp và thân thiện.\n\n"
            f"QUY TẮC BẮT BUỘC:\n"
            f"1. BÁM SÁT 100% VÀO DỮ LIỆU TÀI LIỆU DƯỚI ĐÂY.\n"
            f"2. NẾU CÓ HÌNH ẢNH: Hãy nhìn kỹ màn hình, giao diện, bảng chọn hoặc lỗi hiển thị trong ảnh để chẩn đoán chính xác.\n"
            f"3. NẾU NGƯỜI DÙNG BÁO LỖI KHÔNG MỞ ĐƯỢC TRÌNH DUYỆT ĐỂ TẢI ẢNH: Hãy chỉ rõ nguyên nhân số 1 là do đang mở kèm CỐC CỐC hoặc GOOGLE CHROME gây xung đột ChromeDriver. Hướng dẫn đóng hoàn toàn Cốc Cốc / Chrome trong Task Manager rồi thử lại.\n"
            f"4. NẾU HỎI VỀ GIÁ/GÓI: Liệt kê đầy đủ cụ thể các con số (FREE: 0đ, PRO: 349k/tháng, PREMIUM: 699k/tháng, các gói nạp credit...).\n\n"
            f"DỮ LIỆU KIẾN THỨC SẢN PHẨM THỜI GIAN THỰC:\n{current_knowledge}"
        )

        contents = [system_prompt]
        if image_parts:
            contents.extend(image_parts)
        contents.append(f"Câu hỏi của người dùng '{user_name}': {prompt}")

        tried_models = []
        for model in [self.settings.gemini_model, *self.settings.gemini_fallback_models]:
            if not model or model in tried_models:
                continue
            tried_models.append(model)
            try:
                response = await asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=model,
                    contents=contents,
                )
                text = (response.text or "").strip()
                if text:
                    return text
            except Exception as exc:
                print(f"Gemini reply error on {model}: {exc}")
        return "Chào bạn! Nếu bạn gặp sự cố kỹ thuật về app, vui lòng gửi tin nhắn vào kênh #🐛-báo-lỗi để được hỗ trợ nhé!"

    async def monitor_github_releases(self) -> None:
        await self.wait_until_ready()
        first_check = True

        while not self.is_closed():
            try:
                releases = await asyncio.to_thread(self.fetch_github_releases)
                announced_tags = self.read_github_release_state()

                if not releases:
                    first_check = False
                    await asyncio.sleep(self.settings.github_poll_seconds)
                    continue

                if not announced_tags:
                    latest_tag = str(releases[0].get("tag_name") or "").strip() if releases else ""
                    if latest_tag and not self.settings.github_announce_on_start:
                        self.write_github_release_state({latest_tag})
                        print(f"Initialized GitHub release monitor at {latest_tag}.")
                    elif latest_tag:
                        await self.announce_github_release(releases[0])
                        self.write_github_release_state({latest_tag})
                else:
                    cutoff_index = next(
                        (
                            index
                            for index, release in enumerate(releases)
                            if str(release.get("tag_name") or "").strip() in announced_tags
                        ),
                        0,
                    )
                    new_releases = list(reversed(releases[:cutoff_index]))
                    for release in new_releases:
                        tag = str(release.get("tag_name") or "").strip()
                        await self.announce_github_release(release)
                        announced_tags.add(tag)
                        self.write_github_release_state(announced_tags)
                first_check = False
            except Exception as exc:
                print(f"GitHub release monitor failed: {exc}")

            await asyncio.sleep(self.settings.github_poll_seconds)

    def fetch_github_releases(self) -> list[dict[str, Any]]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "mth-recap-discord-bot",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        response = requests.get(
            f"https://api.github.com/repos/{self.settings.github_repo}/releases?per_page=10",
            headers=headers,
            timeout=20,
        )
        if response.status_code == 404:
            print(f"No GitHub release found for {self.settings.github_repo}.")
            return []
        response.raise_for_status()
        releases = response.json()
        return releases if isinstance(releases, list) else []

    def read_github_release_state(self) -> set[str]:
        if not self.settings.github_state_path.exists():
            return set()
        value = self.settings.github_state_path.read_text(encoding="utf-8").strip()
        if not value:
            return set()
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return {str(item) for item in parsed if str(item).strip()}
        except json.JSONDecodeError:
            pass
        return {value}

    def write_github_release_state(self, tags: set[str]) -> None:
        self.settings.github_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.github_state_path.write_text(
            json.dumps(sorted(tags), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def announce_github_release(self, release: dict[str, Any]) -> None:
        tag = str(release.get("tag_name") or "unknown")
        title = str(release.get("name") or f"MTH Recap {tag}")
        url = str(release.get("html_url") or "")
        body = str(release.get("body") or "Bản cập nhật mới đã sẵn sàng.").strip()
        announcement = await self.generate_release_announcement(release)
        body = announcement or body
        if len(body) > 3500:
            body = body[:3497] + "..."

        payload = {
            "content": "@everyone",
            "allowed_mentions": {"parse": ["everyone"]},
            "embeds": [
                {
                    "title": f"{title} ({tag})",
                    "description": body,
                    "url": url,
                    "color": 0x2F80ED,
                    "fields": [{"name": "Release", "value": url, "inline": False}] if url else [],
                }
            ],
        }

        if self.settings.discord_announce_webhook:
            await asyncio.to_thread(
                requests.post,
                self.settings.discord_announce_webhook,
                json=payload,
                timeout=20,
            )
            print(f"Announced GitHub release {tag} by webhook.")
            return

        channel = self.get_channel(self.settings.announcement_channel_id) if self.settings.announcement_channel_id else None
        if isinstance(channel, discord.abc.Messageable):
            embed = discord.Embed(title=f"{title} ({tag})", description=body, url=url, color=discord.Color.blue())
            if url:
                embed.add_field(name="Release", value=url, inline=False)
            await channel.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
            print(f"Announced GitHub release {tag} by channel.")

    async def generate_release_announcement(self, release: dict[str, Any]) -> str | None:
        if not self.gemini_client:
            return None

        tag = str(release.get("tag_name") or "")
        title = str(release.get("name") or tag or "MTH Recap update")
        body = str(release.get("body") or "").strip()
        url = str(release.get("html_url") or "")

        prompt = (
            "You write Discord product update announcements in Vietnamese for MTH Recap users. "
            "Create a friendly, professional announcement from the GitHub Release data. "
            "Do not invent features not present in the release notes. If notes are sparse, keep it short and say this update improves stability. "
            "Avoid markdown tables. Use a concise title line, 3-6 bullets, and a clear call to update/download.\n\n"
            f"Product knowledge:\n{self.knowledge_base[:4000] or 'MTH Recap is a Windows desktop tool for recap/video production.'}\n\n"
            f"Release tag: {tag}\n"
            f"Release title: {title}\n"
            f"Release URL: {url}\n"
            f"Release notes:\n{body[:6000]}"
        )

        tried_models = []
        for model in [self.settings.gemini_model, *self.settings.gemini_fallback_models]:
            if not model or model in tried_models:
                continue
            tried_models.append(model)
            try:
                response = await asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=model,
                    contents=prompt,
                )
                text = (response.text or "").strip()
                if text:
                    return text
            except Exception as exc:
                print(f"Gemini release announcement failed on {model}: {exc}")
        return None

    async def handle_bug_report(
        self,
        message: discord.Message,
        content: str,
        reporter: discord.abc.User | discord.Member | None = None,
    ) -> None:
        reporter = reporter or message.author
        category, rule = classify_report(content, self.rules)
        report_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        title = f"{rule['title']} - {short_text(content, 42)}"

        embed = discord.Embed(
            title=f"\u0110\u00e3 ghi nh\u1eadn: {rule['title']}",
            description=rule["reply"],
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="M\u00e3 l\u1ed7i", value=report_id, inline=True)
        embed.add_field(name="Ng\u01b0\u1eddi b\u00e1o", value=reporter.mention, inline=True)
        embed.add_field(name="Ph\u00e2n lo\u1ea1i", value=category, inline=True)
        embed.add_field(name="N\u1ed9i dung", value=content[:1024], inline=False)

        mention_text = self.support_mention(message.guild)
        await message.reply(
            content=mention_text,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, replied_user=False),
        )

        thread = await self.create_thread(message, title, content, rule, report_id, reporter)
        await self.write_report_log(message, thread, content, category, report_id, reporter)
        await self.mirror_to_staff(message, thread, content, category, report_id, reporter)

        # Tự động gửi ngay chẩn đoán từ Gemini AI vào Thread
        if thread:
            try:
                attachment_names = [a.filename for a in message.attachments]
                image_parts = await self.extract_image_parts(message)
                async with thread.typing():
                    ai_text = await self.generate_gemini_analysis(thread, category, content, attachment_names, image_parts=image_parts)
                if ai_text:
                    if len(ai_text) <= 4000:
                        embed = discord.Embed(
                            title="🤖 Chẩn đoán & Hướng dẫn tự động từ AI",
                            description=ai_text,
                            color=discord.Color.green(),
                            timestamp=datetime.now(timezone.utc),
                        )
                        await thread.send(embed=embed)
                    else:
                        await thread.send(ai_text)
            except Exception as e:
                print(f"Auto initial AI analysis error: {e}")

    async def analyze_thread(self, thread: discord.Thread, trigger: discord.Message) -> None:
        status_message = await trigger.reply(
            "⏳ AI đang đọc kỹ hình ảnh và phân tích lỗi...",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        messages = [message async for message in thread.history(limit=30, oldest_first=True)]
        user_messages = [message for message in messages if not message.author.bot]
        combined_text = "\n".join(message.content for message in user_messages if message.content).strip()
        attachment_names = [
            attachment.filename
            for message in user_messages
            for attachment in message.attachments
        ]

        image_parts = []
        for msg in user_messages:
            parts = await self.extract_image_parts(msg)
            image_parts.extend(parts)

        category, _rule = classify_report(combined_text or thread.name, self.rules)
        async with thread.typing():
            ai_text = await self.generate_gemini_analysis(thread, category, combined_text, attachment_names, image_parts=image_parts)
        if ai_text:
            if len(ai_text) <= 4000:
                embed = discord.Embed(
                    title="🤖 AI Phân tích lỗi chi tiết",
                    description=ai_text,
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc),
                )
                if attachment_names:
                    embed.add_field(
                        name="📸 File/Ảnh đã phân tích",
                        value=bullet_list(attachment_names[:8])[:1024],
                        inline=False,
                    )
                await status_message.edit(content=None, embed=embed)
            else:
                await status_message.edit(content=ai_text)
            return

        analysis = self.build_analysis(category, combined_text, attachment_names)

        embed = discord.Embed(
            title="Phân tích tạm thời",
            description=analysis["summary"],
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc),
        )
        await status_message.edit(content=None, embed=embed)

    async def generate_gemini_analysis(
        self,
        thread: discord.Thread,
        category: str,
        text: str,
        attachment_names: list[str],
        image_parts: list[Any] | None = None,
    ) -> str | None:
        if not self.gemini_client:
            return None

        current_knowledge = load_knowledge_base()

        prompt = (
            f"Bạn là chuyên gia kỹ thuật AI chính thức của phần mềm MTH Recap Studio (MTH AI Studio trên Windows).\n"
            f"Bạn là AI đa phương thức (Multimodal Vision), CÓ KHẢ NĂNG NHÌN VÀ ĐỌC HÌNH ẢNH CHỤP MÀN HÌNH CỰC KỲ RÕ RÀNG.\n\n"
            f"HÃY ĐỌC KỸ HÌNH ẢNH VÀ MÔ TẢ ĐỂ BẮT ĐÚNG BỆNH VÀ HƯỚNG DẪN KHÁCH HÀNG:\n"
            f"1. Nhìn ảnh chụp màn hình: Quan sát giao diện app, trạng thái các nút bấm, lỗi hiển thị hoặc bảng chọn chapter/ảnh.\n"
            f"2. NẾU LỖI LÀ KHÔNG MỞ ĐƯỢC TRÌNH DUYỆT / KHÔNG CÀO ĐƯỢC ẢNH / LỖI CHROMEDRIVER:\n"
            f"   -> NGUYÊN NHÂN CHÍNH: Người dùng đang mở sẵn trình duyệt CỐC CỐC hoặc GOOGLE CHROME làm xung đột cổng debug hoặc khóa profile khiến app không nhận được driver.\n"
            f"   -> HƯỚNG DẪN: Bảo người dùng đóng hoàn toàn trình duyệt Cốc Cốc / Chrome (Mở Task Manager Ctrl+Shift+Esc để tắt sạch tiến trình coccoc.exe / chrome.exe), sau đó quay lại tool MTH Recap bấm tải lại.\n"
            f"3. NẾU LỖI RENDER: Hướng dẫn đổi tên thư mục không dấu tiếng Việt, loại trừ Antivirus chặn FFmpeg, giảm thread count.\n\n"
            f"Trả lời bằng tiếng Việt thân thiện, rõ ràng, thực tế theo 4 mục:\n"
            f"📌 1. Tóm tắt lỗi\n"
            f"🔍 2. Nguyên nhân chính xác\n"
            f"🛠️ 3. Cách khắc phục nhanh từng bước\n"
            f"💬 4. Hỗ trợ thêm\n\n"
            f"TÀI LIỆU KỸ THUẬT THỜI GIAN THỰC:\n{current_knowledge}\n\n"
            f"Tên Thread: {thread.name}\n"
            f"Mô tả của người dùng: {text}"
        )

        contents = [prompt]
        if image_parts:
            contents.extend(image_parts)

        tried_models = []
        for model in [self.settings.gemini_model, *self.settings.gemini_fallback_models]:
            if not model or model in tried_models:
                continue
            tried_models.append(model)
            try:
                response = await asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=model,
                    contents=contents,
                )
                text = (response.text or "").strip()
                if text:
                    return text
            except Exception as exc:
                print(f"Gemini analysis failed on {model}: {exc}")
        return None

    def build_analysis(self, category: str, text: str, attachment_names: list[str]) -> dict[str, Any]:
        normalized = text.lower()
        has_image = any(name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")) for name in attachment_names)
        has_log = any(name.lower().endswith((".log", ".txt", ".json")) for name in attachment_names)
        mentions_windows = "win11" in normalized or "windows 11" in normalized or "windows11" in normalized

        missing = []
        if not mentions_windows:
            missing.append("Windows version")
        if "phi\u00ean b\u1ea3n" not in normalized and "version" not in normalized:
            missing.append("Phi\u00ean b\u1ea3n app")
        if not has_log:
            missing.append("File log ho\u1eb7c n\u1ed9i dung l\u1ed7i d\u1ea1ng text")
        if not has_image:
            missing.append("\u1ea2nh/video m\u00e0n h\u00ecnh l\u1ed7i")

        if category == "render":
            summary = (
                "Bot \u0111ang th\u1ea5y \u0111\u00e2y l\u00e0 nh\u00f3m l\u1ed7i render/xu\u1ea5t video. "
                "Windows 11 th\u01b0\u1eddng kh\u00f4ng ph\u1ea3i nguy\u00ean nh\u00e2n ch\u00ednh; c\u1ea7n log \u0111\u1ec3 ch\u1ed1t l\u1ed7i."
                if mentions_windows
                else "Bot \u0111ang th\u1ea5y \u0111\u00e2y l\u00e0 nh\u00f3m l\u1ed7i render/xu\u1ea5t video."
            )
            causes = [
                "FFmpeg thi\u1ebfu, sai phi\u00ean b\u1ea3n, ho\u1eb7c kh\u00f4ng ch\u1ea1y \u0111\u01b0\u1ee3c trong m\u00f4i tr\u01b0\u1eddng app.",
                "\u0110\u01b0\u1eddng d\u1eabn project/output c\u00f3 k\u00fd t\u1ef1 \u0111\u1eb7c bi\u1ec7t, qu\u00e1 d\u00e0i, ho\u1eb7c thi\u1ebfu quy\u1ec1n ghi.",
                "Thi\u1ebfu file \u0111\u1ea7u v\u00e0o: audio, subtitle, image/video frame, model, ho\u1eb7c file b\u1ecb move/x\u00f3a.",
                "Render b\u1ecb d\u1eebng do GPU/RAM/VRAM kh\u00f4ng \u0111\u1ee7, nh\u1ea5t l\u00e0 khi project d\u00e0i.",
            ]
            actions = [
                "Ch\u1ea1y l\u1ea1i v\u1edbi project ng\u1eafn 10-20 gi\u00e2y \u0111\u1ec3 xem l\u1ed7i c\u00f3 l\u1eb7p l\u1ea1i kh\u00f4ng.",
                "\u0110\u1ed5i output sang th\u01b0 m\u1ee5c d\u1ec5 ghi nh\u01b0 `D:\\mthrecap\\temp\\render_test`.",
                "Ki\u1ec3m tra `ffmpeg_bin\\ffmpeg.exe` c\u00f3 t\u1ed3n t\u1ea1i v\u00e0 app c\u00f3 quy\u1ec1n ch\u1ea1y file \u0111\u00f3.",
                "G\u1eedi th\u00eam file log sau l\u1ea7n render fail \u0111\u1ec3 team x\u00e1c \u0111\u1ecbnh \u0111\u00fang d\u00f2ng l\u1ed7i.",
            ]
        elif category == "login":
            summary = "Bot \u0111ang th\u1ea5y \u0111\u00e2y l\u00e0 nh\u00f3m l\u1ed7i \u0111\u0103ng nh\u1eadp/k\u00edch ho\u1ea1t."
            causes = [
                "Token/license sai, h\u1ebft h\u1ea1n, ho\u1eb7c \u0111ang d\u00f9ng tr\u00ean thi\u1ebft b\u1ecb kh\u00e1c.",
                "M\u00e1y kh\u00e1ch kh\u00f4ng k\u1ebft n\u1ed1i \u0111\u01b0\u1ee3c server x\u00e1c th\u1ef1c.",
                "Th\u1eddi gian h\u1ec7 th\u1ed1ng sai l\u00e0m request b\u1ecb t\u1eeb ch\u1ed1i.",
            ]
            actions = [
                "Che key/license tr\u01b0\u1edbc khi g\u1eedi \u1ea3nh.",
                "Ki\u1ec3m tra l\u1ea1i internet, VPN/proxy, ng\u00e0y gi\u1edd Windows.",
                "G\u1eedi email t\u00e0i kho\u1ea3n v\u00e0 th\u00f4ng b\u00e1o l\u1ed7i nguy\u00ean v\u0103n.",
            ]
        else:
            summary = "Bot \u0111\u00e3 gom th\u00f4ng tin ban \u0111\u1ea7u, nh\u01b0ng ch\u01b0a \u0111\u1ee7 log \u0111\u1ec3 k\u1ebft lu\u1eadn ch\u00ednh x\u00e1c."
            causes = [
                "Ch\u01b0a \u0111\u1ee7 th\u00f4ng tin \u0111\u1ec3 ph\u00e2n lo\u1ea1i ch\u00ednh x\u00e1c.",
                "C\u1ea7n th\u00f4ng b\u00e1o l\u1ed7i nguy\u00ean v\u0103n ho\u1eb7c log \u0111\u1ec3 truy nguy\u00ean nh\u00e2n.",
            ]
            actions = [
                "G\u1eedi l\u1ea1i c\u00e1c b\u01b0\u1edbc t\u1ea1o l\u1ea1i l\u1ed7i theo th\u1ee9 t\u1ef1.",
                "G\u1eedi \u1ea3nh/video m\u00e0n h\u00ecnh v\u00e0 file log n\u1ebfu c\u00f3.",
                "N\u00f3i r\u00f5 l\u1ed7i x\u1ea3y ra sau khi b\u1ea5m n\u00fat n\u00e0o trong app.",
            ]

        if has_image and not has_log:
            actions.append("\u1ea2nh \u0111\u00e3 gi\u00fap team xem ng\u1eef c\u1ea3nh, nh\u01b0ng v\u1eabn c\u1ea7n log/text l\u1ed7i \u0111\u1ec3 ph\u00e2n t\u00edch ch\u00ednh x\u00e1c.")
        if has_log:
            missing = [item for item in missing if "log" not in item.lower()]
        if not missing:
            missing = ["T\u1ea1m \u0111\u1ee7 th\u00f4ng tin c\u01a1 b\u1ea3n. Support c\u00f3 th\u1ec3 xem log/\u1ea3nh \u0111\u1ec3 k\u1ebft lu\u1eadn."]

        return {
            "summary": summary,
            "causes": causes,
            "actions": actions,
            "missing": missing,
        }

    def support_mention(self, guild: discord.Guild | None) -> str:
        if not guild or not self.settings.support_role_id:
            return ""
        role = guild.get_role(self.settings.support_role_id)
        return f"{role.mention} " if role else ""

    async def create_thread(
        self,
        message: discord.Message,
        title: str,
        content: str,
        rule: dict[str, Any],
        report_id: str,
        reporter: discord.abc.User | discord.Member,
    ) -> discord.Thread | None:
        if not hasattr(message, "create_thread"):
            return None

        thread = await message.create_thread(name=title[:100], auto_archive_duration=1440)
        checklist = (
            f"**M\u00e3 l\u1ed7i:** `{report_id}`\n"
            f"**Ng\u01b0\u1eddi b\u00e1o:** {reporter.mention}\n\n"
            f"{rule['reply']}\n\n"
            "**Checklist c\u1ea7n b\u1ed5 sung:**\n"
            "- Phi\u00ean b\u1ea3n app\n"
            "- Windows version\n"
            "- \u1ea2nh/video m\u00e0n h\u00ecnh l\u1ed7i\n"
            "- C\u00e1c b\u01b0\u1edbc t\u1ea1o l\u1ea1i l\u1ed7i\n"
            "- File log n\u1ebfu c\u00f3\n\n"
            f"**N\u1ed9i dung ban \u0111\u1ea7u:** {content}"
        )
        await thread.send(checklist, allowed_mentions=discord.AllowedMentions(users=True))
        return thread

    async def write_report_log(
        self,
        message: discord.Message,
        thread: discord.Thread | None,
        content: str,
        category: str,
        report_id: str,
        reporter: discord.abc.User | discord.Member,
    ) -> None:
        self.settings.bug_log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": report_id,
            "created_at": now_iso(),
            "guild_id": message.guild.id if message.guild else None,
            "channel_id": message.channel.id,
            "thread_id": thread.id if thread else None,
            "message_id": message.id,
            "reporter_id": reporter.id,
            "reporter_name": str(reporter),
            "category": category,
            "content": content,
            "message_url": message.jump_url,
            "thread_url": thread.jump_url if thread else None,
        }
        with self.settings.bug_log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    async def mirror_to_staff(
        self,
        message: discord.Message,
        thread: discord.Thread | None,
        content: str,
        category: str,
        report_id: str,
        reporter: discord.abc.User | discord.Member,
    ) -> None:
        if not self.settings.staff_bug_channel_id:
            return

        channel = self.get_channel(self.settings.staff_bug_channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return

        embed = discord.Embed(
            title=f"Bug m\u1edbi #{report_id}",
            description=content[:2048],
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Ph\u00e2n lo\u1ea1i", value=category, inline=True)
        embed.add_field(name="Ng\u01b0\u1eddi b\u00e1o", value=f"{reporter} ({reporter.id})", inline=True)
        embed.add_field(name="Link", value=thread.jump_url if thread else message.jump_url, inline=False)
        await channel.send(embed=embed)


async def start_health_server(port: int) -> None:
    try:
        from aiohttp import web
        async def handle_health(request: web.Request) -> web.Response:
            return web.json_response({"status": "healthy", "service": "mth-discord-bot", "timestamp": now_iso()})

        app = web.Application()
        app.router.add_get("/", handle_health)
        app.router.add_get("/health", handle_health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"🌐 Web health server đã khởi động trên cổng {port} (Hỗ trợ Render Free Web Service)")
    except Exception as exc:
        print(f"⚠️ Không thể khởi động web health server: {exc}")


async def main() -> None:
    settings = load_settings()
    port = os.getenv("PORT")
    if port:
        await start_health_server(int(port))

    bot = SupportBot(settings)
    async with bot:
        await bot.start(settings.token)


if __name__ == "__main__":
    asyncio.run(main())
