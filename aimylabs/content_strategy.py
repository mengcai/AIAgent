from __future__ import annotations

import re
import random
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
    """Determine the best content strategy based on news importance and user preferences."""
    
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
        score += 0.2  # Reduced from 0.3
    
    # Content length
    content_words = len(content.split())
    if content_words > 200:
        score += 0.25  # Reduced from 0.4
    
    # Key technology indicators
    high_impact_keywords = [
        "breakthrough", "revolutionary", "game-changing", "paradigm shift",
        "first time", "unprecedented", "major announcement", "launch",
        "partnership", "acquisition", "funding", "IPO", "regulation"
    ]
    
    for keyword in high_impact_keywords:
        if keyword.lower() in (title + " " + content).lower():
            score += 0.15  # Reduced from 0.2
    
    # Company/entity mentions
    major_entities = [
        "openai", "google", "microsoft", "anthropic", "deepmind",
        "ethereum", "bitcoin", "a16z", "sequoia", "y combinator"
    ]
    
    for entity in major_entities:
        if entity.lower() in (title + " " + content).lower():
            score += 0.08  # Reduced from 0.1
    
    return min(score, 1.0)  # Cap at 1.0


def _auto_determine_type(
    importance_score: float,
    enable_threads: bool,
    enable_images: bool
) -> str:
    """Automatically determine content type based on importance score."""
    if importance_score > 0.7 and enable_threads:
        return "thread"
    elif importance_score > 0.1:  # Much lower threshold - almost everything gets long posts
        return "long"
    elif importance_score > 0.15 and enable_images:  # Only use image if enabled
        return "image"
    else:
        return "short"


def _create_short_post_strategy(
    title: str,
    content: str,
    url: str,
    tone: str
) -> ContentStrategy:
    """Create a short tweet strategy with personality and insight."""
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], 3)
    mentions = pick_mentions(title + " " + content)
    
    # Create a bold, engaging statement that's NOT just the headline
    post_content = _create_engaging_short_post(title, content, tone, url)
    
    return ContentStrategy(
        content_type="short",
        content_parts=[post_content],
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
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], 5)
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
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], 5)
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
    hashtags = mix_hashtags(["#AI", "#Web3", "#DeFi", "#Crypto"], 4)
    mentions = pick_mentions(title + " " + content)
    
    # Create engaging content for image posts (more substantial than just title + URL)
    post_content = _create_engaging_image_post(title, content, tone, url)
    
    # Create image prompt
    image_prompt = f"Visual representation of: {title}. Key elements: AI/Web3 technology, {tone} style, modern aesthetic."
    
    return ContentStrategy(
        content_type="image",
        content_parts=[post_content],
        hashtags=hashtags,
        mentions=mentions,
        use_image=True,
        image_prompt=image_prompt
    )


def _create_engaging_short_post(title: str, content: str, tone: str, url: str = "") -> str:
    """Create a short post that's engaging and original, not just a headline copy."""
    
    # Extract the real story beyond the headline
    story_angle = _extract_story_angle(title, content)
    
    # Create a bold POV statement
    if tone == "witty":
        post = _create_witty_short_post(story_angle, title)
    elif tone == "hype":
        post = _create_hype_short_post(story_angle, title)
    elif tone == "thought_leader":
        post = _create_thought_leader_short_post(story_angle, title)
    elif tone == "meme":
        post = _create_meme_short_post(story_angle, title)
    else:
        post = _create_professional_short_post(story_angle, title)
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, content, story_angle)
    
    # Add URL if provided
    if url:
        post += f"\n\n🔗 {url}"
    
    # Add viral elements
    post += f"\n\n{viral_elements}"
    
    return post


def _extract_story_angle(title: str, content: str) -> str:
    """Extract the real story angle beyond the headline."""
    
    # Look for key themes and implications
    text = (title + " " + content).lower()
    
    if any(word in text for word in ["etf", "approval", "regulatory"]):
        return "regulatory_breakthrough"
    elif any(word in text for word in ["partnership", "acquisition", "merger"]):
        return "business_move"
    elif any(word in text for word in ["launch", "release", "announcement"]):
        return "product_launch"
    elif any(word in text for word in ["funding", "investment", "valuation"]):
        return "financial_news"
    elif any(word in text for word in ["breakthrough", "innovation", "research"]):
        return "technical_breakthrough"
    elif any(word in text for word in ["competition", "rival", "challenge"]):
        return "competitive_dynamics"
    else:
        return "general_development"


def _create_witty_short_post(story_angle: str, title: str) -> str:
    """Create a witty, clever short post."""
    
    witty_takes = {
        "regulatory_breakthrough": [
            "🚨 Wall Street just gave this its 'gold stamp of approval' 🏦💎",
            "🎯 The regulators finally caught up with reality",
            "⚡️ This just got the government's blessing (and we all know what that means 😏)"
        ],
        "business_move": [
            "🤝 Plot twist: The industry just got a lot more interesting",
            "🎬 The corporate chess game continues...",
            "💼 Someone's playing 4D chess while we're playing checkers"
        ],
        "product_launch": [
            "🚀 Another day, another 'revolutionary' launch",
            "🎉 The future is here (again, for the 47th time this month)",
            "⚡️ Innovation speed: 0 to 100 real quick"
        ],
        "financial_news": [
            "💰 Money talks, and it's saying some interesting things",
            "📈 The numbers don't lie (but they do tell stories)",
            "💎 Someone's making moves while we're making memes"
        ],
        "technical_breakthrough": [
            "🧠 The AI just got smarter (and we're still trying to figure out our phones)",
            "⚡️ Technology: Moving faster than our ability to understand it",
            "🔮 The future is now, and it's wearing a neural network"
        ],
        "competitive_dynamics": [
            "🥊 The gloves are off in the tech world",
            "🎯 Someone's playing to win, not just to participate",
            "⚔️ The battle for supremacy continues..."
        ],
        "general_development": [
            "🎯 Another piece of the puzzle falls into place",
            "🚀 Progress doesn't wait for permission",
            "💡 Innovation happens whether we're ready or not"
        ]
    }
    
    # Pick a random witty take
    take = random.choice(witty_takes.get(story_angle, witty_takes["general_development"]))
    
    # Create the post with personality
    post = f"{take}\n\n"
    
    # Add a clever question or statement
    if story_angle == "regulatory_breakthrough":
        post += "The question isn't 'if' anymore, it's 'how fast' 🏃‍♂️💨"
    elif story_angle == "business_move":
        post += "Who's next on the chessboard? 🤔♟️"
    elif story_angle == "product_launch":
        post += "Will this one actually change the world, or just our Twitter feeds? 🌍📱"
    elif story_angle == "financial_news":
        post += "The market giveth, and the market taketh away 📊"
    elif story_angle == "technical_breakthrough":
        post += "Humanity: Still trying to keep up with our own creations 🤖"
    else:
        post += "The plot thickens... 🕵️‍♂️"
    
    return post


def _create_hype_short_post(story_angle: str, title: str) -> str:
    """Create a high-energy, hype short post."""
    
    hype_takes = {
        "regulatory_breakthrough": [
            "🔥 THIS IS HUGE! The game just changed forever! 🚀",
            "⚡️ BREAKING: The future just got the green light! 🎯",
            "🚨 MASSIVE NEWS: The revolution is officially sanctioned! 💥"
        ],
        "business_move": [
            "💥 BOOM! The industry landscape just shifted! 🌋",
            "🚀 GAME ON! Someone's making power moves! ⚡️",
            "🔥 THE HEAT IS ON! Things are getting spicy! 🌶️"
        ],
        "product_launch": [
            "🚀 THE FUTURE IS HERE! Innovation at warp speed! ⚡️",
            "💥 REVOLUTIONARY! This changes everything! 🔥",
            "⚡️ LIGHTNING STRIKE! The tech world just got upgraded! 🌩️"
        ],
        "financial_news": [
            "💰 MONEY MOVES! The financial world is watching! 👀",
            "📈 TO THE MOON! The numbers are speaking! 🚀",
            "💎 DIAMOND HANDS! The market is responding! 💪"
        ],
        "technical_breakthrough": [
            "🧠 MIND-BLOWING! The AI just leveled up! 🚀",
            "⚡️ BREAKTHROUGH! Technology is evolving! 🔥",
            "🔮 FUTURISTIC! We're living in the future! 🌟"
        ],
        "competitive_dynamics": [
            "🥊 THE BATTLE IS ON! Competition is heating up! 🔥",
            "⚔️ WAR GAMES! The stakes just got higher! 🎯",
            "🚀 RACE TO THE TOP! Innovation is accelerating! ⚡️"
        ],
        "general_development": [
            "🎯 TARGET ACQUIRED! Progress is unstoppable! 🚀",
            "⚡️ LIGHTNING SPEED! The future is now! 🔥",
            "💥 EXPLOSIVE GROWTH! Innovation is everywhere! 🌟"
        ]
    }
    
    take = random.choice(hype_takes.get(story_angle, hype_takes["general_development"]))
    
    post = f"{take}\n\n"
    
    # Add hype question
    if story_angle == "regulatory_breakthrough":
        post += "Are you ready for what's coming? Because it's COMING! 🚀💥"
    elif story_angle == "business_move":
        post += "The competition just got REAL! 💪🔥"
    elif story_angle == "product_launch":
        post += "This isn't just an update, it's a REVOLUTION! 🌟⚡️"
    elif story_angle == "financial_news":
        post += "The money is flowing! 💰💎"
    elif story_angle == "technical_breakthrough":
        post += "Humanity just got an upgrade! 🚀🧠"
    else:
        post += "The future is BRIGHT! ✨🔥"
    
    return post


def _create_thought_leader_short_post(story_angle: str, title: str) -> str:
    """Create a thought leader style short post."""
    
    thought_leader_takes = {
        "regulatory_breakthrough": [
            "💭 This regulatory milestone represents more than just approval—it's validation of an entire ecosystem.",
            "🎯 The institutional embrace of this technology signals a fundamental shift in how we think about innovation.",
            "⚡️ This moment will be remembered as the day the old guard finally acknowledged the new reality."
        ],
        "business_move": [
            "💼 This strategic move reveals the underlying dynamics reshaping our industry.",
            "🎯 The consolidation we're seeing isn't just business—it's evolution in action.",
            "💡 This partnership represents the convergence of complementary visions for the future."
        ],
        "product_launch": [
            "🚀 This launch isn't just a product—it's a platform for the next generation of innovation.",
            "💡 What we're seeing here is the maturation of technology from novelty to necessity.",
            "⚡️ This represents the bridge between current capabilities and future possibilities."
        ],
        "financial_news": [
            "💰 The financial markets are beginning to understand what technologists have known for years.",
            "📊 This valuation reflects not just current performance, but future potential.",
            "💎 We're witnessing the monetization of innovation at scale."
        ],
        "technical_breakthrough": [
            "🧠 This breakthrough represents a fundamental advancement in our technological capabilities.",
            "⚡️ What we're seeing here is the acceleration of human potential through technology.",
            "🔮 This isn't just progress—it's a glimpse into a future we're actively creating."
        ],
        "competitive_dynamics": [
            "🥊 The competitive landscape is evolving faster than traditional business models can adapt.",
            "⚔️ What we're witnessing is the natural selection of innovation in the marketplace.",
            "🎯 This competition isn't just about market share—it's about defining the future."
        ],
        "general_development": [
            "💭 Every development like this brings us closer to the future we're building.",
            "🎯 The pace of innovation is accelerating beyond our ability to predict outcomes.",
            "⚡️ We're living through a period of unprecedented technological transformation."
        ]
    }
    
    take = random.choice(thought_leader_takes.get(story_angle, thought_leader_takes["general_development"]))
    
    post = f"{take}\n\n"
    
    # Add thought-provoking question
    if story_angle == "regulatory_breakthrough":
        post += "The question now is: how will this reshape the landscape? 🤔"
    elif story_angle == "business_move":
        post += "What does this tell us about the direction of the industry? 💭"
    elif story_angle == "product_launch":
        post += "How will this change the way we think about technology? 🔍"
    elif story_angle == "financial_news":
        post += "What does this reveal about market sentiment? 📊"
    elif story_angle == "technical_breakthrough":
        post += "How will this advance our collective capabilities? 🚀"
    else:
        post += "What does this development mean for the future? 🌟"
    
    return post


def _create_meme_short_post(story_angle: str, title: str) -> str:
    """Create a meme-style short post."""
    
    meme_takes = {
        "regulatory_breakthrough": [
            "🚨 The regulators finally woke up and chose violence 😤",
            "🎯 Government: 'We approve' | Me: 'About time' 😏",
            "⚡️ The bureaucracy just got a speed upgrade 🚀"
        ],
        "business_move": [
            "🤝 Plot twist: The industry just got a lot more interesting 🎬",
            "💼 Business: *makes move* | Me: *surprised Pikachu face* 😱",
            "🎯 Someone's playing 4D chess while we're playing tic-tac-toe ♟️"
        ],
        "product_launch": [
            "🚀 Another 'revolutionary' product that will definitely change everything (this time for real) 😅",
            "🎉 The future is here (again, for the 47th time this month) 🕐",
            "⚡️ Innovation speed: 0 to 100 real quick 🏃‍♂️💨"
        ],
        "financial_news": [
            "💰 Money talks, and it's saying some spicy things 🌶️",
            "📈 The numbers don't lie (but they do tell stories) 📊",
            "💎 Someone's making moves while we're making memes 😎"
        ],
        "technical_breakthrough": [
            "🧠 The AI just got smarter (and we're still trying to figure out our phones) 📱",
            "⚡️ Technology: Moving faster than our ability to understand it 🚀",
            "🔮 The future is now, and it's wearing a neural network 🤖"
        ],
        "competitive_dynamics": [
            "🥊 The gloves are off in the tech world 🥊",
            "🎯 Someone's playing to win, not just to participate 🏆",
            "⚔️ The battle for supremacy continues... (popcorn time) 🍿"
        ],
        "general_development": [
            "🎯 Another piece of the puzzle falls into place 🧩",
            "🚀 Progress doesn't wait for permission (and neither do we) 💪",
            "💡 Innovation happens whether we're ready or not 🚀"
        ]
    }
    
    take = random.choice(meme_takes.get(story_angle, meme_takes["general_development"]))
    
    post = f"{take}\n\n"
    
    # Add meme-style ending
    if story_angle == "regulatory_breakthrough":
        post += "The timeline just got a major upgrade ⚡️😎"
    elif story_angle == "business_move":
        post += "The plot thickens... 🕵️‍♂️🍿"
    elif story_angle == "product_launch":
        post += "Will this one actually work? (Asking for a friend) 🤔"
    elif story_angle == "financial_news":
        post += "The market giveth and the market taketh away 📊🙏"
    elif story_angle == "technical_breakthrough":
        post += "Humanity: Still trying to keep up with our own creations 🤖💀"
    else:
        post += "The future is now, old man 👴⚡️"
    
    return post


def _create_professional_short_post(story_angle: str, title: str) -> str:
    """Create a professional short post."""
    
    professional_takes = {
        "regulatory_breakthrough": [
            "📊 This regulatory approval represents a significant milestone for the industry.",
            "🎯 The green light from regulators opens new opportunities for growth and innovation.",
            "⚡️ This approval signals broader acceptance of emerging technologies."
        ],
        "business_move": [
            "💼 This strategic development reflects the evolving landscape of the industry.",
            "🎯 The partnership demonstrates the value of collaboration in driving innovation.",
            "💡 This move positions the company for future growth and market expansion."
        ],
        "product_launch": [
            "🚀 This launch introduces new capabilities that address evolving market needs.",
            "💡 The product represents a significant advancement in technological innovation.",
            "⚡️ This release demonstrates the company's commitment to continuous improvement."
        ],
        "financial_news": [
            "💰 The financial performance reflects strong market fundamentals and growth potential.",
            "📈 This development indicates positive market sentiment and investor confidence.",
            "💎 The valuation reflects the company's strategic position and future prospects."
        ],
        "technical_breakthrough": [
            "🧠 This technical advancement represents a significant step forward in the field.",
            "⚡️ The breakthrough demonstrates the potential for transformative innovation.",
            "🔮 This development opens new possibilities for technological advancement."
        ],
        "competitive_dynamics": [
            "🥊 The competitive landscape continues to evolve with new market entrants.",
            "⚔️ This development reflects the dynamic nature of the industry.",
            "🎯 The competition drives innovation and benefits consumers."
        ],
        "general_development": [
            "📈 This development represents continued progress in the industry.",
            "🎯 The advancement demonstrates the ongoing evolution of technology.",
            "⚡️ This progress contributes to the overall growth of the sector."
        ]
    }
    
    take = random.choice(professional_takes.get(story_angle, professional_takes["general_development"]))
    
    post = f"{take}\n\n"
    
    # Add professional closing
    if story_angle == "regulatory_breakthrough":
        post += "This milestone paves the way for future developments. 📈"
    elif story_angle == "business_move":
        post += "The strategic implications are significant. 💼"
    elif story_angle == "product_launch":
        post += "The market impact will be worth monitoring. 📊"
    elif story_angle == "financial_news":
        post += "The financial implications are positive. 💰"
    elif story_angle == "technical_breakthrough":
        post += "The technical implications are substantial. 🧠"
    else:
        post += "The development represents positive progress. ✅"
    
    return post


def _create_engaging_image_post(title: str, content: str, tone: str, url: str) -> str:
    """Create engaging content for image posts that's substantial and engaging."""
    
    # Extract story angle for better content
    story_angle = _extract_story_angle(title, content)
    
    # Create engaging opening based on tone and story angle
    if tone == "witty":
        opening = _create_witty_image_opening(story_angle, title)
    elif tone == "hype":
        opening = _create_hype_image_opening(story_angle, title)
    elif tone == "thought_leader":
        opening = _create_thought_leader_image_opening(story_angle, title)
    elif tone == "meme":
        opening = _create_meme_image_opening(story_angle, title)
    else:
        opening = _create_professional_image_opening(story_angle, title)
    
    # Add engaging middle content
    middle = _create_image_post_middle(story_angle, content)
    
    # Add strategic mentions and hashtags for virality
    viral_elements = _add_viral_elements(title, content, story_angle)
    
    # Add URL and hashtags
    closing = f"\n\n🔗 {url}"
    
    return f"{opening}\n\n{middle}\n\n{viral_elements}{closing}"


def _create_witty_image_opening(story_angle: str, title: str) -> str:
    """Create witty opening for image posts."""
    
    witty_openings = {
        "regulatory_breakthrough": [
            "🚨 The regulators finally woke up and chose violence 😤",
            "🎯 Government: 'We approve' | Me: 'About time' 😏",
            "⚡️ The bureaucracy just got a speed upgrade 🚀"
        ],
        "business_move": [
            "🤝 Plot twist: The industry just got a lot more interesting",
            "🎬 The corporate chess game continues...",
            "💼 Someone's playing 4D chess while we're playing checkers"
        ],
        "product_launch": [
            "🚀 Another day, another 'revolutionary' launch",
            "🎉 The future is here (again, for the 47th time this month)",
            "⚡️ Innovation speed: 0 to 100 real quick"
        ],
        "financial_news": [
            "💰 Money talks, and it's saying some interesting things",
            "📈 The numbers don't lie (but they do tell stories)",
            "💎 Someone's making moves while we're making memes"
        ],
        "technical_breakthrough": [
            "🧠 The AI just got smarter (and we're still trying to figure out our phones)",
            "⚡️ Technology: Moving faster than our ability to understand it",
            "🔮 The future is now, and it's wearing a neural network"
        ],
        "competitive_dynamics": [
            "🥊 The gloves are off in the tech world",
            "🎯 Someone's playing to win, not just to participate",
            "⚔️ The battle for supremacy continues..."
        ],
        "general_development": [
            "🎯 Another piece of the puzzle falls into place",
            "🚀 Progress doesn't wait for permission",
            "💡 Innovation happens whether we're ready or not"
        ]
    }
    
    take = random.choice(witty_openings.get(story_angle, witty_openings["general_development"]))
    
    # Add engaging follow-up
    if story_angle == "regulatory_breakthrough":
        follow_up = "The question isn't 'if' anymore, it's 'how fast' 🏃‍♂️💨"
    elif story_angle == "business_move":
        follow_up = "Who's next on the chessboard? 🤔♟️"
    elif story_angle == "product_launch":
        follow_up = "Will this one actually change the world, or just our Twitter feeds? 🌍📱"
    elif story_angle == "financial_news":
        follow_up = "The market giveth, and the market taketh away 📊"
    elif story_angle == "technical_breakthrough":
        follow_up = "Humanity: Still trying to keep up with our own creations 🤖"
    else:
        follow_up = "The plot thickens... 🕵️‍♂️"
    
    return f"{take}\n\n{follow_up}"


def _create_hype_image_opening(story_angle: str, title: str) -> str:
    """Create hype opening for image posts."""
    
    hype_openings = {
        "regulatory_breakthrough": [
            "🔥 THIS IS HUGE! The game just changed forever! 🚀",
            "⚡️ BREAKING: The future just got the green light! 🎯",
            "🚨 MASSIVE NEWS: The revolution is officially sanctioned! 💥"
        ],
        "business_move": [
            "💥 BOOM! The industry landscape just shifted! 🌋",
            "🚀 GAME ON! Someone's making power moves! ⚡️",
            "🔥 THE HEAT IS ON! Things are getting spicy! 🌶️"
        ],
        "product_launch": [
            "🚀 THE FUTURE IS HERE! Innovation at warp speed! ⚡️",
            "💥 REVOLUTIONARY! This changes everything! 🔥",
            "⚡️ LIGHTNING STRIKE! The tech world just got upgraded! 🌩️"
        ],
        "financial_news": [
            "💰 MONEY MOVES! The financial world is watching! 👀",
            "📈 TO THE MOON! The numbers are speaking! 🚀",
            "💎 DIAMOND HANDS! The market is responding! 💪"
        ],
        "technical_breakthrough": [
            "🧠 MIND-BLOWING! The AI just leveled up! 🚀",
            "⚡️ BREAKTHROUGH! Technology is evolving! 🔥",
            "🔮 FUTURISTIC! We're living in the future! 🌟"
        ],
        "competitive_dynamics": [
            "🥊 THE BATTLE IS ON! Competition is heating up! 🔥",
            "⚔️ WAR GAMES! The stakes just got higher! 🎯",
            "🚀 RACE TO THE TOP! Innovation is accelerating! ⚡️"
        ],
        "general_development": [
            "🎯 TARGET ACQUIRED! Progress is unstoppable! 🚀",
            "⚡️ LIGHTNING SPEED! The future is now! 🔥",
            "💥 EXPLOSIVE GROWTH! Innovation is everywhere! 🌟"
        ]
    }
    
    take = random.choice(hype_openings.get(story_angle, hype_openings["general_development"]))
    
    # Add hype follow-up
    if story_angle == "regulatory_breakthrough":
        follow_up = "Are you ready for what's coming? Because it's COMING! 🚀💥"
    elif story_angle == "business_move":
        follow_up = "The competition just got REAL! 💪🔥"
    elif story_angle == "product_launch":
        follow_up = "This isn't just an update, it's a REVOLUTION! 🌟⚡️"
    elif story_angle == "financial_news":
        follow_up = "The money is flowing! 💰💎"
    elif story_angle == "technical_breakthrough":
        follow_up = "Humanity just got an upgrade! 🚀🧠"
    else:
        follow_up = "The future is BRIGHT! ✨🔥"
    
    return f"{take}\n\n{follow_up}"


def _create_thought_leader_image_opening(story_angle: str, title: str) -> str:
    """Create thought leader opening for image posts."""
    
    thought_leader_openings = {
        "regulatory_breakthrough": [
            "💭 This regulatory milestone represents more than just approval—it's validation of an entire ecosystem.",
            "🎯 The institutional embrace of this technology signals a fundamental shift in how we think about innovation.",
            "⚡️ This moment will be remembered as the day the old guard finally acknowledged the new reality."
        ],
        "business_move": [
            "💼 This strategic move reveals the underlying dynamics reshaping our industry.",
            "🎯 The consolidation we're seeing isn't just business—it's evolution in action.",
            "💡 This partnership represents the convergence of complementary visions for the future."
        ],
        "product_launch": [
            "🚀 This launch isn't just a product—it's a platform for the next generation of innovation.",
            "💡 What we're seeing here is the maturation of technology from novelty to necessity.",
            "⚡️ This represents the bridge between current capabilities and future possibilities."
        ],
        "financial_news": [
            "💰 The financial markets are beginning to understand what technologists have known for years.",
            "📊 This valuation reflects not just current performance, but future potential.",
            "💎 We're witnessing the monetization of innovation at scale."
        ],
        "technical_breakthrough": [
            "🧠 This breakthrough represents a fundamental advancement in our technological capabilities.",
            "⚡️ What we're seeing here is the acceleration of human potential through technology.",
            "🔮 This isn't just progress—it's a glimpse into a future we're actively creating."
        ],
        "competitive_dynamics": [
            "🥊 The competitive landscape is evolving faster than traditional business models can adapt.",
            "⚔️ What we're witnessing is the natural selection of innovation in the marketplace.",
            "🎯 This competition isn't just about market share—it's about defining the future."
        ],
        "general_development": [
            "💭 Every development like this brings us closer to the future we're building.",
            "🎯 The pace of innovation is accelerating beyond our ability to predict outcomes.",
            "⚡️ We're living through a period of unprecedented technological transformation."
        ]
    }
    
    take = random.choice(thought_leader_openings.get(story_angle, thought_leader_openings["general_development"]))
    
    # Add thought-provoking follow-up
    if story_angle == "regulatory_breakthrough":
        follow_up = "The question now is: how will this reshape the landscape? 🤔"
    elif story_angle == "business_move":
        follow_up = "What does this tell us about the direction of the industry? 💭"
    elif story_angle == "product_launch":
        follow_up = "How will this change the way we think about technology? 🔍"
    elif story_angle == "financial_news":
        follow_up = "What does this reveal about market sentiment? 📊"
    elif story_angle == "technical_breakthrough":
        follow_up = "How will this advance our collective capabilities? 🚀"
    else:
        follow_up = "What does this development mean for the future? 🌟"
    
    return f"{take}\n\n{follow_up}"


def _create_meme_image_opening(story_angle: str, title: str) -> str:
    """Create meme opening for image posts."""
    
    meme_openings = {
        "regulatory_breakthrough": [
            "🚨 The regulators finally woke up and chose violence 😤",
            "🎯 Government: 'We approve' | Me: 'About time' 😏",
            "⚡️ The bureaucracy just got a speed upgrade 🚀"
        ],
        "business_move": [
            "🤝 Plot twist: The industry just got a lot more interesting 🎬",
            "💼 Business: *makes move* | Me: *surprised Pikachu face* 😱",
            "🎯 Someone's playing 4D chess while we're playing tic-tac-toe ♟️"
        ],
        "product_launch": [
            "🚀 Another 'revolutionary' product that will definitely change everything (this time for real) 😅",
            "🎉 The future is here (again, for the 47th time this month) 🕐",
            "⚡️ Innovation speed: 0 to 100 real quick 🏃‍♂️💨"
        ],
        "financial_news": [
            "💰 Money talks, and it's saying some spicy things 🌶️",
            "📈 The numbers don't lie (but they do tell stories) 📊",
            "💎 Someone's making moves while we're making memes 😎"
        ],
        "technical_breakthrough": [
            "🧠 The AI just got smarter (and we're still trying to figure out our phones) 📱",
            "⚡️ Technology: Moving faster than our ability to understand it 🚀",
            "🔮 The future is now, and it's wearing a neural network 🤖"
        ],
        "competitive_dynamics": [
            "🥊 The gloves are off in the tech world 🥊",
            "🎯 Someone's playing to win, not just to participate 🏆",
            "⚔️ The battle for supremacy continues... (popcorn time) 🍿"
        ],
        "general_development": [
            "🎯 Another piece of the puzzle falls into place 🧩",
            "🚀 Progress doesn't wait for permission (and neither do we) 💪",
            "💡 Innovation happens whether we're ready or not 🚀"
        ]
    }
    
    take = random.choice(meme_openings.get(story_angle, meme_openings["general_development"]))
    
    # Add meme-style follow-up
    if story_angle == "regulatory_breakthrough":
        follow_up = "The timeline just got a major upgrade ⚡️😎"
    elif story_angle == "business_move":
        follow_up = "The plot thickens... 🕵️‍♂️🍿"
    elif story_angle == "product_launch":
        follow_up = "Will this one actually work? (Asking for a friend) 🤔"
    elif story_angle == "financial_news":
        follow_up = "The market giveth and the market taketh away 📊🙏"
    elif story_angle == "technical_breakthrough":
        follow_up = "Humanity: Still trying to keep up with our own creations 🤖💀"
    else:
        follow_up = "The future is now, old man 👴⚡️"
    
    return f"{take}\n\n{follow_up}"


def _create_professional_image_opening(story_angle: str, title: str) -> str:
    """Create professional opening for image posts."""
    
    professional_openings = {
        "regulatory_breakthrough": [
            "📊 This regulatory approval represents a significant milestone for the industry.",
            "🎯 The green light from regulators opens new opportunities for growth and innovation.",
            "⚡️ This approval signals broader acceptance of emerging technologies."
        ],
        "business_move": [
            "💼 This strategic development reflects the evolving landscape of the industry.",
            "🎯 The partnership demonstrates the value of collaboration in driving innovation.",
            "💡 This move positions the company for future growth and market expansion."
        ],
        "product_launch": [
            "🚀 This launch introduces new capabilities that address evolving market needs.",
            "💡 The product represents a significant advancement in technological innovation.",
            "⚡️ This release demonstrates the company's commitment to continuous improvement."
        ],
        "financial_news": [
            "💰 The financial performance reflects strong market fundamentals and growth potential.",
            "📈 This development indicates positive market sentiment and investor confidence.",
            "💎 The valuation reflects the company's strategic position and future prospects."
        ],
        "technical_breakthrough": [
            "🧠 This technical advancement represents a significant step forward in the field.",
            "⚡️ The breakthrough demonstrates the potential for transformative innovation.",
            "🔮 This development opens new possibilities for technological advancement."
        ],
        "competitive_dynamics": [
            "🥊 The competitive landscape continues to evolve with new market entrants.",
            "⚔️ This development reflects the dynamic nature of the industry.",
            "🎯 The competition drives innovation and benefits consumers."
        ],
        "general_development": [
            "📈 This development represents continued progress in the industry.",
            "🎯 The advancement demonstrates the ongoing evolution of technology.",
            "⚡️ This progress contributes to the overall growth of the sector."
        ]
    }
    
    take = random.choice(professional_openings.get(story_angle, professional_openings["general_development"]))
    
    # Add professional follow-up
    if story_angle == "regulatory_breakthrough":
        follow_up = "This milestone paves the way for future developments. 📈"
    elif story_angle == "business_move":
        follow_up = "The strategic implications are significant. 💼"
    elif story_angle == "product_launch":
        follow_up = "The market impact will be worth monitoring. 📊"
    elif story_angle == "financial_news":
        follow_up = "The financial implications are positive. 💰"
    elif story_angle == "technical_breakthrough":
        follow_up = "The technical implications are substantial. 🧠"
    else:
        follow_up = "The development represents positive progress. ✅"
    
    return f"{take}\n\n{follow_up}"


def _create_image_post_middle(story_angle: str, content: str) -> str:
    """Create engaging middle content for image posts."""
    
    # Extract key insights from content
    key_points = _extract_key_points(content)
    
    if key_points:
        middle = "🔍 Key insights:\n\n"
        for i, point in enumerate(key_points[:2], 1):  # Limit to 2 points for image posts
            middle += f"• {point}\n"
        middle += "\n"
    else:
        # Create engaging content based on story angle
        angle_content = {
            "regulatory_breakthrough": "This regulatory green light opens doors for institutional adoption and mainstream acceptance.",
            "business_move": "Strategic partnerships and acquisitions are reshaping the competitive landscape.",
            "product_launch": "New innovations are hitting the market at an unprecedented pace.",
            "financial_news": "Investment flows are accelerating the pace of technological development.",
            "technical_breakthrough": "We're witnessing breakthroughs that seemed impossible just months ago.",
            "competitive_dynamics": "The race for market dominance is driving innovation faster than ever.",
            "general_development": "The pace of progress continues to accelerate across all sectors."
        }
        middle = f"💡 {angle_content.get(story_angle, 'Innovation continues to surprise us.')}\n\n"
    
    # Add engaging question or statement
    engaging_questions = {
        "regulatory_breakthrough": "What does this mean for the future of the industry? 🤔",
        "business_move": "Who will be the next to make a strategic move? 🎯",
        "product_launch": "How will this change the game? 🚀",
        "financial_news": "Where will the money flow next? 💰",
        "technical_breakthrough": "What's the next breakthrough on the horizon? 🔮",
        "competitive_dynamics": "Who's leading the innovation race? 🏆",
        "general_development": "What's the next big thing we should watch? 👀"
    }
    
    middle += engaging_questions.get(story_angle, "The future is unfolding before our eyes. ✨")
    
    return middle


def _add_viral_elements(title: str, content: str, story_angle: str) -> str:
    """Add strategic mentions, hashtags, and viral elements for maximum engagement."""
    
    # Strategic mentions based on story angle
    strategic_mentions = _get_strategic_mentions(story_angle, title, content)
    
    # Extract and hashtag key keywords
    key_hashtags = _extract_key_hashtags(title, content)
    
    # Add viral closing statements
    viral_closing = _get_viral_closing(story_angle)
    
    # Combine all viral elements
    viral_section = ""
    
    if strategic_mentions:
        viral_section += f"👥 Tagging the key players: {strategic_mentions}\n\n"
    
    if key_hashtags:
        viral_section += f"🏷️ Trending: {key_hashtags}\n\n"
    
    if viral_closing:
        viral_section += f"💭 {viral_closing}\n\n"
    
    return viral_section


def _get_strategic_mentions(story_angle: str, title: str, content: str) -> str:
    """Get strategic mentions for maximum visibility and virality."""
    
    # Company/entity mentions
    company_mentions = {
        "openai": "@OpenAI @sama",
        "google": "@Google @sundarpichai",
        "microsoft": "@Microsoft @satyanadella",
        "anthropic": "@AnthropicAI @dario_amodei",
        "deepmind": "@DeepMind @demishassabis",
        "ethereum": "@ethereum @VitalikButerin",
        "bitcoin": "@Bitcoin @SBF_FTX",
        "a16z": "@a16z @marcandreessen",
        "sequoia": "@sequoia @michael_moritz",
        "ycombinator": "@ycombinator @paulg"
    }
    
    # Story-specific mentions
    story_mentions = {
        "regulatory_breakthrough": "@SECGov @GaryGensler @WhiteHouse",
        "business_move": "@elonmusk @cz_binance @SBF_FTX",
        "product_launch": "@OpenAI @GoogleAI @Microsoft",
        "financial_news": "@CNBC @Bloomberg @WSJ",
        "technical_breakthrough": "@MIT @Stanford @Berkeley"
    }
    
    # Check for company mentions in title/content
    mentions = []
    for company, handle in company_mentions.items():
        if company.lower() in (title + " " + content).lower():
            mentions.append(handle)
    
    # Add story-specific mentions
    if story_angle in story_mentions:
        mentions.append(story_mentions[story_angle])
    
    # Add trending mentions
    trending_mentions = ["@balajis", "@naval", "@pmarca", "@elonmusk", "@VitalikButerin"]
    mentions.extend(trending_mentions[:2])  # Limit to 2 trending mentions
    
    return " ".join(mentions[:4])  # Limit total mentions


def _extract_key_hashtags(title: str, content: str) -> str:
    """Extract and hashtag key keywords for maximum visibility."""
    
    # Core technology hashtags
    core_hashtags = ["#AI", "#Web3", "#DeFi", "#Crypto", "#Blockchain"]
    
    # Story-specific hashtags
    story_hashtags = {
        "regulatory_breakthrough": ["#Regulation", "#Compliance", "#Innovation"],
        "business_move": ["#Business", "#Strategy", "#Partnership"],
        "product_launch": ["#ProductLaunch", "#Innovation", "#Technology"],
        "financial_news": ["#Finance", "#Investment", "#Markets"],
        "technical_breakthrough": ["#Tech", "#Innovation", "#Breakthrough"],
        "competitive_dynamics": ["#Competition", "#Strategy", "#Market"],
        "general_development": ["#Innovation", "#Future", "#Technology"]
    }
    
    # Extract keywords from title/content
    text = (title + " " + content).lower()
    keyword_hashtags = []
    
    # Technology keywords
    tech_keywords = {
        "ai": "#AI", "artificial intelligence": "#AI", "machine learning": "#ML",
        "ethereum": "#Ethereum", "bitcoin": "#Bitcoin", "blockchain": "#Blockchain",
        "defi": "#DeFi", "nft": "#NFT", "dao": "#DAO", "web3": "#Web3",
        "funding": "#Funding", "investment": "#Investment", "startup": "#Startup",
        "partnership": "#Partnership", "acquisition": "#Acquisition"
    }
    
    for keyword, hashtag in tech_keywords.items():
        if keyword in text and hashtag not in keyword_hashtags:
            keyword_hashtags.append(hashtag)
    
    # Combine all hashtags
    all_hashtags = core_hashtags + keyword_hashtags
    
    # Limit to 8 hashtags for optimal engagement
    return " ".join(all_hashtags[:8])


def _get_viral_closing(story_angle: str) -> str:
    """Get viral closing statements to boost engagement."""
    
    viral_closings = {
        "regulatory_breakthrough": "The future of regulation is being written right now. What's your take? 🤔",
        "business_move": "Who's next to make a power move? The chess game continues... ♟️",
        "product_launch": "Will this change everything, or just our Twitter feeds? The jury's out! 🧑‍⚖️",
        "financial_news": "Money talks, but what is it saying? The plot thickens... 📊",
        "technical_breakthrough": "Humanity just leveled up. What's the next breakthrough? 🔮",
        "competitive_dynamics": "The race is on! Who's leading the innovation charge? 🏃‍♂️",
        "general_development": "The future is unfolding before our eyes. Are you ready? ✨"
    }
    
    return viral_closings.get(story_angle, "The future is now. What's next? 🚀")


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
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, " ".join(key_points), "general_development")
    content += viral_elements
    
    content += f"🔗 {url}"
    
    return content


def _format_professional_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in professional style."""
    content = f"📊 {title}\n\n"
    content += "Key highlights:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"• {point}\n"
    
    content += "\nThis represents a significant advancement in the field.\n\n"
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, " ".join(key_points), "general_development")
    content += viral_elements
    
    content += f"Read more: {url}"
    
    return content


def _format_witty_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in witty style."""
    content = f"🤖 {title}\n\n"
    content += "Plot twist: The future is happening faster than expected! Here's what's going down:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"{i}. {point}\n"
    
    content += "\nThe AI/Web3 crossover we've been waiting for? It's here, and it's spectacular.\n\n"
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, " ".join(key_points), "general_development")
    content += viral_elements
    
    content += f"🎬 {url}"
    
    return content


def _format_hype_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in hype style."""
    content = f"🔥 {title}\n\n"
    content += "THIS IS HUGE! 🚀\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"💥 {point}\n"
    
    content += "\nThe game is changing, and we're here for it! This is what innovation looks like.\n\n"
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, " ".join(key_points), "general_development")
    content += viral_elements
    
    content += f"⚡ {url}"
    
    return content


def _format_default_post(title: str, key_points: List[str], url: str) -> str:
    """Format content in default style."""
    content = f"📰 {title}\n\n"
    content += "Key points:\n\n"
    
    for i, point in enumerate(key_points, 1):
        content += f"{i}. {point}\n"
    
    content += "\n"
    
    # Add viral elements for maximum engagement
    viral_elements = _add_viral_elements(title, " ".join(key_points), "general_development")
    content += viral_elements
    
    content += f"Read the full story: {url}"
    
    return content
