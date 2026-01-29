# Contributing to News Parser Agent

Thank you for your interest in contributing to the News Parser Agent! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/merllinsbeard/first_agent_claudesdk.git
   cd first_agent_claudesdk/first_agent
   ```

2. **Install dependencies using uv**:

   ```bash
   uv sync
   ```

3. **Set up environment variables**:

   ```bash
   cp .env.example .env
   # Edit .env and add your ZAI_API_KEY
   ```

4. **Install the package in editable mode**:

   ```bash
   uv pip install -e .
   ```

5. **Verify installation**:
   ```bash
   news-parser status
   ```

## Code Style

- Use **Python 3.12+** type hints
- Follow **PEP 8** style guidelines
- Use **absolute imports** within the package
- Add docstrings to all public functions and classes
- Keep functions focused and modular

## Running Tests

Before submitting a pull request:

1. **Test CLI installation**:

   ```bash
   uv run news-parser status
   ```

2. **Test individual commands**:

   ```bash
   uv run news-parser timeline --count 5
   uv run news-parser bookmarks --count 5
   ```

3. **Test AI analysis** (requires API key):
   ```bash
   uv run news-parser analyze --source timeline --count 10
   ```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Update documentation as needed
- Follow the existing code style

## Reporting Issues

When reporting bugs or requesting features:

- Use the GitHub issue tracker
- Provide clear steps to reproduce
- Include error messages and stack traces
- Specify your environment (OS, Python version, etc.)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
