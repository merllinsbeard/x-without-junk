#!/bin/bash
# Commands to commit and push changes

git add -A
git status
git diff --staged

git commit -m "Add custom configuration system for prompts and filters

- Add config.yaml for agent, prompts, filters, and output settings
- Add prompts/system.md and prompts/analysis.md (English, replaced Russian)
- Add config/patterns.yaml with filter patterns
- Modify filters.py: YAML pattern loading, from_config() method
- Modify agent.py: prompt loading from markdown, removed hard-coded Russian
- Modify main.py: new CLI flags --config, --system-prompt, --analysis-prompt, --patterns
- Add pyyaml>=6.0.0 to dependencies
- Update .gitignore for user configs
- Update README with configuration docs and Russian implementation section
- Move demo image to canonical top position

Co-Authored-By: Claude (glm-4.7) <noreply@anthropic.com>"

git push
