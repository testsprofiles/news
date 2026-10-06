import os

import requests
from dotenv import load_dotenv

# Allow the notifier to be used standalone (bot polling, scripts, tests).
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_subscriber_chat_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT chat_id FROM subscribers")
        return [row["chat_id"] for row in cur.fetchall()]


def _truncate(text: str, limit: int = 300) -> str:
    if not text:
        return "Tavsif kiritilmagan"
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def _build_caption(product: dict, updated: bool = False) -> str:
    prefix = "✏️ <b>MAHSULOT YANGILANDI</b>" if updated else "🆕 <b>YANGI MAHSULOT</b>"
    price_formatted = f"{product['price']:,.0f}".replace(",", " ")

    return (
        f"{prefix}\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"📦 <b>{product['name']}</b>\n\n"
        f"{_truncate(product.get('description'))}\n\n"
        f"💰 <b>Narxi:</b> {price_formatted} so'm\n"
        f"📂 <b>Kategoriya:</b> {product.get('category_name', '-')}\n\n"
        f"━━━━━━━━━━━━━━"
    )


def _send_to_chat(chat_id, caption, image_path, has_image):
    if has_image:
        with open(image_path, "rb") as photo:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                files={"photo": photo},
            )
    else:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": chat_id, "text": caption, "parse_mode": "HTML"},
        )
    print(f"[notifier] chat_id={chat_id} status={resp.status_code} response={resp.text}")


def notify_product(product: dict, conn, image_path: str = None, updated: bool = False):
    caption = _build_caption(product, updated=updated)
    has_image = bool(image_path and os.path.exists(image_path))

    if CHANNEL_ID:
        _send_to_chat(CHANNEL_ID, caption, image_path, has_image)

    chat_ids = get_subscriber_chat_ids(conn)
    for chat_id in chat_ids:
        _send_to_chat(chat_id, caption, image_path, has_image)