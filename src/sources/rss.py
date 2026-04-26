import feedparser
import requests
from datetime import datetime, timezone
from src.sources import NewsItem

SOURCE_FEEDS = [
    {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "name": "TechCrunch AI",
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "name": "Ars Technica",
    },
    {
        "url": "https://venturebeat.com/category/ai/feed/",
        "name": "VentureBeat AI",
    },
]


def fetch(days_back: int = 7) -> list[NewsItem]:
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    items = []

    for feed_cfg in SOURCE_FEEDS:
        try:
            resp = requests.get(feed_cfg["url"], timeout=20)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            for entry in parsed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue
                title = entry.get("title", "").strip()
                if not title:
                    continue
                items.append(NewsItem(
                    title=title,
                    url=entry.get("link", ""),
                    description="",
                    published_at=published,
                    source_name=feed_cfg["name"],
                ))
        except Exception as e:
            print(f"[RSS] {feed_cfg['name']} failed: {e}")
            continue

    print(f"[RSS] collected {len(items)} items from {len(SOURCE_FEEDS)} feeds")
    return items


def _parse_date(entry) -> datetime | None:
    from time import mktime
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        return datetime.fromtimestamp(mktime(published), tz=timezone.utc)
    return None
