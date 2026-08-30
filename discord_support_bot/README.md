# Discord Support Bot

Bot này dùng cho server Discord hỗ trợ người dùng MTH Recap:

- Tự phản hồi khi người dùng báo lỗi trong kênh cấu hình.
- Tạo thread riêng cho từng lỗi để team xử lý gọn hơn.
- Ping role hỗ trợ khi có lỗi mới.
- Lưu log báo lỗi vào file JSONL local.
- Gửi thông báo phát hành/cập nhật qua Discord webhook.

## Cấu trúc server Discord đề xuất

Tạo các category/channel sau:

| Category | Channel | Mục đích |
| --- | --- | --- |
| Thông báo | `#announcements` | Chỉ admin/bot đăng update, bản vá, bảo trì |
| Hỗ trợ | `#support` | Hỏi đáp chung |
| Hỗ trợ | `#bao-loi` | Người dùng báo lỗi, bot tự tạo thread |
| Hỗ trợ | `#huong-dan` | FAQ, cách gửi log, cách cập nhật app |
| Nội bộ | `#staff-bugs` | Bot mirror lỗi mới cho team nếu cần |

Role nên có:

- `Admin`: quản trị server.
- `Support`: nhận ping khi có lỗi mới.
- `Customer`: người dùng đã mua hoặc đã đăng ký.
- `Bot`: role riêng cho bot, đặt cao hơn role user thường.

## Tạo bot trên Discord

1. Vào Discord Developer Portal.
2. Tạo Application mới, mở mục Bot và tạo bot.
3. Bật `Message Content Intent`.
4. Copy bot token, không đưa token vào Git.
5. Ở OAuth2 URL Generator chọn scope `bot` và `applications.commands`.
6. Chọn quyền: `View Channels`, `Send Messages`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`, `Use Slash Commands`, `Manage Threads` nếu muốn bot khóa thread.
7. Mời bot vào server bằng URL OAuth2.

## Cài đặt

```powershell
cd D:\mthrecap\discord_support_bot
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Sửa `.env`:

```env
DISCORD_TOKEN=bot_token_cua_ban
BUG_CHANNEL_ID=123456789012345678
SUPPORT_ROLE_ID=123456789012345678
STAFF_BUG_CHANNEL_ID=
BUG_LOG_PATH=data/bug_reports.jsonl
```

Lấy channel/role ID bằng cách bật Discord Developer Mode, rồi right click channel/role và chọn Copy ID.

## Chạy bot

```powershell
cd D:\mthrecap\discord_support_bot
.\.venv\Scripts\Activate.ps1
python bot.py
```

## Bật phân tích bằng Gemini

Nếu muốn bot phân tích lỗi thông minh hơn thay vì chỉ trả lời theo rule, tạo Gemini API key trong Google AI Studio rồi thêm vào `.env`:

```env
GEMINI_API_KEY=api_key_cua_ban
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite
```

Sau đó cài lại dependency và restart bot:

```powershell
pip install -r requirements.txt
python bot.py
```

Khi người dùng nhắn thêm trong thread hoặc gõ `!analyze`, bot sẽ ưu tiên gọi Gemini. Nếu thiếu API key hoặc Gemini lỗi, bot tự dùng phân tích rule nội bộ.

Gemini không tự biết toàn bộ phần mềm. Bot đưa cho Gemini các nguồn sau:

- Nội dung người dùng gửi trong thread.
- Tên file đính kèm, ví dụ ảnh/log. Bot chưa OCR nội dung ảnh.
- Phân loại rule từ `responses.json`.
- Kiến thức sản phẩm trong `knowledge_base.md`.

Muốn bot trả lời sát phần mềm hơn, bổ sung thêm lỗi thường gặp, đường dẫn log, quy trình render, license, voice, download vào `knowledge_base.md`.

## Cách người dùng báo lỗi

Người dùng có thể:

- Nhắn trực tiếp trong `#bao-loi`.
- Dùng lệnh slash `/bug mo_ta:...`.
- Gõ `!bug nội dung lỗi`.

Bot sẽ tự:

- Phân loại lỗi theo từ khóa trong `responses.json`.
- Trả lời checklist phù hợp.
- Tạo thread riêng.
- Ghi log vào `data/bug_reports.jsonl`.

## Gửi thông báo bằng webhook

Tạo Discord webhook trong channel `#announcements`, rồi chạy:

```powershell
$env:DISCORD_ANNOUNCE_WEBHOOK="https://discord.com/api/webhooks/..."
python announce.py --title "MTH Recap 1.2.0" --message "Đã sửa lỗi đăng nhập và cải thiện tốc độ render." --url "https://your-site/download"
```

Muốn tự đăng khi có update mới, thêm webhook vào `.env`:

```env
DISCORD_ANNOUNCE_WEBHOOK=https://discord.com/api/webhooks/...
```

Sau đó gọi script này sau khi build/release:

```powershell
python discord_support_bot\announce_update.py --notes "Đã sửa lỗi render và cải thiện ổn định." --url "https://your-site/download"
```

Script tự đọc version từ `backend/__init__.py` và chỉ đăng một lần cho mỗi version. Nếu cần đăng lại cùng version:

```powershell
python discord_support_bot\announce_update.py --force --notes "Hotfix nhỏ cho bản hiện tại."
```

## Tự đăng khi có GitHub Release mới

Nếu bot chạy trên Render, cấu hình các biến môi trường sau:

```env
GITHUB_REPO=your-github-user/your-repo
GITHUB_TOKEN=
GITHUB_POLL_SECONDS=300
GITHUB_ANNOUNCE_ON_START=false
DISCORD_ANNOUNCE_WEBHOOK=https://discord.com/api/webhooks/...
```

Bot sẽ kiểm tra GitHub Releases định kỳ. Khi thấy release tag mới, bot đăng nội dung release vào `#announcements`.
Nếu `GEMINI_API_KEY` được cấu hình, bot sẽ dùng Gemini để viết lại nội dung release thành bài thông báo tiếng Việt thân thiện hơn trước khi đăng.

Ghi chú:

- `GITHUB_TOKEN` có thể để trống nếu repo public. Nếu repo private, tạo GitHub token chỉ có quyền đọc repo.
- `GITHUB_ANNOUNCE_ON_START=false` giúp bot không đăng lại release cũ ngay lần deploy đầu tiên. Sau đó release mới sẽ tự đăng.
- Nếu không dùng webhook, có thể dùng `ANNOUNCEMENT_CHANNEL_ID`, nhưng webhook đơn giản hơn khi deploy Render.

## Deploy nhanh

Bot cần chạy 24/7. Có thể dùng:

- VPS Windows/Linux.
- Railway/Fly.io/Render.
- Docker hoặc PM2/systemd.

Không nên chạy bot bằng máy cá nhân nếu cần hỗ trợ khách hàng liên tục.
