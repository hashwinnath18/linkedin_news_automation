import os
import feedparser
import random
import textwrap
from datetime import datetime, timezone

from groq import Groq  # pip install groq

# AI / ML focused feeds only.
RSS_FEEDS = [
    # Data science / ML
    "https://feeds.feedburner.com/kdnuggets-data-science-news",

    # Core AI research & industry labs
    "https://openai.com/blog/rss",                # OpenAI blog
    "https://deepmind.com/blog/feed/basic",       # DeepMind blog
    "https://blog.google/technology/ai/rss/",     # Google AI blog
    "https://news.microsoft.com/source/topics/ai/feed/",  # Microsoft AI
    "https://machinelearning.apple.com/rss.xml",  # Apple ML research
    "https://bair.berkeley.edu/blog/feed.xml",    # Berkeley AI Research
    "https://lastweekin.ai/feed",                 # Curated AI news digest
    # You can add more AI-only feeds here later
]

MAX_FEED_SNIPPET_LENGTH = 1000  # chars to keep from the raw RSS summary before sending to LLM
MAX_DAYS_OLD = 3                # prefer items from last N days
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq model name
TARGET_SUMMARY_WORDS = 120       # shorter, high-signal post


# Keywords we care more about (to bias selection)
PRIORITY_KEYWORDS = [
    "agent", "agentic", "multi-agent",
    "autonomous", "autonomy",
    "military", "defense", "defence", "warfare", "army", "navy", "air force",
    "surveillance", "drone", "uav", "robotics", "robot",
    "industry", "industrial", "manufacturing", "factory", "supply chain",
    "deployment", "production", "enterprise"
]


def _entry_datetime(entry):
    for key in ("published_parsed", "updated_parsed"):
        dt_struct = getattr(entry, key, None)
        if dt_struct:
            return datetime(*dt_struct[:6], tzinfo=timezone.utc)
    return None


def _entry_text_for_scoring(entry):
    title = entry.get("title", "") or ""
    summary = entry.get("summary", "") or entry.get("description", "") or ""
    text = f"{title} {summary}".lower()
    return text


def _is_priority_entry(entry):
    text = _entry_text_for_scoring(entry)
    return any(kw in text for kw in PRIORITY_KEYWORDS)


def _choose_recent_entry(feed):
    now = datetime.now(timezone.utc)
    recent = []
    priority_recent = []

    for entry in feed.entries:
        dt = _entry_datetime(entry)
        if not dt:
            continue
        if (now - dt).days <= MAX_DAYS_OLD:
            recent.append(entry)
            if _is_priority_entry(entry):
                priority_recent.append(entry)

    # Prefer recent + priority (military, industry, agentic, etc.)
    if priority_recent:
        return random.choice(priority_recent)
    if recent:
        return random.choice(recent)

    # If nothing recent, look at all entries with priority keywords
    all_priority = [e for e in feed.entries if _is_priority_entry(e)]
    if all_priority:
        return random.choice(all_priority)

    # Fallback: any entry
    if feed.entries:
        return random.choice(feed.entries)
    return None


def _clean_feed_summary(raw_summary: str) -> str:
    """Crude HTML-ish cleanup + shortening for the RSS summary snippet."""
    summary = raw_summary.replace("\n", " ").replace("\r", " ")
    for tag in ["<p>", "</p>", "<br>", "<br/>", "<br />"]:
        summary = summary.replace(tag, " ")
    summary = " ".join(summary.split())
    if MAX_FEED_SNIPPET_LENGTH:
        summary = textwrap.shorten(
            summary,
            width=MAX_FEED_SNIPPET_LENGTH,
            placeholder="..."
        )
    return summary


def _summarize_with_llm(title: str, snippet: str, link: str) -> str | None:
    """
    Generate a short, engagement-triggering, first-person post
    in three tiny paragraphs, optimized for fast scrolling.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)
    except Exception:
        return None

    user_prompt = f"""
Write a short, personal AI commentary post in my voice. It should sound like I just came across this update, reflected on it for a moment, and am thinking aloud about its real-world potential.

The style must feel human, slightly conversational, subtly expert, and naturally varied from post to post.

FORMAT:
- **Exactly 3 short paragraphs**, 1–2 sentences each.
- ~70–120 words total.
- Flow should feel organic, not formulaic.

TONE STYLE (mix these naturally):
- First-person reflections: “I came across this…”, “I feel like…”, “It got me thinking…”, “What stood out to me…”
- Light expert cues: implications for agentic systems, deployment constraints, safety, scaling, autonomy.
- Human texture: small hedges (“I’m wondering whether…”, “It seems to me…”, “I get the sense that…”).
- No hype, no corporate noise, no buzzword stuffing.

CONTENT:
Paragraph 1 → A natural, personal reaction to discovering this update (what caught my attention & why).  
Paragraph 2 → What I personally feel this technology enables, plus a subtle expert insight (e.g., deployment, autonomy, operational reality, industry/military relevance).  
Paragraph 3 → A conversation-starting question (“Where else do you think this could fit?”, “How would you apply this?”, etc.).

RULES:
- No emojis, no hashtags, no lists.
- Must read as if written by a thoughtful engineer who follows AI developments closely.
- Vary sentence structure and tone slightly so not every post feels the same.

ARTICLE:
Title: {title}
Link: {link}
Snippet: {snippet}

Now write the post.
""".strip()



    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write first-person, high-engagement AI commentary "
                        "in three ultra-short paragraphs that trigger curiosity and discussion."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        )

        content = completion.choices[0].message.content.strip()
        return content or None
    except Exception:
        return None


def get_article():
    """
    Returns: (title, summary, link)
        - title: str (from the RSS entry)
        - summary: str (LLM-generated short engagement post if possible,
                     otherwise a short cleaned snippet)
        - link: str (article URL)
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

    if not link:
        raise RuntimeError(f"Entry has no link: {title}")

    # First build a cleaned, short snippet directly from the RSS entry (for fallback and as LLM context)
    snippet = _clean_feed_summary(raw_summary)

    # Try to upgrade to a richer LLM-based engagement post
    llm_summary = _summarize_with_llm(title, snippet, link)
    summary_out = llm_summary if llm_summary else snippet

    return title, summary_out, link


if __name__ == "__main__":
    t, s, l = get_article()
    print("Title:", t)
    print("Summary:", s)
    print("Link:", l)
