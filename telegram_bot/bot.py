"""
Telegram bot — asosiy handler'lar va komandalar.
Aiogram 3.x bilan ishlaydi.
"""
from __future__ import annotations

import logging
from textwrap import dedent

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from telegram_bot.config import DEFAULT_MODEL, TELEGRAM_BOT_TOKEN
from telegram_bot.conversation import conversation_manager
from telegram_bot.omniroute_client import (
    OmniRouteError,
    chat_completion,
    close_session,
)

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────
router = Router(name="main")


# ══════════════════════════════════════════════════════════
#  KOMANDALAR
# ══════════════════════════════════════════════════════════


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    /start — botni boshlash.
    """
    user = message.from_user
    name = user.first_name if user else "do'stim"

    await message.answer(
        f"👋 Salom, {name}!\n\n"
        "Men — AI kod yordamchisiman. Menga istalgan dasturlash savolingizni yozing.\n\n"
        "🔹 Kod yozishda yordam\n"
        "🔹 Xatolarni tuzatish\n"
        "🔹 Tushuntirish va maslahat\n\n"
        "📌 Komandalar:\n"
        "/help — yordam\n"
        "/clear — suhbatni tozalash\n"
        "/model — modelni o'zgartirish\n\n"
        "💬 Qaysi tilda yozsangiz, o'sha tilda javob beraman!"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    /help — yordam xabari.
    """
    await message.answer(
        "🤖 *AI Kod Yordamchisi*\n\n"
        "Menga istalgan dasturlash savolingizni yozing — "
        "Python, JavaScript, Java, C++, SQL va boshqa tillarda yordam bera olaman.\n\n"
        "*Komandalar:*\n"
        "• /start — botni boshlash\n"
        "• /help — shu yordam xabari\n"
        "• /clear — suhbat tarixini tozalash\n"
        "• /model — hozirgi modelni ko'rish/o'zgartirish\n\n"
        "*Nimalar qila olaman:*\n"
        "✅ Kod yozish va tushuntirish\n"
        "✅ Xatolarni topish va tuzatish\n"
        "✅ Algoritmlarni tushuntirish\n"
        "✅ Code review qilish\n"
        "✅ Database so'rovlari yozish\n"
        "✅ API integratsiya yordam\n\n"
        "💡 _Savolingizni iloji boricha aniq yozing — "
        "yaxshi savol = yaxshi javob!_",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    """
    /clear — suhbat tarixini tozalash.
    """
    user_id = message.from_user.id if message.from_user else 0
    conversation_manager.clear(user_id)
    await message.answer("🗑️ Suhbat tarixi tozalandi. Yangi mavzudan boshlashingiz mumkin!")


@router.message(Command("model"))
async def cmd_model(message: Message) -> None:
    """
    /model — hozirgi modelni ko'rish yoki o'zgartirish.
    /model auto/coding  — modelni o'zgartirish
    """
    user_id = message.from_user.id if message.from_user else 0
    args = message.text.strip().split(maxsplit=1) if message.text else []

    if len(args) < 2:
        # Hozirgi modelni ko'rsatish
        current = conversation_manager.get_model(user_id) or DEFAULT_MODEL
        await message.answer(
            f"🤖 Hozirgi model: `{current}`\n\n"
            "Modelni o'zgartirish:\n"
            "`/model auto` — balansli\n"
            "`/model auto/coding` — kod uchun sifatli\n"
            "`/model auto/fast` — tez javob\n"
            "`/model auto/cheap` — arzon\n",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    new_model = args[1].strip()
    conversation_manager.set_model(user_id, new_model)
    await message.answer(f"✅ Model o'zgartirildi: `{new_model}`", parse_mode=ParseMode.MARKDOWN)


# ══════════════════════════════════════════════════════════
#  XABAR HANDLER — asosiy AI suhbat
# ══════════════════════════════════════════════════════════


@router.message(F.text)
async def handle_message(message: Message) -> None:
    """
    Har qanday matnli xabarni AI ga yuboradi va javobni qaytaradi.
    """
    if not message.text or not message.from_user:
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    if not user_text:
        return

    # "Typing..." ko'rsatish
    await message.chat.do(ChatAction.TYPING)

    # Foydalanuvchi xabarini tarixga qo'shish
    conversation_manager.add_user_message(user_id, user_text)

    # Suhbat xabarlarini olish
    messages = conversation_manager.get_messages(user_id)
    model = conversation_manager.get_model(user_id)

    try:
        # OmniRoute ga so'rov
        response = await chat_completion(messages, model=model)

        if not response:
            await message.answer("🤔 Javob bo'sh keldi. Qayta urinib ko'ring.")
            return

        # Javobni tarixga qo'shish
        conversation_manager.add_assistant_message(user_id, response)

        # Telegram 4096 belgi limitiga mos qilish
        await _send_long_message(message, response)

    except OmniRouteError as exc:
        logger.error("OmniRoute xatoligi: %s | detail=%s", exc, exc.detail)
        # Xatolik yuzaga kelganda, oxirgi user xabarini olib tashlash
        # chunki javob bermadi
        conversation_manager._history[user_id].pop()
        await message.answer(exc.user_message())

    except Exception as exc:
        logger.exception("Kutilmagan xatolik: %s", exc)
        conversation_manager._history[user_id].pop()
        await message.answer(
            "❌ Kutilmagan xatolik yuzaga keldi. Keyinroq urinib ko'ring."
        )


# ══════════════════════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ══════════════════════════════════════════════════════════


async def _send_long_message(
    message: Message,
    text: str,
    max_len: int = 4096,
) -> None:
    """
    Uzun xabarni bo'laklarga bo'lib yuboradi (Telegram 4096 limit).
    Kod bloklari ichida bo'linmasligi uchun ehtiyotkor bo'ladi.
    """
    if len(text) <= max_len:
        await message.answer(text, parse_mode=ParseMode.MARKDOWN)
        return

    # Matnni bo'laklarga bo'lish
    chunks = _split_text(text, max_len)
    for chunk in chunks:
        try:
            await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Markdown xatoligi bo'lsa, oddiy matn sifatida yuborish
            await message.answer(chunk)


def _split_text(text: str, max_len: int = 4096) -> list[str]:
    """
    Matnni max_len belgidan oshmaydigan bo'laklarga bo'ladi.
    Satr oxiridan yoki paragraf oxiridan bo'lishga harakat qiladi.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        # Bo'lish joyini topish (oxirgi \n\n yoki \n)
        split_at = max_len
        for sep in ("\n\n", "\n", ". ", " "):
            pos = remaining.rfind(sep, 0, max_len)
            if pos > max_len // 2:  # Juda qisqa bo'laklar bo'lmasin
                split_at = pos + len(sep)
                break

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]

    return chunks


# ══════════════════════════════════════════════════════════
#  BOT FACTORY
# ══════════════════════════════════════════════════════════


def create_bot() -> Bot:
    """Bot instance yaratadi."""
    return Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher() -> Dispatcher:
    """Dispatcher yaratadi va router'ni ulaydi."""
    dp = Dispatcher()
    dp.include_router(router)

    # Shutdown hook — aiohttp sessionni yopish
    dp.shutdown.register(lambda: close_session())

    return dp
