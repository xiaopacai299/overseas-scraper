from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from src.proxy_helper import get_requests_proxies


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def scrape_hackernews_top(query: str = "", limit: int = 35) -> list[dict]:
    proxies = get_requests_proxies()
    endpoint = "https://hn.algolia.com/api/v1/search"
    params = {
        "tags": "story" if query.strip() else "front_page",
        "hitsPerPage": min(limit, 100),
    }
    if query.strip():
        params["query"] = query.strip()

    resp = requests.get(endpoint, params=params, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=15)
    resp.raise_for_status()
    hits = (resp.json() or {}).get("hits") or []
    results = []
    for idx, hit in enumerate(hits[:limit], start=1):
        obj_id = hit.get("objectID") or ""
        results.append(
            {
                "序号": idx,
                "帖子标题": hit.get("title") or "",
                "作者": hit.get("author") or "",
                "热度赞数": hit.get("points") or 0,
                "评论数": hit.get("num_comments") or 0,
                "发布时间": (hit.get("created_at") or "")[:19].replace("T", " "),
                "原文链接": hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}",
                "HN讨论区链接": f"https://news.ycombinator.com/item?id={obj_id}",
            }
        )
    return results


def parse_generic_html_to_records(html: str, base_url: str = "", limit: int = 100) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    for table in tables:
        trs = table.find_all("tr")
        if len(trs) < 2:
            continue
        header_cells = [c.get_text(" ", strip=True) for c in trs[0].find_all(["th", "td"])]
        if not header_cells:
            continue
        records = []
        for tr in trs[1 : limit + 1]:
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if not any(cells):
                continue
            row_dict = {}
            for col_i, col_name in enumerate(header_cells):
                key = col_name or f"列_{col_i + 1}"
                row_dict[key] = cells[col_i] if col_i < len(cells) else ""
            records.append(row_dict)
        if records:
            return records

    records = []
    idx = 1
    for tag in soup.find_all(["h1", "h2", "h3", "a"]):
        text = tag.get_text(" ", strip=True)
        if len(text) < 6:
            continue
        href = tag.get("href") or ""
        if href and base_url:
            href = urljoin(base_url, href)
        records.append(
            {
                "序号": idx,
                "元素类型": tag.name.upper(),
                "标题或文本内容": text[:200],
                "跳转链接": href,
            }
        )
        idx += 1
        if len(records) >= limit:
            break
    return records


def scrape_generic_webpage(url: str, limit: int = 100) -> list[dict]:
    proxies = get_requests_proxies()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=15)
    resp.raise_for_status()
    return parse_generic_html_to_records(resp.text, base_url=url, limit=limit)
