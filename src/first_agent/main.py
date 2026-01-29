"""CLI entry point for the News Parser Agent."""

import asyncio
import os
import random
import shlex
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from first_agent.agent import analyze_tweets_with_agent
from first_agent.bird_client import BirdClient
from first_agent.filters import ContentFilter
from first_agent.parsers import MarkdownWriter, ParsedContent, TweetParser

console = Console()
app = typer.Typer(
    name="news-parser",
    help="X/Twitter News Parser Agent - Fetch, filter, and analyze tweets",
    add_completion=False,
)

# Global configuration (loaded at startup)
_config: dict | None = None
_config_path: Path | None = None
_system_prompt_path: Path | None = None
_analysis_prompt_path: Path | None = None
_patterns_path: Path | None = None


def load_config(config_path: str | None = None) -> dict:
    """Load configuration from file, falling back to defaults.

    Args:
        config_path: Optional path to config file. If not provided, searches
                     in default locations: config.yaml, ./config.yaml,
                     ~/.config/news-parser/config.yaml.

    Returns:
        Configuration dictionary. Empty dict if no config found.
    """
    if config_path:
        path = Path(config_path).expanduser()
        if path.exists():
            console.print(f"[dim]Loading config from: {path}[/dim]")
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

    # Try default locations
    default_paths = [
        Path("config.yaml"),
        Path("./config.yaml"),
        Path.home() / ".config" / "news-parser" / "config.yaml",
    ]

    for path in default_paths:
        if path.exists():
            console.print(f"[dim]Loading config from: {path}[/dim]")
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}

    return {}


def get_config() -> dict:
    """Get the current configuration, loading if not already loaded.

    Returns:
        Configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_config(str(_config_path) if _config_path else None)
    return _config


def _run_ai_analysis(
    tweets: list,
    source: str,
    save: bool = False,
    output: Optional[str] = None,
    system_prompt: Optional[str] = None,
    analysis_prompt: Optional[str] = None,
) -> None:
    """Run AI analysis on filtered tweets, display and optionally save results.

    Args:
        tweets: List of Tweet objects to analyze.
        source: Source identifier for the tweets.
        save: If True, save with auto-timestamped name.
        output: If set, save to this specific path.
        system_prompt: Optional path to custom system prompt.
        analysis_prompt: Optional path to custom analysis prompt.
    """
    config = get_config()
    content_filter = ContentFilter(
        patterns_file=str(_patterns_path) if _patterns_path else None,
        config=config,
    )
    filtered_tweets, _ = content_filter.filter_tweets(tweets)
    console.print(f"[green]Filtered to {len(filtered_tweets)} quality tweets[/green]")

    # Extract tweet texts (limited for token efficiency)
    tweet_texts = [
        f"@{t.author_username}: {t.text}\n🔗 https://x.com/{t.author_username}/status/{t.id}"
        for t in filtered_tweets
    ]

    console.print("[cyan]Running AI analysis...[/cyan]")

    # Load custom prompts if provided
    sys_prompt = None
    if system_prompt:
        sys_prompt = Path(system_prompt).read_text(encoding="utf-8")

    ana_prompt = None
    if analysis_prompt:
        ana_prompt = Path(analysis_prompt).read_text(encoding="utf-8")

    result = asyncio.run(
        analyze_tweets_with_agent(
            tweet_texts,
            system_prompt=sys_prompt,
            analysis_prompt=ana_prompt,
            config=config,
        )
    )
    console.print(Panel(result, title=f"AI Analysis: {source}", border_style="blue"))

    # Always save analysis to file
    if output:
        filename = output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{source}_{timestamp}.md"
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename
    filepath.write_text(f"# AI Analysis: {source}\n\n{result}\n")
    console.print(f"[green]✓ Analysis saved to {filepath}[/green]")


def _output_report(
    parsed: ParsedContent,
    default_prefix: str,
    save: bool = False,
    output: Optional[str] = None,
) -> None:
    """Output parsed content to stdout or file.

    Args:
        parsed: Parsed tweet content.
        default_prefix: Prefix for auto-generated filenames.
        save: If True, save with auto-timestamped name.
        output: If set, save to this specific path.
    """
    if not save and output is None:
        _print_report_stdout(parsed)
        return

    writer = MarkdownWriter()
    if output:
        filename = output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{default_prefix}_{timestamp}.md"
    filepath = writer.write_report(parsed, filename)
    console.print(f"[green]✓ Report saved to {filepath}[/green]")


def _print_report_stdout(content: ParsedContent) -> None:
    """Print parsed content to stdout as formatted text."""
    sections = [
        ("📰 Top News", content.news),
        ("🧵 Interesting Threads", content.threads),
        ("🔗 Resources Shared", content.resources),
        ("💬 Notable Discussions", content.discussions),
    ]

    for title, items in sections:
        if not items:
            continue
        console.print(f"\n[bold]{title}[/bold]\n")
        sorted_items = sorted(items, key=lambda x: x['engagement'], reverse=True)
        if title.startswith("💬"):
            sorted_items = sorted_items[:10]
        for item in sorted_items:
            console.print(f"  [cyan]@{item['author']}[/cyan] ({item['engagement']} engagement)")
            console.print(f"  {item['text'][:200]}")
            if item['urls']:
                for url in item['urls']:
                    console.print(f"  [blue]{url}[/blue]")
            console.print()


SAVE_HELP = "Save to file with auto-timestamped name."
OUTPUT_HELP = "Save to file at specified path."


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(None, "--config", "-C", help="Path to configuration file (YAML)"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Path to custom system prompt (Markdown)"),
    analysis_prompt: Optional[str] = typer.Option(None, "--analysis-prompt", help="Path to custom analysis prompt (Markdown)"),
    patterns: Optional[str] = typer.Option(None, "--patterns", "-P", help="Path to custom filter patterns (YAML)"),
):
    """Global options for all commands."""
    global _config_path, _system_prompt_path, _analysis_prompt_path, _patterns_path

    _config_path = Path(config).expanduser() if config else None
    _system_prompt_path = Path(system_prompt).expanduser() if system_prompt else None
    _analysis_prompt_path = Path(analysis_prompt).expanduser() if analysis_prompt else None
    _patterns_path = Path(patterns).expanduser() if patterns else None

    # Store in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = _config_path
    ctx.obj["system_prompt_path"] = _system_prompt_path
    ctx.obj["analysis_prompt_path"] = _analysis_prompt_path
    ctx.obj["patterns_path"] = _patterns_path


@app.command()
def timeline(
    ctx: typer.Context,
    count: int = typer.Option(50, "--count", "-c", help="Number of tweets to fetch"),
    save: bool = typer.Option(False, "--save", "-s", help=SAVE_HELP),
    output: Optional[str] = typer.Option(None, "--output", "-o", help=OUTPUT_HELP),
    no_filter: bool = typer.Option(False, "--no-filter", help="Skip content filtering"),
    analyze: bool = typer.Option(False, "--analyze", help="Run AI analysis on fetched tweets"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Path to custom system prompt"),
    analysis_prompt: Optional[str] = typer.Option(None, "--analysis-prompt", help="Path to custom analysis prompt"),
):
    """Fetch and optionally analyze your home timeline.

    Use --analyze to get AI-powered insights from your timeline.
    """
    console.print(Panel.fit("📱 Fetching Home Timeline", style="cyan bold"))

    client = BirdClient(count=count)
    filter_enabled = not no_filter
    config = get_config()

    tweets = client.fetch_home_timeline()
    console.print(f"[green]Fetched {len(tweets)} tweets[/green]")

    if not tweets:
        console.print("[yellow]No tweets found[/yellow]")
        raise typer.Exit()

    if filter_enabled:
        content_filter = ContentFilter(
            min_engagement=3,
            filter_marketing=True,
            filter_self_improvement=True,
            patterns_file=str(_patterns_path) if _patterns_path else None,
            config=config,
        )
        filtered_tweets, _ = content_filter.filter_tweets(tweets)
        console.print(f"[green]Filtered to {len(filtered_tweets)} quality tweets[/green]")

        filtered_out = len(tweets) - len(filtered_tweets)
        if filtered_out > 0:
            console.print(f"[dim]{filtered_out} tweets filtered out[/dim]")
    else:
        filtered_tweets = tweets

    if analyze:
        _run_ai_analysis(
            tweets,
            "home_timeline",
            save=save,
            output=output,
            system_prompt=system_prompt,
            analysis_prompt=analysis_prompt,
        )
        return

    parser = TweetParser()
    parsed = parser.parse_tweets(filtered_tweets, source="home_timeline")
    _output_report(parsed, "timeline", save=save, output=output)


@app.command()
def bookmarks(
    ctx: typer.Context,
    count: int = typer.Option(50, "--count", "-c", help="Number of bookmarks to fetch"),
    save: bool = typer.Option(False, "--save", "-s", help=SAVE_HELP),
    output: Optional[str] = typer.Option(None, "--output", "-o", help=OUTPUT_HELP),
    no_filter: bool = typer.Option(False, "--no-filter", help="Skip content filtering"),
    analyze: bool = typer.Option(False, "--analyze", help="Run AI analysis on fetched bookmarks"),
    shuffle: bool = typer.Option(False, "--shuffle", help="Randomize bookmark order"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Path to custom system prompt"),
    analysis_prompt: Optional[str] = typer.Option(None, "--analysis-prompt", help="Path to custom analysis prompt"),
):
    """Fetch and optionally analyze your bookmarks.

    Use --analyze to get AI-powered insights from your bookmarks.
    Use --shuffle to randomize the order of results.
    """
    console.print(Panel.fit("🔖 Fetching Bookmarks", style="cyan bold"))

    client = BirdClient(count=count)
    config = get_config()

    if shuffle:
        all_tweets = client.fetch_all_bookmarks()
        console.print(f"[green]Fetched {len(all_tweets)} total bookmarks[/green]")
        if not all_tweets:
            console.print("[yellow]No bookmarks found[/yellow]")
            raise typer.Exit()
        tweets = random.sample(all_tweets, min(count, len(all_tweets)))
        console.print(f"[green]Randomly selected {len(tweets)} bookmarks[/green]")
    else:
        tweets = client.fetch_bookmarks()
        console.print(f"[green]Fetched {len(tweets)} bookmarks[/green]")
        if not tweets:
            console.print("[yellow]No bookmarks found[/yellow]")
            raise typer.Exit()

    if not no_filter:
        content_filter = ContentFilter(
            min_engagement=2,
            filter_marketing=False,
            patterns_file=str(_patterns_path) if _patterns_path else None,
            config=config,
        )
        filtered_tweets, _ = content_filter.filter_tweets(tweets)
        console.print(f"[green]Kept {len(filtered_tweets)} bookmarks[/green]")
    else:
        filtered_tweets = tweets

    if analyze:
        _run_ai_analysis(
            tweets,
            "bookmarks",
            save=save,
            output=output,
            system_prompt=system_prompt,
            analysis_prompt=analysis_prompt,
        )
        return

    parser = TweetParser()
    parsed = parser.parse_tweets(filtered_tweets, source="bookmarks")
    _output_report(parsed, "bookmarks", save=save, output=output)


@app.command()
def user(
    ctx: typer.Context,
    handle: str = typer.Argument(..., help="Twitter handle (with or without @)"),
    count: int = typer.Option(50, "--count", "-c", help="Number of tweets to fetch"),
    save: bool = typer.Option(False, "--save", "-s", help=SAVE_HELP),
    output: Optional[str] = typer.Option(None, "--output", "-o", help=OUTPUT_HELP),
    analyze: bool = typer.Option(False, "--analyze", help="Run AI analysis on fetched tweets"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Path to custom system prompt"),
    analysis_prompt: Optional[str] = typer.Option(None, "--analysis-prompt", help="Path to custom analysis prompt"),
):
    """Fetch and optionally analyze tweets from a specific user.

    Use --analyze to get AI-powered insights from a user's tweets.
    """
    console.print(Panel.fit(f"👤 Fetching tweets from {handle}", style="cyan bold"))

    client = BirdClient(count=count)

    tweets = client.fetch_user_tweets(handle)
    console.print(f"[green]Fetched {len(tweets)} tweets from @{handle}[/green]")

    if not tweets:
        console.print(f"[yellow]No tweets found for @{handle}[/yellow]")
        raise typer.Exit()

    if analyze:
        clean = handle.lstrip('@')
        _run_ai_analysis(
            tweets,
            f"@{clean}",
            save=save,
            output=output,
            system_prompt=system_prompt,
            analysis_prompt=analysis_prompt,
        )
        return

    parser = TweetParser()
    clean = handle.lstrip('@')
    parsed = parser.parse_tweets(tweets, source=f"user_{clean}")
    _output_report(parsed, clean, save=save, output=output)


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query"),
    count: int = typer.Option(50, "--count", "-c", help="Number of tweets to fetch"),
    save: bool = typer.Option(False, "--save", "-s", help=SAVE_HELP),
    output: Optional[str] = typer.Option(None, "--output", "-o", help=OUTPUT_HELP),
    analyze: bool = typer.Option(False, "--analyze", help="Run AI analysis on search results"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", help="Path to custom system prompt"),
    analysis_prompt: Optional[str] = typer.Option(None, "--analysis-prompt", help="Path to custom analysis prompt"),
):
    """Search for and optionally analyze tweets matching a query.

    Use --analyze to get AI-powered insights from search results.
    """
    console.print(Panel.fit(f"🔍 Searching for '{query}'", style="cyan bold"))

    client = BirdClient(count=count)

    tweets = client.search_tweets(query)
    console.print(f"[green]Found {len(tweets)} tweets[/green]")

    if not tweets:
        console.print(f"[yellow]No tweets found for '{query}'[/yellow]")
        raise typer.Exit()

    if analyze:
        _run_ai_analysis(
            tweets,
            f"search_{query[:20]}",
            save=save,
            output=output,
            system_prompt=system_prompt,
            analysis_prompt=analysis_prompt,
        )
        return

    parser = TweetParser()
    parsed = parser.parse_tweets(tweets, source=f"search_{query}")
    _output_report(parsed, f"search_{query[:20]}", save=save, output=output)


@app.command()
def status():
    """Show system status and configuration."""
    console.print(Panel.fit("🔧 System Status", style="cyan bold"))

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    client = BirdClient()
    bird_auth = client.verify_credentials()
    table.add_row("Bird CLI", "✓ Authenticated" if bird_auth else "✗ Not authenticated")

    # Show authentication method
    auth_method = "Headless (env vars)" if os.getenv("AUTH_TOKEN") else "Browser (bird login)"
    table.add_row("Auth method", auth_method)

    api_key = os.getenv("ZAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    table.add_row("API Key", "✓ Set" if api_key else "✗ Not set")

    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    table.add_row("Base URL", base_url)

    output_dir = Path("output")
    table.add_row(
        "Output directory",
        "✓ Exists" if output_dir.exists() else "✗ Not found",
    )

    console.print(table)


@app.command()
def interactive():
    """Enter interactive mode for running multiple commands."""
    console.print(Panel.fit("🔄 Interactive Mode", style="cyan bold"))
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]")

    while True:
        try:
            cmd = console.input("\n[bold cyan]news-parser>[/bold cyan] ").strip()

            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                break
            if cmd.lower() == "help":
                console.print("""
Available commands:
- timeline [--count N] [--analyze] [--output [file]] [--no-filter]
- bookmarks [--count N] [--analyze] [--output [file]] [--no-filter] [--shuffle]
- user <handle> [--count N] [--analyze] [--output [file]]
- search <query> [--count N] [--analyze] [--output [file]]
- status
- exit
                """)
                continue

            # Delegate to typer for parsing
            try:
                args = shlex.split(cmd)
                app(args, standalone_mode=False)
            except SystemExit:
                pass
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            break
        except EOFError:
            break


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
