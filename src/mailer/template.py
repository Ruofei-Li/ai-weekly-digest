from datetime import datetime, timezone, timedelta

# 板块配色
SECTION_COLORS = {
    "AI 科技资讯": {
        "accent": "#3182ce",
        "light": "#ebf8ff",
        "header_bg": "linear-gradient(135deg, #2b6cb0, #2c5282)",
    },
    "AI 安全技术洞察": {
        "accent": "#2c7a7b",
        "light": "#e6fffa",
        "header_bg": "linear-gradient(135deg, #285e61, #234e52)",
    },
}

FONT_FAMILY = "'Microsoft YaHei', '微软雅黑', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
BASE_SIZE = "14px"
TITLE_SIZE = "16px"
SECTION_TITLE_SIZE = "20px"
SMALL_SIZE = "12px"
COLOR_BODY = "#2d3748"
COLOR_MUTED = "#718096"
COLOR_LIGHT = "#a0aec0"
COLOR_BG = "#f7fafc"


def build_html(digest: dict) -> str:
    beijing = datetime.now(timezone.utc) + timedelta(hours=8)
    date_str = beijing.strftime("%Y 年 %m 月 %d 日")
    overview = digest.get("overview", "")
    sections = digest.get("sections", [])

    section_blocks = "\n".join(_build_section(s) for s in sections)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:{COLOR_BG};font-family:{FONT_FAMILY};font-size:{BASE_SIZE};color:{COLOR_BODY};line-height:1.7">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{COLOR_BG};padding:24px 0">
<tr><td align="center">
<table width="660" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06)">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:36px 44px;text-align:center">
<h1 style="color:#ffffff;margin:0 0 6px;font-size:26px;font-weight:600">AI 技术洞察周报</h1>
<p style="color:#a0aec0;margin:0;font-size:14px">{date_str}</p>
</td></tr>

<!-- Overview -->
<tr><td style="padding:24px 44px 12px">
<h2 style="font-size:{TITLE_SIZE};color:{COLOR_BODY};margin:0 0 10px;padding-bottom:10px;border-bottom:2px solid #4299e1">📌 本周概览</h2>
<p style="font-size:{BASE_SIZE};color:#4a5568;line-height:1.8;margin:0">{overview}</p>
</td></tr>

{section_blocks}

<!-- Footer -->
<tr><td style="padding:24px 44px;border-top:1px solid #e2e8f0;text-align:center">
<p style="font-size:{SMALL_SIZE};color:{COLOR_LIGHT};margin:0 0 4px">AI 技术洞察周报 · 自动生成</p>
<p style="font-size:{SMALL_SIZE};color:{COLOR_LIGHT};margin:0">数据来源: Hacker News · arXiv · NewsAPI · RSS Feeds</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def _build_section(section: dict) -> str:
    name = section.get("name", "")
    colors = SECTION_COLORS.get(name, SECTION_COLORS["AI 科技资讯"])
    columns = section.get("columns", [])

    column_blocks = "\n".join(_build_column(c, colors["accent"]) for c in columns)
    if not column_blocks:
        return ""

    return f"""<tr><td style="padding:4px 0">
<!-- Section header -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin:0">
<tr><td style="background:{colors['header_bg']};padding:14px 44px">
<h2 style="font-size:{SECTION_TITLE_SIZE};color:#ffffff;margin:0;font-weight:600">{name}</h2>
</td></tr>
</table>
</td></tr>
{column_blocks}"""


def _build_column(column: dict, accent: str) -> str:
    name = column.get("name", "")
    items = column.get("items", [])

    items_html = "\n".join(_build_item(item) for item in items)
    if not items_html:
        return ""

    return f"""<tr><td style="padding:4px 44px">
<h3 style="font-size:{TITLE_SIZE};color:{accent};margin:16px 0 10px;padding-bottom:8px;border-bottom:2px solid {accent}">✦ {name}</h3>
<table width="100%" cellpadding="0" cellspacing="0">
{items_html}
</table>
</td></tr>"""


def _build_item(item: dict) -> str:
    title = item.get("title", "")
    summary = item.get("summary", "")
    url = item.get("url", "#")
    source = item.get("source", "")

    return f"""<tr>
<td style="padding:10px 0;border-bottom:1px solid #edf2f7">
<a href="{url}" style="font-size:{BASE_SIZE};color:#2b6cb0;text-decoration:none;font-weight:600;display:block;margin-bottom:4px">{title}</a>
<p style="font-size:{BASE_SIZE};color:#4a5568;margin:4px 0 2px;line-height:1.8">{summary}</p>
<span style="font-size:{SMALL_SIZE};color:{COLOR_LIGHT}">来源: {source}</span>
</td>
</tr>"""
