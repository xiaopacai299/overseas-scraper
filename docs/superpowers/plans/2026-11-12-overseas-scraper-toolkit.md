# Overseas Data Scraper Freelance Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local proxy-aware overseas data scraping toolkit (`toolkit/`) that exports both a 20-row watermarked preview Excel (for client verification on Xianyu/Xiaohongshu) and a full styled Excel + CSV deliverable, paired with a ready-to-post freelance copywriting handbook.

**Architecture:** Python 3.13 CLI toolkit under `toolkit/` with automatic local proxy port detection (`127.0.0.1:10808` / `10809` or auto-starting `scripts/client.ps1`), `openpyxl`-based dual-Excel styled exporter, and modular scrapers for YouTube (`yt-dlp`), Reddit JSON/RSS endpoints, HackerNews Firebase/Algolia API, and generic web tables/articles.

**Tech Stack:** Python 3.13+, `requests[socks]`, `openpyxl`, `beautifulsoup4`, `yt-dlp`.

## Global Constraints

- `.gitignore` MUST ignore `deliverables/`, `__pycache__/`, and `*.pyc` so client deliverables never enter Git.
- Every scrape task MUST output three files into `deliverables/`: `[验货预览-前20条]_<name>.xlsx`, `[完整交付-共N条]_<name>.xlsx`, and `[完整交付-共N条]_<name>.csv` (UTF-8 with BOM for Excel direct open).
- Local proxy helper MUST automatically detect running proxy on `127.0.0.1:10808` or `127.0.0.1:10809`, and auto-start `scripts/client.ps1 start -NoSystemProxy` if neither is listening.

---

### Task 1: Proxy Auto-Detection & Dual-Excel Styled Exporter

**Files:**
- Modify: `.gitignore`
- Create: `toolkit/requirements.txt`
- Create: `toolkit/__init__.py`
- Create: `toolkit/proxy_helper.py`
- Create: `toolkit/exporter.py`
- Test: `tests/test-toolkit.py`

**Interfaces:**
- Produces:
  - `get_local_proxy_url(auto_start: bool = True) -> str`
  - `get_requests_proxies(auto_start: bool = True) -> dict[str, str]`
  - `mask_preview_text(text: str) -> str`
  - `export_deliverables(records: list[dict], task_name: str, output_dir: str, preview_limit: int = 20) -> dict[str, str]`

- [ ] **Step 1: Install dependencies & write failing test (`tests/test-toolkit.py`)**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `toolkit/proxy_helper.py` and `toolkit/exporter.py`**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

---

### Task 2: Overseas Scrapers (YouTube, Reddit, HackerNews & Generic Web) + Unified CLI

**Files:**
- Create: `toolkit/scrapers/__init__.py`
- Create: `toolkit/scrapers/youtube_scraper.py`
- Create: `toolkit/scrapers/reddit_scraper.py`
- Create: `toolkit/scrapers/web_scraper.py`
- Create: `toolkit/run.py`
- Modify: `tests/test-toolkit.py`

**Interfaces:**
- Consumes: `toolkit.proxy_helper`, `toolkit.exporter`
- Produces:
  - `scrape_youtube_search(query: str, limit: int = 30) -> list[dict]`
  - `scrape_youtube_comments(video_url: str, limit: int = 50) -> list[dict]`
  - `scrape_reddit_search(query: str, limit: int = 50) -> list[dict]`
  - `scrape_hackernews_top(limit: int = 50) -> list[dict]`
  - `scrape_generic_webpage(url: str, limit: int = 100) -> list[dict]`
  - CLI `python toolkit/run.py <youtube-search|youtube-comments|reddit|hn|web>`

- [ ] **Step 1: Add scraper & CLI tests to `tests/test-toolkit.py`**
- [ ] **Step 2: Implement scrapers and `toolkit/run.py`**
- [ ] **Step 3: Run unit tests to verify**
- [ ] **Step 4: Commit**

---

### Task 3: Freelance Copywriting Handbook & Live Sample Deliverables Generation

**Files:**
- Create: `toolkit/闲鱼小红书接单实战手册.md`
- Modify: `README.md`

- [ ] **Step 1: Write `toolkit/闲鱼小红书接单实战手册.md` and update `README.md`**
- [ ] **Step 2: Run live scrapes over the cloud proxy tunnel (`youtube-search`, `reddit`, `hn`) to generate real sample Excel files in `deliverables/`**
- [ ] **Step 3: Verify all test suites pass and commit**
