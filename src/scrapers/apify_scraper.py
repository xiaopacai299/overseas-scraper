import os
from pathlib import Path
import requests
from src.proxy_helper import get_requests_proxies

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def get_apify_token(explicit_token: str = "") -> str:
    """Read Apify API token from argument, environment variable, or .env file."""
    if explicit_token and explicit_token.strip():
        return explicit_token.strip()
    env_tok = os.environ.get("APIFY_API_TOKEN", "").strip()
    if env_tok:
        return env_tok
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("APIFY_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def run_apify_actor(actor_id: str, run_input: dict, token: str = "", timeout_sec: int = 180) -> list[dict]:
    """
    Call Apify's synchronous REST API (run-sync-get-dataset-items) and return dataset items as a list of dicts.
    """
    api_token = get_apify_token(token)
    if not api_token:
        raise ValueError(
            "未检测到 APIFY_API_TOKEN！请先在项目根目录 .env 文件中配置 APIFY_API_TOKEN=apify_api_xxxx"
        )
    # Apify API uses '~' instead of '/' in URL path for actor_id
    actor_slug = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_slug}/run-sync-get-dataset-items"
    proxies = get_requests_proxies()
    resp = requests.post(
        url,
        params={"token": api_token, "format": "json", "clean": "true"},
        json=run_input,
        proxies=proxies,
        timeout=timeout_sec,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Apify 调用失败 (HTTP {resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    return data if isinstance(data, list) else []


def scrape_x_tweets(query: str, limit: int = 50, token: str = "") -> list[dict]:
    """Search X (Twitter) posts by keyword or hashtag via Apify."""
    items = run_apify_actor(
        "apidojo/tweet-scraper",
        {
            "searchTerms": [query],
            "maxItems": limit,
            "sort": "Latest",
        },
        token=token,
    )
    results = []
    for idx, item in enumerate(items[:limit], start=1):
        author_obj = item.get("author") or {}
        username = (
            author_obj.get("userName")
            or item.get("user", {}).get("screen_name")
            or item.get("username")
            or "x_user"
        )
        text = (item.get("text") or item.get("full_text") or "").replace("\r\n", " ").replace("\n", " ").strip()
        tweet_url = item.get("url") or item.get("twitterUrl") or f"https://x.com/{username}"
        created_at = item.get("createdAt") or item.get("created_at") or ""
        likes = item.get("likeCount") or item.get("favorite_count") or 0
        retweets = item.get("retweetCount") or item.get("retweet_count") or 0
        replies = item.get("replyCount") or 0
        if not text:
            continue
        results.append(
            {
                "序号": idx,
                "平台": "X (Twitter)",
                "作者账号": f"@{username}",
                "发布时间": str(created_at),
                "点赞数": likes,
                "转发数": retweets,
                "回复数": replies,
                "推文内容": text,
                "推文链接": tweet_url,
            }
        )
    return results


def scrape_tiktok_search(query: str, limit: int = 50, token: str = "") -> list[dict]:
    """Search TikTok videos/posts by keyword or hashtag via Apify."""
    clean_tag = query.lstrip("#").strip()
    items = run_apify_actor(
        "clockworks/free-tiktok-scraper",
        {
            "hashtags": [clean_tag],
            "resultsPerPage": limit,
        },
        token=token,
    )
    results = []
    for idx, item in enumerate(items[:limit], start=1):
        author_meta = item.get("authorMeta") or {}
        username = author_meta.get("name") or item.get("author") or "tiktok_user"
        text = (item.get("text") or item.get("desc") or "").replace("\r\n", " ").replace("\n", " ").strip()
        web_url = item.get("webVideoUrl") or item.get("url") or f"https://www.tiktok.com/tag/{clean_tag}"
        created_at = item.get("createTimeISO") or item.get("createTime") or ""
        likes = item.get("diggCount") or 0
        comments = item.get("commentCount") or 0
        plays = item.get("playCount") or 0
        if not text:
            continue
        results.append(
            {
                "序号": idx,
                "平台": "TikTok",
                "作者账号": f"@{username}",
                "发布时间": str(created_at),
                "播放量": plays,
                "点赞数": likes,
                "评论数": comments,
                "视频文案": text,
                "视频链接": web_url,
            }
        )
    return results


def scrape_instagram_hashtag(hashtag: str, limit: int = 40, token: str = "") -> list[dict]:
    """Scrape Instagram posts by hashtag via Apify."""
    clean_tag = hashtag.lstrip("#").replace(" ", "").strip()
    items = run_apify_actor(
        "apify/instagram-hashtag-scraper",
        {
            "hashtags": [clean_tag],
            "resultsLimit": limit,
        },
        token=token,
    )
    results = []
    for idx, item in enumerate(items[:limit], start=1):
        username = item.get("ownerUsername") or "ig_user"
        caption = (item.get("caption") or "").replace("\r\n", " ").replace("\n", " ").strip()
        url = item.get("url") or f"https://www.instagram.com/explore/tags/{clean_tag}/"
        timestamp = item.get("timestamp") or ""
        likes = item.get("likesCount") or 0
        comments = item.get("commentsCount") or 0
        if not caption:
            continue
        results.append(
            {
                "序号": idx,
                "平台": "Instagram",
                "作者账号": f"@{username}",
                "发布时间": str(timestamp),
                "点赞数": likes,
                "评论数": comments,
                "帖子正文": caption,
                "帖子链接": url,
            }
        )
    return results


def scrape_facebook_page_posts(page_url: str, limit: int = 30, token: str = "") -> list[dict]:
    """Scrape Facebook public page posts via Apify."""
    items = run_apify_actor(
        "apify/facebook-posts-scraper",
        {
            "startUrls": [{"url": page_url}],
            "resultsLimit": limit,
        },
        token=token,
    )
    results = []
    for idx, item in enumerate(items[:limit], start=1):
        page_name = item.get("pageName") or item.get("user", {}).get("name") or "Facebook Page"
        text = (item.get("text") or "").replace("\r\n", " ").replace("\n", " ").strip()
        url = item.get("url") or item.get("postUrl") or page_url
        time_str = item.get("time") or item.get("timestamp") or ""
        likes = item.get("likes") or 0
        comments = item.get("comments") or 0
        shares = item.get("shares") or 0
        if not text:
            continue
        results.append(
            {
                "序号": idx,
                "平台": "Facebook",
                "主页名称": page_name,
                "发布时间": str(time_str),
                "点赞数": likes,
                "评论数": comments,
                "分享数": shares,
                "帖子内容": text,
                "帖子链接": url,
            }
        )
    return results
