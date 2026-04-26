from __future__ import annotations

import requests
from datetime import datetime, timedelta, timezone
from src.sources import NewsItem


def fetch(api_key: str, days_back: int = 7) -> list[NewsItem]:
    if not api_key:
        print("[NewsAPI] no API key configured, skipping")
        return []

    since = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    queries = [
        "artificial intelligence",
        "large language model",
        "AI safety",
        "machine learning",
    ]

    items = []
    for query in queries:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "from": since,
                    "sortBy": "popularity",
                    "language": "en",
                    "pageSize": 30,
                    "apiKey": api_key,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "ok":
                continue
            for article in data.get("articles", []):
                title = (article.get("title") or "").strip()
                if not title:
                    continue
                items.append(NewsItem(
                    title=title,
                    url=article.get("url", ""),
                    description=(article.get("description") or "")[:500],
                    published_at=_parse_date(article.get("publishedAt")),
                    source_name=article.get("source", {}).get("name", "NewsAPI"),
                ))
        except requests.RequestException as e:
            print(f"[NewsAPI] query '{query}' failed: {e}")

    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in items:
        if item.url not in seen:
            seen.add(item.url)
            deduped.append(item)

    print(f"[NewsAPI] collected {len(deduped)} items (from {len(items)} raw)")
    return deduped


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
