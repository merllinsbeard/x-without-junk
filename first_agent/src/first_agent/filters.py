"""Content filtering logic for the "bullshit filter"."""

import re
from dataclasses import dataclass
from typing import Literal

from first_agent.bird_client import Tweet

# Patterns for content we want to filter out
MARKETING_PATTERNS = [
    r"\b🚀\b",  # Rocket emoji (common in marketing)
    r"launching\s+soon",
    r"early\s+access",
    r"limited\s+time",
    r"\d+%\s+off",
    r"buy\s+now",
    r"shop\s+now",
    r"link\s+in\s+bio",
    r"follow\s+for\s+more",
    r"dm\s+me",
    r"subscribe\s+now",
]

SELF_IMPROVEMENT_KEYWORDS = [
    "morning routine",
    "productivity hack",
    "life coach",
    "mindset",
    "grindset",
    "hustle",
    "10x",
    "growth mindset",
    "affirmation",
    "manifest",
    "self-care",
    "wellness tips",
    "habit tracker",
]

LOW_QUALITY_PATTERNS = [
    r"^rt\s+",  # Retweets without added content
    r"^\s*[👍❤️😂🔥]+",  # Pure emoji reactions
    r"^\s*\.\s*$",  # Single dot responses
    r"this\.",
    r"^wow$",
    r"^amazing$",
    r"^incredible$",
]

SPAM_PATTERNS = [
    r"(?:https?://t\.co/)\S{10}",  # Multiple t.co links
    r"free\s+(?:money|crypto|btc|eth)",
    r"click\s+here",
    r"claim\s+now",
    r"giveaway",
    r"contest\s+alert",
]


@dataclass(frozen=True)
class FilterResult:
    """Result of filtering a single tweet.

    Immutable dataclass to prevent modification of filter results.
    """

    tweet: Tweet
    passed: bool
    reason: str | None = None
    score: float = 0.0


class ContentFilter:
    """Filters tweets based on quality and relevance criteria."""

    def __init__(
        self,
        min_engagement: int = 3,
        filter_marketing: bool = True,
        filter_self_improvement: bool = True,
        filter_spam: bool = True,
        custom_keywords: list[str] | None = None,
    ):
        """Initialize the content filter.

        Args:
            min_engagement: Minimum total engagement to pass filter.
            filter_marketing: Filter out marketing/promotional content.
            filter_self_improvement: Filter out self-improvement content.
            filter_spam: Filter out spam and low-quality content.
            custom_keywords: Additional keywords to filter out.
        """
        self.min_engagement = min_engagement
        self.filter_marketing = filter_marketing
        self.filter_self_improvement = filter_self_improvement
        self.filter_spam = filter_spam
        self.custom_keywords = custom_keywords or []

    def _check_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the given patterns.

        Args:
            text: Text to check.
            patterns: List of regex patterns.

        Returns:
            True if any pattern matches.
        """
        combined = "|".join(patterns)
        return bool(re.search(combined, text, re.IGNORECASE))

    def _check_keywords(self, text: str, keywords: list[str]) -> bool:
        """Check if text contains any of the given keywords.

        Args:
            text: Text to check.
            keywords: List of keywords to look for.

        Returns:
            True if any keyword is found.
        """
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def filter_tweet(self, tweet: Tweet) -> FilterResult:
        """Filter a single tweet based on configured criteria.

        Args:
            tweet: Tweet to filter.

        Returns:
            FilterResult indicating whether the tweet passed.
        """
        reasons = []
        score = 0.0

        # Engagement score (0-40 points)
        engagement = tweet.engagement_rate
        if engagement >= self.min_engagement:
            score += min(40, engagement * 2)
        else:
            reasons.append(f"Low engagement ({engagement})")

        # Length score (0-20 points) - prefer substantial content
        text_length = len(tweet.text)
        if 50 <= text_length <= 500:
            score += 20
        elif text_length < 20:
            reasons.append("Too short")
            score -= 10

        # Media bonus (0-10 points)
        if tweet.has_media:
            score += 5

        # URL bonus (0-15 points) - indicates shared content
        if tweet.urls:
            score += min(15, len(tweet.urls) * 5)

        # Quote tweet bonus (0-15 points)
        if tweet.is_quote:
            score += 15

        # Marketing filter
        if self.filter_marketing:
            if self._check_patterns(tweet.text, MARKETING_PATTERNS):
                return FilterResult(
                    tweet=tweet, passed=False, reason="Marketing content", score=score
                )

        # Self-improvement filter
        if self.filter_self_improvement:
            if self._check_keywords(tweet.text, SELF_IMPROVEMENT_KEYWORDS):
                return FilterResult(
                    tweet=tweet,
                    passed=False,
                    reason="Self-improvement content",
                    score=score,
                )

        # Spam filter
        if self.filter_spam:
            if self._check_patterns(tweet.text, SPAM_PATTERNS):
                return FilterResult(
                    tweet=tweet, passed=False, reason="Spam detected", score=score
                )
            if self._check_patterns(tweet.text, LOW_QUALITY_PATTERNS):
                return FilterResult(
                    tweet=tweet, passed=False, reason="Low quality", score=score
                )

        # Custom keyword filter
        if self.custom_keywords:
            if self._check_keywords(tweet.text, self.custom_keywords):
                return FilterResult(
                    tweet=tweet,
                    passed=False,
                    reason="Matched custom filter",
                    score=score,
                )

        # Overall quality check
        passed = score >= 30 and not reasons

        return FilterResult(
            tweet=tweet,
            passed=passed,
            reason="; ".join(reasons) if reasons else None,
            score=score,
        )

    def filter_tweets(self, tweets: list[Tweet]) -> tuple[list[Tweet], list[FilterResult]]:
        """Filter a list of tweets.

        Args:
            tweets: List of tweets to filter.

        Returns:
            Tuple of (passed tweets, all filter results as FilterResult objects).
        """
        results = [self.filter_tweet(tweet) for tweet in tweets]
        passed = [r.tweet for r in results if r.passed]
        return passed, results
