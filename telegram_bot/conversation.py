"""
Suhbat xotirasi — har bir foydalanuvchi uchun alohida.
Xotirada saqlanadi (in-memory), bot qayta ishga tushganda tozalanadi.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import TypedDict

from telegram_bot.config import MAX_HISTORY, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class Message(TypedDict):
    role: str       # "system" | "user" | "assistant"
    content: str


class ConversationManager:
    """Har bir user_id uchun xabarlar tarixini boshqaradi."""

    def __init__(self) -> None:
        # {user_id: [Message, ...]}
        self._history: dict[int, list[Message]] = defaultdict(list)
        # {user_id: model_name}
        self._models: dict[int, str] = {}

    # ── Public API ────────────────────────────────────────

    def get_messages(self, user_id: int) -> list[Message]:
        """System prompt + suhbat tarixini qaytaradi."""
        system: Message = {"role": "system", "content": SYSTEM_PROMPT}
        return [system] + self._history[user_id]

    def add_user_message(self, user_id: int, text: str) -> None:
        """Foydalanuvchi xabarini qo'shadi."""
        self._history[user_id].append({"role": "user", "content": text})
        self._trim(user_id)

    def add_assistant_message(self, user_id: int, text: str) -> None:
        """AI javobini qo'shadi."""
        self._history[user_id].append({"role": "assistant", "content": text})
        self._trim(user_id)

    def clear(self, user_id: int) -> None:
        """Suhbat tarixini tozalaydi."""
        self._history.pop(user_id, None)
        logger.info("Suhbat tozalandi: user_id=%s", user_id)

    def set_model(self, user_id: int, model: str) -> None:
        """Foydalanuvchi uchun modelni o'zgartiradi."""
        self._models[user_id] = model

    def get_model(self, user_id: int) -> str | None:
        """Foydalanuvchi tanlagan modelni qaytaradi (None = default)."""
        return self._models.get(user_id)

    # ── Internal ──────────────────────────────────────────

    def _trim(self, user_id: int) -> None:
        """Tarixni MAX_HISTORY ga qisqartiradi (eng eski xabarlar o'chiriladi)."""
        history = self._history[user_id]
        if len(history) > MAX_HISTORY:
            # Eng eski xabarlarni o'chirish (juftlab — user+assistant)
            excess = len(history) - MAX_HISTORY
            self._history[user_id] = history[excess:]
            logger.debug(
                "Tarix qisqartirildi: user_id=%s, o'chirildi=%d",
                user_id, excess,
            )


# Global instance — bot davomida bitta
conversation_manager = ConversationManager()
