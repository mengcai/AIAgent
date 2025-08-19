## Aimylabs — Autonomous AI + Web3 News-to-X Agent

Aimylabs continuously monitors trusted AI and Web3 sources, distills key insights with an LLM, and automatically posts concise, engaging tweets (≤280 chars) to your X (Twitter) account on a schedule.

### Features
- **News collection**: Monitor curated RSS feeds from credible AI and Web3 sources; filter by recency and domain allowlist.
- **Summarization**: Use an LLM to craft tweet-ready, human-like summaries with optional hashtags/emojis and tone controls.
- **Scheduling**: Post automatically at configured daily times (e.g., 09:00 and 15:00) using a lightweight scheduler.
- **Customization**: Configure tone, frequency, hashtags, schedule times, dry-run, and source lists.
- **Safety**: De-duplicate and avoid re-posting the same links; basic domain allowlisting.

### Quick Start
1) Create and activate a virtual environment
```bash
python3 -m venv .venv && source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure environment
```bash
cp env.sample .env
# Fill in the required keys in .env
```

Required env vars for posting to X (Twitter):
- `X_CONSUMER_KEY`
- `X_CONSUMER_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Required env var for summarization (OpenAI; pluggable):
- `OPENAI_API_KEY`

Optional:
- `AIMYLABS_DB_PATH` — where to store the SQLite DB (default: `~/.aimylabs/aimylabs.db`).

4) Configure Aimylabs behavior
Edit `config.yaml` to control tone, hashtags, schedule, and sources.

5) Run once (dry-run)
```bash
python -m aimylabs.cli run --dry-run
```

6) Post for real (one cycle)
```bash
python -m aimylabs.cli run
```

7) Run the scheduler (keeps running)
```bash
python -m aimylabs.cli schedule
```

### Configuration (`config.yaml`)
```yaml
app:
  timezone: local          # 'local' or IANA TZ like 'America/Los_Angeles'
  dry_run: true            # if true, does not post; logs instead
  max_daily_posts: 2       # cap posts per day
  post_times: ["09:00", "15:00"]  # local times or TZ-aware per timezone

style:
  tone: professional       # professional | witty | hype
  use_emojis: true
  default_hashtags: ["#AI", "#Web3"]

sources:
  min_recency_hours: 36
  rss_feeds:
    # AI
    - https://openai.com/blog/rss.xml
    - https://www.deepmind.com/blog/rss.xml
    - https://www.anthropic.com/news/rss.xml
    - https://ai.googleblog.com/atom.xml
    - https://www.technologyreview.com/feed/tag/artificial-intelligence/
    # Web3
    - https://www.coindesk.com/arc/outboundfeeds/rss/
    - https://feeds.feedburner.com/TheMerkle
    - https://blog.chain.link/feed/
    - https://a16z.com/feed/

allowlist_domains:
  - openai.com
  - deepmind.com
  - anthropic.com
  - ai.googleblog.com
  - technologyreview.com
  - coindesk.com
  - themerkle.com
  - chain.link
  - a16z.com
```

### How it works
- Fetches recent articles via RSS.
- Filters by allowlisted domains and recency.
- Extracts readable content and feeds it to the LLM with a 280-char constraint and desired tone.
- Optionally appends configured hashtags.
- Posts via X API at configured times; records posted URLs to avoid duplicates.

### Development
- Formatting/linting is not enforced; keep code readable and well-structured.
- Key modules live under `aimylabs/`.

### Notes on X (Twitter) API access
- Posting programmatically requires appropriate API credentials and access tier. Ensure your developer account and app are authorized to post on behalf of your user.

### Disclaimer
This tool summarizes third-party content. Review outputs and ensure compliance with platform policies and applicable laws.


