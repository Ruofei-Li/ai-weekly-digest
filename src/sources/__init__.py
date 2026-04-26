from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    title: str
    url: str
    description: str
    published_at: Optional[datetime] = None
    source_name: str = ""
    category_hint: str = ""
