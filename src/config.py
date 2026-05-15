import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # Claude API
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # NewsAPI (optional, free tier: 100 req/day)
    newsapi_api_key: str = ""

    # Email (SMTP)
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = ""

    # Digest settings
    days_back: int = 7
    max_news_per_category: int = 5
    max_total_news: int = 60

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", ""),
            newsapi_api_key=os.getenv("NEWSAPI_API_KEY", ""),
            smtp_host=os.getenv("SMTP_HOST", "smtp.qq.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            email_to=os.getenv("EMAIL_TO", ""),
        )
