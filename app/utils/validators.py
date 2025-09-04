import logging

logger = logging.getLogger(__name__)

# Validate URLs
def validate_url(url: str):
    if not url.startswith(("http://", "https://")):
        logger.error(f"Invalid URL: {url}")
        raise ValueError("Invalid URL - please provide a valid URL starting with http or https")
    return url