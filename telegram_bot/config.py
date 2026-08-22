"""
Konfiguratsiya — .env fayldan o'qiydi.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── OmniRoute ─────────────────────────────────────────────
OMNIROUTE_BASE_URL: str = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
OMNIROUTE_API_KEY: str = os.getenv("OMNIROUTE_API_KEY", "")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "auto")

# ── Suhbat sozlamalari ────────────────────────────────────
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "20"))
MAX_RESPONSE_TOKENS: int = int(os.getenv("MAX_RESPONSE_TOKENS", "4096"))

# ── System prompt ─────────────────────────────────────────
SYSTEM_PROMPT: str = os.getenv("SYSTEM_PROMPT", """Sen — tajribali dasturchi yordamchisan. 
Qoidalaring:
- Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob ber.
- Javoblaring aniq va qisqa bo'lsin.
- Kod yozganda izohlar bilan tushuntir.
- Bilmagan narsangni halol ayt — o'ylab topma.
- Xatolarni tuzatishda sabab va yechimni ko'rsat.
- Telegram formatiga mos yoz (Markdown V2 emas, oddiy Markdown).
""")


def validate() -> None:
    """Muhim konfiguratsiyalar borligini tekshiradi."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "❌ TELEGRAM_BOT_TOKEN topilmadi!\n"
            "   .env faylga TELEGRAM_BOT_TOKEN=... qo'shing.\n"
            "   Token olish: Telegramda @BotFather ga /newbot yozing."
        )
