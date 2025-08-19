from __future__ import annotations

import re
from typing import List, Optional

import httpx
import trafilatura


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def extract_readable(url: str) -> Optional[str]:
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if not downloaded:
            return None
        result = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not result:
            return None
        return _clean_text(result)
    except Exception:
        return None


def _build_heuristic_tweet(*, url: str, title: Optional[str], content: str, hashtags: List[str], mentions: List[str]) -> str:
    base = (title or content or url).strip()
    suffix = f" {url}" if url else ""
    tag_str = " ".join([*hashtags, *mentions]).strip()
    add_str = f" {tag_str}" if tag_str else ""
    tweet = f"{base}{suffix}{add_str}"
    if len(tweet) <= 280:
        return tweet
    max_len = 280 - len(suffix) - len(add_str)
    if max_len <= 0:
        return (suffix + add_str).strip()[:280]
    trimmed = (base[: max_len - 1] + "…") if len(base) > max_len and max_len > 1 else base[:max_len]
    tweet = f"{trimmed}{suffix}{add_str}"
    return tweet[:280]


def build_prompt(content: str, title: Optional[str], tone: str, use_emojis: bool, hashtags: List[str], mentions: List[str]) -> str:
    hashtag_str = " ".join(hashtags) if hashtags else ""
    mention_str = " ".join(mentions) if mentions else ""
    emoji_hint = "Include 0-2 tasteful emojis." if use_emojis else "Do not use emojis."
    tone_hint = {
        "professional": "Use a concise, professional tone.",
        "witty": "Use a witty, clever tone without being cringey.",
        "hype": "Use a high-energy, hype tone but avoid spam.",
    }.get(tone, "Use a concise, professional tone.")

    title_part = f"Title: {title}\n" if title else ""
    extras = " ".join(x for x in [hashtag_str, mention_str] if x).strip()
    extra_part = f"\nIf space allows, append: {extras}" if extras else ""

    return (
        f"You are drafting a single X (Twitter) post based on the article below.\n"
        f"Constraint: 280 characters MAXIMUM.\n"
        f"{tone_hint} {emoji_hint}\n"
        f"Avoid hashtags in the middle of the sentence. Keep it human-like.\n"
        f"Start directly with the insight (no preamble).\n\n"
        f"{title_part}Content:\n{content}\n\n"
        f"Output: one tweet-ready sentence ≤280 chars.{extra_part}"
    )


async def summarize_to_tweet(
    *,
    url: str,
    title: Optional[str],
    tone: str,
    use_emojis: bool,
    hashtags: List[str],
    mentions: List[str],
    openai_api_key: str,
    model: str,
) -> Optional[str]:
    content = extract_readable(url)
    if not content:
        content = title or url

    # Fallback if no API key: produce a heuristic tweet
    if not (openai_api_key and openai_api_key.strip()):
        return _build_heuristic_tweet(url=url, title=title, content=content or url, hashtags=hashtags, mentions=mentions)

    prompt = build_prompt(content=content, title=title, tone=tone, use_emojis=use_emojis, hashtags=hashtags, mentions=mentions)

    headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You write concise, engaging tweets based on tech news."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 180,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            # Ensure 280 chars max
            return text[:280]
        except Exception:
            # If the API call fails (e.g., invalid model/permissions), fall back to heuristic tweet
            return _build_heuristic_tweet(url=url, title=title, content=content or url, hashtags=hashtags, mentions=mentions)


