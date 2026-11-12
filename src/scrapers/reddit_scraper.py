from datetime import datetime
import re
import requests
from src.proxy_helper import get_requests_proxies


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def format_reddit_post_entry(idx: int, post: dict) -> dict:
    created = post.get("created_utc") or post.get("created") or 0
    time_str = (
        datetime.fromtimestamp(float(created)).strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(created, (int, float)) and created > 0
        else str(created or "")
    )
    subreddit = str(post.get("subreddit") or "").lstrip("r/").strip("/")
    permalink = str(post.get("permalink") or post.get("url") or "")
    if permalink.startswith("/"):
        permalink = f"https://www.reddit.com{permalink}"
    body = (post.get("selftext") or "").replace("\r\n", " ").replace("\n", " ").strip()
    return {
        "序号": idx,
        "所属板块": f"r/{subreddit}" if subreddit else "r/all",
        "帖子标题": (post.get("title") or "").strip(),
        "作者": post.get("author") or "unknown",
        "点赞得分": post.get("score") if post.get("score") is not None else 0,
        "评论数量": post.get("num_comments") if post.get("num_comments") is not None else 0,
        "发布时间": time_str,
        "正文内容": body[:500] if body else "(纯链接/图片帖)",
        "帖子链接": permalink,
    }


def _resolve_subreddit_and_keywords(query: str, proxies: dict) -> tuple[str, list[str]]:
    clean = query.strip()
    if clean.lower().startswith("r/"):
        parts = clean[2:].split(None, 1)
        sub = parts[0].strip("/")
        kws = parts[1].lower().split() if len(parts) > 1 else []
        return sub, kws

    tokens = [re.sub(r"[^a-zA-Z0-9_]", "", t) for t in clean.split()]
    tokens = [t for t in tokens if t]
    prefix = tokens[0].lower() if tokens else "technology"

    try:
        resp = requests.get(
            "https://arctic-shift.photon-reddit.com/api/subreddits/search",
            params={"subreddit_prefix": prefix, "limit": 5},
            headers={"User-Agent": USER_AGENT},
            proxies=proxies,
            timeout=10,
        )
        if resp.status_code == 200:
            subs = (resp.json() or {}).get("data") or []
            if subs:
                chosen = subs[0].get("display_name") or prefix
                extra_kws = [t.lower() for t in tokens[1:]]
                return chosen, extra_kws
    except Exception:
        pass

    return prefix, [t.lower() for t in tokens[1:]]


def _scrape_via_arctic_shift(query: str, limit: int, proxies: dict) -> list[dict]:
    subreddit, extra_kws = _resolve_subreddit_and_keywords(query, proxies)
    fetch_size = min(max(limit * 3, 60), 100)
    resp = requests.get(
        "https://arctic-shift.photon-reddit.com/api/posts/search",
        params={"subreddit": subreddit, "limit": fetch_size, "sort": "desc"},
        headers={"User-Agent": USER_AGENT},
        proxies=proxies,
        timeout=15,
    )
    resp.raise_for_status()
    posts = (resp.json() or {}).get("data") or []
    if extra_kws:
        matched = [
            p
            for p in posts
            if any(
                kw in (str(p.get("title") or "") + " " + str(p.get("selftext") or "")).lower()
                for kw in extra_kws
            )
        ]
        if len(matched) >= min(5, limit):
            posts = matched + [p for p in posts if p not in matched]
    return [format_reddit_post_entry(idx, p) for idx, p in enumerate(posts[:limit], start=1)]


def scrape_reddit_search(query: str, limit: int = 35) -> list[dict]:
    proxies = get_requests_proxies()
    headers = {
        "User-Agent": "android:com.overseas.research.toolkit:v1.2 (by /u/data_analyst_bot)",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(
            "https://www.reddit.com/search.json",
            params={"q": query, "limit": min(limit, 100), "sort": "relevance", "t": "year"},
            headers=headers,
            proxies=proxies,
            timeout=10,
        )
        if resp.status_code == 200:
            children = ((resp.json() or {}).get("data") or {}).get("children") or []
            if children:
                return [
                    format_reddit_post_entry(idx, child.get("data") or {})
                    for idx, child in enumerate(children[:limit], start=1)
                ]
    except Exception:
        pass

    return _scrape_via_arctic_shift(query, limit, proxies)
