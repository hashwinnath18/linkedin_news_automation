from content_fetcher import get_article
from linkedin_poster import post_to_linkedin



def build_caption(title: str, summary: str, link: str) -> str:
    lines = [
        f"🚀 {title}",
        "",
        summary,
        "",
        f"🔗 Read more: {link}",
        "",
        "#AI #MachineLearning #Tech"
    ]
    return "\n".join(lines)


def main():
    title, summary, link = get_article()
    caption = build_caption(title, summary, link)

    print("About to post:\n")
    print(caption)
    print("\n---\n")

    result = post_to_linkedin(caption, link)
    print("Posted successfully. LinkedIn response:")
    print(result)


if __name__ == "__main__":
    main()
