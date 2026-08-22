"""
Telegram botni ishga tushirish.
Foydalanish: python -m telegram_bot.run
"""
import asyncio
import logging
import os
import sys

from telegram_bot.bot import create_bot, create_dispatcher
from telegram_bot.config import validate

# Windows console uchun UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def main() -> None:
    """Botni polling rejimida ishga tushiradi."""

    # ── Logging sozlash ───────────────────────────────────
    # Windows da emoji va unicode to'g'ri chiqishi uchun
    stdout_handler = logging.StreamHandler(
        open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
        if sys.platform == "win32"
        else sys.stdout
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            stdout_handler,
            logging.FileHandler("telegram_bot.log", encoding="utf-8"),
        ],
    )
    # Aiogram va aiohttp ning debug loglarini pasaytirish
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    # ── Konfiguratsiyani tekshirish ───────────────────────
    try:
        validate()
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    # ── Bot yaratish va ishga tushirish ───────────────────
    bot = create_bot()
    dp = create_dispatcher()

    logger.info("=" * 50)
    logger.info("🤖 Telegram AI Bot ishga tushmoqda...")
    logger.info("=" * 50)

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
