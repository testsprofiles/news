"""Unit tests for the Telegram product notifier (bot/notifier.py).

No network access is performed - ``requests.post`` is patched and the
telegram API base URL is only built from environment variables.
"""

from unittest.mock import patch

import pytest

from bot import notifier


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, query):
        self.query = query

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _Conn:
    def __init__(self, rows):
        self._cursor = _Cursor(rows)

    def cursor(self):
        return self._cursor


def _product():
    return {
        "id": 1,
        "name": "Noutbuk",
        "description": "Juda tez ishlaydigan noutbuk",
        "price": 12500000,
        "image_url": None,
        "category_id": 2,
        "category_name": "Texnika",
    }


def test_truncate_empty_returns_placeholder():
    assert notifier._truncate("") == "Tavsif kiritilmagan"
    assert notifier._truncate(None) == "Tavsif kiritilmagan"


def test_truncate_short_text_unchanged():
    assert notifier._truncate("qisqa matn") == "qisqa matn"


def test_truncate_long_text_is_cut():
    result = notifier._truncate("a" * 400)

    assert result.endswith("...")
    assert len(result) <= 303


def test_build_caption_contains_name_and_price():
    caption = notifier._build_caption(_product())

    assert "YANGI MAHSULOT" in caption
    assert "Noutbuk" in caption
    assert "12 500 000" in caption
    assert "Texnika" in caption


def test_build_caption_updated_prefix():
    caption = notifier._build_caption(_product(), updated=True)

    assert "YANGILANDI" in caption


def test_get_subscriber_chat_ids():
    conn = _Conn([{"chat_id": 111}, {"chat_id": 222}])

    assert notifier.get_subscriber_chat_ids(conn) == [111, 222]


def test_send_to_chat_message(monkeypatch):
    response = type("R", (), {"status_code": 200, "text": "ok"})()
    with patch.object(notifier.requests, "post", return_value=response) as mock_post:
        notifier._send_to_chat(111, "salom", None, has_image=False)

    mock_post.assert_called_once()
    assert "sendMessage" in mock_post.call_args[0][0]


def test_send_to_chat_photo(tmp_path):
    image = tmp_path / "pic.png"
    image.write_bytes(b"png-bytes")
    response = type("R", (), {"status_code": 200, "text": "ok"})()
    with patch.object(notifier.requests, "post", return_value=response) as mock_post:
        notifier._send_to_chat(111, "salom", str(image), has_image=True)

    mock_post.assert_called_once()
    assert "sendPhoto" in mock_post.call_args[0][0]


def test_notify_product_sends_to_subscribers(monkeypatch):
    sent = []
    monkeypatch.setattr(notifier, "CHANNEL_ID", None)
    monkeypatch.setattr(notifier, "get_subscriber_chat_ids", lambda conn: [111, 222])
    monkeypatch.setattr(
        notifier, "_send_to_chat", lambda chat_id, caption, image_path, has_image: sent.append(chat_id)
    )

    notifier.notify_product(_product(), conn=_Conn([]))

    assert sent == [111, 222]


def test_notify_product_sends_to_channel_and_subscribers(monkeypatch):
    sent = []
    monkeypatch.setattr(notifier, "CHANNEL_ID", "999")
    monkeypatch.setattr(notifier, "get_subscriber_chat_ids", lambda conn: [111])
    monkeypatch.setattr(
        notifier, "_send_to_chat", lambda chat_id, caption, image_path, has_image: sent.append(chat_id)
    )

    notifier.notify_product(_product(), conn=_Conn([]), updated=True)

    assert sent == ["999", 111]
