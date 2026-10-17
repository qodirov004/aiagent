"""
userbot.py — Telegram UserBot (Pyrogram) skripti.

O'quv markazi boshqaruv tizimi uchun to'liq asinxron Telegram UserBot.

Vazifalar:
  1. Morning Scheduler (08:30) — Bugungi darslarni o'qituvchilar guruhiga xabar qilish
  2. Docx Event Handler — Guruhga yuborilgan .docx fayllarni ushlab, Django API ga jo'natish
  3. Evening Summary (22:00) — Direktor xulosasini olish va shaxsiy chatga yuborish

Kutubxonalar: Pyrogram, aiohttp, APScheduler, python-dotenv
"""

import asyncio
import logging
import os
import sys
import tempfile
from datetime import datetime

# Python 3.12+ / 3.14 event loop compatibility before importing Pyrogram
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from pyrogram.types import Message

# ============================================================
# Logging konfiguratsiyasi
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("userbot")

# ============================================================
# .env dan sozlamalarni yuklash
# ============================================================

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING", "")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "edu_center_bot")

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://127.0.0.1:8000")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

TEACHER_GROUP_ID = int(os.getenv("TEACHER_GROUP_ID", "0"))
MARKETING_GROUP_ID = int(os.getenv("MARKETING_GROUP_ID", "0") or os.getenv("TEACHER_GROUP_ID", "0"))
DIRECTOR_CHAT_ID = int(os.getenv("DIRECTOR_CHAT_ID", "0"))


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def _validate_env():
    """Muhit o'zgaruvchilarini tekshiradi. Majburiy qiymatlar bo'lmasa, xatolik beradi."""
    missing = []
    if not API_ID:
        missing.append("TELEGRAM_API_ID")
    if not API_HASH:
        missing.append("TELEGRAM_API_HASH")
    if not INTERNAL_API_KEY:
        missing.append("INTERNAL_API_KEY")
    if not TEACHER_GROUP_ID:
        missing.append("TEACHER_GROUP_ID")
    if not DIRECTOR_CHAT_ID:
        missing.append("DIRECTOR_CHAT_ID")

    if missing:
        logger.critical(
            "Quyidagi muhit o'zgaruvchilari topilmadi: %s", ", ".join(missing)
        )
        sys.exit(1)


_validate_env()


# ============================================================
# Pyrogram Client yaratish
# ============================================================

def _create_client() -> Client:
    """
    Pyrogram klientini yaratadi:
      - Agar TELEGRAM_BOT_TOKEN bo'lsa -> Bot sifatida ulanadi (kod so'ramaydi)
      - Agar TELEGRAM_SESSION_STRING bo'lsa -> String sessiya orqali
      - Aks holda -> Shaxsiy profil (Userbot) sessiyasi orqali
    """
    # Telegram rasmiy Desktop ilovasi parametrlari (Telegram login kodini bloklamasligi uchun)
    client_params = {
        "name": SESSION_NAME,
        "api_id": API_ID,
        "api_hash": API_HASH,
        "device_model": "Desktop",
        "app_version": "5.4.1 x64",
        "system_version": "Windows 11",
    }

    if BOT_TOKEN:
        logger.info("🤖 Bot Token orqali ulanish...")
        client_params["bot_token"] = BOT_TOKEN
    elif SESSION_STRING:
        logger.info("🔑 StringSession orqali ulanish...")
        client_params["session_string"] = SESSION_STRING
    else:
        logger.info("📁 Fayl sessiyasi orqali ulanish: %s", SESSION_NAME)

    return Client(**client_params)


client = _create_client()


# ============================================================
# API yordamchi funksiyalar (aiohttp orqali)
# ============================================================

def _api_headers() -> dict:
    """Django ichki API uchun autentifikatsiya header'lari."""
    return {
        "X-Internal-Api-Key": INTERNAL_API_KEY,
    }


async def api_get(endpoint: str, params: dict | None = None) -> dict:
    """
    Django API ga GET so'rov yuboradi.

    Args:
        endpoint: URL yo'li (masalan: /api/internal/today-schedules/)
        params: Query parametrlari (ixtiyoriy)

    Returns:
        dict — API javobi (JSON)
    """
    url = f"{DJANGO_API_URL.rstrip('/')}{endpoint}"
    logger.debug("API GET: %s", url)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=_api_headers(), params=params, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                body = await response.text()
                logger.error("API GET xatosi [%d]: %s — %s", response.status, url, body)
                raise Exception(
                    f"API GET xatosi [{response.status}]: {body[:300]}"
                )

            data = await response.json()
            logger.debug("API GET muvaffaqiyatli: %s", url)
            return data


async def api_post_json(endpoint: str, payload: dict) -> dict:
    """
    Django API ga JSON POST so'rov yuboradi.

    Args:
        endpoint: URL yo'li
        payload: JSON body

    Returns:
        dict — API javobi
    """
    url = f"{DJANGO_API_URL.rstrip('/')}{endpoint}"
    logger.debug("API POST JSON: %s", url)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers={**_api_headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status not in (200, 201):
                body = await response.text()
                logger.error("API POST xatosi [%d]: %s — %s", response.status, url, body)
                raise Exception(
                    f"API POST xatosi [{response.status}]: {body[:300]}"
                )

            data = await response.json()
            logger.debug("API POST muvaffaqiyatli: %s", url)
            return data


async def api_post_file(
    endpoint: str,
    file_path: str,
    file_name: str,
    extra_fields: dict | None = None,
) -> dict:
    """
    Django API ga fayl (multipart/form-data) yuboradi.

    Args:
        endpoint: URL yo'li
        file_path: Mahalliy fayl yo'li
        file_name: Fayl nomi
        extra_fields: Qo'shimcha form field'lari (masalan: telegram_username)

    Returns:
        dict — API javobi
    """
    url = f"{DJANGO_API_URL.rstrip('/')}{endpoint}"
    logger.debug("API POST FILE: %s — fayl: %s", url, file_name)

    data = aiohttp.FormData()
    data.add_field(
        "file",
        open(file_path, "rb"),
        filename=file_name,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    if extra_fields:
        for key, value in extra_fields.items():
            data.add_field(key, str(value))

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=_api_headers(), data=data,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as response:
            if response.status not in (200, 201):
                body = await response.text()
                logger.error(
                    "API POST FILE xatosi [%d]: %s — %s", response.status, url, body
                )
                raise Exception(
                    f"API POST FILE xatosi [{response.status}]: {body[:300]}"
                )

            result = await response.json()
            logger.debug("API POST FILE muvaffaqiyatli: %s", url)
            return result


# ============================================================
# 1. ERTALABKI VAZIFA — Morning Scheduler (08:30)
# ============================================================

async def morning_schedule_task():
    """
    Har kuni soat 08:30 da:
      1. Django API dan bugungi darslarni oladi (is_notified=False)
      2. TEACHER_GROUP_ID guruhiga chiroyli formatda xabar yozadi
      3. API ga mark-notified so'rovini beradi
    """
    logger.info("🌅 Ertalabki dars jadvali vazifasi boshlandi...")

    try:
        # 1. Bugungi darslarni olish
        data = await api_get("/api/internal/today-schedules/")
        schedules = data.get("schedules", [])

        if not schedules:
            logger.info("Bugun uchun xabardor qilinmagan darslar yo'q.")
            return

        # 2. Chiroyli xabar tayyorlash
        today_str = datetime.now().strftime("%d.%m.%Y (%A)")
        lines = [
            "📚 **Assalomu alaykum, hurmatli ustozlar!**",
            "",
            f"🗓 **Bugungi dars jadvali — {today_str}**",
            "",
        ]

        schedule_ids = []
        for i, schedule in enumerate(schedules, start=1):
            username = schedule.get("teacher_telegram_username", "—")
            group_name = schedule.get("group_name", "—")
            start_time = schedule.get("start_time", "—")
            room = schedule.get("room_number", "")

            room_text = f" | 🏫 {room}-xona" if room else ""
            lines.append(
                f"  {i}. @{username} | **{group_name}** | ⏰ {start_time}{room_text}"
            )
            schedule_ids.append(schedule["id"])

        lines.extend([
            "",
            "✨ **Barchalaringizga samarali dars tilaymiz!**",
            "🤖 _Edu Center Bot_",
        ])

        message_text = "\n".join(lines)

        # 3. Telegram guruhga xabar yuborish
        await client.send_message(
            chat_id=TEACHER_GROUP_ID,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info(
            "✅ Ertalabki xabar yuborildi: %d ta dars haqida.", len(schedules)
        )

        # 4. Mark-notified — API ga xabar berish
        await api_post_json(
            "/api/internal/mark-notified/",
            {"schedule_ids": schedule_ids},
        )
        logger.info(
            "✅ %d ta dars jadval 'notified' deb belgilandi.", len(schedule_ids)
        )

    except Exception as e:
        logger.error(
            "❌ Ertalabki vazifa xatosi: %s", str(e), exc_info=True
        )
        try:
            await client.send_message(
                chat_id=TEACHER_GROUP_ID,
                text=f"⚠️ Dars jadvali xabari yuborishda xatolik yuz berdi.\n`{str(e)[:200]}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


# ============================================================
# 2. DOCX FAYL USHLAGICH — Pyrogram on_message Handler
# ============================================================

async def handle_docx_upload(app: Client, message: Message):
    """
    Guruhga yuborilgan .docx fayllarni ushlaydi:
      1. Yuboruvchining telegram username'ini aniqlaydi
      2. Faylni yuklab oladi (temp papkaga)
      3. Django API upload-report endpointiga multipart/form-data orqali yuboradi
      4. Natija bo'yicha guruhga javob qaytaradi
    """
    doc = message.document
    file_name = doc.file_name or ""

    if not file_name.lower().endswith(".docx"):
        return  # .docx emas — o'tkazib yuboramiz

    logger.info("📄 DOCX fayl aniqlandi: %s", file_name)

    sender = message.from_user
    if not sender or not sender.username:
        logger.warning(
            "Yuboruvchida username yo'q (ID: %s), o'tkazib yuborilmoqda.",
            sender.id if sender else "Noma'lum",
        )
        await message.reply_text(
            "⚠️ Sizning Telegram profilingizda username o'rnatilmagan. "
            "Iltimos, username o'rnating va qayta yuboring."
        )
        return

    username = sender.username

    # Faylni yuklab olish (temp papkaga)
    tmp_dir = tempfile.mkdtemp(prefix="edu_docx_")
    local_file_path = os.path.join(tmp_dir, file_name)

    try:
        logger.info("Fayl yuklab olinmoqda: %s -> %s", file_name, local_file_path)
        downloaded_path = await message.download(file_name=local_file_path)

        # Django API ga yuborish
        result = await api_post_file(
            "/api/internal/upload-report/",
            file_path=downloaded_path,
            file_name=file_name,
            extra_fields={"telegram_username": username},
        )

        report_id = result.get("report_id", "—")
        await message.reply_text(
            f"✅ @{username}, hisobotingiz qabul qilindi va AI tomonidan tahlilga topshirildi.\n"
            f"📋 Hisobot ID: `{report_id}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info(
            "✅ DOCX hisobot muvaffaqiyatli yuborildi: %s (report_id=%s)",
            username,
            report_id,
        )

    except Exception as e:
        logger.error(
            "❌ DOCX yuklash xatosi (%s): %s", username, str(e), exc_info=True
        )
        await message.reply_text(
            f"❌ @{username}, hisobotni qayta ishlashda xatolik yuz berdi.\n"
            f"Iltimos, qayta urinib ko'ring yoki admin bilan bog'laning.\n"
            f"Xatolik: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
        )

    finally:
        # Temp faylni tozalash
        try:
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            os.rmdir(tmp_dir)
        except OSError:
            pass


# ============================================================
# 3. KECHKI VAZIFA — Evening Summary to Director (22:00)
# ============================================================

async def evening_summary_task():
    """
    Har kuni soat 22:00 da:
      1. Django API ga so'rov yuborib, Gemini tuzgan DirectorDailySummary ni oladi
      2. DIRECTOR_CHAT_ID ga Telegram xabari sifatida yuboradi
    """
    logger.info("🌙 Kechki direktor xulosasi vazifasi boshlandi...")

    try:
        # 1. API dan xulosani olish
        data = await api_get(
            "/api/internal/daily-summary-for-director/",
            params={"mark_sent": "true"},
        )

        summary_data = data.get("summary", {})
        summary_text = summary_data.get("summary_markdown", "")

        if not summary_text:
            logger.warning("Direktor uchun xulosa matni bo'sh.")
            return

        # 2. Xulosa hajmini tekshirish (Telegram xabar limiti: 4096 belgi)
        MAX_TG_LENGTH = 4000
        if len(summary_text) > MAX_TG_LENGTH:
            # Uzun xabarni bo'lib yuborish
            parts = _split_long_message(summary_text, MAX_TG_LENGTH)
            for i, part in enumerate(parts, start=1):
                header = f"📊 **Kunlik Xulosa ({i}/{len(parts)})**\n\n" if len(parts) > 1 else ""
                await client.send_message(
                    chat_id=DIRECTOR_CHAT_ID,
                    text=f"{header}{part}",
                    parse_mode=ParseMode.MARKDOWN,
                )
                await asyncio.sleep(1)
        else:
            await client.send_message(
                chat_id=DIRECTOR_CHAT_ID,
                text=summary_text,
                parse_mode=ParseMode.MARKDOWN,
            )

        logger.info("✅ Direktor xulosasi muvaffaqiyatli yuborildi.")

    except Exception as e:
        logger.error(
            "❌ Kechki xulosa xatosi: %s", str(e), exc_info=True
        )
        try:
            await client.send_message(
                chat_id=DIRECTOR_CHAT_ID,
                text=f"⚠️ Bugungi kunlik xulosani tayyorlashda xatolik yuz berdi.\n"
                f"Texnik jamoa xabardor qilindi.\n`{str(e)[:200]}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


def _split_long_message(text: str, max_length: int) -> list[str]:
    """
    Uzun matnni Telegram limiti bo'yicha bo'laklarga bo'ladi.
    Paragraf chegaralariga qarab bo'lishga harakat qiladi.
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break

        split_pos = text.rfind("\n\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        parts.append(text[:split_pos].rstrip())
        text = text[split_pos:].lstrip()

    return parts


async def send_message_safe(chat_id: int | str, text: str, header_prefix: str = "") -> bool:
    """
    Xabarni guruhga yoki shaxsiy chatga xavfsiz yuboradi:
      - Agar xabar 4000 belgidan uzun bo'lsa, avtomatik bo'lib yuboradi
      - Agar PeerIdInvalid bo'lsa, supergroup formatidagi (-100...) variantini sinaydi
      - Xatolik yuz bersa, tushunarli log yozadi
    """
    MAX_TG_LENGTH = 4000
    parts = _split_long_message(text, MAX_TG_LENGTH)
    
    try:
        chat_id_int = int(chat_id)
    except (ValueError, TypeError):
        logger.error("Noto'g'ri chat_id: %s", chat_id)
        return False

    targets = [chat_id_int]
    if chat_id_int < 0 and not str(chat_id).startswith("-100"):
        targets.append(int(f"-100{abs(chat_id_int)}"))

    last_err = None
    for target in targets:
        try:
            for i, part in enumerate(parts, start=1):
                header = f"{header_prefix} ({i}/{len(parts)})\n\n" if (len(parts) > 1 and header_prefix) else ""
                await client.send_message(
                    chat_id=target,
                    text=f"{header}{part}",
                    parse_mode=ParseMode.MARKDOWN,
                )
                if len(parts) > 1:
                    await asyncio.sleep(1)
            logger.info("✅ Xabar Telegramga muvaffaqiyatli yuborildi: chat_id=%s", target)
            return True
        except Exception as e:
            last_err = e
            if "peer id invalid" in str(e).lower() or "channel invalid" in str(e).lower():
                continue
            else:
                break

    logger.warning(
        "⚠️ Telegram xabar yuborishda peer topilmadi (chat_id=%s): %s.\n"
        "ℹ️ Userbot (@%s, ID: %s) guruhga a'zo qilinganmi? Guruhga qo'shing yoki link orqali a'zo qiling.",
        chat_id,
        str(last_err),
        getattr(client.me, "username", "—") if hasattr(client, "me") and client.me else "—",
        getattr(client.me, "id", "—") if hasattr(client, "me") and client.me else "—",
    )
    return False


# ============================================================
# 4. MARKETING GURUHI VAZIFASI — Evening Marketing Report (21:30)
# ============================================================

async def evening_marketing_task():
    """
    Har kuni soat 21:30 da:
      1. Django API dan bugungi marketing + Instagram + AI tahlil hisobotini oladi
      2. MARKETING_GROUP_ID guruhiga chiroyli formatda xabar yuboradi
    """
    logger.info("🚀 Marketing guruhi uchun kechki hisobot vazifasi boshlandi...")
    try:
        data = await api_get("/api/internal/marketing-telegram-report/")
        report_text = data.get("report_markdown", "")
        chat_id = int(data.get("marketing_group_id") or MARKETING_GROUP_ID)

        if not report_text:
            logger.warning("Marketing hisobot matni bo'sh.")
            return

        await send_message_safe(chat_id, report_text, "🚀 **Marketing Hisoboti**")
    except Exception as e:
        logger.error("❌ Marketing hisobotini yuborishda xatolik: %s", str(e), exc_info=True)


# ============================================================
# 5. DASHBOARDDAN ZUDLIK BILAN YUBORISH — Real-time Queue Polling
# ============================================================

async def check_pending_dispatches_loop():
    """
    Har 5 soniyada navbatdagi marketing jo'natmalarini tekshiradi
    (Dashboard tugmasi bosilganda darhol guruhga jo'natish).
    """
    logger.info("📡 Marketing Telegram navbat tekshiruvchisi ishga tushdi...")
    while True:
        try:
            data = await api_get("/api/internal/pending-marketing-dispatches/")
            dispatches = data.get("dispatches", [])
            for item in dispatches:
                dispatch_id = item["id"]
                chat_id = int(item.get("chat_id") or MARKETING_GROUP_ID)
                message_text = item["message_text"]
                logger.info("📤 Navbatdagi marketing xabar yuborilmoqda: dispatch_id=%s, chat_id=%s", dispatch_id, chat_id)

                success = await send_message_safe(chat_id, message_text, "🚀 **Marketing Hisoboti**")
                if success:
                    await api_post_json("/api/internal/pending-marketing-dispatches/", {"dispatch_id": dispatch_id})
                    logger.info("✅ Dispatch %s muvaffaqiyatli yuborildi va belgilandi.", dispatch_id)
                else:
                    await api_post_json(
                        "/api/internal/pending-marketing-dispatches/",
                        {
                            "dispatch_id": dispatch_id,
                            "error_message": f"Peer ID {chat_id} topilmadi. Userbot guruhga qo'shilmagan bo'lishi mumkin."
                        },
                    )
        except Exception:
            pass
        await asyncio.sleep(5)


# ============================================================
# 5.1. DIAGNOSTIKA VA GURUH ID SINI BILISH — /id yoki /ping
# ============================================================

async def handle_id_command(app: Client, message: Message):
    """
    Guruh yoki shaxsiy chatda botning tirikligini tekshirish
    va guruh chat_id sini darhol aniqlab olish buyrug'i.
    """
    user_info = f"@{message.from_user.username}" if message.from_user and message.from_user.username else str(message.from_user.id if message.from_user else "Noma'lum")
    await message.reply_text(
        f"🤖 **Edu Center UserBot faol!**\n\n"
        f"📍 **Ushbu guruh/chat ID:** `{message.chat.id}`\n"
        f"👤 **Sizning profilingiz:** {user_info}\n\n"
        f"💡 _Agar yangi guruh ochgan bo'lsangiz, ushbu ID ni `.env` dagi `TEACHER_GROUP_ID` yoki `MARKETING_GROUP_ID` ga qo'ying._",
        parse_mode=ParseMode.MARKDOWN,
    )


# ============================================================
# 6. GURUHDA STRATEGIK BUYRUQ — /marketing yoki #marketing
# ============================================================

async def handle_marketing_command(app: Client, message: Message):
    """
    /marketing buyrug'i:
    Chuqur marketing tahlili, raqobatchilar yangiliklari va
    Google Gemini AI ning strategik tavsiyalarini jo'natadi.
    """
    logger.info("📊 Marketing buyrug'i qabul qilindi: chat_id=%s", message.chat.id)
    wait_msg = await message.reply_text("⏳ _Marketing tahlili va Gemini AI strategiyasi tayyorlanmoqda..._", parse_mode=ParseMode.MARKDOWN)
    try:
        data = await api_get("/api/internal/marketing-telegram-report/")
        report_text = data.get("report_markdown", "")
        if not report_text:
            await wait_msg.edit_text("⚠️ Marketing hisoboti ma'lumotlari topilmadi.")
            return

        await wait_msg.delete()
        MAX_TG_LENGTH = 4000
        if len(report_text) > MAX_TG_LENGTH:
            parts = _split_long_message(report_text, MAX_TG_LENGTH)
            for part in parts:
                await message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(1)
        else:
            await message.reply_text(report_text, parse_mode=ParseMode.MARKDOWN)
        logger.info("✅ Marketing hisoboti buyruq bo'yicha yuborildi.")
    except Exception as e:
        logger.error("Marketing buyrug'ida xatolik: %s", str(e), exc_info=True)
        await wait_msg.edit_text(f"❌ Hisobot olishda xatolik: `{str(e)[:200]}`", parse_mode=ParseMode.MARKDOWN)


# ============================================================
# 7. TEZKOR RAQAMLAR VA METRIKALAR — /stats yoki /stat
# ============================================================

async def handle_stats_command(app: Client, message: Message):
    """
    /stats yoki /stat buyrug'i:
    O'quv markazi holati (o'quvchilar, guruhlar, darslar) +
    Instagram metrikalari + Marketing xarajat va leadlar raqamlari dashboardi.
    (Uzoq AI matnisiz, tezkor raqamlar ko'rinishida)
    """
    logger.info("📈 Tezkor statistika (/stats) buyrug'i qabul qilindi: chat_id=%s", message.chat.id)
    wait_msg = await message.reply_text("📊 _Tezkor ko'rsatkichlar va statistika yuklanmoqda..._", parse_mode=ParseMode.MARKDOWN)
    try:
        data = await api_get("/api/internal/quick-stats/")
        report_text = data.get("stats_markdown", "")
        if not report_text:
            await wait_msg.edit_text("⚠️ Statistika ma'lumotlari topilmadi.")
            return

        await wait_msg.delete()
        await message.reply_text(report_text, parse_mode=ParseMode.MARKDOWN)
        logger.info("✅ Tezkor statistika (/stats) muvaffaqiyatli yuborildi.")
    except Exception as e:
        logger.error("Stats buyrug'ida xatolik: %s", str(e), exc_info=True)
        await wait_msg.edit_text(f"❌ Statistika olishda xatolik: `{str(e)[:200]}`", parse_mode=ParseMode.MARKDOWN)


# ============================================================
# ASOSIY ISHGA TUSHIRISH
# ============================================================

async def main():
    """
    UserBot ni ishga tushiradi:
      1. Telegram'ga ulanadi
      2. APScheduler orqali kundalik vazifalarni rejalashtiradi
      3. Real-time marketing dispatch navbatini ishga tushiradi
      4. Hodisalarni kutib turadi (idle)
    """
    logger.info("=" * 60)
    logger.info("🤖 Edu Center UserBot (Pyrogram) ishga tushmoqda...")
    logger.info("=" * 60)

    # Telegram'ga ulanish
    await client.start()
    me = await client.get_me()
    logger.info(
        "✅ Telegram'ga ulandi: @%s (ID: %d)",
        me.username or "—",
        me.id,
    )

    # Hodisalarni ro'yxatdan o'tkazish (Dispatcher handlers)
    client.add_handler(MessageHandler(handle_id_command, filters.command(["id", "ping", "test"]) | filters.regex(r"^(/id|/ping|/test)")))
    client.add_handler(MessageHandler(handle_marketing_command, filters.command(["marketing"]) | filters.regex(r"^(/marketing|#marketing)")))
    client.add_handler(MessageHandler(handle_stats_command, filters.command(["stats", "stat", "kpi", "instagram"]) | filters.regex(r"^(/stats|/stat|/kpi|#stats|#stat)")))
    client.add_handler(MessageHandler(handle_docx_upload, filters.document))
    await asyncio.sleep(0.05)
    logger.info("⚡ Hodisa ushlagichlari muvaffaqiyatli ulandi (Faol handlerlar: %d ta).", len(client.dispatcher.groups.get(0, [])))

    # APScheduler — kundalik vazifalar
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # 08:30 — Ertalabki dars jadvali
    scheduler.add_job(
        morning_schedule_task,
        CronTrigger(hour=8, minute=30, timezone="Asia/Tashkent"),
        id="morning_schedule",
        name="Ertalabki dars jadvali",
        replace_existing=True,
        misfire_grace_time=600,
    )
    logger.info("⏰ Ertalabki vazifa rejalashtirildi: 08:30 (Asia/Tashkent)")

    # 21:30 — Marketing guruhi uchun kechki hisobot
    scheduler.add_job(
        evening_marketing_task,
        CronTrigger(hour=21, minute=30, timezone="Asia/Tashkent"),
        id="evening_marketing",
        name="Marketing guruhi kechki hisoboti",
        replace_existing=True,
        misfire_grace_time=600,
    )
    logger.info("⏰ Marketing kechki hisoboti rejalashtirildi: 21:30 (Asia/Tashkent)")

    # 22:00 — Kechki direktor xulosasi
    scheduler.add_job(
        evening_summary_task,
        CronTrigger(hour=22, minute=0, timezone="Asia/Tashkent"),
        id="evening_summary",
        name="Kechki direktor xulosasi",
        replace_existing=True,
        misfire_grace_time=600,
    )
    logger.info("⏰ Kechki direktor xulosasi rejalashtirildi: 22:00 (Asia/Tashkent)")

    scheduler.start()
    logger.info("📅 APScheduler muvaffaqiyatli ishga tushdi.")

    # Real-time marketing dispatch background task
    asyncio.create_task(check_pending_dispatches_loop())

    logger.info("=" * 60)
    logger.info("🟢 Pyrogram UserBot tayyor! Hodisalar kutilmoqda...")
    logger.info("   O'qituvchilar Guruhi ID: %d", TEACHER_GROUP_ID)
    logger.info("   Marketing Guruhi ID: %d", MARKETING_GROUP_ID)
    logger.info("   Direktor ID: %d", DIRECTOR_CHAT_ID)
    logger.info("   Django API: %s", DJANGO_API_URL)
    logger.info("=" * 60)

    # Cheksiz kutish — hodisalar qayta ishlanadi
    await idle()
    await client.stop()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 UserBot to'xtatildi (Ctrl+C).")
    except Exception as e:
        logger.critical("💥 UserBot falokatli xatosi: %s", str(e), exc_info=True)
        sys.exit(1)
