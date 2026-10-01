"""A dead network must cost one short wait, not one per click."""

import httpx
import pytest

from app.core.config import get_settings
from app.domains.llm import client as llm_client


@pytest.fixture
def configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_enabled", True)
    llm_client.reset_circuit()
    yield settings
    llm_client.reset_circuit()


def test_a_failure_opens_the_circuit(configured, monkeypatch):
    calls = []

    def failing_post(*args, **kwargs):
        calls.append(1)
        raise httpx.ConnectTimeout("venue wifi")

    monkeypatch.setattr(httpx, "post", failing_post)
    assert llm_client.chat([{"role": "user", "content": "hi"}]) is None
    assert llm_client.chat([{"role": "user", "content": "hi"}]) is None
    assert llm_client.chat([{"role": "user", "content": "hi"}]) is None
    assert len(calls) == 1
    assert llm_client.is_configured() is False


def test_the_circuit_closes_after_the_cooldown(configured, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(llm_client.time, "monotonic", lambda: clock[0])

    def failing_post(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", failing_post)
    llm_client.chat([{"role": "user", "content": "hi"}])
    assert llm_client.is_configured() is False
    clock[0] += llm_client.COOLDOWN_SECONDS + 1
    assert llm_client.is_configured() is True


def test_disabled_switch_skips_every_call(configured, monkeypatch):
    monkeypatch.setattr(configured, "llm_enabled", False)

    def unexpected(*args, **kwargs):
        raise AssertionError("no call should be made")

    monkeypatch.setattr(httpx, "post", unexpected)
    assert llm_client.is_configured() is False
    assert llm_client.chat([{"role": "user", "content": "hi"}]) is None
