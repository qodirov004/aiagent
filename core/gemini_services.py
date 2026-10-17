"""
core/gemini_services.py — Google Gemini AI integratsiyasi.

Ikki asosiy funksiya:
  1. parse_docx_report() — DOCX faylni o'qib, Gemini orqali structured JSON olish.
  2. generate_supervisor_daily_summary() — Kunlik direktor xulosasini yaratish.

Kutubxonalar:
  - google-genai (rasmiy Google Gen AI SDK)
  - python-docx (DOCX faylni o'qish)
  - pydantic (Structured Output sxemasi)
"""

import logging
from datetime import date as date_type, timedelta
from typing import Optional

from docx import Document as DocxDocument
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)


# ===========================================================================
# Pydantic sxemalari — Gemini Structured Output uchun
# ===========================================================================

class ParsedReportSchema(BaseModel):
    """DOCX hisobotdan Gemini orqali ajratib olinadigan ma'lumotlar sxemasi."""

    teacher_name: str = Field(
        description="Hisobotdagi o'qituvchining ismi (agar mavjud bo'lsa)"
    )
    group_name: str = Field(
        description="Guruh nomi (masalan: Python-10, Frontend-02)"
    )
    attendance_rate: float = Field(
        default=0.0,
        description="Qatnashish foizi 0 dan 100 gacha (masalan: 85.5)",
    )
    topic: str = Field(
        default="",
        description="Darsda o'tilgan mavzu",
    )
    homework_rate: float = Field(
        default=0.0,
        description="Uyga vazifa topshirganlar foizi 0 dan 100 gacha",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Darsda yuzaga kelgan muammolar ro'yxati",
    )
    ai_summary: str = Field(
        default="",
        description=(
            "Hisobotning qisqacha AI xulosasi: umumiy holat, "
            "yaxshi tomonlar va yaxshilanishi kerak bo'lgan joylar"
        ),
    )


class MarketingAnalysisResultSchema(BaseModel):
    """Gemini marketing tahlili va tavsiyalari sxemasi."""

    ai_analysis: str = Field(
        description="Marketing ko'rsatkichlari, lead narxi, reklama samarasi va raqobatchilar bo'yicha tahliliy xulosa (Telegram Markdown formatda)"
    )
    ai_recommendations: str = Field(
        description="Direktor va marketolog uchun aniq 3-5 ta amaliy maslahat va harakat rejasi (Action Points, Telegram Markdown formatda)"
    )



# ===========================================================================
# Gemini klient — singleton pattern
# ===========================================================================

_gemini_client: Optional[genai.Client] = None


def _get_gemini_client() -> genai.Client:
    """Gemini klientni yaratadi yoki mavjudini qaytaradi (lazy singleton)."""
    global _gemini_client
    if _gemini_client is None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY sozlamasi bo'sh. "
                ".env faylda GEMINI_API_KEY ni to'ldiring."
            )
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Gemini AI klient muvaffaqiyatli yaratildi.")
    return _gemini_client


def _get_model_name() -> str:
    """Sozlamalardan Gemini model nomini oladi."""
    return getattr(settings, "GEMINI_MODEL", "gemini-3-flash-preview")


# ===========================================================================
# Yordamchi: DOCX fayldan matn ajratish
# ===========================================================================

def extract_text_from_docx(file_path: str) -> str:
    """
    DOCX fayldan barcha paragraflar matnini ajratib oladi.
    Jadvallar ham qo'shiladi.

    Args:
        file_path: DOCX faylning to'liq yo'li.

    Returns:
        Sof matn (paragraflar va jadvallar birlashtirilgan).
    """
    doc = DocxDocument(file_path)
    text_parts: list[str] = []

    # Paragraflar
    for paragraph in doc.paragraphs:
        stripped = paragraph.text.strip()
        if stripped:
            text_parts.append(stripped)

    # Jadvallar
    for table in doc.tables:
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_data:
                text_parts.append(" | ".join(row_data))

    full_text = "\n".join(text_parts)
    logger.debug("DOCX dan %d ta belgi ajratib olindi: %s", len(full_text), file_path)
    return full_text


# ===========================================================================
# Funksiya 1: DOCX hisobotni Gemini orqali parse qilish
# ===========================================================================

def parse_docx_report(file_path: str) -> dict:
    """
    DOCX faylni o'qiydi va Gemini AI orqali structured JSON ga aylantiradi.

    Qadam 1: python-docx orqali matnni ajratish.
    Qadam 2: Gemini API ga yuborib, ParsedReportSchema ga mos JSON olish.

    Args:
        file_path: DOCX faylning to'liq yo'li.

    Returns:
        dict — ParsedReportSchema ga mos kalit-qiymat juftliklari.

    Raises:
        ValueError: Agar Gemini javob bermasa yoki matn bo'sh bo'lsa.
        Exception: Gemini API xatoliklari.
    """
    # 1-qadam: DOCX dan matnni ajratish
    raw_text = extract_text_from_docx(file_path)

    if not raw_text.strip():
        raise ValueError(f"DOCX fayldan matn ajratib bo'lmadi: {file_path}")

    # 2-qadam: Gemini API ga so'rov
    client = _get_gemini_client()
    model = _get_model_name()

    prompt = f"""Sen o'quv markazi hisobotlarini tahlil qiluvchi AI yordamchisan.

Quyidagi o'qituvchi kunlik hisobotini diqqat bilan o'qi va quyidagi ma'lumotlarni aniqla:

1. **teacher_name** — Hisobotdagi o'qituvchining ismi (agar ko'rsatilmagan bo'lsa, "Noma'lum" deb yoz)
2. **group_name** — Guruh nomi (masalan: Python-10). Agar ko'rsatilmagan bo'lsa, "Noma'lum" deb yoz
3. **attendance_rate** — Darsga qatnashish foizi (0 dan 100 gacha). Agar aniq raqam bo'lmasa, matn asosida taxmin qil
4. **topic** — Darsda o'tilgan mavzu
5. **homework_rate** — Uyga vazifani topshirganlar foizi (0 dan 100 gacha)
6. **issues** — Darsda yuzaga kelgan muammolar ro'yxati (har birini alohida element sifatida)
7. **ai_summary** — Hisobotning qisqacha xulosasi: umumiy holat, ijobiy va salbiy tomonlar (3-5 gap)

---

HISOBOT MATNI:
{raw_text}
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParsedReportSchema,
                temperature=0.2,
            ),
        )

        # Javobni Pydantic model orqali parse qilish
        parsed = ParsedReportSchema.model_validate_json(response.text)
        result = parsed.model_dump()

        logger.info(
            "DOCX hisobot muvaffaqiyatli parse qilindi: teacher=%s, group=%s",
            result.get("teacher_name"),
            result.get("group_name"),
        )
        return result

    except Exception as e:
        logger.error("Gemini DOCX parse xatosi: %s", str(e), exc_info=True)
        raise


# ===========================================================================
# Funksiya 2: Kunlik direktor xulosasini yaratish
# ===========================================================================

def generate_supervisor_daily_summary(target_date: date_type) -> str:
    """
    Berilgan kundagi barcha TeacherDailyReport va MarketingMetric
    yozuvlarini o'qib, Gemini Pro orqali direktor uchun executive summary yaratadi.

    Xulosa 3 bo'limdan iborat:
      1) O'qituvchilar intizomi va qatnashish (muammoli guruhlar)
      2) Marketing ko'rsatkichlari va raqobatchi holati
      3) Direktor uchun 3 ta muhim ogohlantirish / harakat rejasi (Action Points)

    Args:
        target_date: Xulosa yaratiladigan sana (date obyekti).

    Returns:
        str — Telegramda chiroyli ko'rinuvchi Markdown formatdagi xulosa.

    Raises:
        Exception: Gemini API xatoliklari.
    """
    # Import bu yerda — circular import oldini olish uchun
    from core.models import TeacherDailyReport, MarketingMetric

    # ---- Ma'lumotlarni yig'ish ----
    reports = TeacherDailyReport.objects.filter(date=target_date).select_related(
        "teacher__user", "group"
    )
    marketing = MarketingMetric.objects.filter(date=target_date).first()

    if not reports.exists() and marketing is None:
        logger.warning("Xulosa uchun ma'lumot topilmadi: %s", target_date)
        return (
            f"📋 **{target_date} uchun xulosa**\n\n"
            "⚠️ Bugun uchun hech qanday hisobot yoki marketing ma'lumoti topilmadi."
        )

    # ---- Hisobotlar matnini tayyorlash ----
    reports_text_parts: list[str] = []
    for report in reports:
        teacher_name = (
            report.teacher.user.get_full_name() or report.teacher.telegram_username
        )
        group_name = report.group.name if report.group else "Noma'lum guruh"
        issues_str = ", ".join(report.issues) if report.issues else "Muammo yo'q"

        topic_text = report.topic if report.topic else "Ko'rsatilmagan"
        reports_text_parts.append(
            f"- O'qituvchi: {teacher_name}\n"
            f"  Guruh: {group_name}\n"
            f"  Mavzu: {topic_text}\n"
            f"  Qatnashish: {report.attendance_rate:.1f}%\n"
            f"  Uyga vazifa: {report.homework_rate:.1f}%\n"
            f"  Muammolar: {issues_str}\n"
            f"  AI xulosasi: {report.ai_summary or 'Mavjud emas'}"
        )

    reports_text = "\n\n".join(reports_text_parts) if reports_text_parts else "Hisobotlar mavjud emas."

    # ---- Marketing ma'lumotlari ----
    if marketing:
        competitor_notes = (
            marketing.competitor_analysis_notes
            if marketing.competitor_analysis_notes
            else "Ma'lumot yo'q"
        )
        marketing_text = (
            f"- Leadlar soni: {marketing.leads_count}\n"
            f"- Reklama xarajati: {marketing.ad_spend} so'm\n"
            f"- Raqobatchilar tahlili: {competitor_notes}"
        )
    else:
        marketing_text = "Bugun uchun marketing ma'lumotlari kiritilmagan."

    # ---- Gemini ga so'rov ----
    client = _get_gemini_client()
    model = _get_model_name()

    prompt = f"""Sen o'quv markazi direktorining professional AI maslahatchisan.

Quyidagi {target_date} sanasidagi ma'lumotlar asosida direktor uchun batafsil kunlik xulosa (executive summary) yoz.

Xulosa Telegram Markdown formatida bo'lsin va AYNAN quyidagi 3 bo'limdan iborat bo'lsin:

**1. 📚 O'qituvchilar intizomi va qatnashish**
- Har bir o'qituvchi/guruh holati
- Muammoli guruhlarni alohida ta'kidla
- Qatnashish va uyga vazifa foizlarini solishtir

**2. 📈 Marketing ko'rsatkichlari**
- Leadlar soni va reklama samaradorligi
- Raqobatchilar holati va ulardan farqimiz

**3. 🎯 3 ta muhim ogohlantirish va harakat rejasi (Action Points)**
- Direktor darhol e'tibor berishi kerak bo'lgan 3 ta muhim nuqta
- Har bir nuqta uchun aniq harakat rejasi

---

O'QITUVCHILAR HISOBOTLARI:
{reports_text}

MARKETING MA'LUMOTLARI:
{marketing_text}

---

MUHIM: Xulosa professional, aniq va qisqa bo'lsin. Telegram Markdown formatidan foydalaning (bold uchun **matn**, monospace uchun `matn`). Emoji lardan o'rinli foydalaning.
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=2048,
            ),
        )

        summary = response.text.strip()
        logger.info("Direktor xulosasi muvaffaqiyatli yaratildi: %s", target_date)
        return summary

    except Exception as e:
        logger.error(
            "Gemini xulosa yaratish xatosi (%s): %s",
            target_date,
            str(e),
            exc_info=True,
        )
        raise


# ===========================================================================
# Funksiya 3: Marketing tahlili va Strategik maslahatlar (AI ni o'qitish bazasi asosida)
# ===========================================================================

def generate_marketing_ai_analysis(marketing_metric, auto_save: bool = True) -> dict:
    """
    MarketingMetric obyekti va tizimdagi barcha faol MarketingAIInstruction
    (o'qitilgan bilimlar bazasi) asosida Gemini orqali chuqur tahlil va maslahatlar ishlab chiqadi.

    Args:
        marketing_metric: MarketingMetric modeli instansi.
        auto_save: Natijalarni modelga avtomatik saqlash (default: True).

    Returns:
        dict: {"ai_analysis": str, "ai_recommendations": str}
    """
    from core.models import MarketingAIInstruction, MarketingMetric

    # 1. Barcha faol o'qitish ko'rsatmalari (Knowledge Base)
    instructions = MarketingAIInstruction.objects.filter(is_active=True).order_by("order", "category")

    knowledge_blocks = []
    if instructions.exists():
        for inst in instructions:
            knowledge_blocks.append(
                f"### [{inst.get_category_display()}] {inst.title}\n{inst.instruction_text}"
            )
        knowledge_base_text = "\n\n".join(knowledge_blocks)
    else:
        knowledge_base_text = (
            "Standart IT/O'quv markazi marketing mezonlari:\n"
            "- Optimal 1 ta lead narxi (CAC): 20,000 - 45,000 so'm oralig'ida.\n"
            "- Agar lead narxi 50,000 so'mdan oshsa, auditoriyani yangilash va taklifni qayta ko'rib chiqish kerak.\n"
            "- Raqobatchilar narx tushirsa, sifat, kafolatli natija va amaliyotga urg'u berish lozim."
        )

    # 2. O'tgan kunlar bilan taqqoslash (oxirgi 7 kun)
    recent_metrics = MarketingMetric.objects.filter(
        date__lt=marketing_metric.date,
        date__gte=marketing_metric.date - timedelta(days=7)
    )
    if recent_metrics.exists():
        avg_leads = sum(m.leads_count for m in recent_metrics) / recent_metrics.count()
        total_spend = sum(float(m.ad_spend) for m in recent_metrics)
        avg_spend = total_spend / recent_metrics.count()
        comparison_text = (
            f"- Oxirgi 7 kundagi o'rtacha kunlik leadlar: {avg_leads:.1f} ta\n"
            f"- Oxirgi 7 kundagi o'rtacha kunlik xarajat: {avg_spend:,.0f} so'm\n"
        )
    else:
        comparison_text = "- Avvalgi kunlar uchun yetarli taqqoslash ma'lumoti yo'q.\n"

    # 3. Prompt tayyorlash
    cost_per_lead_val = (
        float(marketing_metric.ad_spend) / marketing_metric.leads_count
        if marketing_metric.leads_count > 0
        else 0.0
    )
    cost_per_lead_str = f"{cost_per_lead_val:,.0f} so'm" if cost_per_lead_val > 0 else "0 so'm"
    competitor_notes = (
        marketing_metric.competitor_analysis_notes.strip()
        or "Bugun uchun raqobatchilar haqida maxsus xabar kiritilmagan."
    )

    prompt = f"""Sen o'quv markazining Bosh Marketing Strategisti va AI Biznes Maslahatchisisan.

SENGA RAHBARIYAT TOMONIDAN O'RGATILGAN QOIDALAR, STRATEGIYA VA KURS AFZALLIKLARI (KNOWLEDGE BASE):
========================================================================
{knowledge_base_text}
========================================================================

BUGUNGI MARKETING KO'RSATKICHLARI ({marketing_metric.date}):
- Kelgan yangi leadlar soni: {marketing_metric.leads_count} ta
- Reklama xarajati: {float(marketing_metric.ad_spend):,.0f} so'm
- 1 ta lead narxi (CAC): {cost_per_lead_str}
- Raqobatchilar yangiliklari/aksiyalari haqida ma'lumot:
{competitor_notes}

O'TMISHDAGI TAQQOSLASH (Oxirgi 7 kun):
{comparison_text}

---
VAZIFANG:
Yuqoridagi RAHBARIYAT O'RGATGAN QOIDALARIGA QAT'IY AMAL QILGAN HOLDA quyidagi 2 ta bo'limni tayyorla:

1. **ai_analysis** (Marketing Tahlili va Xulosasi):
   - Byudjet va lead narxi samaradorligi (O'qitilgan byudjet mezonlariga mosmi? Byudjet oqlanyaptimi?)
   - Raqobatchilar tahlili (Agar raqobatchi haqida ma'lumot bo'lsa, o'rgatilgan qoidalar bo'yicha bizning pozitsiyamizni ko'rsat)
   - Markazimizning afzalliklari (USP) dan qanday samarali foydalanilayotgani yoki nimalar yetishmayotgani

2. **ai_recommendations** (Strategik Maslahatlar va Harakat Rejasi):
   - Direktor va Marketolog uchun 3 tadan 5 tagacha aniq, amaliy maslahat (Action points)
   - Aniq tavsiyalar bering: reklama kreativlari, aksiya va takliflar, target auditoriya, narx va kafolat taqdimoti bo'yicha.

Javobing professional, o'zbek tilida, jiddiy biznes tahlil uslubida va aniq raqamlarga tayangan bo'lsin. Markdown formatidan foydalan.
"""

    client = _get_gemini_client()
    model = _get_model_name()

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MarketingAnalysisResultSchema,
                temperature=0.3,
            ),
        )

        parsed = MarketingAnalysisResultSchema.model_validate_json(response.text)
        result = parsed.model_dump()

        if auto_save:
            marketing_metric.ai_analysis = result["ai_analysis"]
            marketing_metric.ai_recommendations = result["ai_recommendations"]
            marketing_metric.cost_per_lead = cost_per_lead_val
            marketing_metric.save()
            logger.info("Marketing AI tahlili muvaffaqiyatli saqlandi: %s", marketing_metric.date)

        return result

    except Exception as e:
        logger.error("Gemini marketing tahlil xatosi: %s", str(e), exc_info=True)
        raise

