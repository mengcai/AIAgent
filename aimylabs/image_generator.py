from __future__ import annotations

import asyncio
import base64
import json
import os
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class ImageGenerationResult:
    success: bool
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    error: Optional[str] = None


async def generate_openai_image(
    prompt: str,
    openai_api_key: str,
    openai_image_model: str = "dall-e-3",
    style: str = "realistic",
    aspect_ratio: str = "1:1"
) -> ImageGenerationResult:
    """
    Generate an image using OpenAI's DALL-E API.
    
    Args:
        prompt: Text description of the image to generate
        openai_api_key: OpenAI API key
        openai_image_model: OpenAI image model to use (dall-e-2, dall-e-3)
        style: Image style (realistic, artistic, cartoon, etc.)
        aspect_ratio: Image aspect ratio (1:1, 16:9, etc.)
    
    Returns:
        ImageGenerationResult with success status and image data
    """
    if not openai_api_key or not openai_api_key.strip():
        return ImageGenerationResult(success=False, error="No OpenAI API key provided")
    
    # Enhanced prompt for better image generation
    enhanced_prompt = f"Create a {style} image: {prompt}. Style: professional, high-quality, relevant to AI/Web3 technology news. Make it eye-catching and shareable on social media."
    
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    # Map aspect ratio to DALL-E size
    size_mapping = {
        "1:1": "1024x1024",
        "16:9": "1792x1024",
        "9:16": "1024x1792"
    }
    
    body = {
        "model": openai_image_model,
        "prompt": enhanced_prompt,
        "n": 1,
        "size": size_mapping.get(aspect_ratio, "1024x1024"),
        "quality": "hd" if openai_image_model == "dall-e-3" else "standard"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=body
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # Extract image URL from OpenAI's response
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]
                    image_url = image_data.get("url")
                    
                    if image_url:
                        # Download the image data
                        img_resp = await client.get(image_url)
                        if img_resp.status_code == 200:
                            return ImageGenerationResult(
                                success=True,
                                image_url=image_url,
                                image_data=img_resp.content
                            )
                
                return ImageGenerationResult(success=False, error="No image data in response")
            else:
                return ImageGenerationResult(
                    success=False, 
                    error=f"OpenAI API error: {resp.status_code} - {resp.text}"
                )
                
    except Exception as e:
        return ImageGenerationResult(success=False, error=f"Image generation failed: {str(e)}")


def create_image_prompt_from_news(title: str, content: str, tone: str) -> str:
    """
    Create an optimized image prompt based on news content and tone.
    
    Args:
        title: News article title
        content: Article content summary
        tone: Desired tone (witty, professional, hype, meme)
    
    Returns:
        Optimized prompt for image generation
    """
    # Extract key concepts from the news
    key_concepts = []
    
    # AI-related keywords
    ai_keywords = ["AI", "artificial intelligence", "machine learning", "GPT", "LLM", "neural network"]
    for keyword in ai_keywords:
        if keyword.lower() in (title + " " + content).lower():
            key_concepts.append(keyword)
    
    # Web3-related keywords
    web3_keywords = ["blockchain", "crypto", "DeFi", "NFT", "Web3", "smart contract"]
    for keyword in web3_keywords:
        if keyword.lower() in (title + " " + content).lower():
            key_concepts.append(keyword)
    
    # Tone-specific styling
    tone_styles = {
        "witty": "playful, clever, with subtle humor",
        "professional": "clean, corporate, business-focused",
        "hype": "energetic, dynamic, exciting",
        "meme": "fun, viral, internet culture style",
        "thought_leader": "sophisticated, insightful, premium"
    }
    
    style = tone_styles.get(tone, "professional")
    
    if not key_concepts:
        key_concepts = ["technology", "innovation", "future"]
    
    # Create the image prompt
    prompt = f"Visual representation of: {title}. "
    prompt += f"Key elements: {', '.join(key_concepts[:3])}. "
    prompt += f"Style: {style}, modern tech aesthetic, suitable for social media sharing."
    
    return prompt


async def generate_news_image(
    title: str,
    content: str,
    tone: str,
    openai_api_key: str,
    openai_image_model: str = "dall-e-3"
) -> ImageGenerationResult:
    """
    Generate an image specifically for news content.
    
    Args:
        title: News article title
        content: Article content summary
        tone: Desired tone
        openai_api_key: OpenAI API key
        openai_image_model: OpenAI image model to use
    
    Returns:
        ImageGenerationResult with generated image
    """
    prompt = create_image_prompt_from_news(title, content, tone)
    
    # Choose aspect ratio based on content type
    aspect_ratio = "16:9" if len(content) > 500 else "1:1"
    
    return await generate_openai_image(
        prompt=prompt,
        openai_api_key=openai_api_key,
        openai_image_model=openai_image_model,
        style="realistic",
        aspect_ratio=aspect_ratio
    )
