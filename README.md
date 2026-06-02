# LinkedIn Auto-Poster

> Post to LinkedIn every day — even when your laptop is completely shut down.

Runs on **GitHub Actions** (free). Set up once, works forever.

## ✅ Features

- 📅 Posts daily at your chosen time
- ☁️ Runs on GitHub's cloud — laptop does not need to be on
- 🔄 LinkedIn tokens auto-refresh silently
- 🔛 `AUTOMATE` secret — pause/resume posting instantly
- 🚨 Email alert if anything fails
- 🆓 100% free

## 🚀 Get started

1. Click **"Use this template"** → **Create a new repository** → set **Private**
2. Clone it to your laptop
3. Open **`SETUP_GUIDE.html`** in your browser — full step-by-step guide

## 📁 Folder structure

```
content/            ← your post_1.txt, post_2.txt, ...
content_images/     ← your post_1_image.jpg, ... (optional)
posted/             ← files move here automatically after posting
poster.py           ← main script (do not edit)
get_token.py        ← run once locally to get LinkedIn tokens
SETUP_GUIDE.html    ← open this in your browser for full setup guide
```

## ✍️ Formatting tags (inside your .txt files)

| Tag | Effect |
|---|---|
| `bold(text)` | **Bold** |
| `italic(text)` | *Italic* |
| `bolditalic(text)` | ***Bold italic*** |
| `semibold(text)` | Serif bold |
| `cursive(text)` | Script style |
| `strikethrough(text)` | ~~Strikethrough~~ |

## 🔒 Required GitHub Secrets

| Secret | What it is |
|---|---|
| `GH_PAT` | GitHub Personal Access Token (repo + workflow scope) |
| `LI_CLIENT_ID` | LinkedIn App Client ID |
| `LI_CLIENT_SECRET` | LinkedIn App Client Secret |
| `LI_ACCESS_TOKEN` | From get_token.py |
| `LI_ACCESS_TOKEN_EXPIRES_AT` | From get_token.py |
| `LI_REFRESH_TOKEN` | From get_token.py |
| `LI_REFRESH_TOKEN_EXPIRES_AT` | From get_token.py |
| `POST_SCHEDULE` | `weekdays` / `all` / `MON,WED,FRI` / `2026-06-15` |
| `AUTOMATE` | `Active` to run · `Inactive` to pause |

Full instructions in `SETUP_GUIDE.html`.

---

*Open `SETUP_GUIDE.html` in your browser for the complete step-by-step guide with screenshots and troubleshooting.*
