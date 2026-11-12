import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.proxy_helper import get_local_proxy_url, get_requests_proxies
from src.exporter import mask_preview_text, export_deliverables
from src.scrapers.youtube_scraper import format_youtube_search_entry, format_youtube_comment_entry
from src.scrapers.reddit_scraper import format_reddit_post_entry
from src.scrapers.web_scraper import parse_generic_html_to_records


class TestOverseasScraper(unittest.TestCase):
    def test_mask_preview_text(self):
        short_str = "Great product!"
        self.assertIn("Great", mask_preview_text(short_str))

        long_str = "This is a very detailed review about the overseas product quality and shipping speed."
        masked = mask_preview_text(long_str)
        self.assertTrue(masked.endswith("...[验货预览，完整版无遮挡]"))
        self.assertLess(len(masked), len(long_str) + 25)

    def test_export_deliverables_creates_three_files(self):
        sample_records = [
            {
                "序号": i,
                "作者": f"user_{i}",
                "点赞数": i * 10,
                "评论内容": f"This is sample comment number {i} for overseas data scraping test.",
                "发布时间": "2026-11-12",
            }
            for i in range(1, 36)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_deliverables(
                records=sample_records,
                task_name="YouTube_Test",
                output_dir=tmpdir,
                preview_limit=20,
            )
            self.assertTrue(os.path.exists(paths["preview_xlsx"]))
            self.assertTrue(os.path.exists(paths["full_xlsx"]))
            self.assertTrue(os.path.exists(paths["full_csv"]))
            self.assertIn("验货预览-前20条", os.path.basename(paths["preview_xlsx"]))
            self.assertIn("完整交付-共35条", os.path.basename(paths["full_xlsx"]))

    def test_proxy_detection_returns_valid_scheme(self):
        proxy_url = get_local_proxy_url()
        self.assertTrue(
            proxy_url.startswith("http://127.0.0.1:") or proxy_url.startswith("socks5h://127.0.0.1:")
        )
        proxies = get_requests_proxies()
        self.assertIn("http", proxies)
        self.assertIn("https", proxies)

    def test_scraper_formatters_and_html_parser(self):
        yt_item = format_youtube_search_entry(
            idx=1,
            entry={
                "id": "abc123xyz",
                "title": "AI Agent Tutorial 2026",
                "uploader": "TechChannel",
                "view_count": 125000,
                "duration": 620,
                "url": "https://www.youtube.com/watch?v=abc123xyz",
            },
        )
        self.assertEqual(yt_item["视频标题"], "AI Agent Tutorial 2026")
        self.assertEqual(yt_item["播放量"], 125000)

        yt_comment = format_youtube_comment_entry(
            idx=1,
            video_title="Demo Video",
            comment={
                "author": "@alice",
                "text": "Super helpful breakdown!",
                "like_count": 42,
                "timestamp": 1760000000,
            },
        )
        self.assertEqual(yt_comment["评论作者"], "@alice")
        self.assertEqual(yt_comment["点赞数"], 42)

        reddit_post = format_reddit_post_entry(
            idx=1,
            post={
                "title": "Best wireless headphones in 2026?",
                "subreddit": "headphones",
                "author": "audiophile99",
                "score": 310,
                "num_comments": 88,
                "selftext": "Looking for recommendations under $300...",
                "permalink": "/r/headphones/comments/xyz/best_wireless/",
                "created_utc": 1760000000,
            },
        )
        self.assertEqual(reddit_post["所属板块"], "r/headphones")
        self.assertEqual(reddit_post["点赞得分"], 310)

        html = """
        <html><body>
            <table>
                <tr><th>Product</th><th>Price</th></tr>
                <tr><td>Starter Plan</td><td>$19</td></tr>
                <tr><td>Pro Plan</td><td>$49</td></tr>
            </table>
        </body></html>
        """
        rows = parse_generic_html_to_records(html, base_url="https://example.com")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Product"], "Starter Plan")
        self.assertEqual(rows[1]["Price"], "$49")


if __name__ == "__main__":
    unittest.main()
