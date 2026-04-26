from datetime import datetime, timezone, timedelta


def build_html(digest: dict) -> str:
    beijing = datetime.now(timezone.utc) + timedelta(hours=8)
    date_str = beijing.strftime("%Y 年 %m 月 %d 日")
    overview = digest.get("overview", "")
    categories = digest.get("categories", [])

    cat_blocks = "\n".join(_build_category(c) for c in categories)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:20px 0">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08)">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px 40px;text-align:center">
<h1 style="color:#ffffff;margin:0 0 4px;font-size:24px">AI 技术洞察周报</h1>
<p style="color:#a0aec0;margin:0;font-size:14px">{date_str}</p>
</td></tr>

<!-- Overview -->
<tr><td style="padding:24px 40px 8px">
<h2 style="font-size:16px;color:#2d3748;margin:0 0 8px;padding-bottom:8px;border-bottom:2px solid #4299e1">📌 本周概览</h2>
<p style="font-size:14px;color:#4a5568;line-height:1.7;margin:0">{overview}</p>
</td></tr>

{cat_blocks}

<!-- Footer -->
<tr><td style="padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center">
<p style="font-size:12px;color:#a0aec0;margin:0 0 4px">AI 技术洞察周报 · 自动生成</p>
<p style="font-size:12px;color:#a0aec0;margin:0">数据来源: Hacker News · arXiv · NewsAPI · RSS Feeds</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def _build_category(cat: dict) -> str:
    name = cat.get("name", "")
    items_html = "\n".join(_build_item(item) for item in cat.get("items", []))
    if not items_html:
        return ""

    return f"""<tr><td style="padding:20px 40px 8px">
<h2 style="font-size:16px;color:#2d3748;margin:0 0 12px;padding-bottom:8px;border-bottom:2px solid #e2e8f0">{name}</h2>
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
<td style="padding:8px 0;border-bottom:1px solid #f0f0f0">
<a href="{url}" style="font-size:14px;color:#2b6cb0;text-decoration:none;font-weight:500;display:block;margin-bottom:2px">{title}</a>
<p style="font-size:13px;color:#718096;margin:2px 0 0;line-height:1.5">{summary}
<br><span style="font-size:11px;color:#a0aec0">来源: {source}</span></p>
</td>
</tr>"""
