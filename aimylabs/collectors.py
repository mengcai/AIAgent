from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, List, Optional

import feedparser
import tldextract


@dataclass
class Article:
    title: str
    url: str
    published: Optional[dt.datetime]
    summary: Optional[str] = None
    source: Optional[str] = None


def _parse_time(entry) -> Optional[dt.datetime]:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return dt.datetime.fromtimestamp(
                dt.datetime(*entry.published_parsed[:6]).timestamp(), tz=dt.timezone.utc
            )
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return dt.datetime.fromtimestamp(
                dt.datetime(*entry.updated_parsed[:6]).timestamp(), tz=dt.timezone.utc
            )
    except Exception:
        return None
    return None


def _domain(url: str) -> str:
    ext = tldextract.extract(url)
    if ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return ext.domain


def collect_rss_articles(
    feeds: Iterable[str],
    min_recency_hours: int,
    allowlist_domains: Optional[Iterable[str]] = None,
) -> List[Article]:
    now = dt.datetime.now(tz=dt.timezone.utc)
    min_age = dt.timedelta(hours=min_recency_hours)
    allow = set(d.lower() for d in (allowlist_domains or []))

    collected: List[Article] = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            continue
        for entry in parsed.entries:
            link = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not link or not title:
                continue

            pub_dt = _parse_time(entry)
            if pub_dt is not None:
                age = now - pub_dt
                if age > min_age:
                    continue

            domain = _domain(link).lower()
            if allow and domain not in allow:
                continue

            collected.append(
                Article(
                    title=title.strip(),
                    url=link.strip(),
                    published=pub_dt,
                    summary=getattr(entry, "summary", None),
                    source=parsed.feed.get("title", None) if getattr(parsed, "feed", None) else None,
                )
            )

    # Deduplicate by URL
    unique_by_url = {}
    for a in collected:
        if a.url not in unique_by_url:
            unique_by_url[a.url] = a
    return list(unique_by_url.values())


