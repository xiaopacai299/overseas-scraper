from datetime import datetime
import yt_dlp
from src.proxy_helper import get_local_proxy_url


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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    video_title = (info or {}).get("title") or video_url
    comments = (info or {}).get("comments") or []
    results = []
    for idx, c in enumerate(comments[:limit], start=1):
        results.append(format_youtube_comment_entry(idx, video_title, c))
    return results
