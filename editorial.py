"""
Editorial Bot - Editorial Generator
Uses Claude to write original editorials based on recent cinema news.
Fetches relevant images from Pexels.
"""

import json
import logging
import hashlib
from datetime import datetime, timezone

import anthropic
import requests
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, AUTHOR_BYLINE, PEXELS_API_KEY

log = logging.getLogger(__name__)


def _build_prompt(articles: list) -> str:
    """Build the prompt with recent articles as context."""

    # Format recent articles into a readable list
    article_list = ""
    for i, art in enumerate(articles, 1):
        article_list += (
            f"\n{i}. [{art.get('category', 'General')}] {art['title']}\n"
            f"   Source: {art.get('source', 'Unknown')} | "
            f"Published: {art.get('published_at', 'N/A')}\n"
            f"   Summary: {art.get('summary', 'No summary')}\n"
            f"   Companies: {', '.join(art.get('companies', []) or [])}\n"
            f"   Tags: {', '.join(art.get('tags', []) or [])}\n"
        )

    return f"""You are {AUTHOR_BYLINE} at CineList Intel, a respected voice in the cinema 
technology world. You write sharp, insightful editorials for camera department professionals: 
DPs, 1st ACs, 2nd ACs, DITs, and operators.

Here are the most recent news stories from the cinema technology world:

{article_list}

Based on these recent stories, write an ORIGINAL EDITORIAL that:
- Identifies a compelling trend, tension, or insight connecting one or more of these stories
- Offers your professional opinion and analysis (not just a summary)
- Is relevant and useful to working camera department professionals
- Has a clear, factual headline — no hype, no clickbait, no dramatic metaphors (never use words like "wars," "arms race," "revolution," "game-changer," "battle," "race"). Write headlines the way CineD or American Cinematographer would
- Is 5-7 paragraphs long with substantial, detailed analysis in each paragraph
- Feels like a column in American Cinematographer or No Film School

Respond ONLY with valid JSON in this exact format (no markdown, no backticks):
{{
    "title": "Your Editorial Headline Here",
    "summary": "A 2-3 sentence teaser that hooks the reader.",
    "body": "The full editorial text, 5-7 substantial paragraphs. Separate each paragraph with two newlines. Use plain text, no HTML.",
    "category": "One of: Camera Technology, Lens Technology, Streaming Industry, Virtual Production, Market Trends, Firmware Update",
    "companies": ["Company1", "Company2"],
    "technologies": ["Tech1", "Tech2"],
    "tags": ["tag1", "tag2", "tag3"],
    "industry_impact": "One sentence on why this matters for the industry.",
    "image_search": "A 2-4 word search query for finding a relevant cinematic photo (e.g. 'cinema camera filmmaking', 'film set production', 'camera lens closeup'). Focus on professional filmmaking imagery."
}}"""


def _fetch_pexels_image(query: str) -> str | None:
    """Search Pexels for a relevant image and return the URL."""
    if not PEXELS_API_KEY:
        log.warning("PEXELS_API_KEY not set, skipping image fetch")
        return None

    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": query, "per_page": 5, "orientation": "landscape"}
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        photos = data.get("photos", [])
        if not photos:
            log.warning(f"No Pexels results for: {query}")
            return None

        # Pick the first landscape photo, use the 'large' size
        photo = photos[0]
        image_url = photo["src"].get("large2x") or photo["src"].get("large")
        log.info(f"Pexels image found: {image_url[:80]}...")
        return image_url

    except Exception as e:
        log.error(f"Pexels image fetch failed: {e}")
        return None


def generate_editorial(articles: list) -> dict | None:
    """Call Claude to generate an editorial based on recent news."""

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY is not set")
        return None

    if not articles:
        log.warning("No articles to base editorial on")
        return None

    prompt = _build_prompt(articles)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()

        # Clean up if Claude wraps in backticks
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        editorial = json.loads(raw)

        # Add metadata
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        slug = hashlib.md5(editorial["title"].encode()).hexdigest()[:10]
        editorial["url"] = f"https://cinelist.pro/editorial/{date_str}-{slug}"
        editorial["published_at"] = now.isoformat()

        # Fetch a relevant image from Pexels
        image_query = editorial.get("image_search", "cinema camera filmmaking")
        image_url = _fetch_pexels_image(image_query)
        if image_url:
            editorial["image_url"] = image_url
        else:
            editorial["image_url"] = None

        log.info(f"Editorial generated: {editorial['title'][:60]}")
        return editorial

    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Claude response as JSON: {e}")
        log.debug(f"Raw response: {raw[:500]}")
        return None
    except Exception as e:
        log.error(f"Claude API call failed: {e}")
        return None
