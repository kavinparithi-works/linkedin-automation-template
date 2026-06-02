import json
import os
import re
import time
import shutil
import datetime
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR        = Path(__file__).parent

CONTENT_DIR     = BASE_DIR / "content"          # subfolder 1: post text files
IMAGES_DIR      = BASE_DIR / "content_images"   # subfolder 2: post image files
POSTED_DIR      = BASE_DIR / "posted"           # archive after posting

CONTENT_GLOB    = "post_*.txt"                  # matches post_1.txt … post_n.txt
IMAGE_TEMPLATE  = "{name}_image"                # matches post_1_image.jpg/jpeg/png

# ---------------------------------------------------------------------------
# Schedule — edit these to control when and how often posts go out
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Master switch — set AUTOMATE secret to "Active" or "Inactive" in GitHub
# ---------------------------------------------------------------------------
# AUTOMATE = "Active"   → runs normally, posts go out as scheduled
# AUTOMATE = "Inactive" → script exits immediately, nothing is posted
#
# To pause all posting: go to GitHub repo → Settings → Secrets → AUTOMATE
# → Update → change value to "Inactive" → Save
# To resume: change it back to "Active"
# ---------------------------------------------------------------------------

AUTOMATE = os.environ.get("AUTOMATE", "Active").strip()

# ---------------------------------------------------------------------------

POST_SCHEDULE = os.environ.get("POST_SCHEDULE", "weekdays")
# The cron schedule in the GitHub Actions workflow controls the actual run time.
# POST_SCHEDULE here controls DAY filtering and how many posts per run:
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  "all"          → post every pending file on every run                  │
# │  "weekdays"     → one post per run, Mon–Fri only, incremental           │
# │  "YYYY-MM-DD"   → one post on that exact date only                      │
# │  "MON,WED,FRI"  → one post per run on those days only, incremental      │
# │  valid tokens   → MON  TUE  WED  THU  FRI  SAT  SUN                    │
# └─────────────────────────────────────────────────────────────────────────┘

# ---------------------------------------------------------------------------

LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

EXPIRY_BUFFER_SECONDS = 300

_DAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


# ---------------------------------------------------------------------------
# Text formatting — bold(text), italic(text), bolditalic(text),
#                   semibold(text), cursive(text), strikethrough(text)
# ---------------------------------------------------------------------------

_ALPHA    = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_ALPHANUM = _ALPHA + "0123456789"

def _t(src, dst):
    return str.maketrans(src, dst)

_MAPS = {
    "bold": _t(
        _ALPHANUM,
        "\U0001D5D4\U0001D5D5\U0001D5D6\U0001D5D7\U0001D5D8\U0001D5D9"
        "\U0001D5DA\U0001D5DB\U0001D5DC\U0001D5DD\U0001D5DE\U0001D5DF"
        "\U0001D5E0\U0001D5E1\U0001D5E2\U0001D5E3\U0001D5E4\U0001D5E5"
        "\U0001D5E6\U0001D5E7\U0001D5E8\U0001D5E9\U0001D5EA\U0001D5EB"
        "\U0001D5EC\U0001D5ED"
        "\U0001D5EE\U0001D5EF\U0001D5F0\U0001D5F1\U0001D5F2\U0001D5F3"
        "\U0001D5F4\U0001D5F5\U0001D5F6\U0001D5F7\U0001D5F8\U0001D5F9"
        "\U0001D5FA\U0001D5FB\U0001D5FC\U0001D5FD\U0001D5FE\U0001D5FF"
        "\U0001D600\U0001D601\U0001D602\U0001D603\U0001D604\U0001D605"
        "\U0001D606\U0001D607"
        "\U0001D7EC\U0001D7ED\U0001D7EE\U0001D7EF\U0001D7F0"
        "\U0001D7F1\U0001D7F2\U0001D7F3\U0001D7F4\U0001D7F5"
    ),
    "italic": _t(
        _ALPHA,
        "\U0001D608\U0001D609\U0001D60A\U0001D60B\U0001D60C\U0001D60D"
        "\U0001D60E\U0001D60F\U0001D610\U0001D611\U0001D612\U0001D613"
        "\U0001D614\U0001D615\U0001D616\U0001D617\U0001D618\U0001D619"
        "\U0001D61A\U0001D61B\U0001D61C\U0001D61D\U0001D61E\U0001D61F"
        "\U0001D620\U0001D621"
        "\U0001D622\U0001D623\U0001D624\U0001D625\U0001D626\U0001D627"
        "\U0001D628\U0001D629\U0001D62A\U0001D62B\U0001D62C\U0001D62D"
        "\U0001D62E\U0001D62F\U0001D630\U0001D631\U0001D632\U0001D633"
        "\U0001D634\U0001D635\U0001D636\U0001D637\U0001D638\U0001D639"
        "\U0001D63A\U0001D63B"
    ),
    "bolditalic": _t(
        _ALPHA,
        "\U0001D63C\U0001D63D\U0001D63E\U0001D63F\U0001D640\U0001D641"
        "\U0001D642\U0001D643\U0001D644\U0001D645\U0001D646\U0001D647"
        "\U0001D648\U0001D649\U0001D64A\U0001D64B\U0001D64C\U0001D64D"
        "\U0001D64E\U0001D64F\U0001D650\U0001D651\U0001D652\U0001D653"
        "\U0001D654\U0001D655"
        "\U0001D656\U0001D657\U0001D658\U0001D659\U0001D65A\U0001D65B"
        "\U0001D65C\U0001D65D\U0001D65E\U0001D65F\U0001D660\U0001D661"
        "\U0001D662\U0001D663\U0001D664\U0001D665\U0001D666\U0001D667"
        "\U0001D668\U0001D669\U0001D66A\U0001D66B\U0001D66C\U0001D66D"
        "\U0001D66E\U0001D66F"
    ),
    "semibold": _t(
        _ALPHANUM,
        "\U0001D400\U0001D401\U0001D402\U0001D403\U0001D404\U0001D405"
        "\U0001D406\U0001D407\U0001D408\U0001D409\U0001D40A\U0001D40B"
        "\U0001D40C\U0001D40D\U0001D40E\U0001D40F\U0001D410\U0001D411"
        "\U0001D412\U0001D413\U0001D414\U0001D415\U0001D416\U0001D417"
        "\U0001D418\U0001D419"
        "\U0001D41A\U0001D41B\U0001D41C\U0001D41D\U0001D41E\U0001D41F"
        "\U0001D420\U0001D421\U0001D422\U0001D423\U0001D424\U0001D425"
        "\U0001D426\U0001D427\U0001D428\U0001D429\U0001D42A\U0001D42B"
        "\U0001D42C\U0001D42D\U0001D42E\U0001D42F\U0001D430\U0001D431"
        "\U0001D432\U0001D433"
        "\U0001D7CE\U0001D7CF\U0001D7D0\U0001D7D1\U0001D7D2"
        "\U0001D7D3\U0001D7D4\U0001D7D5\U0001D7D6\U0001D7D7"
    ),
    "cursive": _t(
        _ALPHA,
        "\U0001D49Cℬ\U0001D49E\U0001D49Fℰℱ\U0001D4A2ℋ"
        "ℐ\U0001D4A5\U0001D4A6ℒℳ\U0001D4A9\U0001D4AA\U0001D4AB"
        "\U0001D4ACℛ\U0001D4AE\U0001D4AF\U0001D4B0\U0001D4B1\U0001D4B2"
        "\U0001D4B3\U0001D4B4\U0001D4B5"
        "\U0001D4B6\U0001D4B7\U0001D4B8\U0001D4B9ℯ\U0001D4BBℊ"
        "\U0001D4BD\U0001D4BE\U0001D4BF\U0001D4C0ℓ\U0001D4C2\U0001D4C3"
        "ℴ\U0001D4C5\U0001D4C6\U0001D4C7\U0001D4C8\U0001D4C9\U0001D4CA"
        "\U0001D4CB\U0001D4CC\U0001D4CD\U0001D4CE\U0001D4CF"
    ),
    "strikethrough": None,
}

_TAG_RE = re.compile(
    r"\b(bold|italic|bolditalic|semibold|cursive|strikethrough)\((.+?)\)",
    re.DOTALL,
)

def _apply(tag, content):
    if tag == "strikethrough":
        return "".join(c + "̶" for c in content)
    return content.translate(_MAPS[tag])

def format_text(text):
    return _TAG_RE.sub(lambda m: _apply(m.group(1), m.group(2)), text)


# ---------------------------------------------------------------------------
# Scheduling — day filter only (time is handled by the cron in GitHub Actions)
# ---------------------------------------------------------------------------

def check_schedule():
    """Returns (should_post, post_all)."""
    today   = datetime.date.today()
    weekday = today.weekday()
    sched   = POST_SCHEDULE.strip()

    if sched.lower() == "all":
        return True, True

    try:
        if today == datetime.date.fromisoformat(sched):
            return True, False
        print(f"[schedule] Specific date {sched}. Today is {today}. Skipping.")
        return False, False
    except ValueError:
        pass

    if sched.lower() == "weekdays":
        if weekday < 5:
            return True, False
        print(f"[schedule] Weekdays only. Today is {today.strftime('%A')}. Skipping.")
        return False, False

    tokens  = [d.strip().upper() for d in sched.split(",")]
    allowed = [_DAY_MAP[d] for d in tokens if d in _DAY_MAP]
    if not allowed:
        print(f"[schedule] Unrecognised POST_SCHEDULE: '{sched}'. Skipping.")
        return False, False
    if weekday in allowed:
        return True, False
    print(f"[schedule] Post days: {sched}. Today ({today.strftime('%A')}) not in list. Skipping.")
    return False, False


# ---------------------------------------------------------------------------
# Token — read from environment variables (set as GitHub Secrets)
# ---------------------------------------------------------------------------

def load_tokens():
    """
    Reads credentials from environment variables.
    These are set as GitHub Actions Secrets and injected at runtime.
    """
    required = ["LI_CLIENT_ID", "LI_CLIENT_SECRET", "LI_ACCESS_TOKEN", "LI_REFRESH_TOKEN"]
    missing  = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}\n"
            "Add them as GitHub Actions Secrets in your repository settings."
        )
    return {
        "client_id":               os.environ["LI_CLIENT_ID"],
        "client_secret":           os.environ["LI_CLIENT_SECRET"],
        "access_token":            os.environ["LI_ACCESS_TOKEN"],
        "access_token_expires_at": int(os.environ.get("LI_ACCESS_TOKEN_EXPIRES_AT", "0")),
        "refresh_token":           os.environ["LI_REFRESH_TOKEN"],
        "refresh_token_expires_at": int(os.environ.get("LI_REFRESH_TOKEN_EXPIRES_AT", "0")),
    }


def is_expired(expires_at):
    return time.time() >= (expires_at - EXPIRY_BUFFER_SECONDS)


def refresh_access_token(config):
    """Silently refresh the access token using the refresh token."""
    print("Access token expired — refreshing...")
    resp = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type":    "refresh_token",
            "refresh_token": config["refresh_token"],
            "client_id":     config["client_id"],
            "client_secret": config["client_secret"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()

    config["access_token"]            = data["access_token"]
    config["access_token_expires_at"] = int(time.time()) + data["expires_in"]
    if "refresh_token" in data:
        config["refresh_token"] = data["refresh_token"]
    if "refresh_token_expires_in" in data:
        config["refresh_token_expires_at"] = int(time.time()) + data["refresh_token_expires_in"]

    # Write refreshed tokens to a file so the workflow can read and update
    # GitHub Secrets automatically via the gh CLI step that follows.
    refreshed = {
        "LI_ACCESS_TOKEN":             config["access_token"],
        "LI_ACCESS_TOKEN_EXPIRES_AT":  str(config["access_token_expires_at"]),
        "LI_REFRESH_TOKEN":            config["refresh_token"],
        "LI_REFRESH_TOKEN_EXPIRES_AT": str(config["refresh_token_expires_at"]),
    }
    token_out = Path(__file__).parent / "refreshed_tokens.json"
    token_out.write_text(json.dumps(refreshed, indent=2))
    print(f"Token refreshed. New values written to {token_out.name} for secret update.")

    # Also write to $GITHUB_OUTPUT for step outputs (modern syntax)
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as fh:
            fh.write(f"token_refreshed=true\n")

    return config


def get_valid_token(config):
    if config.get("refresh_token_expires_at") and is_expired(config["refresh_token_expires_at"]):
        raise RuntimeError(
            "Refresh token has expired. Run get_token.py locally to re-authorize, "
            "then update your GitHub Secrets."
        )
    if is_expired(config.get("access_token_expires_at", 0)):
        config = refresh_access_token(config)
    return config["access_token"], config


# ---------------------------------------------------------------------------
# Post helpers
# ---------------------------------------------------------------------------

def find_image_for_post(post_name):
    stem = IMAGE_TEMPLATE.format(name=post_name)
    for ext in [".jpg", ".jpeg", ".png"]:
        candidate = IMAGES_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def get_pending_posts():
    posts = []
    for content_file in sorted(CONTENT_DIR.glob(CONTENT_GLOB)):
        post_name  = content_file.stem
        image_file = find_image_for_post(post_name)
        posts.append((post_name, content_file, image_file))
    return posts


def get_my_profile(token):
    resp = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()["sub"]


def upload_image(token, author_urn, image_path):
    reg = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner":   author_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier":       "urn:li:userGeneratedContent",
                }],
            }
        },
    )
    reg.raise_for_status()
    reg_data   = reg.json()
    upload_url = reg_data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset = reg_data["value"]["asset"]

    with open(image_path, "rb") as img:
        requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {token}"},
            data=img,
        ).raise_for_status()

    return asset


def post_to_linkedin(token, author_urn, text, image_asset=None):
    content = {
        "shareCommentary":  {"text": text},
        "shareMediaCategory": "IMAGE" if image_asset else "NONE",
    }
    if image_asset:
        content["media"] = [{
            "status":      "READY",
            "description": {"text": "Post image"},
            "media":       image_asset,
            "title":       {"text": "Image"},
        }]

    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization":             f"Bearer {token}",
            "Content-Type":              "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json={
            "author":           author_urn,
            "lifecycleState":   "PUBLISHED",
            "specificContent":  {"com.linkedin.ugc.ShareContent": content},
            "visibility":       {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        },
    )
    resp.raise_for_status()
    return resp.json()


def move_to_posted(content_file, image_file):
    POSTED_DIR.mkdir(exist_ok=True)
    shutil.move(str(content_file), POSTED_DIR / content_file.name)
    if image_file:
        shutil.move(str(image_file), POSTED_DIR / image_file.name)
        print(f"  Moved {content_file.name} + {image_file.name} → posted/")
    else:
        print(f"  Moved {content_file.name} → posted/")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if AUTOMATE.lower() != "active":
        print(f"[AUTOMATE={AUTOMATE}] Automation is inactive — skipping all posts.")
        return

    should_post, post_all = check_schedule()
    if not should_post:
        return

    pending = get_pending_posts()
    if not pending:
        print("No posts ready to publish (check content/ and content_images/ folders).")
        return

    to_publish = pending if post_all else pending[:1]

    config            = load_tokens()
    token, config     = get_valid_token(config)

    print("Fetching LinkedIn profile...")
    author_urn = f"urn:li:person:{get_my_profile(token)}"

    for post_name, content_file, image_file in to_publish:
        print(f"\nProcessing : {post_name}")
        print(f"  Content  : {content_file.name}")
        print(f"  Image    : {image_file.name if image_file else '(none — text only)'}")

        text = format_text(content_file.read_text(encoding="utf-8").strip())
        if not text:
            print("  SKIPPING — content file is empty.")
            continue

        image_asset = None
        if image_file:
            print("  Uploading image...")
            image_asset = upload_image(token, author_urn, image_file)
        else:
            print("  No image — posting text only.")

        print("  Publishing post...")
        post_to_linkedin(token, author_urn, text, image_asset)
        print("  Published successfully.")

        move_to_posted(content_file, image_file)


if __name__ == "__main__":
    main()
