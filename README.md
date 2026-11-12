# Overseas Scraper - 海外数据采集与双版本 Excel 一键导出工具箱

面向闲鱼 / 小红书海外数据代采集与定制脚本接单场景的独立项目。自动识别本机代理端口（如 `v2rayN` 的 `127.0.0.1:10808`），每次采集自动在 `deliverables/` 目录生成 **【前20条验货预览 Excel】+【完整交付 Excel】+【UTF-8 CSV】**。

## 快速使用

```powershell
# 1. 安装依赖（仅首次）
python -m pip install -r requirements.txt

# 2. 按关键词批量采集 YouTube 视频列表与播放数据
python run.py youtube-search --query "AI agent workflow" --limit 30

# 3. 按视频链接批量采集 YouTube 评论
python run.py youtube-comments --url "https://www.youtube.com/watch?v=xxxxxx" --limit 50

# 4. 批量采集 Reddit 海外社区帖子与舆情讨论
python run.py reddit --query "ChatGPT Plus" --limit 30

# 5. 批量采集 HackerNews 海外科技热帖
python run.py hn --query "AI Agent" --limit 30

# 6. 提取任意公开海外网页表格或链接列表
python run.py web --url "https://example.com" --limit 80
```

## 接单指南
可直接复制发布的闲鱼宝贝标题、详情页文案、小红书引流帖模板及报价单，请查看根目录下的 **`闲鱼小红书接单实战手册.md`**。
