from __future__ import annotations

import asyncio
from typing import List

from .collectors import collect_rss_articles
from .config import Config
from .publisher import create_x_client, publish_tweet
from .storage import ensure_db, mark_posted, was_posted
from .summarizer import summarize_to_tweet


class AimylabsAgent:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        ensure_db(cfg.db_path)

    async def run_once(self) -> List[str]:
        cfg = self.cfg

        articles = collect_rss_articles(
            feeds=cfg.sources.rss_feeds,
            min_recency_hours=cfg.sources.min_recency_hours,
            allowlist_domains=cfg.allowlist_domains,
        )

        # Filter out already-posted
        new_articles = [a for a in articles if not was_posted(cfg.db_path, a.url)]

        print(f"Collected {len(articles)} articles; {len(new_articles)} new after dedupe")

        if not new_articles:
            return []

        # Prepare X client
        api = None
        if not cfg.app.dry_run:
            api = create_x_client(
                cfg.x_consumer_key or "",
                cfg.x_consumer_secret or "",
                cfg.x_access_token or "",
                cfg.x_access_token_secret or "",
            )

        # Summarize concurrently (limit concurrency to avoid rate limits)
        sem = asyncio.Semaphore(4)

        async def summarize_article(a):
            async with sem:  # type: ignore[attr-defined]
                text = await summarize_to_tweet(
                    url=a.url,
                    title=a.title,
                    tone=cfg.style.tone,
                    use_emojis=cfg.style.use_emojis,
                    hashtags=cfg.style.default_hashtags,
                    openai_api_key=cfg.openai_api_key or "",
                    model=cfg.openai_model,
                )
                return a, text

        pairs = await asyncio.gather(*(summarize_article(a) for a in new_articles))

        posted_urls: List[str] = []
        posted_count: int = 0
        for article, tweet_text in pairs:
            if not tweet_text:
                print(f"Skip (no summary): {article.title} — {article.url}")
                continue
            if posted_count >= self.cfg.app.max_daily_posts:
                break
            result = publish_tweet(api, tweet_text, dry_run=cfg.app.dry_run)  # type: ignore[arg-type]
            if result.ok:
                if not cfg.app.dry_run:
                    mark_posted(cfg.db_path, article.url, result.id)
                posted_urls.append(article.url)
                posted_count += 1
                print(f"Posted: {article.title} — {article.url}")
            else:
                print(f"Failed to post: {article.title} — {article.url} | error={result.error}")

        return posted_urls


