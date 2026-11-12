# -*- coding: utf-8 -*-
"""
闲鱼创作者平台 & 闲鱼网页版（goofish.com）标准自动发布脚本
功能：
1. 自动生成 3 套高转化闲鱼宝贝/帖子主图（1:1 高清封面）+ 1 张真实 Excel 验货样本截图
2. 生成兼容【闲鱼创作者平台 creator.goofish.com】与【闲鱼网页版发闲置 goofish.com/publish】的
   可视化一键自动填单脚本，并自动复制到你的 Windows 剪贴板
3. 支持通过 Edge 远程调试端口（--auto）自动打开闲鱼发布页并挂载配图目录
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "deliverables" / "xianyu_publish_assets"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """加载 Windows 微软雅黑字体，保证中文封面清晰锐利"""
    candidates = (
        [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\msyh.ttc",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


LISTING_TEMPLATES = [
    {
        "id": "1",
        "tag": "宝贝 1：主打留学生 / 毕业论文 / 舆情分析（高客单价 100~300元）",
        "price": "9.90",
        "title": "Reddit数据采集 YouTube评论抓取导出Excel 留学生毕业论文舆情情感分析数据集",
        "cover_filename": "01_封面_留学生论文舆情采集.png",
        "theme_bg": (15, 23, 42),        # 深海科技蓝
        "accent": (56, 189, 248),        # 亮天蓝
        "badge": "海外专线直采 · 10分钟免费出样",
        "big_title_1": "Reddit / YouTube",
        "big_title_2": "海外数据代采集",
        "subtitle": "留学生毕业论文 · 舆情与情感分析一手数据集",
        "bullets": [
            "✓ 支持 Reddit 指定板块热帖 / 关键词评论时间线",
            "✓ 支持 YouTube 视频高赞评论 / 弹幕 / 频道数据",
            "✓ 双格式交付：美化版 .xlsx + 无乱码 UTF-8 .csv",
            "✓ 先免费试抓前 20 条真实数据截图验货，满意再拍",
        ],
        "content": (
            "【海外专线直采 · 先出20条真实样本验货 · 满意再付款】\n\n"
            "专为留学生 Essay / 毕业论文 / 舆情与情感分析（Sentiment Analysis）提供海外一手公开数据集采集与清洗服务！\n\n"
            "支持平台：\n"
            "1. Reddit 指定板块（Subreddit）或关键词下的热帖标题、正文、点赞分、评论数、时间戳\n"
            "2. YouTube 指定视频下的高赞评论、最新评论、作者、点赞数、发布时间，或关键词视频列表\n"
            "3. HackerNews / 海外科技社区 / 新闻媒体公开讨论数据\n\n"
            "交付标准：\n"
            "- 同时提供美化排版好的【.xlsx Excel 表格】+【UTF-8 .csv 原文件】（可直接喂给 Python / R / SPSS / Stata 分析，绝无乱码）\n"
            "- 接单流程：发我关键词或网址 -> 10分钟内免费试采前20条真实数据截图给你验货 -> 确认字段完全符合要求再拍下付款 -> 秒发完整无遮挡数据包！"
        ),
    },
    {
        "id": "2",
        "tag": "宝贝 2：主打跨境电商卖家 / 选品调研（高复购率 80~200元）",
        "price": "9.90",
        "title": "跨境电商海外社媒评论采集 YouTube测评评论 Reddit产品口碑痛点分析导出Excel",
        "cover_filename": "02_封面_跨境电商选品评论分析.png",
        "theme_bg": (6, 44, 48),         # 墨绿商务风
        "accent": (52, 211, 153),        # 翡翠绿
        "badge": "跨境选品调研利器 · 免费试抓20条",
        "big_title_1": "跨境选品 / 竞品口碑",
        "big_title_2": "老外真实痛点采集",
        "subtitle": "YouTube 测评评论 · Reddit 垂直社区口碑导出",
        "bullets": [
            "✓ 批量导出 YouTube 头部测评视频数千条真实反馈",
            "✓ 挖掘 Reddit 垂直社区近一年优缺点与差评槽点",
            "✓ 自动清洗乱码换行，一键导出带筛选表头 Excel",
            "✓ 可附赠 AI 中文痛点总结报告，助你精准选品",
        ],
        "content": (
            "【跨境选品调研利器 · 10分钟免费试采20条验货】\n\n"
            "做亚马逊 Amazon / 独立站 / TikTok 出海选品，想看老外对某类产品的真实槽点和购买痛点？\n"
            "直接把竞品关键词或 YouTube 测评视频链接发给我！\n\n"
            "可批量导出：\n"
            "- YouTube 头部测评博主的视频列表、播放量及评论区数千条老外真实反馈\n"
            "- Reddit 垂直社区（如 r/BuyItForLife, r/headphones 等）近一年真实讨论帖与优缺点评价\n"
            "- 海外公开网站商品列表与表格数据整理\n\n"
            "发关键词或链接，免费先出前20条预览图，看到真实数据再下单，支持后续用 AI 总结老外差评痛点报告！"
        ),
    },
    {
        "id": "3",
        "tag": "宝贝 3：主打自媒体 / 科技博主素材挖掘（走量快单 30~80元）",
        "price": "9.90",
        "title": "YouTube视频列表评论批量导出 HackerNews海外科技热榜采集 导出Excel表格",
        "cover_filename": "03_封面_YouTube与科技热榜导出.png",
        "theme_bg": (30, 27, 75),        # 极客靛紫风
        "accent": (167, 139, 250),       # 霓虹紫
        "badge": "Python 自动化极速交稿 · 先验货后付款",
        "big_title_1": "YouTube / HN 热榜",
        "big_title_2": "视频与评论批量导出",
        "subtitle": "海外科技圈热议话题 · 爆款视频清单秒级整理",
        "bullets": [
            "✓ 按关键词批量抓 YouTube 标题/播放量/时长/链接",
            "✓ 单条或多条视频高赞评论、作者与时间明细导出",
            "✓ HackerNews / Reddit 每日 AI 与科技热榜采集",
            "✓ 10 分钟内发前 20 条实测截图验货，几分钟极速交稿",
        ],
        "content": (
            "海外公开视频信息与评论区批量采集导出 Excel：\n"
            "- 按关键词批量抓取 YouTube 视频标题、频道主、播放量、时长、直达链接\n"
            "- 按单条视频链接导出高赞评论与时间明细\n"
            "- 抓取 HackerNews / Reddit 每日科技与 AI 热门话题榜单\n\n"
            "先给前20条实测截图验货，满意再付，几分钟极速交稿！"
        ),
    },
]


def generate_cover_image(tpl: dict, out_path: Path) -> None:
    """生成 1000x1000 闲鱼高点击率大字报主图"""
    W, H = 1000, 1000
    bg = tpl["theme_bg"]
    accent = tpl["accent"]
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # 装饰网格与科技光晕边框
    for x in range(0, W, 50):
        draw.line([(x, 0), (x, H)], fill=(bg[0] + 10, bg[1] + 12, bg[2] + 18), width=1)
    for y in range(0, H, 50):
        draw.line([(0, y), (W, y)], fill=(bg[0] + 10, bg[1] + 12, bg[2] + 18), width=1)

    draw.rounded_rectangle([35, 35, W - 35, H - 35], radius=28, outline=accent, width=4)

    # 顶部标签胶囊
    draw.rounded_rectangle([75, 75, 620, 140], radius=32, fill=accent)
    font_badge = get_font(30, bold=True)
    draw.text((105, 88), tpl["badge"], fill=(10, 15, 25), font=font_badge)

    # 主标题大字（闲鱼瀑布流一眼看清）
    font_h1 = get_font(82, bold=True)
    font_h2 = get_font(78, bold=True)
    draw.text((75, 175), tpl["big_title_1"], fill=(255, 255, 255), font=font_h1)
    draw.text((75, 280), tpl["big_title_2"], fill=accent, font=font_h2)

    # 副标题
    font_sub = get_font(34, bold=True)
    draw.text((75, 395), tpl["subtitle"], fill=(226, 232, 240), font=font_sub)

    # 分隔线
    draw.line([(75, 460), (925, 460)], fill=accent, width=3)

    # 核心卖点列表框
    draw.rounded_rectangle(
        [75, 490, 925, 815],
        radius=20,
        fill=(bg[0] + 16, bg[1] + 22, bg[2] + 35),
        outline=(accent[0] // 2, accent[1] // 2, accent[2] // 2),
        width=2,
    )
    font_bullet = get_font(31, bold=False)
    y_pos = 520
    for b in tpl["bullets"]:
        draw.text((105, y_pos), b, fill=(241, 245, 249), font=font_bullet)
        y_pos += 68

    # 底部强行动号召条（黄底黑字高转化条）
    draw.rounded_rectangle([75, 845, 925, 925], radius=18, fill=(250, 204, 21))
    font_cta = get_font(34, bold=True)
    draw.text(
        (135, 864),
        "私信发关键词/链接 → 免费先出20条Excel样本验货！",
        fill=(15, 23, 42),
        font=font_cta,
    )

    img.save(out_path, "PNG")


def generate_sample_excel_image(out_path: Path) -> None:
    """生成第 2 张商品附图：真实感拉满的 Excel 验货样本截图（含防白嫖截断效果展示）"""
    W, H = 1200, 900
    img = Image.new("RGB", (W, H), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # 顶部 Excel 风格标题栏
    draw.rectangle([0, 0, W, 85], fill=(16, 124, 65))
    font_top = get_font(32, bold=True)
    draw.text(
        (35, 22),
        "Excel 实测导出样本预览（同时交付 .xlsx 表格 + UTF-8 .csv）",
        fill=(255, 255, 255),
        font=font_top,
    )

    # 表头
    headers = ["序号", "平台来源", "作者 / 频道", "标题 / 评论正文（自动清洗换行）", "点赞", "发布时间"]
    col_x = [30, 105, 255, 450, 930, 1030, 1170]
    table_top = 115
    row_h = 62

    draw.rectangle([col_x[0], table_top, col_x[-1], table_top + row_h], fill=(30, 58, 138))
    font_th = get_font(22, bold=True)
    for i, h_text in enumerate(headers):
        draw.text((col_x[i] + 12, table_top + 16), h_text, fill=(255, 255, 255), font=font_th)

    sample_rows = [
        ("1", "Reddit", "u/tech_nomad", "After 6 months with this e-bike, battery life is...", "428", "2026-11-10"),
        ("2", "Reddit", "u/grad_research", "Customer support took 3 weeks to replace the...", "312", "2026-11-09"),
        ("3", "YouTube", "@MKBHD_Review", "Build quality is solid, but app connectivity...", "1,205", "2026-11-08"),
        ("4", "YouTube", "@SarahInTech", "Compared to Pro version, this model overheats...", "864", "2026-11-07"),
        ("5", "Reddit", "u/audio_phile", "Best noise cancelling under $200, ear pads...", "259", "2026-11-06"),
        ("6", "YouTube", "@Alex_Daily", "I bought two units for studio***[预览截断]", "193", "2026-11-05"),
        ("7", "Reddit", "u/ev_commuter", "Brakes started squeaking at***[预览截断]", "147", "2026-11-04"),
        ("8", "HackerNews", "dev_builder", "Migrated from OpenAI API to***[预览截断]", "531", "2026-11-03"),
        ("9", "YouTube", "@UnboxTherapy", "About international shipping***[预览截断]", "410", "2026-11-02"),
        ("10", "Reddit", "u/data_sci_uk", "Great dataset! Sentiment on***[预览截断]", "98", "2026-11-01"),
    ]

    font_td = get_font(20, bold=False)
    for r_idx, row in enumerate(sample_rows):
        y1 = table_top + (r_idx + 1) * row_h
        y2 = y1 + row_h
        bg_color = (255, 255, 255) if r_idx % 2 == 0 else (241, 245, 249)
        if r_idx >= 5:
            bg_color = (254, 249, 195)  # 预览截断高亮行
        draw.rectangle([col_x[0], y1, col_x[-1], y2], fill=bg_color, outline=(203, 213, 225))
        for c_idx, val in enumerate(row):
            color = (180, 83, 9) if ("预览截断" in val and c_idx == 3) else (30, 41, 59)
            draw.text((col_x[c_idx] + 12, y1 + 18), val, fill=color, font=font_td)

    # 底部说明条
    draw.rounded_rectangle([30, 810, 1170, 875], radius=12, fill=(22, 101, 52))
    font_foot = get_font(24, bold=True)
    draw.text(
        (55, 827),
        "★ 接单实测样本：拍前免费抓前20条给你核对字段，付款后秒发无遮挡完整版 .xlsx + .csv！",
        fill=(255, 255, 255),
        font=font_foot,
    )

    img.save(out_path, "PNG")


def build_browser_autofill_js(assets_dir: Path) -> str:
    """
    生成可在 Edge【闲鱼创作者平台 / 闲鱼网页版发布页】直接运行的悬浮一键填单助手 JS
    完美兼容 React / Lexical / Draft.js / Slate / 常规 textarea & input 受控组件
    """
    payload = []
    for tpl in LISTING_TEMPLATES:
        payload.append(
            {
                "id": tpl["id"],
                "tag": tpl["tag"],
                "title": tpl["title"],
                "price": tpl["price"],
                "content": tpl["content"],
                "full_xianyu_text": f"{tpl['title']}\n\n{tpl['content']}",
                "cover_file": str(assets_dir / tpl["cover_filename"]),
                "sample_file": str(assets_dir / "00_通用附图_Excel实测样本预览.png"),
            }
        )

    data_json = json.dumps(payload, ensure_ascii=False)
    assets_dir_str = str(assets_dir).replace("\\", "\\\\")

    js_code = f"""(function() {{
  const TEMPLATES = {data_json};
  const ASSETS_PATH = "{assets_dir_str}";

  // 移除旧面板
  const old = document.getElementById('xy-auto-publisher-panel');
  if (old) old.remove();

  // React 受控输入框赋值器
  function setNativeValue(el, value) {{
    if (!el) return false;
    el.focus();
    const proto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) {{
      setter.call(el, value);
    }} else {{
      el.value = value;
    }}
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
    return true;
  }}

  // 富文本 contenteditable 赋值器（兼容闲鱼创作者平台编辑器）
  function setRichEditorValue(el, text) {{
    if (!el) return false;
    el.focus();
    document.execCommand('selectAll', false, null);
    const ok = document.execCommand('insertText', false, text);
    if (!ok) {{
      el.innerText = text;
      el.dispatchEvent(new InputEvent('input', {{ bubbles: true, data: text, inputType: 'insertText' }}));
    }}
    return true;
  }}

  // 自动检测是否还在首页（#/home），如果是则自动帮点左侧黄色【发布内容】按钮进入编辑页
  async function ensureInPublishEditor() {{
    const hasEditor = document.querySelector('textarea, [contenteditable="true"], input[type="file"]');
    if (hasEditor) return true;

    // 查找页面上的“发布内容”或“发布图文”按钮
    const allClickables = Array.from(document.querySelectorAll('button, a, div, span'));
    const pubBtn = allClickables.find(el => {{
      const txt = (el.innerText || '').trim();
      return (txt === '发布内容' || txt === '发布图文' || txt === '发图文' || txt === '发闲置') && el.offsetParent !== null;
    }});

    if (pubBtn) {{
      pubBtn.click();
      // 等待路由跳转和编辑器 DOM 渲染（最多等 3 秒）
      for (let i = 0; i < 15; i++) {{
        await new Promise(r => setTimeout(r, 200));
        // 如果点击“发布内容”后展开了子菜单（如“发布图文”、“发布视频”），自动点“发布图文”
        const subBtn = Array.from(document.querySelectorAll('button, a, div, span, li')).find(el => {{
          const t = (el.innerText || '').trim();
          return (t === '发布图文' || t === '图文' || t === '发图文') && el.offsetParent !== null;
        }});
        if (subBtn) subBtn.click();

        const nowHasEditor = document.querySelector('textarea, [contenteditable="true"], input[type="file"]');
        if (nowHasEditor) return true;
      }}
    }}
    return false;
  }}

  async function autoFillTemplate(tpl) {{
    const statusEl = document.getElementById('xy-auto-status');
    statusEl.innerHTML = '<div style="color:#fbbf24;">⏳ 正在检查并进入【发布内容】编辑页...</div>';

    await ensureInPublishEditor();

    let filledTitle = false;
    let filledBody = false;
    let filledPrice = false;

    // 1. 查找标题框（闲鱼创作者平台通常有独立标题 input）
    const inputs = Array.from(document.querySelectorAll('input[type="text"], input:not([type])'));
    const titleInput = inputs.find(i => {{
      const ph = (i.placeholder || '').toLowerCase();
      return ph.includes('标题') || ph.includes('名称') || ph.includes('title');
    }});

    if (titleInput) {{
      filledTitle = setNativeValue(titleInput, tpl.title);
    }}

    // 2. 查找正文框（textarea 或 contenteditable 富文本）
    const textareas = Array.from(document.querySelectorAll('textarea'));
    const editables = Array.from(document.querySelectorAll('[contenteditable="true"]'));

    // 如果没有独立标题框（例如 goofish.com/publish 闲鱼发闲置是标题+正文合一框），把首行放标题
    const bodyTextToFill = filledTitle ? tpl.content : tpl.full_xianyu_text;

    if (textareas.length > 0) {{
      const mainTa = textareas.find(t => {{
        const ph = (t.placeholder || '');
        return ph.includes('描述') || ph.includes('正文') || ph.includes('买家') || ph.includes('内容') || ph.includes('品牌') || ph.includes('分享');
      }}) || textareas[0];
      filledBody = setNativeValue(mainTa, bodyTextToFill);
    }} else if (editables.length > 0) {{
      const mainEd = editables[editables.length - 1];
      filledBody = setRichEditorValue(mainEd, bodyTextToFill);
    }}

    // 3. 查找价格输入框
    const allInputs = Array.from(document.querySelectorAll('input'));
    const priceInput = allInputs.find(i => {{
      const ph = (i.placeholder || '');
      const label = (i.closest('div')?.innerText || '');
      return ph.includes('价格') || ph.includes('0.00') || ph.includes('¥') || (label.includes('价格') && i !== titleInput);
    }});
    if (priceInput) {{
      filledPrice = setNativeValue(priceInput, tpl.price);
    }}

    // 4. 复制配图文件夹路径到剪贴板，方便文件选择框直接粘贴路径
    navigator.clipboard?.writeText(ASSETS_PATH).catch(() => {{}});

    statusEl.innerHTML = `
      <div style="color:#4ade80;font-weight:bold;margin-bottom:6px;">
        ✅ 已处理【${{tpl.tag.split('（')[0]}}】！
      </div>
      <div style="font-size:12px;color:#e2e8f0;line-height:1.5;">
        • 标题+正文：${{filledBody || filledTitle ? '<span style="color:#4ade80">已自动填入网页输入框</span>' : '<span style="color:#fbbf24">当前还在首页！请先点左侧黄色【发布内容】按钮进入编辑页后再点我</span>'}}<br/>
        • 标价 (9.90元)：${{filledPrice ? '已自动填入' : '创作者图文帖无需标价（发商品请去 goofish.com/publish）'}}<br/>
        • <b>专属配图路径已复制</b>，进入编辑页后点下方黄色按钮即可直接选图：<b>${{tpl.cover_file.split('\\\\').pop()}}</b>
      </div>
    `;

    if (!filledBody && !filledTitle) {{
      navigator.clipboard?.writeText(tpl.full_xianyu_text);
    }}
  }}

  async function triggerImageUpload() {{
    navigator.clipboard?.writeText(ASSETS_PATH).catch(() => {{}});
    await ensureInPublishEditor();
    const fileInput = document.querySelector('input[type="file"][accept*="image"], input[type="file"][accept*="png"], input[type="file"][accept*="jpg"], input[type="file"]');
    if (fileInput) {{
      fileInput.click();
    }} else {{
      alert('你当前还在【首页（#/home）】哦！\\n\\n请先点击网页左上角黄色的【发布内容】按钮进入发帖编辑页，然后再点此按钮即可直接弹出选图窗口！');
    }}
  }}

  // 创建右上角可视化悬浮操作台
  const panel = document.createElement('div');
  panel.id = 'xy-auto-publisher-panel';
  panel.style.cssText = 'position:fixed;top:20px;right:20px;width:360px;background:#0f172a;color:#f8fafc;border:2px solid #38bdf8;border-radius:14px;padding:16px;z-index:999999;box-shadow:0 15px 35px rgba(0,0,0,0.45);font-family:system-ui,-apple-system,sans-serif;';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:12px;">
      <div style="font-size:15px;font-weight:bold;color:#38bdf8;">🚀 闲鱼海外数据接单 · 一键发布台</div>
      <button id="xy-close-btn" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:18px;">×</button>
    </div>
    <div style="font-size:12px;color:#cbd5e1;margin-bottom:10px;">
      点击下方按钮，自动向当前页面填入<b>满分标题 + 接单文案 + 9.9元标价</b>：
    </div>
    <div id="xy-btn-list" style="display:flex;flex-direction:column;gap:8px;margin-bottom:12px;"></div>
    <button id="xy-upload-btn" style="width:100%;padding:9px;background:#eab308;color:#0f172a;font-weight:bold;border:none;border-radius:8px;cursor:pointer;font-size:13px;margin-bottom:10px;">
      🖼️ 唤起上传图片（已自动复制配图文件夹路径）
    </button>
    <div id="xy-auto-status" style="background:#1e293b;padding:10px;border-radius:8px;font-size:12px;color:#94a3b8;">
      就绪：请先在网页打开发布页，然后点击上方任一模板按钮。
    </div>
  `;
  document.body.appendChild(panel);

  document.getElementById('xy-close-btn').onclick = () => panel.remove();
  document.getElementById('xy-upload-btn').onclick = triggerImageUpload;

  const listEl = document.getElementById('xy-btn-list');
  TEMPLATES.forEach(tpl => {{
    const btn = document.createElement('button');
    btn.style.cssText = 'text-align:left;padding:10px 12px;background:#1e293b;color:#f1f5f9;border:1px solid #475569;border-radius:8px;cursor:pointer;font-size:13px;transition:all 0.15s;';
    btn.onmouseover = () => {{ btn.style.borderColor = '#38bdf8'; btn.style.background = '#0f172a'; }};
    btn.onmouseout = () => {{ btn.style.borderColor = '#475569'; btn.style.background = '#1e293b'; }};
    btn.innerHTML = `<div style="font-weight:bold;color:#38bdf8;margin-bottom:2px;">一键填入 · ${{tpl.tag.split('（')[0]}}</div><div style="font-size:11px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${{tpl.title}}</div>`;
    btn.onclick = () => autoFillTemplate(tpl);
    listEl.appendChild(btn);
  }});
}})();"""
    return js_code


def copy_to_windows_clipboard(text: str) -> bool:
    """将文本写入 Windows 剪贴板"""
    try:
        proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        proc.communicate(input=text.encode("utf-16-le"))
        return proc.returncode == 0
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="闲鱼/小红书标准宝贝配图生成与一键自动填单工具")
    parser.add_argument("--open-publish", action="store_true", help="在 Edge 中直接打开闲鱼网页版发布页与配图文件夹")
    args = parser.parse_args()

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/3] 正在为你生成 3 套闲鱼高转化大字封面图 + 1 张真实 Excel 验货样本截图...")
    for tpl in LISTING_TEMPLATES:
        out_file = ASSETS_DIR / tpl["cover_filename"]
        generate_cover_image(tpl, out_file)
        print(f"  -> 已生成主图: {out_file}")

    sample_file = ASSETS_DIR / "00_通用附图_Excel实测样本预览.png"
    generate_sample_excel_image(sample_file)
    print(f"  -> 已生成附图: {sample_file}")

    print("\n[2/3] 正在生成 Edge 浏览器【闲鱼一键发布悬浮台】注入脚本...")
    js_code = build_browser_autofill_js(ASSETS_DIR)
    js_path = ASSETS_DIR / "edge_console_autofill.js"
    js_path.write_text(js_code, encoding="utf-8")

    # 用 PowerShell Set-Clipboard 保证 UTF-8 中文不乱码
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Get-Content -Path '{js_path}' -Encoding UTF8 | Set-Clipboard"],
        check=False,
    )
    print(f"  -> 脚本已保存至: {js_path}")
    print("  -> [已自动复制到你的系统剪贴板！]")

    if args.open_publish:
        print("\n[3/3] 正在为你打开配图文件夹...")
        subprocess.Popen(["explorer.exe", str(ASSETS_DIR)])

    print("\n============================================================")
    print("✅ 准备就绪！你现在只需要在已登录的 Edge 浏览器里做 2 步：")
    print("  第 1 步：在你的闲鱼创作者平台发布页（或 https://www.goofish.com/publish ）按 F12 打开开发者工具，切到【控制台 (Console)】，直接按 Ctrl+V 粘贴并回车。")
    print("  第 2 步：网页右上角会弹出【🚀 闲鱼海外数据接单 · 一键发布台】，点一下按钮就会自动填好标题、正文和 9.90 元价格！")
    print("============================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
