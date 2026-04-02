"""
Daily Financial Briefing
Pulls Reddit + news data, analyzes your portfolio, sends a Telegram message.
"""

import praw
import feedparser
import anthropic
import requests
import yfinance as yf
from datetime import datetime

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
            data         = yf.Ticker(ticker)
            current      = data.fast_info["last_price"]
            invested     = shares * avg_price
            current_val  = shares * current
            pnl_pct      = ((current - avg_price) / avg_price) * 100
            pnl_abs      = current_val - invested
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


# ── AI BRIEFING ───────────────────────────────────────────────────────────────

def generate_briefing(portfolio, reddit, news):
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    today  = datetime.now().strftime("%A, %B %d %Y")

    portfolio_section = (
        f"Here is {config.YOUR_NAME}'s current portfolio with live prices and P&L:\n{portfolio}"
        if portfolio != "No portfolio configured."
        else "No portfolio configured yet."
    )

    prompt = f"""You are {config.YOUR_NAME}'s personal investment manager. Today is {today}.

{portfolio_section}

Today's top Reddit investing discussions (sorted by upvotes):
{reddit}

Today's financial news headlines:
{news}

Write a daily briefing for {config.YOUR_NAME} with these sections:

1. PORTFOLIO HEALTH
   Review each position. Note anything up/down significantly today.
   Flag any positions impacted by today's news. If no portfolio, skip this.

2. MARKET MOOD
   Risk-on or risk-off? Fear or greed? One paragraph.

3. TOP 3 THEMES TODAY
   What is the market conversation dominated by? Keep it punchy.

4. ACTION ITEMS
   Anything worth acting on, or is it a hold-steady day?
   Be specific — vague advice is useless.

5. ONE-LINE TAKEAWAY

Tone: direct, sharp, no corporate speak. Write like a smart friend texting you.
Maximum 400 words total."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
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

    print("  Fetching portfolio prices...")
    portfolio = get_portfolio_status()

    print("  Fetching Reddit posts...")
    reddit = get_reddit_posts()

    print("  Fetching news headlines...")
    news = get_news()

    print("  Generating briefing with Claude...")
    briefing = generate_briefing(portfolio, reddit, news)

    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60 + "\n")

    send_telegram(briefing)


if __name__ == "__main__":
    main()
