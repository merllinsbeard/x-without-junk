"""Tests for prompt rendering."""

from first_agent.agent import render_analysis_prompt


def test_render_analysis_prompt_keeps_literal_braces():
    template = "Tweets:\n{tweets}\nFocus: {focus}\nLiteral: {not_a_var}\n"
    tweets = "Hello {world}!"
    focus = "news"

    rendered = render_analysis_prompt(template, tweets, focus)

    assert "Hello {world}!" in rendered
    assert "Focus: news" in rendered
    assert "Literal: {not_a_var}" in rendered
