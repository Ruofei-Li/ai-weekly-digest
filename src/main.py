#!/usr/bin/env python3
"""
AI Weekly Digest — collect, summarize, and email AI news every Monday.
"""

import sys
import os

# Allow running as `python src/main.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.config import Config
from src.sources import hackernews, arxiv, rss, newsapi
from src.llm.claude import refine
from src.mailer.template import build_html
from src.mailer.sender import send


def collect_news(cfg: Config) -> list:
    """Collect news from all configured sources."""
    all_items = []

    # Hacker News (no API key needed)
    all_items.extend(hackernews.fetch(days_back=cfg.days_back))

    # arXiv (free)
    all_items.extend(arxiv.fetch(days_back=cfg.days_back))

    # RSS feeds (free)
    all_items.extend(rss.fetch(days_back=cfg.days_back))

    # NewsAPI (optional, needs key)
    all_items.extend(newsapi.fetch(api_key=cfg.newsapi_api_key, days_back=cfg.days_back))

    # Limit total items to avoid excessive Claude API usage
    if len(all_items) > cfg.max_total_news:
        print(f"[Main] trimming from {len(all_items)} to {cfg.max_total_news}")
        all_items = all_items[: cfg.max_total_news]

    print(f"[Main] total news items collected: {len(all_items)}")
    return all_items


def main():
    cfg = Config.from_env()

    # Diagnostic: print non-sensitive config
    print(f"[Main] claude_model={cfg.claude_model}")
    print(f"[Main] smtp_host={cfg.smtp_host} smtp_port={cfg.smtp_port}")
    print(f"[Main] email_from={cfg.email_from} email_to={cfg.email_to}")
    print(f"[Main] anthropic_base_url={cfg.anthropic_base_url}")

    missing = []
    if not cfg.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not cfg.smtp_user or not cfg.smtp_password:
        missing.append("SMTP_USER / SMTP_PASSWORD")
    if not cfg.email_to:
        missing.append("EMAIL_TO")
    if missing:
        print(f"[Main] missing required config: {', '.join(missing)}")
        sys.exit(1)

    # Step 1: Collect news
    print("=" * 50)
    print("Step 1/3: Collecting news...")
    items = collect_news(cfg)

    if not items:
        print("[Main] no news collected, aborting")
        sys.exit(1)

    # Step 2: Refine with Claude
    print("Step 2/3: Refining with Claude...")
    digest = refine(cfg, items)

    # Step 3: Build and send email
    print("Step 3/3: Building and sending email...")
    from datetime import datetime, timezone, timedelta
    beijing = datetime.now(timezone.utc) + timedelta(hours=8)
    date_str = beijing.strftime("%Y-%m-%d")
    subject = f"AI 技术洞察周报 {date_str}"

    html = build_html(digest)
    send(cfg, subject, html)

    sections = digest.get("sections", [])
    columns_count = sum(len(s.get("columns", [])) for s in sections)
    print(f"[Main] Digest sent! Sections: {len(sections)}, Columns: {columns_count}")
    print("Done.")


if __name__ == "__main__":
    main()
