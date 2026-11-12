import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.exporter import export_deliverables
from src.proxy_helper import get_local_proxy_url
from src.scrapers.reddit_scraper import scrape_reddit_search
from src.scrapers.web_scraper import scrape_generic_webpage, scrape_hackernews_top
from src.scrapers.youtube_scraper import scrape_youtube_comments, scrape_youtube_search


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Overseas Scraper - 海外数据采集与双版本 Excel（验货预览 + 完整交付）一键导出工具"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_yt_s = sub.add_parser("youtube-search", help="按关键词批量采集 YouTube 视频列表与播放数据")
    p_yt_s.add_argument("--query", "-q", required=True, help="搜索关键词，例如 'AI agent tutorial'")
    p_yt_s.add_argument("--limit", "-n", type=int, default=30, help="采集条数（默认 30）")

    p_yt_c = sub.add_parser("youtube-comments", help="按视频链接批量采集 YouTube 视频高赞评论")
    p_yt_c.add_argument("--url", "-u", required=True, help="YouTube 视频完整 URL")
    p_yt_c.add_argument("--limit", "-n", type=int, default=40, help="采集评论条数（默认 40）")

    p_rd = sub.add_parser("reddit", help="按关键词批量采集 Reddit 海外社区帖子与舆情数据")
    p_rd.add_argument("--query", "-q", required=True, help="搜索关键词，例如 'ChatGPT Plus'")
    p_rd.add_argument("--limit", "-n", type=int, default=35, help="采集条数（默认 35）")

    p_hn = sub.add_parser("hn", help="采集 HackerNews 海外科技热榜或指定关键词讨论")
    p_hn.add_argument("--query", "-q", default="", help="可选关键词（留空则抓首页热榜）")
    p_hn.add_argument("--limit", "-n", type=int, default=35, help="采集条数（默认 35）")

    p_web = sub.add_parser("web", help="采集任意公开海外网页表格或结构化链接列表")
    p_web.add_argument("--url", "-u", required=True, help="目标网页 URL")
    p_web.add_argument("--limit", "-n", type=int, default=80, help="最大提取行数（默认 80）")

    args = parser.parse_args()
    proxy_url = get_local_proxy_url()
    print(f"[Proxy] 当前使用本地代理通道: {proxy_url}")

    if args.command == "youtube-search":
        print(f"[Task] 正在从 YouTube 搜索关键词: {args.query} (目标 {args.limit} 条)...")
        records = scrape_youtube_search(args.query, limit=args.limit)
        task_name = f"YouTube视频搜索_{args.query}"
    elif args.command == "youtube-comments":
        print(f"[Task] 正在采集 YouTube 视频评论: {args.url} (目标 {args.limit} 条)...")
        records = scrape_youtube_comments(args.url, limit=args.limit)
        task_name = "YouTube视频评论采集"
    elif args.command == "reddit":
        print(f"[Task] 正在采集 Reddit 海外舆情: {args.query} (目标 {args.limit} 条)...")
        records = scrape_reddit_search(args.query, limit=args.limit)
        task_name = f"Reddit舆情采集_{args.query}"
    elif args.command == "hn":
        label = args.query if args.query else "首页热榜"
        print(f"[Task] 正在采集 HackerNews 科技讨论: {label} (目标 {args.limit} 条)...")
        records = scrape_hackernews_top(query=args.query, limit=args.limit)
        task_name = f"HackerNews_{label}"
    elif args.command == "web":
        print(f"[Task] 正在提取海外网页结构化数据: {args.url} ...")
        records = scrape_generic_webpage(args.url, limit=args.limit)
        task_name = "海外网页提取"
    else:
        parser.print_help()
        return 1

    if not records:
        print("[Warn] 未采集到匹配记录，请检查关键词或目标链接。")
        return 2

    paths = export_deliverables(records=records, task_name=task_name)
    print(f"\n[OK] 采集完成！共获取 {len(records)} 条真实数据，已自动生成客户交付三件套：")
    print(f"  1. [发给客户截图验货] : {paths['preview_xlsx']}")
    print(f"  2. [收款后发完整Excel]: {paths['full_xlsx']}")
    print(f"  3. [收款后发完整CSV]  : {paths['full_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
