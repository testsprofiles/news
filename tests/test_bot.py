"""Tests for bot/bot.py startup behaviour.

The module deliberately tolerates a missing token and transient Telegram API
errors - these tests lock that behaviour in without any network access.
"""

import logging

import pytest

import bot.bot as bot_module


def test_start_bot_without_token_returns(monkeypatch, caplog):
    monkeypatch.setattr(bot_module, "bot", None)

    with caplog.at_level(logging.ERROR):
        bot_module.start_bot()

    assert "ishga tushmadi" in caplog.text


def test_start_bot_retries_after_error(monkeypatch):
    calls = {"poll": 0}

    def flaky_polling(**kwargs):
        calls["poll"] += 1
        if calls["poll"] == 1:
            raise RuntimeError("boom")

    fake_bot = type("FakeBot", (), {"infinity_polling": staticmethod(flaky_polling)})()
    monkeypatch.setattr(bot_module, "bot", fake_bot)
    monkeypatch.setattr(bot_module.time, "sleep", lambda _seconds: None)

    bot_module.start_bot()

    assert calls["poll"] == 2


def test_start_bot_stops_on_keyboard_interrupt(monkeypatch):
    def interrupt(**kwargs):
        raise KeyboardInterrupt

    fake_bot = type("FakeBot", (), {"infinity_polling": staticmethod(interrupt)})()
    monkeypatch.setattr(bot_module, "bot", fake_bot)

    bot_module.start_bot()  # must not propagate


def test_bot_message_handler_requires_token(monkeypatch):
    monkeypatch.setattr(bot_module, "bot", None)

    with pytest.raises(RuntimeError):
        bot_module.bot_message_handler(commands=["start"])(lambda message: None)


def test_send_welcome_builds_webapp_keyboard(monkeypatch):
    """Regression: /start used to crash because the keyboard types were
    imported inside a different function (local scope)."""
    import types

    sent = {}

    class FakeBot:
        def send_message(self, chat_id, text, **kwargs):
            sent["chat_id"] = chat_id
            sent["text"] = text
            sent["markup"] = kwargs.get("reply_markup")

    monkeypatch.setattr(bot_module, "bot", FakeBot())
    monkeypatch.setattr(bot_module, "WEBAPP_URL", "https://example.test")

    message = types.SimpleNamespace(
        from_user=types.SimpleNamespace(first_name="Musavvir"),
        chat=types.SimpleNamespace(id=123),
    )

    bot_module.send_welcome(message)

    assert sent["chat_id"] == 123
    assert "Musavvir" in sent["text"]
    buttons = sent["markup"].keyboard
    assert buttons, "WebApp button should be attached when WEBAPP_URL is set"
    # pyTelegramBotAPI exposes the keyboard as plain dicts after building it.
    assert buttons[0][0]["web_app"]["url"] == "https://example.test"
