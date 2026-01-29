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

# Get project root dynamically
DEFAULT_CWD = Path(__file__).parent.parent.resolve()


SYSTEM_PROMPT = """Ты — AI-аналитик новостей из X/Twitter. Отвечай ТОЛЬКО на русском языке.
Никогда не используй китайские, японские или другие иероглифы — только кириллица и латиница.

Твоя задача:
- Анализировать твиты и выделять ценную информацию
- ЖЁСТКО фильтровать мусор: мотивационные цитаты, relationship advice, односложные реплики, "comment X and I'll DM you", самопиар без substance
- Фокус: AI/dev tools, автоматизация, маркетинг через AI, бизнес-кейсы с конкретными цифрами, новые инструменты и техники
- Выводить структурированные Markdown-отчёты

Критерии качества:
- Есть конкретный actionable инсайт или инструмент? → оставить
- Есть реальные цифры/кейс? → оставить
- Мотивашка, platitude, "hustle porn"? → выбросить
- Односложная реплика без контекста? → выбросить
- "Comment X to get Y"? → выбросить
"""

def get_agent_options(
    base_url: str | None = None,
    api_key: str | None = None,
    cwd: Path | None = None,
) -> ClaudeAgentOptions:
    """Create ClaudeAgentOptions for the News Parser Agent.

    Args:
        base_url: Custom base URL for Anthropic API (defaults to z.ai).
        api_key: API key (defaults to ZAI_API_KEY from environment).
        cwd: Working directory for the agent.

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

    options = ClaudeAgentOptions(
        # System prompt
        system_prompt=SYSTEM_PROMPT,
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
        max_turns=5,
        max_budget_usd=0.50,
        # Model selection
        model="claude-sonnet-4-5",
        fallback_model="claude-haiku-3-5",
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
) -> str:
    """Analyze tweets using the Claude agent.

    Args:
        tweets: List of tweet texts to analyze.
        focus: What to focus the analysis on.

    Returns:
        Analysis result from the agent.
    """
    tweets_text = "\n\n---\n\n".join(tweets)

    prompt = f"""Проанализируй эти твиты. Отвечай строго на русском (кириллица + латиница для терминов, БЕЗ иероглифов).

Твиты:
{tweets_text}

ИНСТРУКЦИИ:
1. Сначала отфильтруй мусор: мотивационные цитаты, relationship advice, односложные реплики, engagement bait ("comment X"), пустой самопиар. НЕ включай их в отчёт вообще.
2. Оставшиеся твиты ранжируй по ценности (самые полезные первыми).

Формат ответа:

## Ценные твиты (ранжированы по полезности)

Для каждого твита:
### [номер]. @автор — краткий заголовок
**Оригинал:** краткая цитата ключевой мысли (не весь твит)
**Перевод:** перевод на русский
**Почему важно:** 1-2 предложения — конкретная польза, что можно применить (фокус: {focus})
**Ссылка:** ссылка на оригинальный твит (из данных твита)

## Общий анализ
1. Топ 3-5 actionable инсайтов (что конкретно делать)
2. Упомянутые инструменты и ресурсы (список)
3. Тренды и паттерны

## Отфильтровано
Одной строкой: сколько твитов выброшено и почему (например: "5 твитов отфильтровано: мотивашки, engagement bait, односложные реплики")"""

    return await query_agent(prompt)
