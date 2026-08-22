"""
OmniRoute API client — OpenAI-compatible /v1/chat/completions endpoint bilan ishlaydi.
Streaming va oddiy rejimlarni qo'llab-quvvatlaydi.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import aiohttp

from telegram_bot.config import (
    DEFAULT_MODEL,
    MAX_RESPONSE_TOKENS,
    OMNIROUTE_API_KEY,
    OMNIROUTE_BASE_URL,
)
from telegram_bot.conversation import Message

logger = logging.getLogger(__name__)

# OmniRoute bilan ulanish uchun umumiy session
_session: aiohttp.ClientSession | None = None


async def get_session() -> aiohttp.ClientSession:
    """aiohttp session — lazy initialization."""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=120, connect=10)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def close_session() -> None:
    """Bot to'xtaganda sessionni yopish."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


def _build_headers() -> dict[str, str]:
    """API so'rov uchun headerlar."""
    headers = {
        "Content-Type": "application/json",
    }
    if OMNIROUTE_API_KEY:
        headers["Authorization"] = f"Bearer {OMNIROUTE_API_KEY}"
    return headers


async def chat_completion(
    messages: list[Message],
    model: str | None = None,
) -> str:
    """
    OmniRoute ga so'rov yuborib, to'liq javobni qaytaradi (non-streaming).

    Args:
        messages: Suhbat xabarlari (system + user + assistant).
        model: Model nomi (None bo'lsa DEFAULT_MODEL ishlatiladi).

    Returns:
        AI javob matni.

    Raises:
        OmniRouteError: API xatoligi yuzaga kelganda.
    """
    model = model or DEFAULT_MODEL
    session = await get_session()

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_RESPONSE_TOKENS,
        "stream": False,
    }

    url = f"{OMNIROUTE_BASE_URL}/chat/completions"
    logger.info("OmniRoute so'rov: model=%s, xabarlar=%d", model, len(messages))

    try:
        async with session.post(url, json=payload, headers=_build_headers()) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logger.error(
                    "OmniRoute xatolik: status=%d, body=%s",
                    resp.status, error_text[:500],
                )
                raise OmniRouteError(
                    f"API xatoligi (status {resp.status})",
                    status=resp.status,
                    detail=error_text[:300],
                )

            data = await resp.json()
            content = data["choices"][0]["message"]["content"]

            # Model va usage ma'lumotlarini log qilish
            used_model = data.get("model", model)
            usage = data.get("usage", {})
            logger.info(
                "OmniRoute javob: model=%s, tokens=%s",
                used_model,
                usage.get("total_tokens", "?"),
            )

            return content

    except aiohttp.ClientError as exc:
        logger.error("OmniRoute ulanish xatoligi: %s", exc)
        raise OmniRouteError(
            "OmniRoute serveriga ulanib bo'lmadi. "
            "Server ishlayotganini tekshiring: http://localhost:20128",
            detail=str(exc),
        ) from exc


async def chat_completion_stream(
    messages: list[Message],
    model: str | None = None,
) -> AsyncIterator[str]:
    """
    OmniRoute ga streaming so'rov — javobni qism-qism qaytaradi.

    Args:
        messages: Suhbat xabarlari.
        model: Model nomi.

    Yields:
        Har bir chunk (matn bo'lagi).
    """
    model = model or DEFAULT_MODEL
    session = await get_session()

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_RESPONSE_TOKENS,
        "stream": True,
    }

    url = f"{OMNIROUTE_BASE_URL}/chat/completions"
    logger.info("OmniRoute streaming: model=%s, xabarlar=%d", model, len(messages))

    try:
        async with session.post(url, json=payload, headers=_build_headers()) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise OmniRouteError(
                    f"API xatoligi (status {resp.status})",
                    status=resp.status,
                    detail=error_text[:300],
                )

            # SSE stream o'qish
            async for line in resp.content:
                decoded = line.decode("utf-8", errors="replace").strip()

                if not decoded or not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]  # "data: " ni olib tashlash

                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    except aiohttp.ClientError as exc:
        logger.error("OmniRoute streaming xatoligi: %s", exc)
        raise OmniRouteError(
            "Streaming jarayonida xatolik yuzaga keldi.",
            detail=str(exc),
        ) from exc


class OmniRouteError(Exception):
    """OmniRoute API bilan bog'liq xatolik."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        detail: str = "",
    ) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail

    def user_message(self) -> str:
        """Foydalanuvchiga ko'rsatiladigan xabar."""
        if self.status == 429:
            return "⏳ Hozir juda ko'p so'rov bor. Bir ozdan keyin qayta urinib ko'ring."
        if self.status and self.status >= 500:
            return "🔧 AI server hozir ishlamayapti. Keyinroq urinib ko'ring."
        if self.status is None:
            return (
                "🔌 OmniRoute serveriga ulanib bo'lmadi.\n"
                "Server ishlayotganini tekshiring."
            )
        return f"❌ Xatolik yuz berdi: {self}"
