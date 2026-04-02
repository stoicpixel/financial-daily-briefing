"""
Daily Financial Briefing
Pulls Reddit + news data, analyzes your portfolio, sends a Telegram message.
Stores daily history and uses it to reason about trends and future opportunities.
"""

import json
import os
import praw
import feedparser
import anthropic
import requests
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

import config


# ── PORTFOLIO ────────────────────────────────────────────────────────────────

def get_portfolio_status():
    if not config.PORTFOLIO:
        return "No portfolio configured."

    lines = []
    total_invested = 0.0
    total_current  = 0.0

    for ticker, (shares, avg_price) in config.PORTFOLIO.items():
        try:
            data        = yf.Ticker(ticker)
            current     = data.fast_info["last_price"]
            invested    = shares * avg_price
            current_val = shares * current
            pnl_pct     = ((current - avg_price) / avg_price) * 100
            pnl_abs     = current_val - invested
            total_invested += invested
            total_current  += current_val
            sign = "▲" if pnl_pct >= 0 else "▼"
            lines.append(
                f"  {ticker}: {current:.2f} | "
                f"{sign} {pnl_pct:+.1f}% ({config.PORTFOLIO_CURRENCY}{pnl_abs:+.0f}) | "
                f"Pos: {config.PORTFOLIO_CURRENCY}{current_val:.0f}"
            )
        except Exception as e:
            lines.append(f"  {ticker}: price unavailable ({e})")

    if total_invested > 0:
        total_pnl_pct = ((total_current - total_invested) / total_invested) * 100
        total_pnl_abs = total_current - total_invested
        lines.append(
            f"\n  TOTAL: {config.PORTFOLIO_CURRENCY}{total_current:.0f} | "
            f"Invested: {config.PORTFOLIO_CURRENCY}{total_invested:.0f} | "
            f"P&L: {config.PORTFOLIO_CURRENCY}{total_pnl_abs:+.0f} ({total_pnl_pct:+.1f}%)"
        )

    return "\n".join(lines)


# ── REDDIT ───────────────────────────────────────────────────────────────────

def get_reddit_posts():
    reddit = praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_SECRET,
        user_agent="financial_briefing/1.0",
    )
    posts = []
    for sub in config.SUBREDDITS:
        try:
            for post in reddit.subreddit(sub).top(
                time_filter="day", limit=config.REDDIT_POSTS_PER_SUB
            ):
                posts.append(
                    f"[r/{sub} | {post.score:,} upvotes] {post.title}"
                )
        except Exception as e:
            posts.append(f"[r/{sub}] Error fetching: {e}")
    return "\n".join(posts)


# ── NEWS ──────────────────────────────────────────────────────────────────────

def get_news():
    headlines = []
    for source, url in config.NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[: config.HEADLINES_PER_FEED]:
                headlines.append(f"[{source}] {entry.title}")
        except Exception as e:
            headlines.append(f"[{source}] Error fetching: {e}")
    return "\n".join(headlines)


# ── HISTORY ───────────────────────────────────────────────────────────────────

def save_history(date_str, headlines, reddit_posts, portfolio_snapshot, briefing_text):
    """Save today's data as a JSON file in the history folder."""
    history_dir = Path(config.HISTORY_DIR)
    history_dir.mkdir(exist_ok=True)

    record = {
        "date":               date_str,
        "headlines":          headlines.split("\n") if headlines else [],
        "reddit_posts":       reddit_posts.split("\n") if reddit_posts else [],
        "portfolio_snapshot": portfolio_snapshot,
        "briefing":           briefing_text,
    }

    filepath = history_dir / f"{date_str}.json"
    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)
    print(f"  History saved to {filepath}")


def load_history():
    """
    Load previous briefings in three tiers:
    - Last 7 days:   full briefing text
    - Last 8–30 days: headlines list only
    - Last 31–90 days: date + first line of briefing only
    """
    history_dir = Path(config.HISTORY_DIR)
    if not history_dir.exists():
        return "", "", ""

    today = datetime.now().date()
    full_entries    = []  # last 7 days
    medium_entries  = []  # last 8–30 days
    summary_entries = []  # last 31–90 days

    # Load all history files sorted newest-first
    files = sorted(history_dir.glob("*.json"), reverse=True)

    for filepath in files:
        try:
            with open(filepath) as f:
                record = json.load(f)

            file_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
            days_ago  = (today - file_date).days

            if days_ago == 0:
                continue  # skip today (not saved yet)
            elif days_ago <= config.HISTORY_DAYS_FULL:
                full_entries.append(
                    f"--- {record['date']} ---\n{record['briefing']}"
                )
            elif days_ago <= config.HISTORY_DAYS_THEMES:
                headlines_preview = "\n".join(record.get("headlines", [])[:5])
                medium_entries.append(
                    f"{record['date']}:\n{headlines_preview}"
                )
            elif days_ago <= config.HISTORY_DAYS_SUMMARY:
                first_line = record["briefing"].split("\n")[0][:120] if record.get("briefing") else ""
                summary_entries.append(f"{record['date']}: {first_line}")

        except Exception:
            continue

    return (
        "\n\n".join(full_entries)    or "No recent history yet.",
        "\n\n".join(medium_entries)  or "No data for this period.",
        "\n".join(summary_entries)   or "No data for this period.",
    )


# ── AI BRIEFING ───────────────────────────────────────────────────────────────

def generate_briefing(portfolio, reddit, news, history_full, history_medium, history_summary):
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    today  = datetime.now().strftime("%A, %B %d %Y")

    portfolio_section = (
        f"Here is {config.YOUR_NAME}'s current portfolio with live prices and P&L:\n{portfolio}"
        if portfolio != "No portfolio configured."
        else "No portfolio configured yet."
    )

    prompt = f"""You are {config.YOUR_NAME}'s personal investment manager. Today is {today}.

Your job is not to report what already happened — prices have already moved on that.
Your job is to think ONE STEP AHEAD: what has not priced in yet? What comes next?

═══════════════════════════════════════
HISTORICAL CONTEXT
═══════════════════════════════════════

LAST {config.HISTORY_DAYS_FULL} DAYS — full briefings:
{history_full}

LAST 8–{config.HISTORY_DAYS_THEMES} DAYS — top headlines:
{history_medium}

LAST 31–{config.HISTORY_DAYS_SUMMARY} DAYS — summary:
{history_summary}

═══════════════════════════════════════
TODAY'S DATA
═══════════════════════════════════════

PORTFOLIO:
{portfolio_section}

REDDIT (top posts by upvotes):
{reddit}

NEWS HEADLINES:
{news}

═══════════════════════════════════════
YOUR BRIEFING
═══════════════════════════════════════

Write a sharp, forward-looking briefing with these sections:

1. CAUSAL CHAIN
   Where did today's reality come from? Connect today's events to earlier signals
   in the history above. Example: "The oil spike today is the 3rd-order effect
   of the Iran tensions flagged 2 weeks ago → gold rose first → now energy."
   If no history yet, skip this section.

2. WHAT COMES NEXT
   What second and third-order effects have NOT priced in yet?
   Think in chains: X is happening → therefore Y should follow → then Z.
   Be specific about timing (days / weeks / months).

3. OPPORTUNITY WINDOW (1–4 weeks)
   What specific assets or sectors are likely to move BEFORE the market fully
   prices this in? For each: ticker or sector, direction (long/avoid),
   reasoning in one sentence, estimated window.
   Rate confidence: HIGH / MEDIUM / LOW.

4. PORTFOLIO HEALTH
   Any positions directly affected by today's developments or the trends above?
   Skip if no portfolio configured.

5. ONE-LINE TAKEAWAY

Tone: direct, no fluff. Write like a sharp friend who trades for a living.
Max 500 words."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ── TELEGRAM ──────────────────────────────────────────────────────────────────

def send_telegram(text):
    date_str = datetime.now().strftime("%b %d, %Y")
    full_msg = f"📊 *Daily Briefing — {date_str}*\n\n{text}"

    resp = requests.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id":    config.TELEGRAM_CHAT_ID,
            "text":       full_msg,
            "parse_mode": "Markdown",
        },
        timeout=10,
    )
    if resp.status_code == 200:
        print("Sent to Telegram.")
    else:
        print(f"Telegram error {resp.status_code}: {resp.text}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Running briefing at {datetime.now().strftime('%H:%M %Z')}...")

    print("  Loading history...")
    history_full, history_medium, history_summary = load_history()

    print("  Fetching portfolio prices...")
    portfolio = get_portfolio_status()

    print("  Fetching Reddit posts...")
    reddit = get_reddit_posts()

    print("  Fetching news headlines...")
    news = get_news()

    print("  Generating briefing with Claude...")
    briefing = generate_briefing(
        portfolio, reddit, news,
        history_full, history_medium, history_summary
    )

    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60 + "\n")

    print("  Saving history...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    save_history(today_str, news, reddit, portfolio, briefing)

    send_telegram(briefing)


if __name__ == "__main__":
    main()
