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
    thread_ids: Optional[List[str]] = None  # For thread posts
    image_attached: bool = False


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


def publish_thread(clients: XClients, thread_parts: List[str], dry_run: bool = False) -> PostResult:
    """Publish a thread of tweets."""
    if dry_run:
        return PostResult(ok=True, id=None, url=None, thread_ids=["dry_run"])
    
    thread_ids = []
    in_reply_to_id = None
    
    try:
        for i, part in enumerate(thread_parts):
            if i == 0:
                # First tweet
                resp = clients.client_v2.create_tweet(text=part)
            else:
                # Reply to previous tweet
                resp = clients.client_v2.create_tweet(
                    text=part,
                    in_reply_to_tweet_id=in_reply_to_id
                )
            
            tweet_id = str(resp.data.get("id")) if getattr(resp, "data", None) else None
            if tweet_id:
                thread_ids.append(tweet_id)
                in_reply_to_id = tweet_id
            else:
                return PostResult(ok=False, id=None, url=None, error="Failed to create thread part")
        
        # Return success with thread IDs
        first_tweet_url = f"https://x.com/i/web/status/{thread_ids[0]}" if thread_ids else None
        return PostResult(
            ok=True,
            id=thread_ids[0] if thread_ids else None,
            url=first_tweet_url,
            thread_ids=thread_ids
        )
        
    except Exception as e:
        return PostResult(ok=False, id=None, url=None, error=f"Thread creation failed: {str(e)}")


def publish_long_post(clients: XClients, text: str, dry_run: bool = False) -> PostResult:
    """Publish a long-form post (Premium X feature)."""
    if dry_run:
        return PostResult(ok=True, id=None, url=None)
    
    try:
        # Use v2 API for long posts
        resp = clients.client_v2.create_tweet(text=text)
        tweet_id = str(resp.data.get("id")) if getattr(resp, "data", None) else None
        url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None
        
        if tweet_id:
            return PostResult(ok=True, id=tweet_id, url=url)
        else:
            return PostResult(ok=False, id=None, url=None, error="Failed to create long post")
            
    except Exception as e:
        return PostResult(ok=False, id=None, url=None, error=f"Long post creation failed: {str(e)}")


def publish_with_image(clients: XClients, text: str, image_data: bytes, dry_run: bool = False) -> PostResult:
    """Publish a tweet with an attached image."""
    if dry_run:
        return PostResult(ok=True, id=None, url=None, image_attached=True)
    
    try:
        # For now, we'll use v1.1 API for media upload
        # In the future, this could be enhanced with v2 media endpoints
        
        # Upload media first
        media = clients.api_v1.media_upload(filename="news_image.jpg", file=image_data)
        
        # Create tweet with media
        status = clients.api_v1.update_status(
            status=text,
            media_ids=[media.media_id]
            )
        
        tweet_id = str(status.id)
        screen_name = status.user.screen_name if getattr(status, "user", None) else ""
        url = f"https://x.com/{screen_name}/status/{tweet_id}" if screen_name else None
        
        if tweet_id:
            return PostResult(ok=True, id=tweet_id, url=url, image_attached=True)
        else:
            return PostResult(ok=False, id=None, url=None, error="Failed to create tweet with image")
            
    except Exception as e:
        return PostResult(ok=False, id=None, url=None, error=f"Image tweet creation failed: {str(e)}")


