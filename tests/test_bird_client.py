"""Tests for bird_client.py."""

import os
from unittest.mock import Mock, patch

import pytest

from first_agent.bird_client import BirdClient


class TestGetBirdEnv:
    """Tests for _get_bird_env() method."""

    def test_no_auth_tokens_set(self):
        """Test environment without auth tokens."""
        # Ensure tokens are not set
        os.environ.pop("AUTH_TOKEN", None)
        os.environ.pop("CT0", None)

        client = BirdClient()
        env = client._get_bird_env()

        # Should have all normal env vars but NOT add auth tokens
        assert env is not None
        assert "AUTH_TOKEN" not in env or env.get("AUTH_TOKEN") is None
        assert "CT0" not in env or env.get("CT0") is None

    def test_with_auth_tokens(self, monkeypatch):
        """Test environment with valid auth tokens."""
        monkeypatch.setenv("AUTH_TOKEN", "test_auth_token_123")
        monkeypatch.setenv("CT0", "test_csrf_token_456")

        client = BirdClient()
        env = client._get_bird_env()

        assert env["AUTH_TOKEN"] == "test_auth_token_123"
        assert env["CT0"] == "test_csrf_token_456"

    def test_whitespace_stripping(self, monkeypatch):
        """Test that whitespace is stripped from tokens."""
        monkeypatch.setenv("AUTH_TOKEN", "  token_with_spaces  ")
        monkeypatch.setenv("CT0", "\ttab_token\n")

        client = BirdClient()
        env = client._get_bird_env()

        assert env["AUTH_TOKEN"] == "token_with_spaces"
        assert env["CT0"] == "tab_token"

    def test_empty_tokens_ignored(self, monkeypatch):
        """Test that empty/whitespace-only tokens are not added."""
        monkeypatch.setenv("AUTH_TOKEN", "   ")
        monkeypatch.setenv("CT0", "")

        client = BirdClient()
        env = client._get_bird_env()

        # Empty tokens should not be added to env
        # The env has the base copy, but stripped tokens shouldn't be added back
        assert env.get("AUTH_TOKEN") != "   " or env.get("AUTH_TOKEN") is None
        assert env.get("CT0") != "" or env.get("CT0") is None

    def test_only_auth_token_set(self, monkeypatch):
        """Test with only AUTH_TOKEN set (CT0 missing)."""
        monkeypatch.setenv("AUTH_TOKEN", "test_token")
        monkeypatch.delenv("CT0", raising=False)

        client = BirdClient()
        env = client._get_bird_env()

        assert env.get("AUTH_TOKEN") == "test_token"
        # CT0 should not be added
        assert env.get("CT0") is None or "CT0" not in env

    def test_only_ct0_set(self, monkeypatch):
        """Test with only CT0 set (AUTH_TOKEN missing)."""
        monkeypatch.delenv("AUTH_TOKEN", raising=False)
        monkeypatch.setenv("CT0", "test_csrf")

        client = BirdClient()
        env = client._get_bird_env()

        # AUTH_TOKEN should not be added
        assert env.get("AUTH_TOKEN") is None or "AUTH_TOKEN" not in env
        assert env.get("CT0") == "test_csrf"


class TestTweetDataclass:
    """Tests for Tweet dataclass."""

    def test_tweet_validation(self):
        """Test that Tweet validates required fields."""
        from first_agent.bird_client import Tweet

        # Valid tweet
        tweet = Tweet(
            id="123",
            text="Test tweet",
            created_at="2024-01-01",
            author_username="testuser",
            author_name="Test User",
            author_id="456",
            reply_count=0,
            retweet_count=0,
            like_count=0,
            conversation_id="789",
        )
        assert tweet.id == "123"

    def test_tweet_invalid_id_raises(self):
        """Test that empty ID raises ValueError."""
        from first_agent.bird_client import Tweet

        with pytest.raises(ValueError, match="Tweet ID cannot be empty"):
            Tweet(
                id="",
                text="Test",
                created_at="2024-01-01",
                author_username="user",
                author_name="User",
                author_id="123",
                reply_count=0,
                retweet_count=0,
                like_count=0,
                conversation_id="456",
            )
