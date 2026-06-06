import os
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def send_telegram_message(message: str) -> bool:
    token = os.getenv("BATCH_TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("BATCH_TELEGRAM_BOT_ID")

    if not token or not chat_id:
        logging.warning("Telegram token or chat id is not configured.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )

        response.raise_for_status()
        return True

    except Exception as e:
        logging.error("Failed to send Telegram message.")
        logging.exception(e)
        return False
