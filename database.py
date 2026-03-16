"""
Editorial Bot - Database
Reads recent news and saves editorials to the same Supabase table.
"""

import logging
from typing import Optional

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE

log = logging.getLogger(__name__)
_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def get_recent_articles(limit: int = 20) -> list:
    """Fetch the most recent news articles for editorial context."""
    try:
        db = get_client()
        result = (
            db.table(SUPABASE_TABLE)
            .select("title, summary, category, companies, tags, published_at, source, url")
            .neq("source", "CineList Editorial")  # skip previous editorials
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        log.error(f"Failed to fetch recent articles: {e}")
        return []


def editorial_exists_today(today_str: str) -> bool:
    """Check if we already published an editorial today."""
    try:
        db = get_client()
        result = (
            db.table(SUPABASE_TABLE)
            .select("id")
            .eq("source", "CineList Editorial")
            .gte("published_at", f"{today_str}T00:00:00Z")
            .lte("published_at", f"{today_str}T23:59:59Z")
            .execute()
        )
        return len(result.data) > 0
    except Exception as e:
        log.warning(f"Could not check for existing editorial: {e}")
        return False


def save_editorial(editorial: dict) -> bool:
    """Save the generated editorial to the cinema_news table."""
    try:
        db = get_client()

        # Combine the teaser summary and full body into one field
        # so the full editorial is displayed on the site.
        full_content = editorial.get("summary", "")
        if editorial.get("body"):
            full_content = editorial["summary"] + "\n\n" + editorial["body"]

        row = {
            "title": editorial["title"][:500],
            "summary": full_content,
            "source": "CineList Editorial",
            "url": editorial["url"],
            "published_at": editorial["published_at"],
            "category": editorial["category"],
            "companies": editorial.get("companies", []),
            "products": [],
            "technologies": editorial.get("technologies", []),
            "tags": editorial.get("tags", []) + ["editorial", "opinion"],
            "industry_impact": editorial.get("industry_impact", ""),
            "is_product_release": False,
            "relevance_score": 9,
            "image_url": editorial.get("image_url"),
        }
        db.table(SUPABASE_TABLE).upsert(row, on_conflict="url").execute()
        log.info(f"Editorial saved: {editorial['title'][:60]}")
        return True
    except Exception as e:
        log.error(f"Failed to save editorial: {e}")
        return False
