# Reddit Investing Community Digest

An open-source tool that surfaces the most upvoted discussions from Reddit's investing communities and major financial news outlets — delivered as a daily digest so you never miss what the community is talking about.

Built for Reddit users who want to stay meaningfully engaged with r/investing, r/stocks, r/economics, and related communities without having to scroll through everything manually.

---

## What it does

Every morning the tool:

1. **Reads the top posts** from investing-related subreddits (ranked by community upvotes — the crowd's own signal of what matters)
2. **Pulls headlines** from major financial news RSS feeds (Reuters, FT, CNBC, Bloomberg, MarketWatch)
3. **Summarises the themes** using Claude AI — what are people discussing, what's the market mood, what narratives are gaining traction
4. **Delivers a digest** to your Telegram

The result: a daily briefing that reflects what Reddit's investing communities are genuinely interested in — so you can join the most relevant conversations.

---

## Why this helps Reddit communities

Reddit's investing subreddits move fast. High-quality discussions get buried. This tool:

- **Surfaces what the community voted on** — only top posts by upvote count, reflecting genuine community interest
- **Drives re-engagement** — users who see a summary of what's trending come back to Reddit to read the full threads and participate
- **Helps moderators** understand what topics are dominating their communities each week
- **Never posts, votes, or interacts** — purely read-only

---

## Data sources

| Source | Type | Access |
|---|---|---|
| r/investing, r/stocks, r/wallstreetbets, r/economics, r/SecurityAnalysis, r/GlobalMarkets | Reddit API (read-only) | PRAW |
| Reuters, FT, CNBC, Bloomberg, MarketWatch | RSS feeds | Public |

**API usage is minimal:** one read request per subreddit per day, well within Reddit's rate limits.

---

## Setup

### Prerequisites
- Python 3.11+
- Reddit API credentials (script app)
- Anthropic API key
- Telegram bot token

### Install

```bash
git clone https://github.com/stoicpixel/financial-daily-briefing.git
cd financial-daily-briefing
pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `config.py` to set your portfolio and preferred subreddits.

### Run manually

```bash
python briefing.py
```

### Schedule (GitHub Actions)

The included `.github/workflows/daily_briefing.yml` runs the script automatically every weekday morning. Add your credentials as GitHub Secrets and it runs hands-free.

---

## Tech stack

- [PRAW](https://praw.readthedocs.io/) — Reddit API wrapper
- [feedparser](https://feedparser.readthedocs.io/) — RSS feed parsing
- [yfinance](https://github.com/ranaroussi/yfinance) — Live price data
- [Anthropic Claude](https://www.anthropic.com/) — AI summarisation
- [python-telegram-bot](https://python-telegram-bot.org/) — Telegram delivery

---

## Privacy & data handling

- **No user data is collected** — the tool only reads public post titles and scores
- **No data is stored** — each run fetches fresh data and discards it after sending the digest
- **No posting or interaction** — the tool never writes to Reddit in any form
- **Fully local or self-hosted** — your data stays on your own infrastructure

---

## Contributing

PRs welcome. If you want to add new subreddits, news sources, or delivery methods (email, Slack, Discord), open an issue or submit a pull request.

---

## License

MIT — free to use, modify, and distribute.
