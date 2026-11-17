from datetime import datetime
import json
import re
import requests
import yt_dlp
from src.proxy_helper import get_local_proxy_url, get_requests_proxies


def _get_ytdlp_proxy() -> str:
    proxy = get_local_proxy_url()
    return proxy.replace("socks5h://", "socks5://")


def format_youtube_search_entry(idx: int, entry: dict) -> dict:
    vid = entry.get("id") or ""
    url = entry.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
    if url and not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={vid}"
    duration_sec = entry.get("duration") or 0
    return {
        "序号": idx,
        "视频标题": entry.get("title") or "",
        "频道名称": entry.get("uploader") or entry.get("channel") or "",
        "播放量": entry.get("view_count") if entry.get("view_count") is not None else "未知",
        "时长(秒)": duration_sec,
        "视频ID": vid,
        "视频链接": url,
    }


def format_youtube_comment_entry(idx: int, video_title: str, comment: dict) -> dict:
    ts = comment.get("timestamp")
    time_str = (
        datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(ts, (int, float)) and ts > 0
        else str(comment.get("time_text") or "")
    )
    return {
        "序号": idx,
        "所属视频": video_title,
        "评论作者": comment.get("author") or "匿名用户",
        "点赞数": comment.get("like_count") or 0,
        "是否置顶": "是" if comment.get("is_pinned") else "否",
        "发布时间": time_str,
        "评论内容": (comment.get("text") or "").replace("\r\n", " ").replace("\n", " ").strip(),
    }


def scrape_youtube_search(query: str, limit: int = 30) -> list[dict]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "proxy": _get_ytdlp_proxy(),
    }
    search_spec = f"ytsearch{limit}:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_spec, download=False)
    entries = (info or {}).get("entries") or []
    results = []
    for idx, entry in enumerate(entries[:limit], start=1):
        if entry:
            results.append(format_youtube_search_entry(idx, entry))
    return results


def _scrape_youtube_comments_innertube(video_url: str, limit: int = 50) -> list[dict]:
    proxies = get_requests_proxies()
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    html = sess.get(video_url, proxies=proxies, timeout=15).text
    m_title = re.search(r"<title>(.*?)</title>", html)
    video_title = (m_title.group(1).replace(" - YouTube", "") if m_title else video_url).strip()
    m_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    if not m_key:
        return []
    api_key = m_key.group(1)
    tokens = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', html)
    ctx = {"client": {"clientName": "WEB", "clientVersion": "2.20241111.01.00"}}

    payload_items = []
    for tok in tokens[:3]:
        r1 = sess.post(
            f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
            json={"context": ctx, "continuation": tok},
            proxies=proxies,
            timeout=15,
        )
        sub_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', r1.text)
        next_tok = sub_toks[0] if sub_toks else None
        page_text = r1.text
        for _ in range(4):
            if '"commentEntityPayload"' not in page_text and next_tok:
                r2 = sess.post(
                    f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
                    json={"context": ctx, "continuation": next_tok},
                    proxies=proxies,
                    timeout=15,
                )
                page_text = r2.text
                more_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', page_text)
                next_tok = more_toks[-1] if more_toks else None
            if '"commentEntityPayload"' in page_text:
                data = json.loads(page_text)
                mutations = (
                    data.get("frameworkUpdates", {})
                    .get("entityBatchUpdate", {})
                    .get("mutations", [])
                )
                for mut in mutations:
                    ce = mut.get("payload", {}).get("commentEntityPayload")
                    if ce:
                        payload_items.append(ce)
                if len(payload_items) >= limit or not next_tok:
                    break
                r_next = sess.post(
                    f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
                    json={"context": ctx, "continuation": next_tok},
                    proxies=proxies,
                    timeout=15,
                )
                page_text = r_next.text
                more_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', page_text)
                next_tok = more_toks[-1] if more_toks else None
        if payload_items:
            break

    results = []
    for idx, ce in enumerate(payload_items[:limit], start=1):
        props = ce.get("properties", {})
        text = (props.get("content", {}).get("content") or "").replace("\r\n", " ").replace("\n", " ").strip()
        author = ce.get("author", {}).get("displayName") or "匿名用户"
        likes = ce.get("toolbar", {}).get("likeCountNotliked") or ce.get("toolbar", {}).get("likeCountLiked") or 0
        time_text = props.get("publishedTime") or ""
        results.append(
            {
                "序号": idx,
                "所属视频": video_title,
                "评论作者": author,
                "点赞数": likes,
                "是否置顶": "否",
                "发布时间": time_text,
                "评论内容": text,
            }
        )
    return results


def scrape_youtube_comments(video_url: str, limit: int = 50) -> list[dict]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "getcomments": True,
        "proxy": _get_ytdlp_proxy(),
        "extractor_args": {
            "youtube": {
                "max_comments": [str(limit), str(limit), str(limit), "5"],
                "comment_sort": ["top"],
            }
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = (info or {}).get("title") or video_url
        comments = (info or {}).get("comments") or []
        if comments:
            return [
                format_youtube_comment_entry(idx, video_title, c)
                for idx, c in enumerate(comments[:limit], start=1)
            ]
    except Exception:
        pass
    return _scrape_youtube_comments_innertube(video_url, limit=limit)
