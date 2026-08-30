# Deploy Discord Bot on Render

Use a Render Background Worker for this bot. A regular free web service can sleep when idle, which is not suitable for a Discord bot that needs to stay connected.

## Option A: Blueprint

1. Push this repo to GitHub.
2. In Render, choose **New** -> **Blueprint**.
3. Select the GitHub repo.
4. Render detects `render.yaml`.
5. Fill the secret environment variables.
6. Deploy.

## Option B: Manual Worker

Create a new **Background Worker** and use:

```text
Root Directory: discord_support_bot
Build Command: pip install -r requirements.txt
Start Command: python bot.py
```

## Environment Variables

Required:

```env
DISCORD_TOKEN=
BUG_CHANNEL_ID=
SUPPORT_ROLE_ID=
```

Recommended:

```env
STAFF_BUG_CHANNEL_ID=
DISCORD_ANNOUNCE_WEBHOOK=
GITHUB_REPO=owner/repo
GITHUB_POLL_SECONDS=300
GITHUB_ANNOUNCE_ON_START=false
```

Gemini:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.5-flash-lite
```

Private GitHub repo:

```env
GITHUB_TOKEN=
```

## Notes

- If `GITHUB_ANNOUNCE_ON_START=false`, the first Render deploy records the latest release without posting it. New releases after that will be announced.
- If you want the current latest release to post immediately after deploy, set `GITHUB_ANNOUNCE_ON_START=true`.
- Keep Discord token, Gemini key, webhook URL, and GitHub token secret. Do not commit them.
