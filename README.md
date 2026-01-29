# X Without Junk 🐦

![Demo output](docs/demo.png)

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

## 🤖 AI-Powered Analysis

Unlock deeper insights with Claude AI analysis. Use the `--analyze` flag to get intelligent summaries and categorization of your Twitter content.

```bash
# Analyze your timeline with AI
uv run news-parser timeline --analyze

# Analyze bookmarks with custom focus
uv run news-parser bookmarks --analyze --count 100

# Analyze a specific user's tweets
uv run news-parser user @anthropic --analyze

# Analyze search results
uv run news-parser search "Claude AI" --analyze --count 50
```

**AI analysis provides:**

- **Smart categorization** - Automatically groups tweets by topic (news, threads, resources, discussions)
- **Key insights** - Extracts the most important information and themes
- **Trend detection** - Identifies emerging patterns and conversations
- **Clean summaries** - Removes noise and highlights what matters

Results are automatically saved to `output/analysis_*.md` files with timestamped filenames.

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
git clone https://github.com/merllinsbeard/first_agent_claudesdk.git
cd first_agent_claudesdk

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

## 🔐 Authentication

The tool supports two authentication methods:

### Method 1: Browser-Based Authentication (Default)

**Recommended for personal use and interactive sessions.**

1. Run `bird login` in your terminal
2. Authenticate in the browser window that opens
3. No configuration needed - bird CLI stores your session

Verify authentication:

```bash
bird whoami
# Expected output: @yourusername
```

### Method 2: Headless Authentication (Environment Variables)

**Recommended for CI/CD, servers, and automated workflows.**

Headless authentication allows the tool to run without a browser by providing authentication tokens directly via environment variables.

#### Extracting Authentication Tokens

1. **Open X.com in your browser** while logged in
2. **Open Developer Tools**:
   - Chrome/Edge: `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (Mac)
   - Firefox: `F12` or `Ctrl+Shift+K` (Windows/Linux) / `Cmd+Option+K` (Mac)
3. **Navigate to Application/Storage**:
   - Chrome/Edge: Application tab → Storage → Cookies → https://x.com
   - Firefox: Storage tab → Cookies → https://x.com
4. **Find and copy two cookies**:
   - `auth_token` → Copy the Value column
   - `ct0` → Copy the Value column

#### Configure Environment Variables

Add to your `.env` file:

```bash
# X/Twitter Authentication (Headless)
AUTH_TOKEN=your_auth_token_value_here
CT0=your_ct0_value_here
```

**Security Notes:**

- Treat these tokens as sensitive passwords
- Never commit `.env` to version control
- Tokens expire periodically and may need refreshing
- Use separate tokens for different environments

#### Verify Headless Authentication

```bash
uv run news-parser status
```

Expected output should show `Bird CLI ✓ Authenticated`

#### When to Use Each Method

| Scenario                | Recommended Method           |
| ----------------------- | ---------------------------- |
| Personal laptop/desktop | Browser-based (`bird login`) |
| CI/CD pipelines         | Headless (env vars)          |
| Docker containers       | Headless (env vars)          |
| Remote servers          | Headless (env vars)          |
| Interactive development | Browser-based (`bird login`) |

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
| `AUTH_TOKEN`         | X.com auth token (headless)   | Use `bird login`                 |
| `CT0`                | X.com CSRF token (headless)   | Use `bird login`                 |

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

---

## 🔧 Troubleshooting

| Problem                                        | Solution                                                                                                  |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `bird: command not found`                      | Install bird CLI: `brew install bird`                                                                     |
| `python: command not found`                    | Install Python 3.12+ from python.org                                                                      |
| `uv: command not found`                        | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh`                                            |
| `No API key found`                             | Check `.env` file exists and contains `ZAI_API_KEY`                                                       |
| `Bird CLI not authenticated`                   | Run `bird login` and authenticate in browser                                                              |
| `Bird CLI auth fails with headless tokens`     | Tokens may be expired. Re-extract from browser and update `.env`. Ensure both AUTH_TOKEN and CT0 are set. |
| `bird login not available in CI/CD`            | Use headless authentication by setting AUTH_TOKEN and CT0 environment variables                           |
| `401 Unauthorized with headless auth`          | Verify tokens are correctly copied from browser cookies. Check for extra spaces or quotes in `.env`       |
| `ModuleNotFoundError: No module 'first_agent'` | Run `uv sync` to install dependencies                                                                     |
| API returns 401/403                            | Check `ANTHROPIC_BASE_URL` in `.env`                                                                      |
| MiniMax API errors                             | Try switching to z.ai or Anthropic API key                                                                |

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/merllinsbeard/first_agent_claudesdk.git
cd first_agent_claudesdk

# Install dependencies in development mode
uv sync

# Create a local environment file
cp .env.example .env
# Edit .env and add your API key
```

### Code Quality

Run with type checking:

```bash
uv run mypy src/
```

### Testing

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=first_agent --cov-report=html
```

### Project Structure

```
src/first_agent/
├── __init__.py      # Package initialization
├── main.py          # CLI entry point (Typer commands)
├── agent.py         # Claude Agent SDK integration
├── bird_client.py   # Bird CLI wrapper (Tweet dataclass)
├── filters.py       # Content filtering logic
└── parsers.py       # Tweet parsing and Markdown output
```

### Development Guidelines

- Use type hints for all functions
- Prefer `@dataclass(frozen=True)` for immutable data structures
- Follow PEP 8 style guidelines
- Keep modules focused on single responsibilities
- Use Rich console for CLI output formatting

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

MIT
