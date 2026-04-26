from __future__ import annotations

import feedparser
from datetime import datetime, timedelta, timezone
from src.sources import NewsItem

CATEGORIES = [
    "cs.AI",
    "cs.CL",
    "cs.LG",
    "cs.CV",
    "cs.MA",
    "cs.RO",
    "stat.ML",
]


def fetch(days_back: int = 7, max_results: int = 80) -> list[NewsItem]:
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    query = "+OR+".join(f"cat:{c}" for c in CATEGORIES)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )

    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = _parse_date(entry)
            if published and published < since:
                continue
            title = entry.get("title", "").replace("\n", " ").strip()
            summary = entry.get("summary", "")[:500].replace("\n", " ")
            link = entry.get("link", "")
            items.append(NewsItem(
                title=title,
                url=link,
                description=summary,
                published_at=published,
                source_name="arXiv",
                category_hint=_guess_category(entry.get("tags", [])),
            ))
    except Exception as e:
        print(f"[arXiv] fetch failed: {e}")

    print(f"[arXiv] collected {len(items)} papers")
    return items


def _parse_date(entry) -> datetime | None:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        from time import mktime
        from datetime import timezone
        return datetime.fromtimestamp(mktime(published), tz=timezone.utc)
    return None


def _guess_category(tags: list) -> str:
    for tag in tags:
        term = tag.get("term", "")
        if term.startswith("cs.CL"):
            return "新模型发布"
        if term.startswith("cs.CV"):
            return "新模型发布"
        if term.startswith("cs.AI"):
            return "重磅方案"
        if term.startswith("cs.LG") or term.startswith("stat.ML"):
            return "重磅方案"
    return ""
