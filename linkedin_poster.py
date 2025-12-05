import os
import requests

ACCESS_TOKEN_ENV = "LINKEDIN_ACCESS_TOKEN"
MEMBER_URN_ENV = "LINKEDIN_MEMBER_URN"


class LinkedInError(RuntimeError):
    pass


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise LinkedInError(f"Environment variable {name} is not set.")
    return value


def post_to_linkedin(text: str, link: str | None = None) -> dict:
    """
    Post text (and optional article link) to LinkedIn as the authenticated member.
    Uses the UGC posts endpoint.
    """
    access_token = _get_env(ACCESS_TOKEN_ENV)
    author_urn = _get_env(MEMBER_URN_ENV)

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
                "shareCommentary": {"text": text},
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

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    if resp.status_code not in (200, 201):
        raise LinkedInError(
            f"LinkedIn post failed ({resp.status_code}): {resp.text}"
        )

    return resp.json()
