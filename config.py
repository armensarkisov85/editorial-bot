"""
Editorial Bot - Config
Environment variables and constants.
"""

import os

# ── Supabase (same project as cinema-bot) ──────────────────────────────
SUPABASE_URL = "https://ypzdefbymopkbwlacrij.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlw"
    "emRlZmJ5bW9wa2J3bGFjcmlqIiwicm9sZSI6Im"
    "Fub24iLCJpYXQiOjE3NzI2MzAxODksImV4cCI6"
    "MjA4ODIwNjE4OX0.pTbbSNhF4yzfqvN1P1kvCey"
    "Z2HR-_fGWJ4tremlQ_EY"
)
SUPABASE_TABLE = "cinema_news"

# ── Anthropic API ──────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# ── Editorial persona ─────────────────────────────────────────────────
AUTHOR_NAME = "Armen Sarkisov"
AUTHOR_TITLE = "Tech Editor"
AUTHOR_BYLINE = f"{AUTHOR_NAME}, {AUTHOR_TITLE}"

# ── How many recent articles to read for context ──────────────────────
RECENT_ARTICLES_LIMIT = 20

# ── Pexels API (free, for editorial images) ───────────────────────────
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
