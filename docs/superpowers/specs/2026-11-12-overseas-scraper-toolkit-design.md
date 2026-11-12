# 海外数据采集与自动化导出接单工具箱（Local Via Proxy）设计文档

- **日期**：2026-11-12
- **运行环境**：Windows 10/11 + Python 3.13 + 本地代理隧道（`127.0.0.1:10808` SOCKS5 / `127.0.0.1:10809` HTTP）
- **定位**：面向闲鱼 / 小红书个人开发者接单场景的海外公开数据采集、清洗与双版本 Excel（免费试抓验货版 + 付款完整交付版）一键生成工具箱。

---

## 1. 背景与目标

用户已搭建好基于腾讯云境外服务器的 `VLESS + Reality` 代理环境，希望利用“独享海外网络环境 + 本地快速自动化脚本”在闲鱼、小红书开展海外数据代采集与定制脚本接单业务。

本工具箱解决新人接单的三大核心痛点：
1. **接单响应快**：买家发来 YouTube 视频/关键词、Reddit 话题/帖子或海外资讯需求，1 分钟内即可跑出结果。
2. **零信任破冰（20 条验货预览机制）**：每次采集自动生成两份 Excel：
   - `[验货预览-前20条]_*.xlsx`：包含表头、真实前 20 条记录（部分长文本适当截断并附带防白嫖水印提示），专供截图发给买家验货促单；
   - `[完整交付-共N条]_*.xlsx`：包含全部清洗后的数据、冻结首行、深蓝表头美化与自适应列宽，买家付款后直接发送交付。
3. **新人获客落地**：配套可直接复制发布的闲鱼垂直宝贝文案、小红书引流笔记模板、阶梯报价单与接单防坑话术。

---

## 2. 目录与模块结构

```text
D:\project\prometheus\
├── toolkit/
│   ├── requirements.txt                # Python 依赖清单（requests, PySocks, openpyxl, beautifulsoup4, yt-dlp）
│   ├── proxy_helper.py                 # 自动探测本机活跃代理端口（10808/10809）并构造 requests/yt-dlp 代理配置
│   ├── exporter.py                     # 双版本 Excel（验货预览版 + 完整交付版）与 CSV 导出及表格美化引擎
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── youtube_scraper.py          # 基于 yt-dlp 免 API Key 采集 YouTube 视频元数据与评论列表
│   │   ├── reddit_scraper.py           # 采集 Reddit 关键词搜索结果或指定帖子下的评论数据
│   │   └── web_scraper.py              # 采集 HackerNews 热门话题或通用海外网页链接/表格结构化数据
│   ├── run.py                          # 统一命令行入口（支持 youtube / reddit / hn / web 四个子命令）
│   └── 闲鱼小红书接单实战手册.md         # 6 套垂直商品文案、主图指南、报价表与成交话术
├── deliverables/                       # 自动生成的 Excel 交付物目录（加入 .gitignore，不入库）
└── tests/
    └── test-toolkit.py                 # 针对代理探测、数据脱敏与双版本 Excel 导出的单元测试
```

---

## 3. 核心模块设计

### 3.1 本地代理自动探测模块（`toolkit/proxy_helper.py`）
- 按优先级检测环境变量 `PROMETHEUS_PROXY`，若未设置则使用 `socket` 检测本机 `127.0.0.1:10808`（`v2rayN` 默认混合端口 / 本项目 SOCKS5 端口）与 `127.0.0.1:10809`（本项目 HTTP 端口）。
- 若 `v2rayN` 与内置客户端均未启动，支持自动调用 `scripts/client.ps1 start -NoSystemProxy` 拉起隧道，确保采集命令任何时候都能直接跑通。

### 3.2 双份 Excel 美化导出引擎（`toolkit/exporter.py`）
- **输入**：`records: list[dict]`、`task_name: str`、`preview_count: int = 20`。
- **处理逻辑**：
  1. **完整交付版**：写入全部数据行，首行深蓝色背景白字加粗（`#1F4E78`）、开启首行冻结（`freeze_panes = 'A2'`）、开启自动筛选（`auto_filter`），并根据内容长度自动调整列宽（上限 55 字符），同时额外导出一份 UTF-8 with BOM 的 `.csv` 方便做 Python/SPSS 论文分析的买家直接使用。
  2. **验货预览版**：仅截取前 `min(20, len(records))` 条数据，对正文/评论列保留前 60% 字符并在末尾追加 `...[验货预览，完整版共 N 条]`，表格底部附加一行汇总说明（`共采集到 N 条完整数据，以上为前 20 条实测样本`），方便卖家一键框选截图发给闲鱼客户。

### 3.3 三大高频接单采集器（`toolkit/scrapers/`）
1. **YouTube 采集器（`youtube_scraper.py`）**：
   - **模式 A（关键词搜视频列表）**：输入关键词（如 `"AI agent tutorial"`），批量抓取视频标题、频道名、播放量、时长、发布日期、视频链接。
   - **模式 B（单视频评论采集）**：输入视频 URL，调用 `yt-dlp` 免 Google API Key 提取评论作者、评论内容、点赞数、发布时间、是否置顶。
2. **Reddit 舆情采集器（`reddit_scraper.py`）**：
   - 支持按关键词搜索热门帖子（标题、所属板块 `subreddit`、点赞分 `score`、评论数、发布时间、正文摘要、链接）或抓取指定帖子 URL 下的高赞评论，直接契合留学生“舆情/情感分析论文”需求。
3. **科技热榜与通用网页采集器（`web_scraper.py`）**：
   - 支持一键抓取 HackerNews 实时科技热榜（标题、外链、积分、评论数、讨论页地址）及任意公开网页的标题、段落、超链接列表或 `<table>` 表格导出。

---

## 4. 验收标准

1. `python tests/test-toolkit.py` 单元测试全部通过（验证代理探测、脱敏截断、Excel 样式与双文件生成）。
2. 通过真实代理隧道执行 `python toolkit/run.py` 实测采集海外站点，在 `deliverables/` 下成功生成可直接打开截图的【验货预览版 Excel】与【完整交付版 Excel】。
3. `.gitignore` 忽略 `deliverables/` 与 `__pycache__/`，保持 Git 仓库干净。
