from content_fetcher import get_article
from linkedin_poster import post_to_linkedin


def build_caption(title: str, summary: str, link: str) -> str:
    """
    Build a LinkedIn-friendly caption for tech / AI / ML content.
    """
    lines = [
        f"🚀 {title}",
        "",
        summary,
        "",
        f"🔗 Read more: {link}",
        "",
        "#AI #MachineLearning #Tech #Trending"
    ]
    return "\n".join(lines)


def main():
    title, summary, link = get_article()
    caption = build_caption(title, summary, link)
    print("About to post the following content to LinkedIn:")
    print("------------------------------------------------")
    print(caption)
    print("------------------------------------------------")

    # In GitHub Actions, environment variables will be set.
    result = post_to_linkedin(caption, link)
    print("LinkedIn API response:", result)


if __name__ == "__main__":
    main()
