"""
Editorial Bot - Main
Runs once daily. Reads recent cinema news, generates an original
editorial by Armen Sarkisov (Tech Editor), and saves it to Supabase.
"""

import logging
import sys
from datetime import datetime, timezone

from config import RECENT_ARTICLES_LIMIT, AUTHOR_BYLINE
from database import get_recent_articles, editorial_exists_today, save_editorial
from editorial import generate_editorial

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("editorial-bot")


def main():
    log.info(f"=== Editorial Bot started — {AUTHOR_BYLINE} ===")

    # Step 1: Check if we already wrote an editorial today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if editorial_exists_today(today):
        log.info("Editorial already published today. Skipping.")
        return

    # Step 2: Read recent news articles
    log.info(f"Fetching {RECENT_ARTICLES_LIMIT} recent articles for context...")
    articles = get_recent_articles(limit=RECENT_ARTICLES_LIMIT)

    if not articles:
        log.warning("No recent articles found. Nothing to write about.")
        return

    log.info(f"Found {len(articles)} articles. Generating editorial...")

    # Step 3: Generate the editorial with Claude
    editorial = generate_editorial(articles)

    if not editorial:
        log.error("Editorial generation failed.")
        sys.exit(1)

    # Step 4: Save to Supabase
    log.info(f"Saving: \"{editorial['title'][:60]}\"")
    success = save_editorial(editorial)

    if success:
        log.info("Editorial published successfully!")
    else:
        log.error("Failed to save editorial.")
        sys.exit(1)

    log.info("=== Editorial Bot finished ===")


if __name__ == "__main__":
    main()
