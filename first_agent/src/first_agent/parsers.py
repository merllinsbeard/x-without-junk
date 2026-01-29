"""Parse and structure content into Markdown reports."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from first_agent.bird_client import Tweet
from rich.console import Console

console = Console()


@dataclass(frozen=True)
class ParsedContent:
    """Structured content from parsed tweets.

    Immutable dataclass to prevent modification of parsed results.
    """

    news: list[dict] = field(default_factory=list)
    threads: list[dict] = field(default_factory=list)
    resources: list[dict] = field(default_factory=list)
    discussions: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class TweetParser:
    """Parse tweets and structure them into categories."""

    def __init__(self):
        """Initialize the parser."""
        self.seen_ids = set()
        self.seen_urls = set()

    def _extract_urls(self, tweet: Tweet) -> list[str]:
        """Extract and deduplicate URLs from a tweet.

        Args:
            tweet: Tweet to extract URLs from.

        Returns:
            List of unique URLs.
        """
        urls = tweet.urls or []
        # Also extract URLs from text
        text_urls = re.findall(r"https?://\S+", tweet.text)
        all_urls = list(set(urls + text_urls))
        return [u for u in all_urls if "t.co" not in u or u.count("/") > 3]

    def _categorize_tweet(self, tweet: Tweet) -> tuple[str, float]:
        """Categorize a tweet and return its category with confidence.

        Args:
            tweet: Tweet to categorize.

        Returns:
            Tuple of (category, confidence_score).
        """
        text = tweet.text.lower()

        # Check for external links/resources
        if tweet.urls and not tweet.is_quote:
            if any(domain in text for domain in ["github", "git.io", "npm", "pypi"]):
                return ("code", 0.9)
            return ("resource", 0.8)

        # Check for thread indicators
        if (
            "🧵" in text
            or "thread" in text
            or tweet.reply_count > 10
            or (tweet.urls and len(tweet.text) > 280)
        ):
            return ("thread", 0.85)

        # Check for news/announcements
        news_keywords = [
            "release",
            "announc",
            "launch",
            "update",
            "new",
            "v2.",
            "v3.",
            "beta",
            "just shipped",
        ]
        if any(kw in text for kw in news_keywords):
            return ("news", 0.75)

        # Check for discussions
        if tweet.reply_count > 5 or "?" in text:
            return ("discussion", 0.7)

        # Default to discussion
        return ("discussion", 0.5)

    def parse_tweets(self, tweets: list[Tweet], source: str = "unknown") -> ParsedContent:
        """Parse a list of tweets into structured categories.

        Args:
            tweets: List of tweets to parse.
            source: Source of the tweets (e.g., "timeline", "bookmarks").

        Returns:
            ParsedContent with categorized tweets.
        """
        news = []
        threads = []
        resources = []
        discussions = []

        for tweet in tweets:
            if tweet.id in self.seen_ids:
                continue

            self.seen_ids.add(tweet.id)

            category, confidence = self._categorize_tweet(tweet)

            item = {
                "id": tweet.id,
                "text": tweet.text,
                "author": f"@{tweet.author_username}",
                "author_name": tweet.author_name,
                "created_at": tweet.created_at,
                "engagement": tweet.engagement_rate,
                "urls": self._extract_urls(tweet),
                "confidence": confidence,
                "is_quote": tweet.is_quote,
            }

            # Track unique URLs
            for url in item["urls"]:
                if url not in self.seen_urls:
                    self.seen_urls.add(url)

            # Add to appropriate category
            if category == "news":
                news.append(item)
            elif category == "thread":
                threads.append(item)
            elif category == "resource" or category == "code":
                resources.append(item)
            else:
                discussions.append(item)

        return ParsedContent(
            news=news,
            threads=threads,
            resources=resources,
            discussions=discussions,
            metadata={
                "source": source,
                "parsed_at": datetime.now().isoformat(),
                "total_parsed": len(self.seen_ids),
            },
        )


class MarkdownWriter:
    """Write parsed content to Markdown files."""

    def __init__(self, output_dir: Path | str = "output"):
        """Initialize the markdown writer.

        Args:
            output_dir: Directory to write output files to.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_tweet_item(self, item: dict) -> str:
        """Format a tweet item as markdown.

        Args:
            item: Tweet item dictionary.

        Returns:
            Formatted markdown string.
        """
        lines = [
            f"### {item['author_name']} ({item['author']})",
            f"*{item['created_at']}* | Engagement: {item['engagement']}",
            "",
            item['text'],
            "",
        ]

        if item['urls']:
            lines.append("**Links:**")
            for url in item['urls']:
                lines.append(f"- {url}")
            lines.append("")

        if item.get('is_quote'):
            lines.append("*Quote tweet*")
            lines.append("")

        lines.append(f"[View on X](https://x.com/i/status/{item['id']})")
        lines.append("---")

        return "\n".join(lines)

    def write_report(self, content: ParsedContent, filename: str | None = None) -> Path:
        """Write a markdown report from parsed content.

        Args:
            content: ParsedContent to write.
            filename: Optional filename. Defaults to timestamped name.

        Returns:
            Path to the written file.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.md"

        filepath = self.output_dir / filename

        lines = [
            f"# X Timeline Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"*Source: {content.metadata['source']}*",
            f"*Total items parsed: {content.metadata['total_parsed']}*",
            "",
            "---",
            "",
        ]

        # News section
        if content.news:
            lines.extend([
                "## 📰 Top News",
                "",
            ])
            for item in sorted(content.news, key=lambda x: x['engagement'], reverse=True):
                lines.append(self._format_tweet_item(item))
            lines.append("")

        # Threads section
        if content.threads:
            lines.extend([
                "## 🧵 Interesting Threads",
                "",
            ])
            for item in sorted(content.threads, key=lambda x: x['engagement'], reverse=True):
                lines.append(self._format_tweet_item(item))
            lines.append("")

        # Resources section
        if content.resources:
            lines.extend([
                "## 🔗 Resources Shared",
                "",
            ])
            for item in sorted(content.resources, key=lambda x: x['engagement'], reverse=True):
                lines.append(self._format_tweet_item(item))
            lines.append("")

        # Discussions section
        if content.discussions:
            lines.extend([
                "## 💬 Notable Discussions",
                "",
            ])
            for item in sorted(content.discussions, key=lambda x: x['engagement'], reverse=True)[:10]:
                lines.append(self._format_tweet_item(item))
            lines.append("")

        try:
            filepath.write_text("\n".join(lines))
            console.print(f"[green]Report written to: {filepath}[/green]")
        except PermissionError:
            console.print(f"[red]Permission denied: Cannot write to {filepath}[/red]")
            console.print(f"[yellow]Check directory permissions and try again[/yellow]")
            raise
        except OSError as e:
            console.print(f"[red]Failed to write report: {e}[/red]")
            raise

        return filepath
