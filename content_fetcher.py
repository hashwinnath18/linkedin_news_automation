import feedparser
import random
import textwrap
from datetime import datetime, timezone

# Tech + AI/ML oriented feeds. You can tweak this list.
RSS_FEEDS = [
    "https://www.technologyreview.com/feed/",                  # MIT Tech Review
    "https://www.theverge.com/rss/index.xml",                  # General tech
    "https://feeds.feedburner.com/kdnuggets-data-science-news" # Data science / ML
]

MAX_SUMMARY_LENGTH = 300  # characters
MAX_DAYS_OLD = 3          # prefer items from last N days


def _entry_datetime(entry):
    for key in ("published_parsed", "updated_parsed"):
        dt_struct = getattr(entry, key, None)
        if dt_struct:
            return datetime(*dt_struct[:6], tzinfo=timezone.utc)
    return None


def _choose_recent_entry(feed):
    now = datetime.now(timezone.utc)
    recent = []

    for entry in feed.entries:
        dt = _entry_datetime(entry)
        if not dt:
            continue
        if (now - dt).days <= MAX_DAYS_OLD:
            recent.append(entry)

    if recent:
        return random.choice(recent)
    elif feed.entries:
        return random.choice(feed.entries)
    return None


def get_article():
    """
    Returns: (title, summary, link)
    Raises: RuntimeError if nothing usable is found.
    """
    if not RSS_FEEDS:
        raise RuntimeError("No RSS feeds configured.")

    feed_url = random.choice(RSS_FEEDS)
    feed = feedparser.parse(feed_url)

    entry = _choose_recent_entry(feed)
    if not entry:
        raise RuntimeError(f"No entries found for feed: {feed_url}")

    title = entry.get("title", "Untitled").strip()
    link = entry.get("link", "").strip()
    raw_summary = (
        entry.get("summary")
        or entry.get("description")
        or ""
    )

    # crude cleanup
    summary = raw_summary.replace("\n", " ").replace("\r", " ")
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        summary = summary.replace(tag, " ")
    summary = " ".join(summary.split())

    summary = textwrap.shorten(summary, width=MAX_SUMMARY_LENGTH, placeholder="...")

    if not link:
        raise RuntimeError(f"Entry has no link: {title}")

    return title, summary, link


if __name__ == "__main__":
    t, s, l = get_article()
    print("Title:", t)
    print("Summary:", s)
    print("Link:", l)
