#!/usr/bin/env python3
"""
Quick manual test for Telegram notifications.

Usage:
    python scripts/test_telegram.py

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


async def send(text: str) -> None:
    if not TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            print(f"✅ Message sent! message_id={data['result']['message_id']}")
        else:
            print(f"❌ Telegram API error: {data}")


SAMPLE_MSG = """\
🧪 <b>DeepThroath — Test Notification</b>

✅ Telegram integration is working correctly.

📊 <b>Sample metrics:</b>
  ✓ Answer Relevancy: <b>82.4%</b>
  ✓ Faithfulness: <b>78.1%</b>
  ✗ Ctx Precision: <b>61.3%</b>
  Порог: 70%

⚡ Duration: 42s
📁 <code>20260421_090000_dataset_ragas</code>
"""


if __name__ == "__main__":
    print(f"Sending test notification to chat_id={CHAT_ID!r}...")
    asyncio.run(send(SAMPLE_MSG))
