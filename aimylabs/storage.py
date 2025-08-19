from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional


@dataclass
class PostedRecord:
    url: str
    tweet_id: Optional[str]


def ensure_db(path: str) -> None:
    os.makedirs(os.path.dirname(os.path.expanduser(path)), exist_ok=True)
    with sqlite3.connect(os.path.expanduser(path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posted (
                url TEXT PRIMARY KEY,
                tweet_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def db_conn(path: str):
    conn = sqlite3.connect(os.path.expanduser(path))
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def was_posted(path: str, url: str) -> bool:
    with db_conn(path) as conn:
        cur = conn.execute("SELECT 1 FROM posted WHERE url = ? LIMIT 1", (url,))
        return cur.fetchone() is not None


def mark_posted(path: str, url: str, tweet_id: Optional[str]) -> None:
    with db_conn(path) as conn:
        conn.execute("INSERT OR REPLACE INTO posted(url, tweet_id) VALUES(?, ?)", (url, tweet_id))


