"""
Editorial Bot - Editorial Generator
Uses Claude to write original editorials based on recent cinema news.
"""

import json
import logging
import hashlib
from datetime import datetime, timezone

import anthropic
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, AUTHOR_BYLINE

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
- Has a strong, attention-grabbing headline
- Is 3-5 paragraphs long
- Feels like a column in American Cinematographer or No Film School

Respond ONLY with valid JSON in this exact format (no markdown, no backticks):
{{
    "title": "Your Editorial Headline Here",
    "summary": "A 2-3 sentence teaser that hooks the reader.",
    "body": "The full editorial text, 3-5 paragraphs. Use plain text, no HTML.",
    "category": "One of: Camera Technology, Lens Technology, Streaming Industry, Virtual Production, Market Trends, Firmware Update",
    "companies": ["Company1", "Company2"],
    "technologies": ["Tech1", "Tech2"],
    "tags": ["tag1", "tag2", "tag3"],
    "industry_impact": "One sentence on why this matters for the industry."
}}"""


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
            max_tokens=2000,
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

        log.info(f"Editorial generated: {editorial['title'][:60]}")
        return editorial

    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Claude response as JSON: {e}")
        log.debug(f"Raw response: {raw[:500]}")
        return None
    except Exception as e:
        log.error(f"Claude API call failed: {e}")
        return None
