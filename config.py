import os

# ── CREDENTIALS (set these as environment variables, never hardcode) ──────────
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
REDDIT_CLIENT_ID   = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SECRET      = os.environ["REDDIT_SECRET"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

# ── YOUR PORTFOLIO ────────────────────────────────────────────────────────────
# Format: "TICKER": (shares_held, average_buy_price)
# Use Yahoo Finance ticker format (e.g. VWCE.DE for Euronext, VUAA.AS for Amsterdam)
PORTFOLIO = {
    # "VWCE.DE":  (10,  142.00),
    # "VUAA.AS":  (5,   95.00),
    # "NVDA":     (2,   800.00),
    # "MSFT":     (1,   380.00),
}

# Portfolio currency label (just for display)
PORTFOLIO_CURRENCY = "€"

# ── DATA SOURCES ──────────────────────────────────────────────────────────────
SUBREDDITS = [
    "investing",
    "wallstreetbets",
    "stocks",
    "economics",
    "SecurityAnalysis",
    "GlobalMarkets",
]

NEWS_FEEDS = {
    "Reuters":    "https://feeds.reuters.com/reuters/businessNews",
    "CNBC":       "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories",
    "FT":         "https://www.ft.com/rss/home/uk",
    "Bloomberg":  "https://feeds.bloomberg.com/markets/news.rss",
}

# Posts per subreddit and headlines per feed to pull
REDDIT_POSTS_PER_SUB = 12
HEADLINES_PER_FEED   = 7

# ── HISTORY ───────────────────────────────────────────────────────────────────
HISTORY_DIR         = "history"   # folder where daily JSON snapshots are saved
HISTORY_DAYS_FULL   = 7           # last N days: full briefing text passed to Claude
HISTORY_DAYS_THEMES = 30          # last N days: headlines only (compressed)
HISTORY_DAYS_SUMMARY = 90         # last N days: one-line summary (very compressed)

# ── BRIEFING STYLE ────────────────────────────────────────────────────────────
# Change this to your name so Claude addresses you personally
YOUR_NAME = "Mikus"
