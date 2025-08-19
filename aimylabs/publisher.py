from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import tweepy


@dataclass
class PostResult:
    ok: bool
    id: Optional[str]
    url: Optional[str]
    error: Optional[str] = None


@dataclass
class XClients:
    api_v1: tweepy.API
    client_v2: tweepy.Client


def create_x_client(consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str) -> XClients:
    # v1.1 client
    auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)

    # v2 client (user context)
    client_v2 = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True,
    )
    return XClients(api_v1=api_v1, client_v2=client_v2)


def publish_tweet(clients: XClients, text: str, dry_run: bool = False) -> PostResult:
    if dry_run:
        return PostResult(ok=True, id=None, url=None)
    try:
        # Try v2 first
        resp = clients.client_v2.create_tweet(text=text)
        tweet_id = str(resp.data.get("id")) if getattr(resp, "data", None) else None
        url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None
        if tweet_id:
            return PostResult(ok=True, id=tweet_id, url=url)
    except Exception as e:
        v2_err = str(e)
        # Fall back to v1.1
        try:
            status = clients.api_v1.update_status(status=text)
            tweet_id = str(status.id)
            screen_name = status.user.screen_name if getattr(status, "user", None) else ""
            url = f"https://x.com/{screen_name}/status/{tweet_id}" if screen_name else None
            return PostResult(ok=True, id=tweet_id, url=url)
        except Exception as e2:
            return PostResult(ok=False, id=None, url=None, error=f"v2_error={v2_err}; v1_error={str(e2)}")
    # Unexpected path
    return PostResult(ok=False, id=None, url=None, error="Unknown posting failure")


