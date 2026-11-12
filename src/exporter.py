import csv
import os
import re
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


MASK_SUFFIX = "...[验货预览，完整版无遮挡]"
LONG_TEXT_KEYS = {"评论内容", "正文内容", "内容摘要", "标题", "视频标题", "帖子标题", "正文", "text", "content", "title"}


def mask_preview_text(text: str) -> str:
    """Truncate long text fields for the 20-row client preview file."""
    if not text:
        return ""
    s = str(text).strip()
    if len(s) <= 28:
        return s
    keep_len = max(18, int(len(s) * 0.55))
    return s[:keep_len] + MASK_SUFFIX


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', "_", str(name).strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:45].strip("_") or "scrape_data"


def _write_styled_workbook(
    filepath: str,
    records: list[dict],
    sheet_title: str,
    is_preview: bool = False,
    total_count: int = 0,
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]

    if not records:
        ws.append(["暂无数据"])
        wb.save(filepath)
        return

    headers = list(records[0].keys())
    ws.append(headers)

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Microsoft YaHei", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Microsoft YaHei", size=10)
    zebra_fill = PatternFill(start_color="F5F8FC", end_color="F5F8FC", fill_type="solid")
    thin_side = Side(border_style="thin", color="D9D9D9")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[1].height = 26

    for row_offset, row_data in enumerate(records, start=2):
        row_values = []
        for idx, h in enumerate(headers):
            val = row_data.get(h, "")
            # Mask long text on rows 6..20 in preview mode so buyer sees full first 5 rows + partial 6..20
            if is_preview and row_offset > 6 and (h in LONG_TEXT_KEYS or (isinstance(val, str) and len(val) > 35)):
                val = mask_preview_text(str(val))
            row_values.append(val)
        ws.append(row_values)

        ws.row_dimensions[row_offset].height = 21
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=row_offset, column=col_idx)
            c.font = body_font
            c.border = border
            if row_offset % 2 == 1:
                c.fill = zebra_fill
            c.alignment = Alignment(vertical="center", wrap_text=False)

    if is_preview:
        notice_row = len(records) + 2
        notice_text = (
            f"【验货说明】本次任务共成功采集 {total_count} 条完整数据。"
            f"以上为前 {len(records)} 条真实样本预览（第 6 条起长文本已做预览截断），确认字段无误后付款即可发送完整无遮挡 Excel + CSV 原文件。"
        )
        ws.cell(row=notice_row, column=1, value=notice_text)
        ws.merge_cells(start_row=notice_row, start_column=1, end_row=notice_row, end_column=max(1, len(headers)))
        notice_cell = ws.cell(row=notice_row, column=1)
        notice_cell.font = Font(name="Microsoft YaHei", size=10, bold=True, color="C00000")
        notice_cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        notice_cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[notice_row].height = 28

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(records) + 1}"

    # Auto-fit column widths
    for col_idx, h in enumerate(headers, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(str(h)) * 2
        for r_idx in range(2, len(records) + 2):
            val_str = str(ws.cell(row=r_idx, column=col_idx).value or "")
            # Count CJK characters as width 2
            visual_len = sum(2 if ord(ch) > 127 else 1 for ch in val_str)
            if visual_len > max_len:
                max_len = visual_len
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 55)

    wb.save(filepath)


def export_deliverables(
    records: list[dict],
    task_name: str,
    output_dir: str = "",
    preview_limit: int = 20,
) -> dict[str, str]:
    """Export Preview Excel (first 20 rows), Full Excel, and Full UTF-8-SIG CSV."""
    if not output_dir:
        output_dir = str( Path(__file__).resolve().parent.parent / "deliverables" )
    os.makedirs(output_dir, exist_ok=True)

    safe_name = _sanitize_filename(task_name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    total = len(records)
    preview_rows = records[:preview_limit]

    preview_xlsx = os.path.join(output_dir, f"[验货预览-前{len(preview_rows)}条]_{safe_name}_{ts}.xlsx")
    full_xlsx = os.path.join(output_dir, f"[完整交付-共{total}条]_{safe_name}_{ts}.xlsx")
    full_csv = os.path.join(output_dir, f"[完整交付-共{total}条]_{safe_name}_{ts}.csv")

    _write_styled_workbook(
        filepath=preview_xlsx,
        records=preview_rows,
        sheet_title="验货预览样本",
        is_preview=True,
        total_count=total,
    )
    _write_styled_workbook(
        filepath=full_xlsx,
        records=records,
        sheet_title="完整采集数据",
        is_preview=False,
        total_count=total,
    )

    if records:
        headers = list(records[0].keys())
        with open(full_csv, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)
    else:
        Path(full_csv).write_text("", encoding="utf-8-sig")

    return {
        "preview_xlsx": preview_xlsx,
        "full_xlsx": full_xlsx,
        "full_csv": full_csv,
    }
