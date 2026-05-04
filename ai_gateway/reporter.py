# ai_gateway/reporter.py
"""
基于当天处理的记录，生成日报/周报并写入飞书文档。
"""
import logging
from datetime import datetime, timezone
from typing import List

from ai_gateway.processor import ProcessResult

logger = logging.getLogger(__name__)


def format_daily_report(results: List[ProcessResult], date: datetime) -> str:
    """生成日报 Markdown 内容。"""
    lines = [
        f"# AI 网关日报 — {date.strftime('%Y-%m-%d')}",
        "",
        f"今日处理 **{len(results)}** 条新记录。",
        "",
    ]
    if results:
        lines.append("## 今日记录")
        for r in results:
            tags_str = "、".join(r.tags[:5])
            lines.append(f"### {r.title}")
            lines.append(f"- **客户：** {r.client}")
            lines.append(f"- **行业：** {r.industry}")
            lines.append(f"- **场景类型：** {r.scene_type}")
            lines.append(f"- **标签：** {tags_str}")
            lines.append(f"- **摘要：** {r.summary}")
            lines.append("")
    return "\n".join(lines)


def format_weekly_report(all_results: List[ProcessResult], date: datetime) -> str:
    """生成周报 Markdown 内容。"""
    week_num = date.isocalendar().week
    lines = [
        f"# AI 网关周报 — 第 {week_num} 周",
        "",
        f"本周共处理 **{len(all_results)}** 条记录。",
        "",
    ]
    by_type: dict[str, list] = {}
    for r in all_results:
        by_type.setdefault(r.scene_type, []).append(r)
    if by_type:
        lines.append("## 场景分布")
        for scene_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            lines.append(f"- **{scene_type}：** {len(items)} 条")
        lines.append("")
    return "\n".join(lines)
