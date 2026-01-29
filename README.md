# X Without Junk 🐦

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Claude Agent SDK](https://img.shields.io/badge/Claude_Agent_SDK-0.1.25+-green.svg)](https://github.com/anthropics/claude-agent-sdk)

> A Python tool that fetches content from X.com using bird CLI,
> filters out junk/marketing/spam, and generates clean Markdown reports.

## ⚡ Quick Start (5 min)

```bash
# 1. Install dependencies
uv sync

# 2. Setup environment
cp .env.example .env
# Edit .env and add your API key

# 3. Verify setup
uv run news-parser status

# 4. Run!
uv run news-parser timeline --count 5
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Twitter/X Timeline                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │    Bird CLI        │
            │  (fetch tweets)    │
            └────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │   Content Filter           │
         │  (filter spam/marketing)    │
         └────────┬──────────────────┘
                     │
                     ▼
         ┌─────────────────────────────┐
         │      Tweet Parser            │
         │  (categorize → news/threads)  │
         └────────┬──────────────────────┘
                     │
         ┌───────────┴────────────────┐
         ▼                           ▼
   ┌─────────────┐          ┌──────────────┐
   │Markdown     │          │Claude Agent  │
   │Writer       │          │(AI Analysis) │
   └─────────────┘          └──────────────┘
         │                           │
         ▼                           ▼
    📄 Report.md              🤖 Analysis.md
```

**Data flow:** Bird CLI → tweets → ContentFilter → filtered → TweetParser → categorized → MarkdownWriter → report

## 📋 Requirements

Before installing, ensure you have:

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **uv** — package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **bird CLI** — X.com client: `brew install bird`
- **API key** — from [z.ai console](https://console.z.ai) or [Anthropic](https://console.anthropic.com)

## 📥 Installation

### Step 1: Verify Prerequisites

```bash
# Check Python version (must be 3.12+)
python --version

# Check uv is installed
uv --version

# Check bird CLI is installed and authenticated
bird whoami
```

**Trouble?** See [Troubleshooting](#-troubleshooting) below.

### Step 2: Install Dependencies

```bash
# Clone repository
git clone https://github.com/merllinsbeard/x-without-junk.git
cd x-without-junk

# Install dependencies
uv sync
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Get key from: https://console.z.ai
nano .env  # or your preferred editor
```

### Step 4: Verify Installation

```bash
# Check system status
uv run news-parser status
```

Expected output:

```
✓ System Status Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bird CLI         ✓ Authenticated
API Key         ✓ Set
Base URL        https://api.z.ai/api/anthropic
Output directory ✓ Exists
```

## 🚀 Usage

### Basic Commands

```bash
# Run with uv (recommended)
uv run news-parser timeline

# Or install and run directly
uv pip install -e .
news-parser timeline
```

### Available Commands

#### Fetch Timeline

```bash
uv run news-parser timeline [OPTIONS]
```

Options:

- `-c, --count <number>` - Number of tweets to fetch (default: 50)
- `-o, --output <path>` - Output file path
- `--no-filter` - Skip content filtering

#### Fetch Bookmarks

```bash
uv run news-parser bookmarks [OPTIONS]
```

Options:

- `-c, --count <number>` - Number of bookmarks to fetch (default: 50)
- `-o, --output <path>` - Output file path
- `--no-filter` - Skip content filtering
- `--shuffle` - Randomize bookmark order

#### Fetch User Tweets

```bash
uv run news-parser user <handle> [OPTIONS]
```

Example:

```bash
uv run news-parser user @anthropic
```

#### Search Tweets

```bash
uv run news-parser search <query> [OPTIONS]
```

Example:

```bash
uv run news-parser search "Claude AI" --count 100
```

#### AI Analysis

```bash
uv run news-parser analyze [OPTIONS]
```

Analyzes tweets using Claude AI for deeper insights.

#### System Status

```bash
uv run news-parser status
```

Shows authentication status and configuration.

#### Interactive Mode

```bash
uv run news-parser interactive
```

Run multiple commands in an interactive session.

## Examples

```bash
# Fetch last 100 timeline tweets with filtering
uv run news-parser timeline --count 100

# Get bookmarks without filtering
uv run news-parser bookmarks --no-filter

# Analyze a specific user's tweets
uv run news-parser user @openai --output openai_report.md

# Search for AI-related content
uv run news-parser search "artificial intelligence"

# Run AI analysis on timeline
uv run news-parser analyze --source timeline --count 50
```

## Output Structure

![Demo output](docs/demo.png)

Reports are saved to the `output/` directory by default:

```
# X Timeline Report - 2026-01-29

## 📰 Top News
### Author Name (@handle)
*Timestamp* | Engagement: 42
Tweet text content...
[View on X](https://x.com/i/status/...)

## 🧵 Interesting Threads
...

## 🔗 Resources Shared
...
```

## Content Filtering

The agent filters out:

- Marketing and promotional content
- Self-improvement cliches
- Spam and low-quality posts
- Pure emoji reactions
- Duplicate content

## Project Structure

```
├── src/
│   └── first_agent/      # Main package
│       ├── __init__.py
│       ├── main.py       # CLI entry point
│       ├── agent.py      # Claude Agent SDK setup
│       ├── bird_client.py # Wrapper for bird CLI commands
│       ├── filters.py    # Content filtering logic
│       └── parsers.py    # Parse and structure content
├── output/               # Generated markdown reports
├── docs/                 # Documentation and images
├── config/               # Optional configuration files
├── prompts/              # Custom prompt templates
├── .env.example          # Environment variables template
├── .env                  # Your local environment (gitignored)
├── pyproject.toml
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # Contribution guidelines
└── README.md
```

## Configuration

The agent reads configuration from the `.env` file:

| Variable             | Description                   | Default                          |
| -------------------- | ----------------------------- | -------------------------------- |
| `ZAI_API_KEY`        | API key for z.ai or Anthropic | _Required_                       |
| `ANTHROPIC_BASE_URL` | API base URL                  | `https://api.z.ai/api/anthropic` |

To get an API key, visit [https://console.z.ai](https://console.z.ai).

### Custom Configuration (Optional)

You can customize the agent's behavior using YAML configuration files and custom prompt templates.

#### Config File (`config.yaml`)

Create a `config.yaml` file to override default settings:

```yaml
# Agent Configuration
agent:
  model: "claude-sonnet-4-5"
  fallback_model: "claude-haiku-3-5"
  max_budget_usd: 0.50
  max_turns: 5

# Prompt File Paths
prompts:
  system: "prompts/system.md"
  analysis: "prompts/analysis.md"

# Filter Configuration
filters:
  enabled: true
  min_score: 30
  patterns_file: "config/patterns.yaml"

# Output Configuration
output:
  default_source: "timeline"
  timestamp_format: "%Y%m%d_%H%M%S"
```

#### Custom Prompts

Create custom prompt templates in Markdown:

**`prompts/system.md`:**

```markdown
You are a specialized AI analyst focusing on machine learning research.
Your task is to analyze tweets and extract technical insights...
```

**`prompts/analysis.md`:**

```markdown
Analyze these tweets.

Tweets:
{tweets}

Focus your analysis on: {focus}
...
```

#### Custom Filter Patterns

Create `config/patterns.yaml` to customize filtering:

```yaml
# Marketing patterns (regex)
marketing:
  - "\\b🚀\\b"
  - "launching\\s+soon"
  # Add your patterns...

# Self-improvement keywords
self_improvement:
  - "morning routine"
  # Add your keywords...

# Spam patterns
spam:
  - "free\\s+money"
  # Add your patterns...

# Low quality patterns
low_quality:
  - "^wow$"
  # Add your patterns...
```

#### CLI Options

Override config files with command-line options:

```bash
# Use custom config file
news-parser --config /path/to/my_config.yaml timeline --analyze

# Use custom prompts
news-parser timeline --analyze \
  --system-prompt my_system.md \
  --analysis-prompt my_analysis.md

# Use custom filter patterns
news-parser timeline --analyze --patterns my_patterns.yaml
```

The default prompts are provided in English. You can create custom prompts in any language.

## 🔧 Troubleshooting

| Problem                                        | Solution                                                       |
| ---------------------------------------------- | -------------------------------------------------------------- |
| `bird: command not found`                      | Install bird CLI: `brew install bird`                          |
| `python: command not found`                    | Install Python 3.12+ from python.org                           |
| `uv: command not found`                        | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `No API key found`                             | Check `.env` file exists and contains `ZAI_API_KEY`            |
| `Bird CLI not authenticated`                   | Run `bird login` and authenticate in browser                   |
| `ModuleNotFoundError: No module 'first_agent'` | Run `uv sync` to install dependencies                          |
| API returns 401/403                            | Check `ANTHROPIC_BASE_URL` in `.env`                           |
| MiniMax API errors                             | Try switching to z.ai or Anthropic API key                     |

## Development

Run with type checking:

```bash
uv run mypy src/
```

Run tests:

```bash
uv run pytest
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

MIT
