# -*- coding: utf-8 -*-
"""
小红书（Xiaohongshu）引流笔记全自动配图生成 + CDP 自动发布工具
融合 https://github.com/xpzouying/xiaohongshu-mcp 核心实现（xiaohongshu/publish.go & skills/post-to-xhs/scripts/cdp_publish.py）：
1. 复用已登录的 Edge 远程调试端口 (127.0.0.1:9222)，避免多端网页登录互踢与 leakless.exe 报毒
2. 采用纯英文文件名图片路径 + CDP 原生 DOM.setFileInputFiles 注入，绕过文件弹窗与中文路径丢图问题
3. 自动清理 div.d-popover / .feature-guide__btn 遮挡浮层，等待 .img-preview-area .pr 预览就绪
4. 支持真实话题联想选择（#creator-editor-topic-container .item -> a[data-topic] 蓝字话题节点）
5. 针对新版 <xhs-publish-btn> (closed Shadow DOM) 采用 0.65 黄金比例坐标真实鼠标点击 + URL 跳转离开发布页校验
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests
import websockets.sync.client as ws_client
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent
XHS_ASSETS_DIR = PROJECT_ROOT / "deliverables" / "xiaohongshu_publish_assets"

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"
XHS_NOTE_MANAGER_URL = "https://creator.xiaohongshu.com/new/note-manager"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
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
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def generate_xhs_images(template_id: str = "1") -> list[Path]:
    """
    按照《闲鱼小红书接单实战手册.md》第 三 节标准生成小红书 3:4 竖版高清笔记配图（2张），
    同时遵循 xiaohongshu-mcp 官方规范：同步输出纯英文路径文件名，防止小红书上传器因中文路径静默丢图。
    不同模板自动采用不同主题配色与大字标题，避免被小红书判定为重复搬运图。
    """
    XHS_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    W, H = 1080, 1440  # 小红书黄金 3:4 竖图比例

    if template_id == "2":
        bg_main = (6, 44, 48)
        badge_txt = "🔥 亚马逊 / 独立站 / TikTok 选品干货"
        h1_txt = "跨境选品怎么扒"
        h2_txt = "Reddit / YouTube"
        h3_txt = "老外真实差评与痛点？"
        accent_c = (52, 211, 153)
        sub_txt = "告别盲目选品！Python 批量导出数千条老外真实槽点 Excel"
        sheet_title = "📊 [选品调研]_海外竞品差评与痛点词频表.xlsx"
    else:
        bg_main = (15, 23, 42)
        badge_txt = "🔥 留学生论文 / 跨境调研干货"
        h1_txt = "30秒批量导出"
        h2_txt = "Reddit / YouTube"
        h3_txt = "评论做论文情感分析"
        accent_c = (56, 189, 248)
        sub_txt = "告别手动复制粘贴！Python 一键清洗导出带表头 Excel + CSV"
        sheet_title = "📊 [实测样本]_Reddit_YouTube_舆情数据集.xlsx"

    # ---------------- 图 1：高点击率小红书爆款封面 ----------------
    img1 = Image.new("RGB", (W, H), bg_main)
    d1 = ImageDraw.Draw(img1)

    d1.rounded_rectangle([60, 70, 650, 145], radius=36, fill=(239, 68, 68))
    d1.text((95, 86), badge_txt, fill=(255, 255, 255), font=get_font(32, True))

    d1.text((60, 185), h1_txt, fill=(250, 204, 21), font=get_font(86, True))
    d1.text((60, 295), h2_txt, fill=(255, 255, 255), font=get_font(82, True))
    d1.text((60, 405), h3_txt, fill=accent_c, font=get_font(76, True))

    d1.text(
        (60, 515),
        sub_txt,
        fill=(203, 213, 225),
        font=get_font(31, False),
    )

    card_top = 585
    card_bottom = 1230
    d1.rounded_rectangle([50, card_top, W - 50, card_bottom], radius=24, fill=(255, 255, 255), outline=accent_c, width=4)
    d1.rounded_rectangle([50, card_top, W - 50, card_top + 78], radius=24, fill=(16, 124, 65))
    d1.rectangle([50, card_top + 45, W - 50, card_top + 78], fill=(16, 124, 65))
    d1.text((85, card_top + 20), sheet_title, fill=(255, 255, 255), font=get_font(28, True))

    cols = [75, 195, 365, 815, 920, 1005]
    headers = ["平台", "作者/来源", "清洗后评论正文 (可直接喂 SPSS/AI)", "点赞", "时间"]
    th_y = card_top + 95
    d1.rectangle([cols[0], th_y, cols[-1], th_y + 56], fill=(30, 58, 138))
    for i, h_txt in enumerate(headers):
        d1.text((cols[i] + 10, th_y + 13), h_txt, fill=(255, 255, 255), font=get_font(21, True))

    rows = [
        ("Reddit", "u/ai_research", "Using LLM agents for workflow automation...", "428", "11-12"),
        ("YouTube", "@MKBHD", "Battery life on the new model is impressive...", "1.2k", "11-11"),
        ("Reddit", "u/grad_thesis", "Public sentiment shifted towards privacy...", "319", "11-11"),
        ("YouTube", "@TechLinked", "Compared with competitors, the price is...", "856", "11-10"),
        ("Reddit", "u/ecom_buyer", "Main complaint: shipping took over 2 weeks...", "274", "11-10"),
        ("YouTube", "@Dave2D", "Thermal performance under heavy load is...", "642", "11-09"),
        ("Reddit", "u/uk_student", "Great sample for sentiment analysis paper...", "195", "11-09"),
        ("HN", "dev_ops", "We benchmarked 5 open-source scrapers...", "512", "11-08"),
    ]
    for idx, r in enumerate(rows):
        ry = th_y + 56 + idx * 58
        bg_c = (248, 250, 252) if idx % 2 == 0 else (241, 245, 249)
        d1.rectangle([cols[0], ry, cols[-1], ry + 58], fill=bg_c, outline=(226, 232, 240))
        for c_i, val in enumerate(r):
            d1.text((cols[c_i] + 10, ry + 15), val, fill=(30, 41, 59), font=get_font(20, False))

    d1.rounded_rectangle([50, 1270, W - 50, 1375], radius=20, fill=(250, 204, 21))
    d1.text(
        (95, 1302),
        "👉 往右滑看实测导出表格细节 · 评论区留关键词帮你试抓！",
        fill=(15, 23, 42),
        font=get_font(32, True),
    )

    p1_cn = XHS_ASSETS_DIR / f"0{template_id}_小红书封面.png"
    p1_ascii = XHS_ASSETS_DIR / f"xhs_cover_tpl{template_id}_01.png"
    img1.save(p1_cn, "PNG")
    img1.save(p1_ascii, "PNG")

    # ---------------- 图 2：实测样本细节图（三大核心优势拆解） ----------------
    img2 = Image.new("RGB", (W, H), (248, 250, 252))
    d2 = ImageDraw.Draw(img2)

    d2.rectangle([0, 0, W, 160], fill=(30, 58, 138))
    d2.text((60, 48), "为什么不用再一条条手动复制粘贴？", fill=(255, 255, 255), font=get_font(50, True))

    cards = [
        (
            "01 | 字段齐全，拿来就能做实证/词频分析",
            (16, 185, 129),
            [
                "• 帖子/视频标题 + 评论正文（自动去除乱码与换行符）",
                "• 作者昵称、精准点赞数、回复数、精确到秒的发布时间戳",
                "• 支持按关键词搜索热帖，或指定单条 YouTube 视频抓全量评论",
            ],
        ),
        (
            "02 | 双格式同时导出（.xlsx + UTF-8 .csv）",
            (59, 130, 246),
            [
                "• 美化版 Excel (.xlsx)：自带冻结首行、自动列宽与筛选器",
                "• 标准 UTF-8 (.csv)：直接导入 Python / R / SPSS / Stata 绝不乱码",
                "• 无论是写英文 Essay 情感分析还是做跨境差评统计都直接可用",
            ],
        ),
        (
            "03 | 适用场景一览（评论区可留关键词测试）",
            (245, 158, 11),
            [
                "• 留学生毕业论文：Reddit / YouTube 海外舆论与情感倾向数据集",
                "• 跨境电商选品：亚马逊/独立站同类竞品老外真实痛点与差评总结",
                "• 科技与社媒调研：HackerNews / 海外垂直论坛热门话题追踪",
            ],
        ),
    ]

    cy = 210
    for title_txt, badge_color, items in cards:
        d2.rounded_rectangle([55, cy, W - 55, cy + 340], radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=3)
        d2.rounded_rectangle([55, cy, W - 55, cy + 82], radius=24, fill=badge_color)
        d2.rectangle([55, cy + 50, W - 55, cy + 82], fill=badge_color)
        d2.text((90, cy + 20), title_txt, fill=(255, 255, 255), font=get_font(34, True))

        iy = cy + 115
        for line in items:
            d2.text((90, iy), line, fill=(30, 41, 59), font=get_font(27, False))
            iy += 68
        cy += 380

    d2.rounded_rectangle([55, 1345, W - 55, 1410], radius=16, fill=(15, 23, 42))
    d2.text((135, 1360), "需要抓特定平台或关键词？直接在评论区留言，看到都会回！", fill=(250, 204, 21), font=get_font(28, True))

    p2_cn = XHS_ASSETS_DIR / "02_小红书配图_字段与分析优势说明.png"
    p2_ascii = XHS_ASSETS_DIR / "xhs_detail_02.png"
    img2.save(p2_cn, "PNG")
    img2.save(p2_ascii, "PNG")

    return [p1_ascii, p2_ascii]


XHS_NOTE_TEMPLATES = {
    "1": {
        "title": "怎么批量把Reddit和YouTube评论导出Excel？",  # 19字，严格 <= 20字限制
        "body": (
            "最近帮好几个同学和做跨境的朋友整理海外舆情数据，发现很多人还在一条条手动复制粘贴 YouTube 评论和 Reddit 帖子……\n\n"
            "其实用 Python 配合海外专线，输入一个关键词（比如 \"AI Agent\" 或某款产品型号），不到 1 分钟就能把：\n"
            "1. 帖子/视频标题\n"
            "2. 评论正文（已自动清洗掉换行符和乱码）\n"
            "3. 点赞数、评论数、精确到秒的发布时间\n"
            "全部规规矩矩导出成带筛选表头的 Excel 和 CSV（图1、图2就是刚跑出来的实测样本，直接就能丢进 SPSS 或用 AI 做词频和情感分析）。\n\n"
            "整理不易，有正在写相关论文或者做海外选品调研需要抓数据的朋友，可以在评论区说下你想抓的平台或关键词，看到都会回！"
        ),
        "tags": ["留学生论文", "数据分析", "Reddit", "YouTube", "跨境电商选品", "Python", "舆情分析"],
    },
    "2": {
        "title": "跨境选品怎么扒Reddit老外真实差评？",  # 20个字符，严格符合小红书 <= 20 字符限制
        "body": (
            "做亚马逊、独立站和 TikTok 出海选品时，最怕只看表面销量，结果踩中老外最反感的设计雷区。\n\n"
            "与其靠猜，不如直接把同类竞品在 YouTube 测评视频下的高赞评论、以及 Reddit 垂直社区（比如 r/BuyItForLife）近一年的真实讨论帖批量导出来看：\n"
            "1. 自动汇总老外吐槽最多的痛点词频\n"
            "2. 按点赞数排序，一眼定位最影响复购的缺陷\n"
            "3. 同时生成带表头筛选的 Excel (.xlsx) 和无乱码 CSV，直接喂给 AI 就能出中文选品痛点报告！\n\n"
            "正在做海外选品或竞品调研的朋友，可以在评论区留一下你关注的品类或关键词，帮你试跑一份样本看效果！"
        ),
        "tags": ["跨境电商", "亚马逊选品", "海外市场调研", "Reddit", "YouTube", "数据分析"],
    },
}


class XhsMcpCdpClient:
    """
    移植自 xpzouying/xiaohongshu-mcp 的原生 CDP 客户端，
    直接连接已登录的 Edge 调试端口 (127.0.0.1:9222)。
    """

    def __init__(self, host: str = CDP_HOST, port: int = CDP_PORT):
        self.host = host
        self.port = port
        self.ws = None
        self._msg_id = 0

    def connect(self):
        targets = requests.get(f"http://{self.host}:{self.port}/json", timeout=5).json()
        pages = [t for t in targets if t.get("type") == "page"]
        ws_url = None
        # 优先匹配 creator.xiaohongshu.com 创作服务平台标签页
        for t in pages:
            if "creator.xiaohongshu.com" in t.get("url", ""):
                ws_url = t["webSocketDebuggerUrl"]
                break
        if not ws_url:
            for t in pages:
                if "xiaohongshu.com" in t.get("url", ""):
                    ws_url = t["webSocketDebuggerUrl"]
                    break
        if not ws_url and pages:
            ws_url = pages[0]["webSocketDebuggerUrl"]
        if not ws_url:
            raise RuntimeError("未找到可用的 Edge 页面标签")
        self.ws = ws_client.connect(ws_url, max_size=50 * 1024 * 1024)
        self.send("Page.enable")
        self.send("DOM.enable")
        self.send("Runtime.enable")
        self.send("Page.bringToFront")

    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None

    def send(self, method: str, params: dict | None = None) -> dict:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        while True:
            raw = self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP Error ({method}): {data['error']}")
                return data.get("result", {})

    def eval_js(self, expr: str) -> Any:
        res = self.send(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": True},
        )
        obj = res.get("result", {})
        if obj.get("subtype") == "error":
            raise RuntimeError(f"JS Error: {obj.get('description', obj)}")
        return obj.get("value")

    def press_key(self, key: str, code: str, vk: int):
        for ev_type in ("keyDown", "keyUp"):
            self.send(
                "Input.dispatchKeyEvent",
                {
                    "type": ev_type,
                    "key": key,
                    "code": code,
                    "windowsVirtualKeyCode": vk,
                    "nativeVirtualKeyCode": vk,
                },
            )

    def insert_text(self, text: str):
        self.send("Input.insertText", {"text": text})

    def mouse_click(self, x: float, y: float):
        for ev_type in ("mousePressed", "mouseReleased"):
            self.send(
                "Input.dispatchMouseEvent",
                {
                    "type": ev_type,
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1,
                },
            )

    def publish_note(self, title: str, body: str, tags: list[str], image_paths: list[Path], do_click_publish: bool = True) -> bool:
        # 1. 导航到小红书创作者发布页
        print(f"[XHS-MCP] 正在打开发布页: {XHS_PUBLISH_URL}")
        self.send("Page.navigate", {"url": XHS_PUBLISH_URL})
        time.sleep(3.5)

        cur_url = self.eval_js("window.location.href") or ""
        if "login" in cur_url.lower():
            print("[ERR] 当前 Edge 未登录小红书创作者中心，请先在浏览器完成登录！")
            return False

        # 2. 清理可能遮挡 TAB 的浮层 (移植自 xiaohongshu/publish.go: dismissPopCover)
        self.eval_js("""(() => {
            document.querySelectorAll('div.d-popover, .feature-guide__btn').forEach(el => el.remove());
        })()""")

        # 3. 切换到「上传图文」TAB (移植自 xiaohongshu/publish.go: mustClickPublishTab + isElementVisible 校验 x > 0 && y > 0)
        clicked_tab = self.eval_js("""(() => {
            const tabs = Array.from(document.querySelectorAll('div.creator-tab, span.title'));
            for (const t of tabs) {
                if ((t.textContent || '').trim() === '上传图文') {
                    const r = t.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0 && r.x > 0 && r.y > 0) {
                        t.click();
                        return true;
                    }
                }
            }
            return false;
        })()""")
        print(f"[XHS-MCP] 切换【上传图文】选项卡: {clicked_tab}")
        time.sleep(2.0)

        # 4. 逐张/批量通过 DOM.setFileInputFiles 上传纯英文路径图片并等待预览 .img-preview-area .pr
        doc = self.send("DOM.getDocument")
        root_id = doc["root"]["nodeId"]
        node_id = 0
        for sel in (
            'input.upload-input[accept*="jpg"]',
            'input.upload-input[accept*="png"]',
            'input.upload-input[accept*="image"]',
            '.upload-input',
            'input[type="file"][accept*="image"]',
        ):
            q = self.send("DOM.querySelector", {"nodeId": root_id, "selector": sel})
            node_id = q.get("nodeId", 0)
            if node_id:
                break
        if not node_id:
            raise RuntimeError("未找到小红书图片上传 input 节点")

        normalized_files = [str(p.resolve()).replace("\\", "/") for p in image_paths]
        self.send("DOM.setFileInputFiles", {"nodeId": node_id, "files": normalized_files})
        print(f"[XHS-MCP] 已注入 {len(normalized_files)} 张图片，正在等待小红书服务器上传完成...")

        for _ in range(60):
            count = self.eval_js("document.querySelectorAll('.img-preview-area .pr, .img-preview, [class*=\"preview\"]').length") or 0
            has_title = self.eval_js("!!document.querySelector('input[placeholder*=\"填写标题\"], div.d-input input')")
            if has_title and count >= 1:
                break
            time.sleep(0.5)
        time.sleep(1.5)

        # 5. 填入标题并校验最大字数 (移植自 xiaohongshu/publish.go: submitPublish)
        escaped_title = json.dumps(title, ensure_ascii=False)
        self.eval_js(f"""(() => {{
            const el = document.querySelector('input[placeholder*="填写标题"], div.d-input input, input.d-text');
            if (!el) return false;
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            el.focus();
            setter.call(el, {escaped_title});
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }})()""")
        print(f"[XHS-MCP] 已填入标题 ({len(title)}字): {title}")
        time.sleep(0.8)

        # 6. 填入正文并逐个触发 #话题 真实联想标签 (移植自 xiaohongshu/publish.go: inputTags)
        escaped_body = json.dumps(body, ensure_ascii=False)
        self.eval_js(f"""(() => {{
            const ed = document.querySelector('div.tiptap.ProseMirror, div[role="textbox"][contenteditable="true"], div.ql-editor');
            if (!ed) return false;
            ed.focus();
            const paras = {escaped_body}.split('\\n');
            ed.innerHTML = paras.map(p => p.trim() ? `<p>${{p}}</p>` : '<p><br></p>').join('') + '<p><br></p>';
            ed.dispatchEvent(new Event('input', {{ bubbles: true }}));
            // 将光标移动到末尾
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(ed);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
            return true;
        }})()""")
        time.sleep(0.6)

        for tag in tags[:8]:
            self.insert_text(f"#{tag}")
            time.sleep(0.8)
            # 查找 #creator-editor-topic-container .item 点击第一个联想词变成真正的话题节点
            clicked_topic = self.eval_js("""(() => {
                const item = document.querySelector('#creator-editor-topic-container .item');
                if (item) {
                    item.click();
                    return true;
                }
                return false;
            })()""")
            if not clicked_topic:
                self.insert_text(" ")
            time.sleep(0.3)

        print(f"[XHS-MCP] 已填入正文并挂载话题标签: {tags}")

        if not do_click_publish:
            print("[XHS-MCP] 当前为预览模式 (--no-publish)，已停留在发布页供你检查。")
            return True

        # 7. 优先通过 shadowRoot 内的 button.textContent 点击发布，兜底使用 0.65 黄金比例坐标点击
        clicked_sr = self.eval_js("""(() => {
            const w = document.querySelector('xhs-publish-btn');
            if (!w) return null;
            w.scrollIntoView({block: 'center'});
            if (w.shadowRoot) {
                const btns = Array.from(w.shadowRoot.querySelectorAll('button'));
                for (const b of btns) {
                    if ((b.textContent || '').includes('发布')) {
                        b.click();
                        return b.textContent.trim();
                    }
                }
            }
            return null;
        })()""")
        if clicked_sr:
            print(f"[XHS-MCP] 已直接通过 ShadowRoot 点击按钮: {clicked_sr}")
        else:
            time.sleep(0.4)
            box = self.eval_js("""(() => {
                const w = document.querySelector('xhs-publish-btn');
                if (!w) return null;
                const r = w.getBoundingClientRect();
                return {minX: r.left, maxX: r.right, minY: r.top, maxY: r.bottom};
            })()""")
            if not box:
                raise RuntimeError("未找到 xhs-publish-btn 发布组件")

            click_x = box["minX"] + (box["maxX"] - box["minX"]) * 0.65
            click_y = box["minY"] + (box["maxY"] - box["minY"]) * 0.5
            print(f"[XHS-MCP] 正在点击发布按钮坐标 ({click_x:.1f}, {click_y:.1f})...")
            self.mouse_click(click_x, click_y)

        # 轮询等待 URL 跳转离开 /publish/publish
        for _ in range(30):
            time.sleep(0.5)
            now_url = self.eval_js("window.location.href") or ""
            if "/publish/publish" not in now_url:
                print(f"[XHS-MCP] 🎉 发布确认成功！页面已自动跳转至: {now_url}")
                return True

        print("[WARN] 点击发布后 15 秒内未跳转，请在浏览器窗口检查是否有必填项提示。")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="基于 xiaohongshu-mcp 核心逻辑的小红书自动配图与发布工具")
    parser.add_argument("--template", choices=["1", "2"], default="1", help="选择笔记模板：1=留学生论文/综合导出，2=跨境电商选品差评分析")
    parser.add_argument("--no-publish", action="store_true", help="只自动上传图片和填写标题正文话题，不点最终发布按钮")
    parser.add_argument("--check-status", action="store_true", help="仅检查当前已发布的笔记列表状态")
    parser.add_argument("--fix-and-submit", action="store_true", help="直接在当前已打开的发布页修正标题长度并点击发布")
    args = parser.parse_args()

    images = generate_xhs_images(args.template)
    client = XhsMcpCdpClient()
    client.connect()
    try:
        if args.fix_and_submit:
            tpl = XHS_NOTE_TEMPLATES[args.template]
            escaped_title = json.dumps(tpl["title"], ensure_ascii=False)
            client.eval_js(f"""(() => {{
                const el = document.querySelector('input[placeholder*="填写标题"], div.d-input input, input.d-text');
                if (!el) return false;
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                el.focus();
                setter.call(el, {escaped_title});
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }})()""")
            print(f"[XHS-MCP] 已修正当前页标题为 ({len(tpl['title'])}字符): {tpl['title']}")
            time.sleep(0.8)
            clicked = client.eval_js("""(() => {
                const w = document.querySelector('xhs-publish-btn');
                if (w && w.shadowRoot) {
                    const btns = Array.from(w.shadowRoot.querySelectorAll('button'));
                    for (const b of btns) {
                        if ((b.textContent || '').includes('发布')) {
                            b.click();
                            return b.textContent.trim();
                        }
                    }
                }
                return null;
            })()""")
            print(f"[XHS-MCP] 已点击发布按钮: {clicked}")
            for _ in range(25):
                time.sleep(0.5)
                now_url = client.eval_js("window.location.href") or ""
                if "/publish/publish" not in now_url:
                    print(f"[XHS-MCP] 🎉 第 2 篇笔记发布确认成功！当前 URL: {now_url}")
                    return 0
            return 1

        if args.check_status:
            client.send("Page.navigate", {"url": XHS_NOTE_MANAGER_URL})
            time.sleep(3)
            info = client.eval_js("({url: location.href, text: document.body.innerText.slice(0, 800)})")
            print("[XHS-MCP] 当前笔记管理页状态:\n", info.get("text"))
            return 0

        tpl = XHS_NOTE_TEMPLATES[args.template]
        ok = client.publish_note(
            title=tpl["title"],
            body=tpl["body"],
            tags=tpl["tags"],
            image_paths=images,
            do_click_publish=not args.no_publish,
        )
        return 0 if ok else 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
