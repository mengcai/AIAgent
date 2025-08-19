from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .mentions import pick_mentions, mix_hashtags


@dataclass
class ContentStrategy:
    content_type: str  # "short", "long", "thread", "image"
    content_parts: List[str]  # For threads, multiple parts
    hashtags: List[str]
    mentions: List[str]
    use_image: bool = False
    image_prompt: Optional[str] = None


def determine_content_strategy(
    title: str,
    content: str,
    url: str,
    tone: str,
    config_strategy: str,
    max_length: int = 25000,
    enable_threads: bool = True,
    enable_images: bool = True
) -> ContentStrategy:
    """
    Determine the best content strategy based on news importance and user preferences.
    
    Args:
        title: News article title
        content: Article content summary
        url: Article URL
        tone: Desired tone
        config_strategy: User's preferred strategy (auto, short, long, thread, image)
        max_length: Maximum post length (Premium X: 25000)
        enable_threads: Whether threads are enabled
        enable_images: Whether images are enabled
    
    Returns:
        ContentStrategy with content type and parts
    """
    
    # Calculate content importance score
    importance_score = _calculate_importance_score(title, content)
    
    # Determine content type based on strategy and importance
    if config_strategy == "auto":
        content_type = _auto_determine_type(importance_score, enable_threads, enable_images)
    else:
        content_type = config_strategy
    
    # Generate content based on type
    if content_type == "thread" and enable_threads:
        return _create_thread_strategy(title, content, url, tone, importance_score, max_length)
    elif content_type == "long":
        return _create_long_post_strategy(title, content, url, tone, max_length)
    elif content_type == "image" and enable_images:
        return _create_image_strategy(title, content, url, tone)
    else:
        return _create_short_post_strategy(title, content, url, tone)


def _calculate_importance_score(title: str, content: str) -> float:
    """Calculate importance score based on content analysis."""
    score = 0.0
    
    # Title length and complexity
    title_words = len(title.split())
    if title_words > 8:
        score += 0.3  # Longer titles often indicate complex topics
    
    # Content length
    content_words = len(content.split())
    if content_words > 200:
        score += 0.4  # Longer content suggests detailed analysis
    
    # Key technology indicators
    high_impact_keywords = [
        "breakthrough", "revolutionary", "game-changing", "paradigm shift",
        "first time", "unprecedented", "major announcement", "launch",
        "partnership", "acquisition", "funding", "IPO", "regulation"
    ]
    
    for keyword in high_impact_keywords:
        if keyword.lower() in (title + " " + content).lower():
            score += 0.2
    
    # Company/entity mentions
    major_entities = [
        "openai", "google", "microsoft", "anthropic", "deepmind",
        "ethereum", "bitcoin", "a16z", "sequoia", "y combinator"
    ]
    
    for entity in major_entities:
        if entity.lower() in (title + " " + content).lower():
            score += 0.1
    
    return min(score, 1.0)  # Cap at 1.0


def _auto_determine_type(
    importance_score: float,
    enable_threads: bool,
    enable_images: bool
) -> str:
    """Automatically determine content type based on importance score."""
    if importance_score > 0.7 and enable_threads:
        return "thread"
    elif importance_score > 0.5:
        return "long"
    elif importance_score > 0.3 and enable_images:
        return "image"
    else:
        return "short"


def _create_short_post_strategy(
    title: str,
    content: str,
    url: str,
    tone: str
) -> ContentStrategy:
    """Create a short tweet strategy (classic 280 chars)."""
    hashtags = mix_hashtags(["#AI", "#Web3"], max_count=3)
    mentions = pick_mentions(title + " " + content)
    
    return ContentStrategy(
        content_type="short",
        content_parts=[f"{title} {url}"],
        hashtags=hashtags,
        mentions=mentions,
        use_image=False
    )


def _create_long_post_strategy(
    title: str,
    content: str,
    url: str,
    tone: str,
    max_length: int
) -> ContentStrategy:
    """Create a long-form post strategy (Premium X)."""
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], max_count=5)
    mentions = pick_mentions(title + " " + content)
    
    # Create engaging long-form content
    long_content = _format_long_content(title, content, url, tone)
    
    # Ensure it fits within max_length
    if len(long_content) > max_length:
        long_content = long_content[:max_length-3] + "..."
    
    return ContentStrategy(
        content_type="long",
        content_parts=[long_content],
        hashtags=hashtags,
        mentions=mentions,
        use_image=False
    )


def _create_thread_strategy(
    title: str,
    content: str,
    url: str,
    tone: str,
    importance_score: float,
    max_length: int
) -> ContentStrategy:
    """Create a thread strategy for complex stories."""
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], max_count=5)
    mentions = pick_mentions(title + " " + content)
    
    # Split content into thread parts
    thread_parts = _create_thread_parts(title, content, url, tone, importance_score)
    
    # Ensure each part fits within max_length
    formatted_parts = []
    for i, part in enumerate(thread_parts):
        if len(part) > max_length:
            part = part[:max_length-3] + "..."
        
        # Add thread indicators
        if i == 0:
            part += f"\n\n🧵 Thread on {title[:50]}..."
        elif i < len(thread_parts) - 1:
            part += f"\n\n{i+1}/{len(thread_parts)}"
        else:
            part += f"\n\n{i+1}/{len(thread_parts)} 🔗 {url}"
        
        formatted_parts.append(part)
    
    return ContentStrategy(
        content_type="thread",
        content_parts=formatted_parts,
        hashtags=hashtags,
        mentions=mentions,
        use_image=False
    )


def _create_image_strategy(
    title: str,
    content: str,
    url: str,
    tone: str
) -> ContentStrategy:
    """Create a strategy that includes image generation."""
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi"], max_count=4)
    mentions = pick_mentions(title + " " + content)
    
    # Create image prompt
    image_prompt = f"Visual representation of: {title}. Key elements: AI/Web3 technology, {tone} style, modern aesthetic."
    
    return ContentStrategy(
        content_type="image",
        content_parts=[f"{title}\n\n{url}"],
        hashtags=hashtags,
        mentions=mentions,
        use_image=True,
        image_prompt=image_prompt
    )


def _format_long_content(title: str, content: str, url: str, tone: str) -> str:
    """Format content for long-form posts."""
    # Extract key insights
    key_points = _extract_key_points(content)
    
    # Format based on tone
    if tone == "thought_leader":
        return _format_thought_leader_post(title, key_points, url)
    elif tone == "professional":
        return _format_professional_post(title, key_points, url)
    elif tone == "witty":
        return _format_witty_post(title, key_points, url)
    elif tone == "hype":
        return _format_hype_post(title, key_points, url)
    else:
        return _format_default_post(title, key_points, url)


def _create_thread_parts(title: str, content: str, url: str, tone: str, importance_score: float) -> List[str]:
    """Create thread parts for complex stories."""
    parts = []
    
    # Part 1: Hook and overview
    hook = f"🚀 {title}\n\n"
    if importance_score > 0.8:
        hook += "This is BIG news that could reshape the entire industry. Let me break it down:"
    else:
        hook += "Important development worth diving into:"
    
    parts.append(hook)
    
    # Part 2: Key insights
    key_points = _extract_key_points(content)
    insights = "🔍 Key Insights:\n\n"
    for i, point in enumerate(key_points[:3], 1):
        insights += f"{i}. {point}\n"
    parts.append(insights)
    
    # Part 3: Implications
    implications = "💡 What This Means:\n\n"
    if "AI" in title or "artificial intelligence" in content.lower():
        implications += "• Accelerates AI development timeline\n• New opportunities for developers\n• Potential regulatory considerations"
    elif "Web3" in title or "blockchain" in content.lower():
        implications += "• Advances decentralized infrastructure\n• New DeFi protocols possible\n• Enhanced user experiences"
    else:
        implications += "• Industry disruption ahead\n• New market opportunities\n• Technology evolution continues"
    
    parts.append(implications)
    
    # Part 4: Why it matters
    why_matters = "🎯 Why This Matters:\n\n"
    why_matters += "This development represents a significant step forward in the convergence of AI and Web3 technologies."
    
    parts.append(why_matters)
    
    return parts


def _extract_key_points(content: str) -> List[str]:
    """Extract key points from content."""
    # Simple extraction - split by sentences and take key ones
    sentences = re.split(r'[.!?]+', content)
    key_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
            # Look for sentences with key indicators
            if any(word in sentence.lower() for word in ["announced", "launched", "released", "introduced", "developed"]):
                key_sentences.append(sentence)
            elif len(key_sentences) < 3:  # Take first few reasonable sentences
                key_sentences.append(sentence)
    
    return key_sentences[:3]


def _format_thought_leader_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in thought leader style."""
    content = f"💭 {title}\n\n"
    content += "This development caught my attention for several reasons:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"{i}. {point}\n\n"
    
    content += "The implications are profound. We're witnessing the acceleration of technological convergence that will define the next decade.\n\n"
    content += "What are your thoughts on this? How do you see it impacting your work?\n\n"
    content += f"🔗 {url}"
    
    return content


def _format_professional_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in professional style."""
    content = f"📊 {title}\n\n"
    content += "Key highlights:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"• {point}\n"
    
    content += f"\nThis represents a significant advancement in the field. Read more: {url}"
    
    return content


def _format_witty_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in witty style."""
    content = f"🤖 {title}\n\n"
    content += "Plot twist: The future is happening faster than expected! Here's what's going down:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"{i}. {point}\n"
    
    content += "\nThe AI/Web3 crossover we've been waiting for? It's here, and it's spectacular.\n\n"
    content += f"🎬 {url}"
    
    return content


def _format_hype_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in hype style."""
    content = f"🔥 {title}\n\n"
    content += "THIS IS HUGE! 🚀\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"💥 {point}\n"
    
    content += "\nThe game is changing, and we're here for it! This is what innovation looks like.\n\n"
    content += f"⚡ {url}"
    
    return content


def _format_default_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in default style."""
    content = f"📰 {title}\n\n"
    content += "Key points:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"{i}. {point}\n"
    
    content += f"\nRead the full story: {url}"
    
    return content
