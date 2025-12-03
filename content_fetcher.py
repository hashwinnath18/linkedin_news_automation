import feedparser
import random
import textwrap
from datetime import datetime, timezone
from dateutil import tz

# RSS feeds focused on tech, AI, and ML.
# These are examples. The human can edit this list later if desired.
RSS_FEEDS = [
    "https://www.technologyreview.com/feed/",                 # MIT Tech Review
    "https://www.theverge.com/rss/index.xml",                 # The Verge (general tech)
    "https://feeds.feedburner.com/kdnuggets-data-science-news",  # KDNuggets / data science
    "https://rss.art19.com/dirty-ai",                         # Example AI-related RSS (can be changed)
]

MAX_SUMMARY_LENGTH = 300  # characters


def _parse_entry_date(entry):
    """
    Try to extract a datetime from various RSS date fields.
    Returns a timezone-aware datetime or None.
    """
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

    return None


def _choose_recent_entry(feed, max_days=3):
    """
    Prefer items from the last `max_days` days. Fall back to any item if none are recent.
    """
    now = datetime.now(timezone.utc)
    recent = []

    for entry in feed.entries:
        dt = _parse_entry_date(entry)
        if dt is None:
            continue
        age_days = (now - dt).days
        if age_days <= max_days:
            recent.append(entry)

    if recent:
        return random.choice(recent)
    elif feed.entries:
        return random.choice(feed.entries)
    else:
        return None


def get_article():
    """
    Pick one article from the configured RSS feeds.

    Returns:
        (title, summary, link) as a tuple of strings.

    Raises:
        RuntimeError if no article can be selected.
    """
    if not RSS_FEEDS:
        raise RuntimeError("No RSS feeds configured")

    feed_url = random.choice(RSS_FEEDS)
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        # `bozo` means the feed had parse errors.
        # We don't fail immediately; we may still have entries.
        pass

    entry = _choose_recent_entry(feed)
    if entry is None:
        raise RuntimeError(f"No entries found in feed: {feed_url}")

    title = entry.get("title", "Untitled").strip()
    link = entry.get("link", "").strip()
    summary_raw = (
        entry.get("summary")
        or entry.get("description")
        or ""
    )

    # Basic cleanup
    summary_clean = summary_raw.replace("\n", " ").replace("\r", " ")
    # Remove simple HTML tags; this is intentionally naive.
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        summary_clean = summary_clean.replace(tag, " ")

    summary_clean = " ".join(summary_clean.split())

    # Shorten to a reasonable length for LinkedIn
    summary = textwrap.shorten(
        summary_clean,
        width=MAX_SUMMARY_LENGTH,
        placeholder="..."
    )

    if not link:
        raise RuntimeError(f"Entry has no link: title={title}")

    return title, summary, link


if __name__ == "__main__":
    # Simple manual test
    t, s, l = get_article()
    print("Title:", t)
    print("Summary:", s)
    print("Link:", l)
