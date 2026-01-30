"""Claude Agent SDK setup for the News Parser Agent."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from rich.console import Console

# Load .env file (override shell env vars)
load_dotenv(override=True)

console = Console()

def find_repo_root(start_path: Path) -> Path:
    """Find the repository root by searching for pyproject.toml."""
    for parent in [start_path, *start_path.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return start_path.parent.parent.resolve()


# Get project root dynamically
DEFAULT_CWD = find_repo_root(Path(__file__).resolve())

# Default paths for prompts (relative to project root)
DEFAULT_SYSTEM_PROMPT_PATH = DEFAULT_CWD / "prompts" / "system.md"
DEFAULT_ANALYSIS_PROMPT_PATH = DEFAULT_CWD / "prompts" / "analysis.md"


def load_prompt(path: str | Path, variables: dict | None = None) -> str:
    """Load prompt template from markdown file and substitute variables.

    Args:
        path: Path to the markdown file.
        variables: Optional dictionary of variables to substitute in the template.
                   Variables are specified as {key} in the template.

    Returns:
        The prompt content with variables substituted.
    """
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    content = prompt_path.read_text(encoding="utf-8")

    if variables:
        content = content.format(**variables)

    return content


def get_default_system_prompt() -> str:
    """Load default system prompt from prompts/system.md.

    Returns:
        The default system prompt content.
    """
    return load_prompt(DEFAULT_SYSTEM_PROMPT_PATH)


def get_default_analysis_prompt() -> str:
    """Load default analysis prompt from prompts/analysis.md.

    Returns:
        The default analysis prompt template (contains placeholders).
    """
    return load_prompt(DEFAULT_ANALYSIS_PROMPT_PATH)

def get_agent_options(
    base_url: str | None = None,
    api_key: str | None = None,
    cwd: Path | None = None,
    system_prompt: str | None = None,
    config: dict | None = None,
) -> ClaudeAgentOptions:
    """Create ClaudeAgentOptions for the News Parser Agent.

    Args:
        base_url: Custom base URL for Anthropic API (defaults to z.ai).
        api_key: API key (defaults to ZAI_API_KEY from environment).
        cwd: Working directory for the agent.
        system_prompt: Optional custom system prompt (loads from file if None).
        config: Optional configuration dictionary.

    Returns:
        Configured ClaudeAgentOptions.
    """
    # Use z.ai as default
    if base_url is None:
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")

    # Get API key from environment (try AUTH_TOKEN first for minimax, then API_KEY, then ZAI)
    if api_key is None:
        api_key = (
            os.getenv("ANTHROPIC_AUTH_TOKEN")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ZAI_API_KEY")
        )

    if not api_key:
        raise ValueError(
            "No API key found. Set ANTHROPIC_AUTH_TOKEN, ANTHROPIC_API_KEY, or ZAI_API_KEY environment variable."
        )

    # Set working directory
    work_dir = cwd or DEFAULT_CWD

    # Load system prompt (from parameter, config, or default file)
    if system_prompt is None:
        if config and "prompts" in config:
            system_path = config["prompts"].get("system")
            if system_path:
                # Path is relative to project root
                full_path = DEFAULT_CWD / system_path
                system_prompt = load_prompt(full_path)
        else:
            system_prompt = get_default_system_prompt()

    # Get agent config values
    if config and "agent" in config:
        agent_config = config["agent"]
        model = agent_config.get("model", "claude-sonnet-4-5")
        fallback_model = agent_config.get("fallback_model", "claude-haiku-3-5")
        max_turns = agent_config.get("max_turns", 5)
        max_budget = agent_config.get("max_budget_usd", 0.50)
    else:
        model = "claude-sonnet-4-5"
        fallback_model = "claude-haiku-3-5"
        max_turns = 5
        max_budget = 0.50

    options = ClaudeAgentOptions(
        # System prompt
        system_prompt=system_prompt,
        # Working directory
        cwd=str(work_dir),
        # Environment variables for the agent
        env={
            "ANTHROPIC_API_KEY": api_key,
            "ANTHROPIC_AUTH_TOKEN": api_key,
            "ANTHROPIC_BASE_URL": base_url,
        },
        # Tool permissions - we only need read-only tools
        allowed_tools=["Read", "Bash"],
        permission_mode="acceptEdits",
        # Conversation settings
        max_turns=max_turns,
        max_budget_usd=max_budget,
        # Model selection
        model=model,
        fallback_model=fallback_model,
    )

    console.print("[dim]Agent configured:[/dim]")
    console.print(f"  Base URL: {base_url}")
    console.print(f"  Model: {options.model}")
    console.print(f"  Working directory: {work_dir}")

    return options


async def query_agent(prompt: str, options: ClaudeAgentOptions | None = None) -> str:
    """Query the Claude agent with a prompt.

    Args:
        prompt: The prompt to send to the agent.
        options: Optional ClaudeAgentOptions. Uses default if not provided.

    Returns:
        The agent's response text.
    """
    if options is None:
        options = get_agent_options()

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)

        response_parts = []
        async for msg in client.receive_response():
            from claude_agent_sdk import AssistantMessage, TextBlock

            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            elif hasattr(msg, "total_cost_usd"):
                cost = msg.total_cost_usd
                console.print(f"[dim]Query cost: ${cost:.4f}[/dim]")

        return "".join(response_parts)


async def analyze_tweets_with_agent(
    tweets: list[str],
    focus: str = "news and insights",
    system_prompt: str | None = None,
    analysis_prompt: str | None = None,
    config: dict | None = None,
) -> str:
    """Analyze tweets using the Claude agent.

    Args:
        tweets: List of tweet texts to analyze.
        focus: What to focus the analysis on.
        system_prompt: Optional custom system prompt.
        analysis_prompt: Optional custom analysis prompt template.
        config: Optional configuration dictionary.

    Returns:
        Analysis result from the agent.
    """
    tweets_text = "\n\n---\n\n".join(tweets)

    # Load analysis prompt (from parameter, config, or default file)
    if analysis_prompt is None:
        if config and "prompts" in config:
            analysis_path = config["prompts"].get("analysis")
            if analysis_path:
                # Path is relative to project root
                full_path = DEFAULT_CWD / analysis_path
                analysis_prompt = load_prompt(full_path)
        else:
            analysis_prompt = get_default_analysis_prompt()

    # Substitute placeholders in the analysis prompt
    prompt = analysis_prompt.format(tweets=tweets_text, focus=focus)

    # Get options with custom system prompt if provided
    options = get_agent_options(system_prompt=system_prompt, config=config)

    return await query_agent(prompt, options)
