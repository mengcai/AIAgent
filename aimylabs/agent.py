from __future__ import annotations

import asyncio
from typing import List

from .collectors import collect_rss_articles
from .config import Config
from .publisher import create_x_client, publish_tweet, publish_thread, publish_long_post, publish_with_image
from .storage import ensure_db, mark_posted, was_posted
from .summarizer import summarize_to_tweet
from .content_strategy import determine_content_strategy
from .image_generator import generate_news_image


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
        if articles:
            print(f"Sample articles: {[a.title[:50] + '...' for a in articles[:3]]}")
        if new_articles:
            print(f"New articles to process: {[a.title[:50] + '...' for a in new_articles[:3]]}")
        else:
            print("No new articles to post (all may have been posted before)")

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

        # Process articles with content strategy
        sem = asyncio.Semaphore(4)

        async def process_article(a):
            async with sem:  # type: ignore[attr-defined]
                # Determine content strategy
                strategy = determine_content_strategy(
                    title=a.title,
                    content=a.summary or "",
                    url=a.url,
                    tone=cfg.style.tone,
                    config_strategy=cfg.style.content_strategy,
                    max_length=cfg.app.max_post_length if cfg.app.use_premium_features else 280,
                    enable_threads=cfg.app.enable_threads,
                    enable_images=cfg.app.enable_images
                )
                
                # Generate content based on strategy
                if strategy.content_type == "image" and cfg.app.enable_images and cfg.openai_api_key:
                    # Generate image
                    image_result = await generate_news_image(
                        title=a.title,
                        content=a.summary or "",
                        tone=cfg.style.tone,
                        openai_api_key=cfg.openai_api_key,
                        openai_image_model=cfg.openai_image_model
                    )
                    strategy.use_image = image_result.success
                    if image_result.success:
                        strategy.image_prompt = image_result.image_data
                
                return a, strategy

        pairs = await asyncio.gather(*(process_article(a) for a in new_articles))

        posted_urls: List[str] = []
        posted_count: int = 0
        for article, strategy in pairs:
            if not strategy.content_parts:
                print(f"Skip (no content): {article.title} — {article.url}")
                continue
            if posted_count >= self.cfg.app.max_daily_posts:
                break
            
            # Post based on content strategy
            if strategy.content_type == "thread":
                result = publish_thread(api, strategy.content_parts, dry_run=cfg.app.dry_run)
            elif strategy.content_type == "long":
                result = publish_long_post(api, strategy.content_parts[0], dry_run=cfg.app.dry_run)
            elif strategy.content_type == "image" and strategy.use_image and strategy.image_prompt:
                result = publish_with_image(api, strategy.content_parts[0], strategy.image_prompt, dry_run=cfg.app.dry_run)
            else:
                # Default to short tweet
                result = publish_tweet(api, strategy.content_parts[0], dry_run=cfg.app.dry_run)
            
            if result.ok:
                if not cfg.app.dry_run:
                    mark_posted(cfg.db_path, article.url, result.id)
                posted_urls.append(article.url)
                posted_count += 1
                
                # Log posting details
                if strategy.content_type == "thread":
                    print(f"Posted thread ({len(strategy.content_parts)} parts): {article.title} — {article.url}")
                elif strategy.content_type == "long":
                    print(f"Posted long-form: {article.title} — {article.url}")
                elif strategy.content_type == "image":
                    print(f"Posted with image: {article.title} — {article.url}")
                else:
                    print(f"Posted: {article.title} — {article.url}")
            else:
                print(f"Failed to post: {article.title} — {article.url} | error={result.error}")

        return posted_urls


