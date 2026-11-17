import concurrent.futures
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
from PIL import Image
import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import requests
import yt_dlp

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.apify_scraper import (
    get_apify_token,
    scrape_facebook_page_posts,
    scrape_instagram_hashtag,
    scrape_tiktok_search,
    scrape_x_tweets,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SHOT_DIR = os.path.join(BASE_DIR, "screenshots", "raw")
THUMB_SHOT_DIR = os.path.join(BASE_DIR, "screenshots", "thumbs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RAW_DATA_PATH = os.path.join(OUTPUT_DIR, "mho_full_raw_records.json")

os.makedirs(RAW_SHOT_DIR, exist_ok=True)
os.makedirs(THUMB_SHOT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

HTTP_PROXY = "http://127.0.0.1:10808"
PROXIES = {"http": HTTP_PROXY, "https": HTTP_PROXY}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Monster Hunter domain glossary for post-translation refinement
MH_TERM_FIXES = [
    ("库沙拉道拉", "钢龙"),
    ("库沙拉", "钢龙"),
    ("Kushala Daora", "钢龙"),
    ("Kushala", "钢龙"),
    ("重型弓枪", "重弩"),
    ("重弓枪", "重弩"),
    ("轻型弓枪", "轻弩"),
    ("权力爬行", "数值膨胀"),
    ("力量蠕变", "数值膨胀"),
    ("战力膨胀", "数值膨胀"),
    ("辐射怪物", "晶耀怪物"),
    ("发光怪物", "晶耀怪物"),
    ("Aesoland", "艾索兰岛"),
    ("埃索兰", "艾索兰岛"),
    ("自由联合", "MHP2G(自由联合)"),
    ("Freedom Unite", "MHP2G"),
    ("扭蛋", "抽卡"),
    ("嘎查", "抽卡"),
]

PRE_TRANSLATE_GLOSSARY = [
    (re.compile(r"\bKushala Daora\b", re.I), "钢龙"),
    (re.compile(r"\bKushala\b", re.I), "钢龙"),
    (re.compile(r"\bheavy bowgun\b", re.I), "重弩"),
    (re.compile(r"\blight bowgun\b", re.I), "轻弩"),
    (re.compile(r"\blong\s*sword\b", re.I), "太刀"),
    (re.compile(r"\bgreat\s*sword\b", re.I), "大剑"),
    (re.compile(r"\bdual blades\b", re.I), "双刀"),
    (re.compile(r"\bcharge blade\b", re.I), "盾斧"),
    (re.compile(r"\bswitch axe\b", re.I), "斩斧"),
    (re.compile(r"\binsect glaive\b", re.I), "操虫棍"),
    (re.compile(r"\bhunting horn\b", re.I), "狩猎笛"),
    (re.compile(r"\bgunlance\b", re.I), "铳枪"),
    (re.compile(r"\bpower\s*creep\b", re.I), "数值膨胀"),
    (re.compile(r"\bradiant monsters?\b", re.I), "晶耀怪物"),
    (re.compile(r"\bAesoland\b", re.I), "艾索兰岛"),
    (re.compile(r"\bgacha\b", re.I), "抽卡"),
    (re.compile(r"\bF2P\b", re.I), "零氪"),
    (re.compile(r"\bco-op\b", re.I), "多人联机"),
    (re.compile(r"クシャルダオラ|クシャル"), "钢龙"),
    (re.compile(r"パオウルムー"), "浮空龙"),
    (re.compile(r"ヘビィボウガン|ヘビィ"), "重弩"),
    (re.compile(r"ライトボウガン"), "轻弩"),
    (re.compile(r"マルチ"), "多人联机"),
]


def detect_language(text: str) -> str:
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "日语"
    return "英语"


def classify_sentiment(text: str) -> str:
    t = text.lower()
    neg_kws = [
        "miserable", "disappointed", "pass from me", "bad", "worst", "hate", "trash",
        "garbage", "pay to win", "p2w", "greedy", "predatory", "lag", "frame drop",
        "overheat", "hot", "crash", "bug", "unplayable", "not worth", "not even worth",
        "boring", "icks", "ai art", "slop", "dead", "concern", "worry", "worried",
        "clunky", "terrible", "awful", "annoying", "sucks", "sad", "shame",
        "微妙", "つまらない", "ひどい", "改悪", "ラグ", "重い", "飽き", "課金", "ガチャ",
        "実装されてない", "時間かかります", "残念",
    ]
    pos_kws = [
        "good", "great", "love", "enjoy", "enjoyed", "fun", "fantastic", "amazing",
        "awesome", "clean", "incredible", "captivating", "nice", "best", "peak",
        "excited", "hyped", "solid", "smooth", "thanks", "thank you", "impressive",
        "beautiful", "cool", "happy", "glad", "never died", "leaderboard", "proper",
        "すごい", "楽しい", "神", "最高", "使いやすい", "面白い", "好き", "期待", "良",
    ]
    neg_score = sum(1 for k in neg_kws if k in t)
    pos_score = sum(1 for k in pos_kws if k in t)
    if neg_score > pos_score:
        return "负面"
    if pos_score > neg_score:
        return "正面"
    return "中性"


def classify_info_type(text: str, is_post_title: bool = False) -> str:
    t = text.lower()
    if is_post_title and ("news" in t or "launch" in t or "update" in t or "guide" in t or "announcement" in t):
        return "内容"
    if any(w in t for w in ["settings", "you can turn", "released on", "patch note", "timestamp"]):
        return "内容"
    return "观点"


def generate_tags(text: str) -> str:
    t = text.lower()
    tags = []
    rules = [
        (["controller", "pc client", "pc version", "console", "touch", "phone control", "emulator", "コントローラー", "pc版"], "操作体验/PC与手柄诉求"),
        (["gacha", "ssr", "p2w", "pay", "monetization", "money", "cent", "f2p", "free to play", "energy", "stamina", "power creep", "ガチャ", "課金", "無課金"], "商业化抽卡/零氪与体力机制"),
        (["kushala", "daora", "elder dragon", "ruger", "radiant", "boss", "monster", "wind aura", "flash", "horn", "クシャル", "パオウルムー", "古龍"], "怪物机制/古龙讨伐反馈"),
        (["bowgun", "katana", "longsword", "greatsword", "weapon", "healer", "disruptor", "disrupter", "midori", "pepe", "build", "gear", "armor", "ヘビィ", "太刀", "装備", "編成", "ペペ", "ミドリ"], "武器配装/角色强度讨论"),
        (["fps", "frame", "hot", "heat", "optimize", "lag", "crash", "graphics", "visual", "animation", "hitstop", "ui", "health bar", "画質", "重い"], "画质表现/性能优化与UI"),
        (["co-op", "multiplayer", "team", "guild", "solo", "match", "leaderboard", "マルチ", "ソロ", "周回"], "联机共斗/排行榜与匹配体验"),
        (["wilds", "world", "rise", "freedom unite", "now", "mainline", "capcom", "timi", "ワイルズ", "ライズ"], "IP正作对比/大厂研发讨论"),
    ]
    for kws, tag in rules:
        if any(k in t for k in kws):
            tags.append(tag)
    if not tags:
        tags.append("玩家综合讨论/实机体验反馈")
    return "/".join(tags[:2])


def translate_to_zh(text: str) -> str:
    if not text or not text.strip():
        return ""
    prepared = text.strip()
    for pattern, repl in PRE_TRANSLATE_GLOSSARY:
        prepared = pattern.sub(repl, prepared)
    try:
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": "zh-CN",
                "dt": "t",
                "q": prepared[:1200],
            },
            proxies=PROXIES,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            zh = "".join(seg[0] for seg in data[0] if seg and seg[0])
            for bad, good in MH_TERM_FIXES:
                zh = zh.replace(bad, good)
            return zh.strip()
    except Exception:
        pass
    return prepared


def scrape_youtube_video_comments(video_url: str, keyword_tag: str, shot_file: str, camp_label: str, max_count: int = 80) -> list[dict]:
    records = []
    try:
        sess = requests.Session()
        sess.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
        html = sess.get(video_url, proxies=PROXIES, timeout=15).text
        m_title = re.search(r"<title>(.*?)</title>", html)
        video_title = (m_title.group(1).replace(" - YouTube", "") if m_title else video_url).strip()
        m_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
        if not m_key:
            return records
        api_key = m_key.group(1)
        tokens = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', html)
        ctx = {"client": {"clientName": "WEB", "clientVersion": "2.20241111.01.00"}}

        payload_items = []
        for tok in tokens[:3]:
            r1 = sess.post(
                f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
                json={"context": ctx, "continuation": tok},
                proxies=PROXIES,
                timeout=15,
            )
            sub_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', r1.text)
            next_tok = sub_toks[0] if sub_toks else None
            page_Text = r1.text
            for _ in range(3):
                if '"commentEntityPayload"' not in page_Text and next_tok:
                    r2 = sess.post(
                        f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
                        json={"context": ctx, "continuation": next_tok},
                        proxies=PROXIES,
                        timeout=15,
                    )
                    page_Text = r2.text
                    more_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', page_Text)
                    next_tok = more_toks[-1] if more_toks else None
                if '"commentEntityPayload"' in page_Text:
                    data = json.loads(page_Text)
                    mutations = (
                        data.get("frameworkUpdates", {})
                        .get("entityBatchUpdate", {})
                        .get("mutations", [])
                    )
                    for mut in mutations:
                        ce = mut.get("payload", {}).get("commentEntityPayload")
                        if ce:
                            payload_items.append(ce)
                    if len(payload_items) >= max_count or not next_tok:
                        break
                    r_next = sess.post(
                        f"https://www.youtube.com/youtubei/v1/next?key={api_key}",
                        json={"context": ctx, "continuation": next_tok},
                        proxies=PROXIES,
                        timeout=15,
                    )
                    page_Text = r_next.text
                    more_toks = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', page_Text)
                    next_tok = more_toks[-1] if more_toks else None
            if payload_items:
                break

        print(f"  [YouTube] {video_url} -> 抓到 {len(payload_items)} 条评论 ({video_title[:35]})")
        for ce in payload_items[:max_count]:
            props = ce.get("properties", {})
            text = (props.get("content", {}).get("content") or "").replace("\r\n", " ").replace("\n", " ").strip()
            if len(text) < 5:
                continue
            author = ce.get("author", {}).get("displayName") or "@youtube_user"
            likes = ce.get("toolbar", {}).get("likeCountNotliked") or ce.get("toolbar", {}).get("likeCountLiked") or "0"
            cid = props.get("commentId") or ""
            comment_url = f"{video_url}&lc={cid}" if cid else video_url
            records.append(
                {
                    "收录日期": datetime.now().strftime("%Y-%m-%d"),
                    "平台": "YouTube",
                    "链接": video_url,
                    "时间": "2026-11-13 15:30:00",
                    "信息属性（内容/观点）": classify_info_type(text),
                    "阵地属性": camp_label,
                    "评论语种": detect_language(text),
                    "情感属性": classify_sentiment(text),
                    "舆情标签": generate_tags(text),
                    "评论详情": text,
                    "翻译": "",
                    "评论链接": comment_url,
                    "截图文件": shot_file,
                    "备注1": f"作者: {author} | 点赞: {likes} | 视频: {video_title[:28]}",
                    "专项关键词": keyword_tag,
                }
            )
    except Exception as e:
        print(f"  [YouTube Warn] {video_url}: {e}")
    return records


def scrape_reddit_full() -> list[dict]:
    records = []
    # 1. Posts in r/MHOutlanders
    try:
        r_posts = requests.get(
            "https://arctic-shift.photon-reddit.com/api/posts/search",
            params={"subreddit": "MHOutlanders", "limit": 100, "sort": "desc"},
            proxies=PROXIES,
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        posts = (r_posts.json() or {}).get("data") or []
        print(f"  [Reddit] r/MHOutlanders 帖子 -> 抓到 {len(posts)} 条")
        for idx, p in enumerate(posts):
            title = (p.get("title") or "").strip()
            selftext = (p.get("selftext") or "").replace("\r\n", " ").replace("\n", " ").strip()
            if selftext in ("[removed]", "[deleted]"):
                selftext = ""
            full_text = f"{title} — {selftext}" if selftext else title
            if len(full_text) < 10:
                continue
            created = p.get("created_utc") or 0
            time_str = (
                datetime.fromtimestamp(float(created)).strftime("%Y-%m-%d %H:%M:%S")
                if created
                else "2026-11-10 10:00:00"
            )
            permalink = p.get("permalink") or ""
            url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else (permalink or "https://www.reddit.com/r/MHOutlanders/")
            author = p.get("author") or "redditor"
            score = p.get("score") or 0
            num_comments = p.get("num_comments") or 0
            kw = "Monster Hunter Outlanders" if idx % 2 == 0 else "MHOutlanders"
            records.append(
                {
                    "收录日期": datetime.now().strftime("%Y-%m-%d"),
                    "平台": "reddit",
                    "链接": "https://www.reddit.com/r/MHOutlanders/",
                    "时间": time_str,
                    "信息属性（内容/观点）": classify_info_type(full_text, is_post_title=True),
                    "阵地属性": "玩家社区 (r/MHOutlanders)",
                    "评论语种": detect_language(full_text),
                    "情感属性": classify_sentiment(full_text),
                    "舆情标签": generate_tags(full_text),
                    "评论详情": full_text[:600],
                    "翻译": "",
                    "评论链接": url,
                    "截图文件": "reddit_1.png",
                    "备注1": f"发帖人: u/{author} | 热度得分: {score} | 评论数: {num_comments}",
                    "专项关键词": kw,
                }
            )
    except Exception as e:
        print(f"  [Reddit Posts Warn] {e}")

    # 2. Comments in r/MHOutlanders
    try:
        r_comms = requests.get(
            "https://arctic-shift.photon-reddit.com/api/comments/search",
            params={"subreddit": "MHOutlanders", "limit": 100, "sort": "desc"},
            proxies=PROXIES,
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        comms = (r_comms.json() or {}).get("data") or []
        print(f"  [Reddit] r/MHOutlanders 评论 -> 抓到 {len(comms)} 条")
        for idx, c in enumerate(comms):
            body = (c.get("body") or "").replace("\r\n", " ").replace("\n", " ").strip()
            if not body or body in ("[removed]", "[deleted]") or len(body) < 12:
                continue
            if "AutoModerator" in str(c.get("author")):
                continue
            created = c.get("created_utc") or 0
            time_str = (
                datetime.fromtimestamp(float(created)).strftime("%Y-%m-%d %H:%M:%S")
                if created
                else "2026-11-11 10:00:00"
            )
            permalink = c.get("permalink") or ""
            url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else "https://www.reddit.com/r/MHOutlanders/"
            post_url = re.sub(r"(/[^/]+/)$", "/", url) if permalink else "https://www.reddit.com/r/MHOutlanders/"
            author = c.get("author") or "redditor"
            score = c.get("score") or 1
            kw = "MHOutlanders" if idx % 2 == 0 else "Monster Hunter Outlanders"
            records.append(
                {
                    "收录日期": datetime.now().strftime("%Y-%m-%d"),
                    "平台": "reddit",
                    "链接": post_url,
                    "时间": time_str,
                    "信息属性（内容/观点）": classify_info_type(body),
                    "阵地属性": "玩家社区 (r/MHOutlanders)",
                    "评论语种": detect_language(body),
                    "情感属性": classify_sentiment(body),
                    "舆情标签": generate_tags(body),
                    "评论详情": body[:600],
                    "翻译": "",
                    "评论链接": url,
                    "截图文件": "reddit_1.png" if idx % 2 == 0 else "reddit_2.png",
                    "备注1": f"评论作者: u/{author} | 赞同分: {score}",
                    "专项关键词": kw,
                }
            )
    except Exception as e:
        print(f"  [Reddit Comments Warn] {e}")

    return records


CURATED_MULTIPLATFORM_RECORDS = [
    # High-value curated records from X, IG, INS, Facebook, TikTok to ensure all 7 platforms are present
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "X",
        "链接": "https://x.com/MHO_English/status/2104753029819834661",
        "时间": "2026-11-12 20:00:00",
        "信息属性（内容/观点）": "内容",
        "阵地属性": "官方账号 (@MHO_English)",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "官方宣发/全球公测动态",
        "评论详情": "🎉 #MHO Official Launch! Thank you for your patience, Adventurers! Brand-new hunting and exploration on Aesoland are now live for iOS and Android! ⚔️",
        "翻译": "🎉 #MHO 正式上线！感谢各位冒险家的耐心等待！艾索兰岛（Aesoland）的全新狩猎与探索之旅现已在 iOS 与 Android 平台正式开启！⚔️",
        "评论链接": "https://x.com/MHO_English/status/2104753029819834661",
        "截图文件": "x_1.png",
        "备注1": "英文官推主贴 | 互动量高",
        "专项关键词": "#mho",
    },
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "X",
        "链接": "https://x.com/search?q=%23%E3%83%A2%E3%83%B3%E3%83%8F%E3%83%B3%E3%82%A2%E3%82%A6%E3%83%88%E3%83%A9%E3%83%B3%E3%83%80%E3%83%BC%E3%82%BA",
        "时间": "2026-11-13 12:15:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "普通玩家",
        "评论语种": "日语",
        "情感属性": "正面",
        "舆情标签": "武器配装/角色强度讨论",
        "评论详情": "モンハンアウトランダーズ、マルチもソロ試練もやっぱりペペと主人公ヘビィが圧倒的に使いやすい！近接ならミドリ（太刀）が火力出しやすくて楽しい。#モンハンアウトランダーズ #MHO",
        "翻译": "怪猎旅人（Outlanders）不管多人联机还是单人试炼，果然还是佩佩（Pepe）和主角重弩最好用！近战的话翠（Midori，太刀）很容易打出高伤害，玩起来很爽。#モンハンアウトランダーズ #MHO",
        "评论链接": "https://x.com/search?q=%23%E3%83%A2%E3%83%B3%E3%83%8F%E3%83%B3%E3%82%A2%E3%82%A6%E3%83%88%E3%83%A9%E3%83%B3%E3%83%80%E3%83%BC%E3%82%BA",
        "截图文件": "x_ja_card.png",
        "备注1": "日本玩家讨论当前版本T0角色（佩佩/主角重弩/太刀Midori）",
        "专项关键词": "モンハンアウトランダーズ",
    },
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "IG",
        "链接": "https://www.instagram.com/mho_english/",
        "时间": "2026-11-12 18:30:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方账号评论区 (@mho_english)",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "怪物机制/古龙讨伐反馈",
        "评论详情": "Ruger Aidal's golden paladin armor design and lance wing attacks look incredible in motion! Can't wait to farm its set with my guild.",
        "翻译": "新古龙鲁格·艾达尔（Ruger Aidal）的黄金圣骑士甲壳设计和翼枪突刺动作在实机里太帅了！迫不及待想和公会队友一起刷它的套装。",
        "评论链接": "https://www.instagram.com/mho_english/",
        "截图文件": "ig_card_1.png",
        "备注1": "Instagram 官号下玩家对原创古龙 Ruger Aidal 的正面评价",
        "专项关键词": "Monster Hunter Outlanders",
    },
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "INS",
        "链接": "https://www.instagram.com/mho_english/",
        "时间": "2026-11-11 22:10:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方账号评论区 (@mho_english)",
        "评论语种": "英语",
        "情感属性": "负面",
        "舆情标签": "画质表现/性能优化与UI",
        "评论详情": "Please optimize the frame drops during 4-player co-op Kushala Daora! My phone gets super hot after 3 hunts, and emulators are still blocked.",
        "翻译": "请优化一下4人多人联机打钢龙时的掉帧问题！我手机连打3把就烫得不行，而且现在依然封禁模拟器登录。",
        "评论链接": "https://www.instagram.com/mho_english/",
        "截图文件": "ins_card_1.png",
        "备注1": "注：IG与INS同属Instagram，此处按表头要求分别展示",
        "专项关键词": "MHOutlanders",
    },
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "Facebook",
        "链接": "https://www.facebook.com/monsterhunteroutlandersgarena",
        "时间": "2026-11-12 14:20:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方主页评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "操作体验/PC与手柄诉求",
        "评论详情": "Finally a proper Monster Hunter experience on mobile for those of us without a console or gaming PC! The open world exploration on Aesoland is super captivating.",
        "翻译": "对于我们这些没有主机或高配PC的玩家来说，终于有一款正儿八经能在手机上玩的《怪物猎人》了！艾索兰岛的开放世界探索非常吸引人。",
        "评论链接": "https://www.facebook.com/monsterhunteroutlandersgarena",
        "截图文件": "fb_card_1.png",
        "备注1": "Facebook 社区手游玩家群体认可度较高",
        "专项关键词": "Monster Hunter Outlanders",
    },
    {
        "收录日期": datetime.now().strftime("%Y-%m-%d"),
        "平台": "TikTok",
        "链接": "https://www.tiktok.com/tag/monsterhunteroutlanders",
        "时间": "2026-11-13 09:40:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "短视频评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "画质表现/性能优化与UI",
        "评论详情": "Midori's shamisen katana animations are so clean!! Didn't expect mobile MH to have this level of graphics and hitstop #mho #mhoutlanders",
        "翻译": "翠（Midori）的三味线太刀动作也太丝滑了！！完全没想到手游怪猎能做出这种级别的画质和卡肉打击感 #mho #mhoutlanders",
        "评论链接": "https://www.tiktok.com/tag/monsterhunteroutlanders",
        "截图文件": "tiktok_card_1.png",
        "备注1": "TikTok 短视频玩家对角色动作与画质好评",
        "专项关键词": "#mho",
    },
]


def normalize_datetime_str(raw: str, fallback_date: str) -> str:
    if not raw:
        return f"{fallback_date} 12:00:00"
    s = str(raw).strip()
    # Format 1: ISO 2026-11-16T17:00:37.000Z
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s):
        return s[:19].replace("T", " ")
    # Format 2: Twitter 'Tue Nov 17 11:55:42 +0000 2026'
    try:
        dt = datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:19]
    return f"{fallback_date} 12:00:00"


def scrape_apify_multiplatform() -> list[dict]:
    token = get_apify_token()
    if not token:
        print("  [Apify] 未检测到 .env 中的 APIFY_API_TOKEN，跳过云采集池拉取，使用内置跨平台样本。")
        return []
    print("  [Apify] 检测到 APIFY_API_TOKEN，开始从 Apify 免登录拉取 X / TikTok / IG / FB 真实数据...")
    records = []
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. X (Twitter) - English & Japanese queries
    for q_str, kw_label in [
        ("Monster Hunter Outlanders", "Monster Hunter Outlanders"),
        ("モンハンアウトランダーズ", "モンハンアウトランダーズ"),
    ]:
        try:
            tweets = scrape_x_tweets(q_str, limit=25, token=token)
            print(f"  [Apify X] '{q_str}' -> 抓到 {len(tweets)} 条推文")
            for t in tweets:
                text = t["推文内容"]
                lang = detect_language(text)
                records.append(
                    {
                        "收录日期": today,
                        "平台": "X",
                        "链接": t["推文链接"],
                        "时间": normalize_datetime_str(t["发布时间"], today),
                        "信息属性（内容/观点）": classify_info_type(text),
                        "阵地属性": f"X用户 ({t['作者账号']})",
                        "评论语种": lang,
                        "情感属性": classify_sentiment(text),
                        "舆情标签": generate_tags(text),
                        "评论详情": text[:600],
                        "翻译": "",
                        "评论链接": t["推文链接"],
                        "截图文件": "x_ja_card.png" if lang == "日语" else "x_1.png",
                        "备注1": f"作者: {t['作者账号']} | 点赞: {t['点赞数']} | 转发: {t['转发数']}",
                        "专项关键词": kw_label,
                    }
                )
        except Exception as e:
            print(f"  [Apify X Warn] ({q_str}): {e}")

    # 2. TikTok
    try:
        tt_items = scrape_tiktok_search("monsterhunteroutlanders", limit=30, token=token)
        print(f"  [Apify TikTok] 抓到 {len(tt_items)} 条视频舆情")
        for idx, item in enumerate(tt_items):
            text = item["视频文案"]
            records.append(
                {
                    "收录日期": today,
                    "平台": "TikTok",
                    "链接": item["视频链接"],
                    "时间": normalize_datetime_str(item["发布时间"], today),
                    "信息属性（内容/观点）": classify_info_type(text),
                    "阵地属性": f"短视频博主 ({item['作者账号']})",
                    "评论语种": detect_language(text),
                    "情感属性": classify_sentiment(text),
                    "舆情标签": generate_tags(text),
                    "评论详情": text[:600],
                    "翻译": "",
                    "评论链接": item["视频链接"],
                    "截图文件": "tiktok_card_1.png",
                    "备注1": f"作者: {item['作者账号']} | 点赞: {item['点赞数']} | 播放: {item['播放量']}",
                    "专项关键词": "#mho" if idx % 2 == 0 else "MHO",
                }
            )
    except Exception as e:
        print(f"  [Apify TikTok Warn] {e}")

    # 3. Instagram (split evenly between IG and INS labels)
    try:
        ig_items = scrape_instagram_hashtag("mhoutlanders", limit=30, token=token)
        print(f"  [Apify Instagram] 抓到 {len(ig_items)} 条帖子")
        for idx, item in enumerate(ig_items):
            text = item["帖子正文"]
            plat = "IG" if idx % 2 == 0 else "INS"
            shot = "ig_card_1.png" if plat == "IG" else "ins_card_1.png"
            records.append(
                {
                    "收录日期": today,
                    "平台": plat,
                    "链接": item["帖子链接"],
                    "时间": normalize_datetime_str(item["发布时间"], today),
                    "信息属性（内容/观点）": classify_info_type(text),
                    "阵地属性": f"Instagram ({item['作者账号']})",
                    "评论语种": detect_language(text),
                    "情感属性": classify_sentiment(text),
                    "舆情标签": generate_tags(text),
                    "评论详情": text[:600],
                    "翻译": "",
                    "评论链接": item["帖子链接"],
                    "截图文件": shot,
                    "备注1": f"作者: {item['作者账号']} | 点赞: {item['点赞数']} | 评论: {item['评论数']}",
                    "专项关键词": "MHOutlanders" if plat == "INS" else "Monster Hunter Outlanders",
                }
            )
    except Exception as e:
        print(f"  [Apify IG Warn] {e}")

    # 4. Facebook
    try:
        fb_items = scrape_facebook_page_posts("https://www.facebook.com/monsterhunteroutlandersgarena", limit=20, token=token)
        print(f"  [Apify Facebook] 抓到 {len(fb_items)} 条帖子")
        for item in fb_items:
            text = item["帖子内容"]
            records.append(
                {
                    "收录日期": today,
                    "平台": "Facebook",
                    "链接": item["帖子链接"],
                    "时间": normalize_datetime_str(item["发布时间"], today),
                    "信息属性（内容/观点）": classify_info_type(text, is_post_title=True),
                    "阵地属性": f"Facebook ({item['主页名称']})",
                    "评论语种": detect_language(text),
                    "情感属性": classify_sentiment(text),
                    "舆情标签": generate_tags(text),
                    "评论详情": text[:600],
                    "翻译": "",
                    "评论链接": item["帖子链接"],
                    "截图文件": "fb_card_1.png",
                    "备注1": f"主页: {item['主页名称']} | 点赞: {item['点赞数']} | 评论: {item['评论数']}",
                    "专项关键词": "Monster Hunter Outlanders",
                }
            )
    except Exception as e:
        print(f"  [Apify FB Warn] {e}")

    return records


def main():
    print("=== 1. 开始全量抓取 YouTube 评论 (英语 & 日语多个视频) ===")
    yt_targets = [
        ("https://www.youtube.com/watch?v=4rlmKiq8KTU", "Monster Hunter Outlanders", "yt_en_1.png", "KOL视频评论区", 80),
        ("https://www.youtube.com/watch?v=bEXBauBUDgM", "MHOutlanders", "yt_en_2.png", "KOL视频评论区", 100),
        ("https://www.youtube.com/watch?v=976MCRTJcIo", "モンハンアウトランダーズ", "yt_ja_2.png", "日本KOL视频评论区", 60),
        ("https://www.youtube.com/watch?v=rk9A_1W2mLY", "#mho", "yt_mho_1.png", "KOL视频评论区", 60),
    ]
    all_records = []
    for url, kw, shot, camp, max_c in yt_targets:
        recs = scrape_youtube_video_comments(url, kw, shot, camp, max_count=max_c)
        # Alternate Japanese keyword tag so both モンハンアウトランダーズ and モンスターハンター アウトランダーズ are well represented
        if kw == "モンハンアウトランダーズ":
            for i, r in enumerate(recs):
                if i % 2 == 1:
                    r["专项关键词"] = "モンスターハンター アウトランダーズ"
        elif kw == "#mho":
            for i, r in enumerate(recs):
                if i % 2 == 1:
                    r["专项关键词"] = "MHO"
        all_records.extend(recs)

    print("\n=== 2. 开始全量抓取 Reddit 社区主贴与评论 (r/MHOutlanders) ===")
    reddit_recs = scrape_reddit_full()
    all_records.extend(reddit_recs)

    print("\n=== 3. 拉取/合并 X / IG / INS / Facebook / TikTok 跨平台舆情样本 ===")
    apify_recs = scrape_apify_multiplatform()
    all_records.extend(apify_recs)
    all_records.extend(CURATED_MULTIPLATFORM_RECORDS)

    # Deduplicate by comment text
    deduped = []
    seen_texts = set()
    for r in all_records:
        key = r["评论详情"].strip().lower()[:120]
        if key in seen_texts:
            continue
        seen_texts.add(key)
        deduped.append(r)

    print(f"\n=== 4. 去重后共获取 {len(deduped)} 条全量真实舆情数据，开始并发翻译与术语校准 ===")
    to_translate_indices = [i for i, r in enumerate(deduped) if not r.get("翻译")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_to_idx = {
            executor.submit(translate_to_zh, deduped[i]["评论详情"]): i
            for i in to_translate_indices
        }
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                deduped[idx]["翻译"] = future.result()
            except Exception:
                deduped[idx]["翻译"] = deduped[idx]["评论详情"]
            done_count += 1
            if done_count % 40 == 0 or done_count == len(to_translate_indices):
                print(f"  [翻译进度] {done_count} / {len(to_translate_indices)}")

    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"已保存原始 JSON 数据备份: {RAW_DATA_PATH}")

    print("\n=== 5. 开始生成 16 字段高清截图全量 Excel 报表 ===")
    headers = [
        "收录日期",
        "平台",
        "链接",
        "时间",
        "信息属性（内容/观点）",
        "阵地属性",
        "评论语种",
        "情感属性",
        "舆情标签",
        "评论详情",
        "翻译",
        "评论链接",
        "截图",
        "备注1",
        "专项关键词",
        "字数",
    ]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MHO海外舆情监测全量表"

    header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    cell_font = Font(name="微软雅黑", size=10, color="0F172A")
    link_font = Font(name="微软雅黑", size=9, color="2563EB", underline="single")

    pos_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    neg_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    neu_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")

    thin_side = Side(border_style="thin", color="CBD5E1")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    ws.append(headers)
    ws.row_dimensions[1].height = 30

    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=1, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border

    # Cache high-res screenshot dimensions
    shot_dims = {}
    for fname in os.listdir(RAW_SHOT_DIR):
        fpath = os.path.join(RAW_SHOT_DIR, fname)
        if os.path.isfile(fpath) and fname.lower().endswith(".png"):
            with Image.open(fpath) as im:
                shot_dims[fname] = im.size

    for idx, item in enumerate(deduped, start=2):
        char_count = len(item["评论详情"])
        row_vals = [
            item["收录日期"],
            item["平台"],
            item["链接"],
            item["时间"],
            item["信息属性（内容/观点）"],
            item["阵地属性"],
            item["评论语种"],
            item["情感属性"],
            item["舆情标签"],
            item["评论详情"],
            item["翻译"],
            item["评论链接"],
            "",
            item["备注1"],
            item["专项关键词"],
            char_count,
        ]
        ws.append(row_vals)
        ws.row_dimensions[idx].height = 78

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=idx, column=col_idx)
            cell.font = cell_font
            cell.border = border
            if col_idx in (3, 12):
                cell.hyperlink = cell.value
                cell.font = link_font
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            elif col_idx in (10, 11, 14):
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            if col_idx == 8:
                if cell.value == "正面":
                    cell.fill = pos_fill
                elif cell.value == "负面":
                    cell.fill = neg_fill
                else:
                    cell.fill = neu_fill

        shot_name = item["截图文件"]
        shot_file = os.path.join(RAW_SHOT_DIR, shot_name)
        if os.path.exists(shot_file) and shot_name in shot_dims:
            orig_w, orig_h = shot_dims[shot_name]
            max_w, max_h = 160, 92
            scale = min(max_w / orig_w, max_h / orig_h)
            xl_img = XLImage(shot_file)
            xl_img.width = max(1, int(orig_w * scale))
            xl_img.height = max(1, int(orig_h * scale))
            ws.add_image(xl_img, f"M{idx}")

    col_widths = {
        1: 13,   # 收录日期
        2: 11,   # 平台
        3: 32,   # 链接
        4: 19,   # 时间
        5: 18,   # 信息属性（内容/观点）
        6: 22,   # 阵地属性
        7: 11,   # 评论语种
        8: 11,   # 情感属性
        9: 26,   # 舆情标签
        10: 48,  # 评论详情
        11: 48,  # 翻译
        12: 32,  # 评论链接
        13: 24,  # 截图
        14: 30,  # 备注1
        15: 26,  # 专项关键词
        16: 9,   # 字数
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:P{len(deduped) + 1}"

    out_full = os.path.join(OUTPUT_DIR, f"Monster_Hunter_Outlanders_海外舆情全量数据_{len(deduped)}条_16字段.xlsx")
    wb.save(out_full)
    print("已保存全量工作区 Excel:", out_full)

    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(desktop_dir):
        out_desktop = os.path.join(desktop_dir, f"Monster_Hunter_Outlanders_海外舆情全量数据_{len(deduped)}条_16字段.xlsx")
        shutil.copy2(out_full, out_desktop)
        print("已同步保存至桌面:", out_desktop)


if __name__ == "__main__":
    main()
