import os
import requests

# These must be supplied as environment variables in GitHub Actions.
ACCESS_TOKEN_ENV = "LINKEDIN_ACCESS_TOKEN"
MEMBER_URN_ENV = "LINKEDIN_MEMBER_URN"


class LinkedInError(RuntimeError):
    pass


def _get_env_or_raise(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise LinkedInError(f"Environment variable {name} is not set.")
    return value


def post_to_linkedin(text: str, link: str | None = None) -> dict:
    """
    Post a text (optionally with a link) to LinkedIn using the UGC Posts API.

    Requires:
        LINKEDIN_ACCESS_TOKEN
        LINKEDIN_MEMBER_URN

    Returns:
        Parsed JSON response from LinkedIn.

    Raises:
        LinkedInError on failures.
    """
    access_token = _get_env_or_raise(ACCESS_TOKEN_ENV)
    author_urn = _get_env_or_raise(MEMBER_URN_ENV)

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    body: dict = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "ARTICLE" if link else "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    if link:
        body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
            {
                "status": "READY",
                "originalUrl": link,
                "title": {"text": "Source"},
            }
        ]

    response = requests.post(url, headers=headers, json=body)
    if response.status_code not in (200, 201):
        raise LinkedInError(
            f"LinkedIn post failed ({response.status_code}): {response.text}"
        )

    return response.json()


if __name__ == "__main__":
    # Simple manual test (requires env vars to be set)
    example_text = "Test post from script. Please ignore."
    try:
        result = post_to_linkedin(example_text)
        print("Posted successfully:", result)
    except Exception as e:
        print("Error posting to LinkedIn:", e)
