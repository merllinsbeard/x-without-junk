"""Wrapper for bird CLI commands to fetch X/Twitter content."""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from rich.console import Console

console = Console()


@dataclass(frozen=True)
class Tweet:
    """Represents a tweet with all relevant fields.

    Immutable dataclass to prevent accidental modification of tweet data.
    """

    id: str
    text: str
    created_at: str
    author_username: str
    author_name: str
    author_id: str
    reply_count: int
    retweet_count: int
    like_count: int
    conversation_id: str
    media: list = field(default_factory=list)
    quoted_tweet: dict | None = None
    urls: list = field(default_factory=list)
    mentions: list = field(default_factory=list)
    hashtags: list = field(default_factory=list)

    def __post_init__(self):
        """Validate tweet data after initialization."""
        if not self.id:
            raise ValueError("Tweet ID cannot be empty")
        if not self.author_username:
            raise ValueError("Author username cannot be empty")
        if not self.author_name:
            raise ValueError("Author name cannot be empty")
        if self.reply_count < 0:
            raise ValueError("Reply count cannot be negative")
        if self.retweet_count < 0:
            raise ValueError("Retweet count cannot be negative")
        if self.like_count < 0:
            raise ValueError("Like count cannot be negative")

    @classmethod
    def from_api(cls, data: dict) -> "Tweet":
        """Create a Tweet from bird CLI API response."""
        author = data.get("author", {})
        media = data.get("media")
        quoted = data.get("quotedTweet")

        # Extract URLs from text and entities
        urls = []
        mentions = []
        hashtags = []
        entities = data.get("entities", {})

        for url_entity in entities.get("urls", []):
            if "expanded_url" in url_entity:
                urls.append(url_entity["expanded_url"])

        for mention in entities.get("user_mentions", []):
            mentions.append(mention["screen_name"])

        for hashtag in entities.get("hashtags", []):
            hashtags.append(hashtag["text"])

        return cls(
            id=data["id"],
            text=data["text"],
            created_at=data["createdAt"],
            author_username=author.get("username", "unknown"),
            author_name=author.get("name", "Unknown"),
            author_id=data.get("authorId", ""),
            reply_count=data.get("replyCount", 0),
            retweet_count=data.get("retweetCount", 0),
            like_count=data.get("likeCount", 0),
            conversation_id=data.get("conversationId", ""),
            media=media,
            quoted_tweet=quoted,
            urls=urls if urls else None,
            mentions=mentions if mentions else None,
            hashtags=hashtags if hashtags else None,
        )

    @property
    def engagement_rate(self) -> float:
        """Calculate total engagement (sum of replies, retweets, and likes).

        Note: Property name is legacy - this returns total engagement count,
        not a normalized rate.
        """
        total_engagements = self.reply_count + self.retweet_count + self.like_count
        return total_engagements

    @property
    def has_media(self) -> bool:
        """Check if tweet has media attachments."""
        return bool(self.media)

    @property
    def is_quote(self) -> bool:
        """Check if tweet is a quote tweet."""
        return self.quoted_tweet is not None


class BirdClient:
    """Wrapper for bird CLI commands."""

    def __init__(self, count: int = 50):
        """Initialize the bird CLI client.

        Args:
            count: Default number of items to fetch per request.
        """
        self.count = count

    def _run_bird_command(
        self, command: str, args: list[str] | None = None, timeout: int = 60
    ) -> list[dict]:
        """Run a bird CLI command and return JSON output.

        Args:
            command: The bird command to run (e.g., 'home', 'bookmarks').
            args: Additional arguments for the command.

        Returns:
            List of tweet dictionaries.

        Raises:
            subprocess.CalledProcessError: If the command fails.
            json.JSONDecodeError: If the output is not valid JSON.
        """
        cmd = ["bird", command, "--json"]
        if args:
            cmd.extend(args)

        console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )

        if not result.stdout.strip():
            return []

        try:
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                # Some commands return a dict with a data or tweets field
                return data.get("tweets") or data.get("data", [])
            return data
        except json.JSONDecodeError as e:
            console.print(f"[red]Failed to parse JSON output[/red]")
            console.print(f"[dim]Output: {result.stdout[:500]}[/dim]")
            raise json.JSONDecodeError(
                f"Failed to parse bird CLI output: {e.msg}",
                e.doc,
                e.pos
            ) from e

    def fetch_home_timeline(self, count: int | None = None) -> list[Tweet]:
        """Fetch the home timeline ("For You" feed).

        Args:
            count: Number of tweets to fetch. Uses default if not specified.

        Returns:
            List of Tweet objects.
        """
        n = count or self.count
        console.print(f"[cyan]Fetching home timeline ({n} tweets)...[/cyan]")
        data = self._run_bird_command("home", ["--count", str(n)])
        return [Tweet.from_api(t) for t in data]

    def fetch_bookmarks(self, count: int | None = None) -> list[Tweet]:
        """Fetch bookmarked tweets.

        Args:
            count: Number of bookmarks to fetch. Uses default if not specified.

        Returns:
            List of Tweet objects.
        """
        n = count or self.count
        console.print(f"[cyan]Fetching bookmarks ({n} tweets)...[/cyan]")
        data = self._run_bird_command("bookmarks", ["--count", str(n)])
        return [Tweet.from_api(t) for t in data]

    def fetch_all_bookmarks(self, max_pages: int = 10) -> list[Tweet]:
        """Fetch all bookmarks using cursor-based pagination.

        Fetches page by page to avoid JSON truncation issues with --all.

        Args:
            max_pages: Maximum pages to fetch (each page ~20 bookmarks).

        Returns:
            List of all bookmarked Tweet objects.
        """
        all_tweets: list[Tweet] = []
        cursor: str | None = None

        for page in range(max_pages):
            console.print(f"[cyan]Fetching bookmarks page {page + 1}...[/cyan]")
            args = ["--all", "--max-pages", "1"]
            if cursor:
                args.extend(["--cursor", cursor])

            cmd = ["bird", "bookmarks", "--json"] + args
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0 or not result.stdout.strip():
                break

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                console.print(f"[yellow]JSON parse error on page {page + 1}, stopping[/yellow]")
                break

            if isinstance(data, dict):
                tweets_data = data.get("tweets") or data.get("data", [])
                cursor = data.get("nextCursor")
            elif isinstance(data, list):
                tweets_data = data
                cursor = None
            else:
                break

            for t in tweets_data:
                try:
                    all_tweets.append(Tweet.from_api(t))
                except Exception:
                    continue

            if not cursor:
                break

        console.print(f"[cyan]Fetched {len(all_tweets)} total bookmarks[/cyan]")
        return all_tweets

    def fetch_user_tweets(self, handle: str, count: int | None = None) -> list[Tweet]:
        """Fetch tweets from a specific user's timeline.

        Args:
            handle: Twitter handle (with or without @).
            count: Number of tweets to fetch. Uses default if not specified.

        Returns:
            List of Tweet objects.
        """
        n = count or self.count
        clean_handle = handle.lstrip("@")
        console.print(f"[cyan]Fetching tweets from @{clean_handle} ({n} tweets)...[/cyan]")
        data = self._run_bird_command("user-tweets", [clean_handle, "--count", str(n)])
        return [Tweet.from_api(t) for t in data]

    def search_tweets(self, query: str, count: int | None = None) -> list[Tweet]:
        """Search for tweets matching a query.

        Args:
            query: Search query string.
            count: Number of tweets to fetch. Uses default if not specified.

        Returns:
            List of Tweet objects.
        """
        n = count or self.count
        console.print(f"[cyan]Searching for '{query}' ({n} tweets)...[/cyan]")
        data = self._run_bird_command("search", [query, "--count", str(n)])
        return [Tweet.from_api(t) for t in data]

    def verify_credentials(self) -> bool:
        """Verify that bird CLI is properly authenticated.

        Returns:
            True if authenticated, False otherwise.
        """
        try:
            result = subprocess.run(
                ["bird", "whoami"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return "@" in result.stdout
        except subprocess.CalledProcessError:
            console.print("[yellow]Bird CLI not authenticated or command failed[/yellow]")
            return False
        except subprocess.TimeoutExpired:
            console.print("[yellow]Bird CLI command timed out[/yellow]")
            return False
        except FileNotFoundError:
            console.print("[yellow]Bird CLI not found - install with 'go install github.com/tea2k/bird@latest'[/yellow]")
            return False
