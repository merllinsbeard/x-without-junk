"""Content filtering logic for the "bullshit filter"."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from first_agent.bird_client import Tweet

# Default patterns for content we want to filter out (used when no config provided)
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
        patterns_file: str | Path | None = None,
        config: dict | None = None,
    ):
        """Initialize the content filter.

        Args:
            min_engagement: Minimum total engagement to pass filter.
            filter_marketing: Filter out marketing/promotional content.
            filter_self_improvement: Filter out self-improvement content.
            filter_spam: Filter out spam and low-quality content.
            custom_keywords: Additional keywords to filter out.
            patterns_file: Path to YAML file containing custom patterns.
            config: Configuration dictionary (takes precedence over patterns_file).
        """
        self.min_engagement = min_engagement
        self.filter_marketing = filter_marketing
        self.filter_self_improvement = filter_self_improvement
        self.filter_spam = filter_spam
        self.custom_keywords = custom_keywords or []

        # Load patterns from file or use defaults
        self._load_patterns(patterns_file, config)

    def _load_patterns(self, patterns_file: str | Path | None, config: dict | None) -> None:
        """Load filter patterns from YAML file or config.

        Args:
            patterns_file: Path to YAML patterns file.
            config: Configuration dictionary with filters.patterns key.
        """
        marketing = MARKETING_PATTERNS
        self_improvement = SELF_IMPROVEMENT_KEYWORDS
        spam = SPAM_PATTERNS
        low_quality = LOW_QUALITY_PATTERNS

        # Try loading from config dict first
        if config and "filters" in config:
            patterns_data = config["filters"].get("patterns", {})
            if patterns_data:
                marketing = patterns_data.get("marketing", MARKETING_PATTERNS)
                self_improvement = patterns_data.get("self_improvement", SELF_IMPROVEMENT_KEYWORDS)
                spam = patterns_data.get("spam", SPAM_PATTERNS)
                low_quality = patterns_data.get("low_quality", LOW_QUALITY_PATTERNS)
        elif patterns_file:
            # Try loading from YAML file
            patterns_path = Path(patterns_file)
            if patterns_path.exists():
                import yaml

                with open(patterns_path, "r", encoding="utf-8") as f:
                    patterns_data = yaml.safe_load(f) or {}

                marketing = patterns_data.get("marketing", MARKETING_PATTERNS)
                self_improvement = patterns_data.get("self_improvement", SELF_IMPROVEMENT_KEYWORDS)
                spam = patterns_data.get("spam", SPAM_PATTERNS)
                low_quality = patterns_data.get("low_quality", LOW_QUALITY_PATTERNS)

        # Store loaded patterns
        self.marketing_patterns = marketing
        self.self_improvement_keywords = self_improvement
        self.spam_patterns = spam
        self.low_quality_patterns = low_quality

    @classmethod
    def from_config(cls, config: dict) -> "ContentFilter":
        """Create ContentFilter from configuration dictionary.

        Args:
            config: Configuration dictionary with filters section.

        Returns:
            Configured ContentFilter instance.
        """
        filter_config = config.get("filters", {})

        return cls(
            min_engagement=filter_config.get("min_score", 30) // 10,  # Approximate mapping
            filter_marketing=filter_config.get("enabled", True),
            filter_self_improvement=filter_config.get("enabled", True),
            filter_spam=filter_config.get("enabled", True),
            config=config,
        )

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
