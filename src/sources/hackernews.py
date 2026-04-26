import requests
from datetime import datetime, timedelta, timezone
from src.sources import NewsItem


def fetch(days_back: int = 7) -> list[NewsItem]:
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    since_ts = int(since.timestamp())

    items = []

    # Query 1: keyword search sorted by points
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": "AI OR artificial intelligence OR LLM OR GPT OR Claude OR "
                         "Anthropic OR OpenAI OR Gemini OR Llama OR DeepSeek",
                "tags": "story",
                "numericFilters": f"points>10,created_at_i>={since_ts}",
                "hitsPerPage": 50,
            },
            timeout=30,
        )
        resp.raise_for_status()
        items.extend(_parse_hits(resp.json()["hits"]))
    except requests.RequestException as e:
        print(f"[HackerNews] keyword search failed: {e}")

    # Query 2: top stories (catch non-obvious AI keywords)
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "tags": "story",
                "numericFilters": f"points>50,created_at_i>={since_ts}",
                "hitsPerPage": 30,
            },
            timeout=30,
        )
        resp.raise_for_status()
        seen_urls = {item.url for item in items}
        for hit in resp.json()["hits"]:
            if hit.get("url") and hit["url"] not in seen_urls:
                items.append(_parse_hit(hit))
    except requests.RequestException as e:
        print(f"[HackerNews] top stories failed: {e}")

    print(f"[HackerNews] collected {len(items)} items")
    return items


def _parse_hits(hits: list) -> list[NewsItem]:
    return [_parse_hit(h) for h in hits if h.get("title")]


def _parse_hit(hit: dict) -> NewsItem:
    return NewsItem(
        title=hit["title"],
        url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
        description=(hit.get("story_text") or "")[:500],
        published_at=datetime.fromtimestamp(hit.get("created_at_i", 0), tz=timezone.utc),
        source_name="Hacker News",
    )
