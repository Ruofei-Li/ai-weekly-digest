from datetime import datetime, timezone, timedelta

# 三号字 = 16pt
FONT_FAMILY = "'Microsoft YaHei', '微软雅黑', sans-serif"
FONT_LINK = "'Microsoft YaHei', '微软雅黑', sans-serif"
BASE = "16pt"
SMALL = "12pt"
TITLE = "18pt"
SECTION = "20pt"

BLUE = "#2b6cb0"
TEAL = "#285e61"
TEAL_ACCENT = "#2c7a7b"
TEAL_LIGHT = "#e6fffa"
DARK = "#1a1a2e"
BODY = "#2d3748"
LIGHT = "#a0aec0"
BG = "#f7fafc"
WHITE = "#ffffff"


def build_html(digest: dict) -> str:
    beijing = datetime.now(timezone.utc) + timedelta(hours=8)
    date_str = beijing.strftime("%Y 年 %m 月 %d 日")
    overview = digest.get("overview", "")
    sections = digest.get("sections", [])

    section_blocks = "\n".join(_build_section(s) for s in sections)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:{BG};font-family:{FONT_FAMILY};font-size:{BASE};color:{BODY};line-height:1.7">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:20px 0">
<tr><td align="center">
<table width="1290" cellpadding="0" cellspacing="0" style="background:{WHITE}">
<!-- ======== 头部 ======== -->
<tr><td bgcolor="{DARK}" style="padding:30px 44px;text-align:center;font-family:{FONT_FAMILY}">
<font face="{FONT_FAMILY}" style="font-size:26pt;color:{WHITE}"><b>AI 技术洞察周报</b></font><br>
<font face="{FONT_FAMILY}" style="font-size:11pt;color:{LIGHT}">{date_str}</font>
</td></tr>
<!-- ======== 概览 ======== -->
<tr><td style="padding:20px 44px 10px;font-family:{FONT_FAMILY}">
<font face="{FONT_FAMILY}" style="font-size:{TITLE};color:{BODY}"><b>📌 本周概览</b></font>
<hr style="border:0;border-top:2px solid #4299e1;margin:8px 0 12px">
<font face="{FONT_FAMILY}" style="font-size:{BASE};color:#4a5568;line-height:1.8">{overview}</font>
</td></tr>
{section_blocks}
<!-- ======== 底部 ======== -->
<tr><td style="padding:20px 44px;border-top:1px solid #e2e8f0;text-align:center;font-family:{FONT_FAMILY}">
<font face="{FONT_FAMILY}" style="font-size:{SMALL};color:{LIGHT}">AI 技术洞察周报 · 自动生成<br>数据来源: Hacker News · arXiv · NewsAPI · RSS Feeds</font>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _build_section(section: dict) -> str:
    name = section.get("name", "")
    columns = section.get("columns", [])

    if "安全" in name:
        header_bg = TEAL
        accent = TEAL_ACCENT
        light_bg = TEAL_LIGHT
    else:
        header_bg = BLUE
        accent = BLUE
        light_bg = "#ebf8ff"

    col_blocks = "\n".join(_build_column(c, accent, light_bg) for c in columns if c.get("items"))
    if not col_blocks:
        return ""

    return f"""<!-- 板块：{name} -->
<tr><td bgcolor="{header_bg}" style="padding:10px 44px;font-family:{FONT_FAMILY}">
<font face="{FONT_FAMILY}" style="font-size:{SECTION};color:{WHITE}"><b>{name}</b></font>
</td></tr>
{col_blocks}"""


def _build_column(col: dict, accent: str, light_bg: str) -> str:
    name = col.get("name", "")
    items = col.get("items", [])

    items_html = "\n".join(_build_item(i) for i in items)
    if not items_html:
        return ""

    return f"""<tr><td bgcolor="{light_bg}" style="padding:8px 44px 2px;font-family:{FONT_FAMILY}">
<font face="{FONT_FAMILY}" style="font-size:14pt;color:{accent}"><b>✦ {name}</b></font>
<hr style="border:0;border-top:1.5px solid {accent};margin:6px 0 8px">
</td></tr>
<tr><td style="padding:0 44px;font-family:{FONT_FAMILY}">
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
<td style="padding:10px 0;border-bottom:1px solid #edf2f7;font-family:{FONT_FAMILY}">
<a href="{url}" style="font-size:{BASE};color:{BLUE};font-weight:600;text-decoration:none;font-family:{FONT_FAMILY}">{title}</a><br>
<font face="{FONT_FAMILY}" style="font-size:{BASE};color:#4a5568;line-height:1.8">{summary}</font><br>
<font face="{FONT_FAMILY}" style="font-size:{SMALL};color:{LIGHT}">来源: {source}</font>
</td>
</tr>"""
