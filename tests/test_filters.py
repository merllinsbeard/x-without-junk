"""Tests for content filtering."""

from first_agent.bird_client import Tweet
from first_agent.filters import ContentFilter


def _make_tweet(text: str) -> Tweet:
    return Tweet(
        id="123",
        text=text,
        created_at="2024-01-01",
        author_username="testuser",
        author_name="Test User",
        author_id="456",
        reply_count=10,
        retweet_count=10,
        like_count=10,
        conversation_id="789",
    )


def test_empty_patterns_do_not_filter_everything():
    config = {
        "filters": {
            "patterns": {
                "marketing": [],
                "self_improvement": [],
                "spam": [],
                "low_quality": [],
            }
        }
    }
    tweet = _make_tweet("This is a solid update about a release and details.")

    content_filter = ContentFilter(
        min_engagement=1,
        filter_marketing=True,
        filter_self_improvement=True,
        filter_spam=True,
        config=config,
    )

    result = content_filter.filter_tweet(tweet)

    assert result.passed is True
    assert result.reason is None
