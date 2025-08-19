from __future__ import annotations

from typing import List, Optional

POPULAR_MENTIONS = [
    "@OpenAI", "@sama", "@gdb", "@ilyasut", "@soumithchintala",
    "@deepmind", "@DemisHassabis", "@GoogleAI", "@anthropic",
    "@a16z", "@cdixon", "@chainlink", "@coindesk",
]

POPULAR_HASHTAGS = [
    "#AI", "#Web3", "#Crypto", "#GenAI", "#LLM", "#DeFi", "#NFT",
]


def pick_mentions(text: str, max_mentions: int = 1) -> List[str]:
    if max_mentions <= 0:
        return []
    # naive heuristic: pick one brand if mentioned
    picks: List[str] = []
    lower = text.lower()
    for handle in POPULAR_MENTIONS:
        base = handle.lower().lstrip("@")
        if base in lower:
            picks.append(handle)
            break
    if not picks and POPULAR_MENTIONS:
        picks.append(POPULAR_MENTIONS[0])
    return picks[:max_mentions]


def mix_hashtags(defaults: List[str], limit: int) -> List[str]:
    seen = set()
    result: List[str] = []
    for tag in defaults + POPULAR_HASHTAGS:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
        if len(result) >= limit:
            break
    return result


