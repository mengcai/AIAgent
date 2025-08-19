from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class AppConfig:
    timezone: str = "local"
    dry_run: bool = True
    max_daily_posts: int = 2
    post_times: List[str] = field(default_factory=lambda: ["09:00", "15:00"])


@dataclass
class StyleConfig:
    tone: str = "professional"  # professional|witty|hype
    use_emojis: bool = True
    default_hashtags: List[str] = field(default_factory=lambda: ["#AI", "#Web3"])


@dataclass
class SourcesConfig:
    min_recency_hours: int = 36
    rss_feeds: List[str] = field(default_factory=list)


@dataclass
class Config:
    app: AppConfig = field(default_factory=AppConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    sources: SourcesConfig = field(default_factory=SourcesConfig)
    allowlist_domains: List[str] = field(default_factory=list)

    openai_api_key: Optional[str] = None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    x_consumer_key: Optional[str] = None
    x_consumer_secret: Optional[str] = None
    x_access_token: Optional[str] = None
    x_access_token_secret: Optional[str] = None

    db_path: str = os.path.expanduser(os.getenv("AIMYLABS_DB_PATH", "~/.aimylabs/aimylabs.db"))


def load_config(path: str = "config.yaml") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    app_cfg = AppConfig(**raw.get("app", {}))
    style_cfg = StyleConfig(**raw.get("style", {}))
    sources_cfg = SourcesConfig(**raw.get("sources", {}))

    cfg = Config(
        app=app_cfg,
        style=style_cfg,
        sources=sources_cfg,
        allowlist_domains=raw.get("allowlist_domains", []),
    )

    cfg.openai_api_key = os.getenv("OPENAI_API_KEY")
    cfg.x_consumer_key = os.getenv("X_CONSUMER_KEY")
    cfg.x_consumer_secret = os.getenv("X_CONSUMER_SECRET")
    cfg.x_access_token = os.getenv("X_ACCESS_TOKEN")
    cfg.x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    return cfg

