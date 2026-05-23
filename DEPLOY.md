# Deploy Instructions

## 1. Supabase Setup

1. Create a free project at https://supabase.com
2. Go to **SQL Editor → New Query**, paste the contents of `schema.sql`, run it
3. Go to **Project Settings → API**:
   - Copy **Project URL** → `SUPABASE_URL`
   - Copy **service_role** key (not anon) → `SUPABASE_KEY`

## 2. Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy the token → `TELEGRAM_BOT_TOKEN`
3. Generate a random secret (e.g. `openssl rand -hex 20`) → `TELEGRAM_WEBHOOK_SECRET`

## 3. Anthropic API Key

Get key from https://console.anthropic.com → `ANTHROPIC_API_KEY`

## 4. YouTube Data API (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **YouTube Data API v3**
3. Create **API Key** → `YOUTUBE_API_KEY`

   If skipped, the agent falls back to curated links + YouTube search URLs.

## 5. Sentry (error tracking)

1. Create a free account at https://sentry.io
2. **Create Project** → platform **Python → FastAPI** → copy the **DSN**
   (looks like `https://<key>@o12345.ingest.de.sentry.io/678`)
3. Set it as a fly secret (this triggers a redeploy automatically):
   ```bash
   fly secrets set SENTRY_DSN="https://<key>@o12345.ingest.de.sentry.io/678"
   ```
4. After deploy, verify it works:
   ```bash
   curl https://gym-agent.fly.dev/health
   # → {"status":"ok","sentry":true}

   curl https://gym-agent.fly.dev/debug/sentry
   # triggers a test error — within ~30s a "Sentry test error"
   # issue appears in your Sentry dashboard
   ```

The app tags each event with the Fly app name (`environment`) and machine
version (`release`), and forwards every `logger.error`/`logger.exception`
(including scheduler and Telegram failures) to Sentry automatically.

Optional tuning secrets:
- `SENTRY_ENVIRONMENT` — override the environment tag (default: Fly app name)
- `SENTRY_TRACES_SAMPLE_RATE` / `SENTRY_PROFILES_SAMPLE_RATE` — default `0.1`

## 6. Fly.io Deploy

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app (first time only)
fly launch --no-deploy --name gym-agent --region fra

# Set secrets
fly secrets set \
  ANTHROPIC_API_KEY="sk-ant-..." \
  TELEGRAM_BOT_TOKEN="123456:ABC..." \
  TELEGRAM_WEBHOOK_SECRET="your-random-secret" \
  SUPABASE_URL="https://xxxx.supabase.co" \
  SUPABASE_KEY="eyJ..." \
  APP_URL="https://gym-agent.fly.dev" \
  YOUTUBE_API_KEY="AIza..." \
  SENTRY_DSN="https://...@sentry.io/..."

# Deploy
fly deploy

# Check logs
fly logs
```

## 7. Verify Webhook

After deploy, check:
```bash
curl https://gym-agent.fly.dev/health
# → {"status":"ok"}
```

Open your bot in Telegram and send `/start`.

## Environment Variables Summary

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `TELEGRAM_BOT_TOKEN` | ✅ | From BotFather |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service_role key |
| `APP_URL` | ✅ | Your Fly.io app URL (for webhook) |
| `TELEGRAM_WEBHOOK_SECRET` | Recommended | Secures webhook endpoint |
| `YOUTUBE_API_KEY` | Optional | Falls back to search URLs |
| `SENTRY_DSN` | Optional | Error tracking |
