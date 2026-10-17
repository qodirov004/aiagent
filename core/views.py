"""
core/views.py — API va Web kabinetlar.

Bo'limlar:
  A) Xavfsizlik — InternalAPIKeyAuthentication (Custom Header Token)
  B) UserBot uchun Ichki API View'lar (4 ta endpoint)
  C) O'qituvchilar Veb-kabineti (Django TemplateView)
"""

import logging
import tempfile
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages as django_messages
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .gemini_services import (
    parse_docx_report,
    generate_supervisor_daily_summary,
    generate_marketing_ai_analysis,
)
from .models import (
    DirectorDailySummary,
    Group,
    LessonSchedule,
    Student,
    Teacher,
    TeacherDailyReport,
    WeeklyFeedback,
    MarketingMetric,
    MarketingAIInstruction,
    InstagramConfig,
    InstagramMetric,
    MarketingTelegramDispatch,
)
from .serializers import (
    DirectorSummarySerializer,
    MarkNotifiedSerializer,
    TodayScheduleSerializer,
    UploadReportSerializer,
    InstagramConfigSerializer,
    InstagramMetricSerializer,
)
from .instagram_services import (
    get_or_create_default_instagram_config,
    sync_instagram_metrics,
    format_marketing_telegram_report,
    format_quick_stats_telegram_report,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# A) XAVFSIZLIK — Custom API Header Token Authentication
# ===========================================================================

class InternalAPIKeyAuthentication(BaseAuthentication):
    """
    UserBot <-> Django ichki API xavfsizligi.
    Header: `X-Internal-Api-Key: <INTERNAL_API_KEY>`

    Agar kalit mos kelmasa yoki bo'lmasa, 403 qaytaradi.
    """

    HEADER_NAME = "HTTP_X_INTERNAL_API_KEY"

    def authenticate(self, request):
        api_key = request.META.get(self.HEADER_NAME)

        if api_key is None:
            raise AuthenticationFailed(
                "X-Internal-Api-Key header topilmadi."
            )

        expected_key = getattr(settings, "INTERNAL_API_KEY", "")
        if not expected_key:
            raise AuthenticationFailed(
                "Server sozlamalarida INTERNAL_API_KEY belgilanmagan."
            )

        if api_key != expected_key:
            raise AuthenticationFailed(
                "Noto'g'ri API kalit. Kirish rad etildi."
            )

        # Muvaffaqiyatli — user=None, auth=api_key
        return (None, api_key)


# ===========================================================================
# B) USERBOT UCHUN ICHKI API VIEW'LAR
# ===========================================================================

class TodaySchedulesView(APIView):
    """
    GET /api/internal/today-schedules/

    Bugungi kungi darslar va xabardor qilinmagan o'qituvchilar ro'yxatini qaytaradi.
    Filtrlash: is_notified=False (faqat hali xabar yuborilmaganlar).
    """

    authentication_classes = [InternalAPIKeyAuthentication]
    permission_classes = []  # Auth orqali himoyalangan, permission kerak emas

    def get(self, request):
        today = date.today()

        schedules = (
            LessonSchedule.objects.filter(date=today, is_notified=False)
            .select_related("teacher__user", "group")
            .order_by("start_time")
        )

        serializer = TodayScheduleSerializer(schedules, many=True)

        return Response(
            {
                "date": today.isoformat(),
                "count": schedules.count(),
                "schedules": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class MarkNotifiedView(APIView):
    """
    POST /api/internal/mark-notified/

    UserBot xabar yuborgan dars jadvallarini is_notified=True ga yangilaydi.
    Body: {"schedule_ids": [1, 2, 3]}
    """

    authentication_classes = [InternalAPIKeyAuthentication]
    permission_classes = []

    def post(self, request):
        serializer = MarkNotifiedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schedule_ids = serializer.validated_data["schedule_ids"]

        updated_count = LessonSchedule.objects.filter(
            id__in=schedule_ids,
            is_notified=False,
        ).update(is_notified=True)

        logger.info(
            "Mark-notified: %d ta dars jadval xabardor qilindi (so'ralgan: %d)",
            updated_count,
            len(schedule_ids),
        )

        return Response(
            {
                "message": f"{updated_count} ta dars xabardor qilindi.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


class UploadReportView(APIView):
    """
    POST /api/internal/upload-report/

    UserBot guruhdan ushlab olgan .docx faylni qabul qiladi.
    Faylni saqlaydi, Gemini orqali parse qiladi va TeacherDailyReport yaratadi.

    Body (multipart/form-data):
      - telegram_username: str (@ belgisisiz)
      - file: .docx fayl
    """

    authentication_classes = [InternalAPIKeyAuthentication]
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = UploadReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_username = serializer.validated_data["telegram_username"]
        uploaded_file = serializer.validated_data["file"]

        # 1. O'qituvchini topish
        try:
            teacher = Teacher.objects.get(
                telegram_username=telegram_username,
                is_active=True,
            )
        except Teacher.DoesNotExist:
            logger.warning(
                "O'qituvchi topilmadi: telegram_username=%s", telegram_username
            )
            return Response(
                {
                    "error": f"Telegram username '{telegram_username}' bilan faol o'qituvchi topilmadi."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Faylni saqlash
        today = date.today()
        file_path = f"reports/docx/{today:%Y}/{today:%m}/{today:%d}/{uploaded_file.name}"
        saved_path = default_storage.save(file_path, uploaded_file)
        full_path = default_storage.path(saved_path)

        logger.info("DOCX fayl saqlandi: %s", full_path)

        # 3. Gemini orqali parse qilish
        try:
            parsed_data = parse_docx_report(full_path)
        except Exception as e:
            logger.error(
                "Gemini parse xatosi (teacher=%s): %s",
                telegram_username,
                str(e),
                exc_info=True,
            )
            # Xatolik bo'lsa ham, faylni bazaga saqlaymiz (raw_text bo'sh)
            parsed_data = {
                "teacher_name": "",
                "group_name": "",
                "attendance_rate": 0.0,
                "topic": "",
                "homework_rate": 0.0,
                "issues": [],
                "ai_summary": f"⚠️ AI tahlil xatosi: {str(e)}",
            }

        # 4. Guruhni aniqlash (parsed_data dan yoki o'qituvchining birinchi guruhi)
        group = None
        parsed_group_name = parsed_data.get("group_name", "")
        if parsed_group_name and parsed_group_name != "Noma'lum":
            group = Group.objects.filter(name__icontains=parsed_group_name).first()
        if group is None:
            group = teacher.groups.first()

        # 5. Raw text ajratish (fayldan)
        try:
            from .gemini_services import extract_text_from_docx
            raw_text = extract_text_from_docx(full_path)
        except Exception:
            raw_text = ""

        # 6. TeacherDailyReport yaratish
        report = TeacherDailyReport.objects.create(
            teacher=teacher,
            group=group,
            date=today,
            raw_file=saved_path,
            raw_text=raw_text,
            attendance_rate=parsed_data.get("attendance_rate", 0.0),
            topic=parsed_data.get("topic", ""),
            homework_rate=parsed_data.get("homework_rate", 0.0),
            issues=parsed_data.get("issues", []),
            ai_summary=parsed_data.get("ai_summary", ""),
        )

        logger.info(
            "TeacherDailyReport yaratildi: id=%d, teacher=%s, group=%s",
            report.id,
            telegram_username,
            group.name if group else "—",
        )

        return Response(
            {
                "message": "Hisobot muvaffaqiyatli qabul qilindi va AI tahlildan o'tkazildi.",
                "report_id": report.id,
                "parsed_data": parsed_data,
            },
            status=status.HTTP_201_CREATED,
        )


class DailySummaryForDirectorView(APIView):
    """
    GET /api/internal/daily-summary-for-director/

    Gemini tuzgan va hali jo'natilmagan direktor hisobotini qaytaradi.
    Agar xulosa mavjud bo'lmasa, yangi yaratadi.
    Jo'natilgandan so'ng is_sent_to_director=True ga yangilaydi.

    Query params:
      - date: YYYY-MM-DD (ixtiyoriy, default: bugun)
      - mark_sent: true/false (ixtiyoriy, default: true)
    """

    authentication_classes = [InternalAPIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        # Sanani aniqlash
        date_str = request.query_params.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Noto'g'ri sana formati. YYYY-MM-DD kerak."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = date.today()

        # Mark sent parametri
        mark_sent = request.query_params.get("mark_sent", "true").lower() == "true"

        # Mavjud xulosa bormi?
        summary_obj = DirectorDailySummary.objects.filter(date=target_date).first()

        if summary_obj is None:
            # Yangi xulosa yaratish
            try:
                summary_text = generate_supervisor_daily_summary(target_date)
            except Exception as e:
                logger.error(
                    "Direktor xulosasi yaratish xatosi: %s", str(e), exc_info=True
                )
                return Response(
                    {"error": f"AI xulosa yaratishda xatolik: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            summary_obj = DirectorDailySummary.objects.create(
                date=target_date,
                summary_markdown=summary_text,
                is_sent_to_director=False,
            )
            logger.info("Yangi direktor xulosasi yaratildi: %s", target_date)

        # Agar allaqachon yuborilgan bo'lsa
        if summary_obj.is_sent_to_director and not mark_sent:
            return Response(
                {
                    "message": "Bu kun uchun xulosa allaqachon direktorga yuborilgan.",
                    "summary": DirectorSummarySerializer(summary_obj).data,
                },
                status=status.HTTP_200_OK,
            )

        # Javob qaytarish va statusni yangilash
        response_data = DirectorSummarySerializer(summary_obj).data

        if mark_sent and not summary_obj.is_sent_to_director:
            summary_obj.is_sent_to_director = True
            summary_obj.save(update_fields=["is_sent_to_director", "updated_at"])
            logger.info("Direktor xulosasi yuborildi deb belgilandi: %s", target_date)

        return Response(
            {
                "message": "Direktor xulosasi tayyor.",
                "summary": response_data,
            },
            status=status.HTTP_200_OK,
        )


class InternalMarketingReportView(APIView):
    """
    GET /api/internal/marketing-telegram-report/
    Userbot yoki scheduler uchun to'liq marketing + Instagram + AI hisobot matnini beradi.
    """
    authentication_classes = [InternalAPIKeyAuthentication]

    def get(self, request):
        date_str = request.query_params.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Noto'g'ri sana formati (YYYY-MM-DD kerak)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = date.today()

        try:
            report_text = format_marketing_telegram_report(target_date)
            marketing_group_id = getattr(settings, "MARKETING_GROUP_ID", "") or getattr(settings, "TEACHER_GROUP_ID", "")
            return Response(
                {
                    "status": "success",
                    "date": str(target_date),
                    "marketing_group_id": marketing_group_id,
                    "report_markdown": report_text,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("Marketing hisobotini tayyorlashda xatolik: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Hisobot tayyorlashda xatolik: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InternalQuickStatsView(APIView):
    """
    GET /api/internal/quick-stats/
    Userbot uchun tezkor ko'rsatkichlar va statistika (/stats buyrug'i uchun).
    """
    authentication_classes = [InternalAPIKeyAuthentication]

    def get(self, request):
        date_str = request.query_params.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Noto'g'ri sana formati (YYYY-MM-DD kerak)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = date.today()

        try:
            report_text = format_quick_stats_telegram_report(target_date)
            return Response(
                {
                    "status": "success",
                    "date": str(target_date),
                    "stats_markdown": report_text,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("Tezkor statistika tayyorlashda xatolik: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Statistika tayyorlashda xatolik: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InternalPendingMarketingDispatchesView(APIView):
    """
    GET /api/internal/pending-marketing-dispatches/ — Yuborilmagan xabarlar navbatini qaytaradi.
    POST /api/internal/pending-marketing-dispatches/ — Xabarni 'yuborildi' yoki 'xatolik' deb belgilaydi.
    """
    authentication_classes = [InternalAPIKeyAuthentication]

    def get(self, request):
        pending = MarketingTelegramDispatch.objects.filter(is_sent=False).order_by("created_at")[:5]
        dispatches_data = []
        for item in pending:
            dispatches_data.append({
                "id": item.id,
                "chat_id": item.chat_id,
                "message_text": item.message_text,
                "date": str(item.date),
            })
        return Response({"pending_count": len(dispatches_data), "dispatches": dispatches_data})

    def post(self, request):
        dispatch_id = request.data.get("dispatch_id")
        error_msg = request.data.get("error_message", "")
        try:
            dispatch = MarketingTelegramDispatch.objects.get(id=dispatch_id)
            if error_msg:
                dispatch.error_message = error_msg
                dispatch.save(update_fields=["error_message", "updated_at"])
            else:
                from django.utils import timezone
                dispatch.is_sent = True
                dispatch.sent_at = timezone.now()
                dispatch.save(update_fields=["is_sent", "sent_at", "updated_at"])
            return Response({"status": "success", "dispatch_id": dispatch.id, "is_sent": dispatch.is_sent})
        except MarketingTelegramDispatch.DoesNotExist:
            return Response({"error": "Dispatch topilmadi"}, status=status.HTTP_404_NOT_FOUND)


# ===========================================================================
# C) O'QITUVCHILAR VEB-KABINETI (React ilovasiga yo'naltirish)
# ===========================================================================

class TeacherCabinetView(View):
    """
    Eski Django HTML shablon kabineti to'liq React frontendga ko'chirilgan.
    Agar kishi /teacher/cabinet/ ga kirsa, to'g'ridan-to'g'ri React ga yo'naltiriladi.
    """

    def get(self, request):
        return redirect("http://localhost:5173")


# ===========================================================================
# D) SUPERVAYZER ADMIN DASHBOARD API (React Frontend uchun)
# ===========================================================================

from django.db.models import Avg, Count, Q, Sum
from .models import MarketingMetric, MarketingAIInstruction
from .serializers import (
    MarketingMetricSerializer,
    MarketingAIInstructionSerializer,
    TeacherSerializer,
    GroupSerializer,
    StudentSerializer,
    WeeklyFeedbackSerializer,
    TeacherDailyReportSerializer,
)


class SupervisorStatsView(APIView):
    """
    GET /api/supervisor/stats/
    Supervayzer dashboardi uchun umumiy metrikalar.
    """

    def get(self, request):
        today = date.today()

        # O'quvchilar soni
        student_counts = Student.objects.aggregate(
            active=Count("id", filter=Q(status="active")),
            frozen=Count("id", filter=Q(status="frozen")),
            left=Count("id", filter=Q(status="left")),
            total=Count("id"),
        )

        # O'qituvchilar va guruhlar
        total_teachers = Teacher.objects.filter(is_active=True).count()
        total_groups = Group.objects.count()

        # Bugungi darslar
        today_schedules_total = LessonSchedule.objects.filter(date=today).count()
        today_schedules_notified = LessonSchedule.objects.filter(
            date=today, is_notified=True
        ).count()

        # Bugungi yoki so'nggi hisobotlar o'rtacha ko'rsatkichlari
        today_reports = TeacherDailyReport.objects.filter(date=today)
        reports_count = today_reports.count()

        if reports_count > 0:
            avg_attendance = today_reports.aggregate(Avg("attendance_rate"))[
                "attendance_rate__avg"
            ] or 0.0
            avg_homework = today_reports.aggregate(Avg("homework_rate"))[
                "homework_rate__avg"
            ] or 0.0
        else:
            # So'nggi 7 kunlik o'rtacha
            recent_reports = TeacherDailyReport.objects.filter(
                date__gte=today - timedelta(days=7)
            )
            avg_attendance = (
                recent_reports.aggregate(Avg("attendance_rate"))["attendance_rate__avg"]
                or 0.0
            )
            avg_homework = (
                recent_reports.aggregate(Avg("homework_rate"))["homework_rate__avg"]
                or 0.0
            )

        # Bugungi marketing
        today_marketing = MarketingMetric.objects.filter(date=today).first()
        marketing_data = (
            MarketingMetricSerializer(today_marketing).data if today_marketing else None
        )

        # Bugungi AI xulosa
        today_summary = DirectorDailySummary.objects.filter(date=today).first()
        summary_data = (
            DirectorSummarySerializer(today_summary).data if today_summary else None
        )

        return Response(
            {
                "date": today.isoformat(),
                "students": student_counts,
                "total_teachers": total_teachers,
                "total_groups": total_groups,
                "today_schedules": {
                    "total": today_schedules_total,
                    "notified": today_schedules_notified,
                },
                "reports_today_count": reports_count,
                "avg_attendance_rate": round(avg_attendance, 1),
                "avg_homework_rate": round(avg_homework, 1),
                "marketing": marketing_data,
                "today_summary": summary_data,
            },
            status=status.HTTP_200_OK,
        )


class SupervisorSummariesView(APIView):
    """
    GET /api/supervisor/summaries/
    POST /api/supervisor/summaries/ (Gemini orqali yangi xulosa generatsiya qilish)
    """

    def get(self, request):
        summaries = DirectorDailySummary.objects.all().order_by("-date")[:30]
        serializer = DirectorSummarySerializer(summaries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        date_str = request.data.get("date")
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Sana formati noto'g'ri (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            target_date = date.today()

        try:
            summary_text = generate_supervisor_daily_summary(target_date)
        except Exception as e:
            return Response(
                {"error": f"Gemini xulosa generatsiyasida xatolik: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        summary_obj, created = DirectorDailySummary.objects.update_or_create(
            date=target_date,
            defaults={"summary_markdown": summary_text},
        )

        return Response(
            {
                "message": "AI xulosasi muvaffaqiyatli yaratildi",
                "summary": DirectorSummarySerializer(summary_obj).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SupervisorReportsView(APIView):
    """
    GET /api/supervisor/reports/
    Kunlik docx hisobotlari ro'yxati (filtrlash: date, teacher_id).
    """

    def get(self, request):
        qs = TeacherDailyReport.objects.select_related(
            "teacher__user", "group"
        ).order_by("-date", "-created_at")

        date_filter = request.query_params.get("date")
        if date_filter:
            qs = qs.filter(date=date_filter)

        teacher_id = request.query_params.get("teacher_id")
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)

        serializer = TeacherDailyReportSerializer(qs[:50], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupervisorMarketingView(APIView):
    """
    GET /api/supervisor/marketing/
    POST /api/supervisor/marketing/ (yangi metric kiritish yoki yangilash)
    """

    def get(self, request):
        metrics = MarketingMetric.objects.all().order_by("-date")[:30]
        serializer = MarketingMetricSerializer(metrics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        date_str = request.data.get("date")
        if not date_str:
            target_date = date.today()
        else:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Sana formati noto'g'ri (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        leads_count = request.data.get("leads_count", 0)
        ad_spend = request.data.get("ad_spend", 0.0)
        competitor_analysis_notes = request.data.get("competitor_analysis_notes", "")

        metric, created = MarketingMetric.objects.update_or_create(
            date=target_date,
            defaults={
                "leads_count": leads_count,
                "ad_spend": ad_spend,
                "competitor_analysis_notes": competitor_analysis_notes,
            },
        )

        # Agar foydalanuvchi generate_ai=True yuborgan bo'lsa yoki avtomatik AI tahlil so'ralsa
        if request.data.get("generate_ai", False):
            try:
                generate_marketing_ai_analysis(metric, auto_save=True)
            except Exception as e:
                logger.warning("Auto AI analysis failed: %s", str(e))

        return Response(
            MarketingMetricSerializer(metric).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SupervisorMarketingAIAnalyzeView(APIView):
    """
    POST /api/supervisor/marketing/ai-analyze/
    Berilgan sana bo'yicha Gemini marketing tahlili va tavsiyalarni ishlab chiqadi.
    """

    def post(self, request):
        date_str = request.data.get("date")
        if not date_str:
            target_date = date.today()
        else:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Noto'g'ri sana formati (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        metric = MarketingMetric.objects.filter(date=target_date).first()
        if not metric:
            metric = MarketingMetric.objects.create(
                date=target_date,
                leads_count=request.data.get("leads_count", 0),
                ad_spend=request.data.get("ad_spend", 0.0),
                competitor_analysis_notes=request.data.get("competitor_analysis_notes", ""),
            )

        try:
            result = generate_marketing_ai_analysis(metric, auto_save=True)
            return Response(
                {
                    "message": "AI tahlili va tavsiyalari muvaffaqiyatli yaratildi!",
                    "metric": MarketingMetricSerializer(metric).data,
                    "analysis": result,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("AI Marketing Analyze error: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Gemini tahlil xatosi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SupervisorMarketingInstructionsView(APIView):
    """
    GET /api/supervisor/marketing/instructions/
    POST /api/supervisor/marketing/instructions/
    AI ni o'qitish (Knowledge Base) qoidalarini ko'rish va boshqarish.
    """

    def get(self, request):
        instructions = MarketingAIInstruction.objects.all().order_by("order", "-created_at")
        serializer = MarketingAIInstructionSerializer(instructions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get("title", "").strip()
        category = request.data.get("category", "usp")
        instruction_text = request.data.get("instruction_text", "").strip()
        is_active = request.data.get("is_active", True)
        order = request.data.get("order", 0)

        if not title or not instruction_text:
            return Response(
                {"error": "Mavzu va ko'rsatma matni majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inst = MarketingAIInstruction.objects.create(
            title=title,
            category=category,
            instruction_text=instruction_text,
            is_active=is_active,
            order=order,
        )
        return Response(
            MarketingAIInstructionSerializer(inst).data,
            status=status.HTTP_201_CREATED,
        )


class SupervisorTeachersView(APIView):
    """GET /api/supervisor/teachers/"""

    def get(self, request):
        teachers = Teacher.objects.filter(is_active=True).select_related("user")
        serializer = TeacherSerializer(teachers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupervisorGroupsView(APIView):
    """GET /api/supervisor/groups/"""

    def get(self, request):
        groups = Group.objects.select_related("teacher__user").prefetch_related("students")
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupervisorFeedbacksView(APIView):
    """GET /api/supervisor/feedbacks/"""

    def get(self, request):
        feedbacks = WeeklyFeedback.objects.select_related(
            "student__group", "teacher__user"
        ).order_by("-week_start_date")[:50]
        serializer = WeeklyFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================================================================
# E) REACT O'QITUVCHI KABINETI API (Teacher Cabinet React Frontend)
# ===========================================================================

class TeacherCabinetApiView(APIView):
    """
    GET /api/teacher/cabinet/
    POST /api/teacher/cabinet/
    React ilovasi uchun to'liq asinxron O'qituvchi Kabineti API.
    """

    def get(self, request):
        teacher_id = request.query_params.get("teacher_id")
        week_str = request.query_params.get("week")

        # Haftaning dushanba sanasini hisoblash
        if week_str:
            try:
                selected_date = date.fromisoformat(week_str)
                week_start = selected_date - timedelta(days=selected_date.weekday())
            except ValueError:
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)
        prev_week = week_start - timedelta(weeks=1)
        next_week = week_start + timedelta(weeks=1)

        teachers_qs = Teacher.objects.filter(is_active=True).select_related("user")
        teachers_list = [
            {
                "id": t.id,
                "full_name": t.user.get_full_name() or t.telegram_username,
                "telegram_username": t.telegram_username,
                "subjects": t.subjects,
                "phone": t.phone,
            }
            for t in teachers_qs
        ]

        # Tanlangan o'qituvchi
        teacher = None
        if teacher_id:
            try:
                teacher = teachers_qs.filter(id=int(teacher_id)).first()
            except ValueError:
                pass
        if not teacher and teachers_qs.exists():
            teacher = teachers_qs.first()

        groups_data = []
        if teacher:
            groups_qs = Group.objects.filter(teacher=teacher).prefetch_related("students")
            for g in groups_qs:
                active_students = g.students.filter(status="active").order_by("full_name")
                students_data = []
                for s in active_students:
                    feedback = WeeklyFeedback.objects.filter(
                        student=s,
                        week_start_date=week_start,
                    ).first()
                    students_data.append({
                        "id": s.id,
                        "full_name": s.full_name,
                        "phone": s.phone,
                        "performance_status": feedback.performance_status if feedback else "",
                        "comment": feedback.comment if feedback else "",
                        "feedback_id": feedback.id if feedback else None,
                    })
                groups_data.append({
                    "id": g.id,
                    "name": g.name,
                    "room_number": g.room_number,
                    "schedule_days": g.schedule_days,
                    "students": students_data,
                    "students_count": len(students_data),
                })

        return Response({
            "teachers_list": teachers_list,
            "teacher": {
                "id": teacher.id,
                "full_name": teacher.user.get_full_name() or teacher.telegram_username,
                "telegram_username": teacher.telegram_username,
                "subjects": teacher.subjects,
                "phone": teacher.phone,
            } if teacher else None,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "prev_week": prev_week.isoformat(),
            "next_week": next_week.isoformat(),
            "performance_choices": [
                {"value": "excellent", "label": "A'lo", "color": "emerald"},
                {"value": "good", "label": "Yaxshi", "color": "indigo"},
                {"value": "average", "label": "O'rtacha", "color": "amber"},
                {"value": "poor", "label": "Qoniqarsiz", "color": "rose"},
            ],
            "groups": groups_data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        teacher_id = request.data.get("teacher_id")
        week_start_str = request.data.get("week_start")
        feedbacks = request.data.get("feedbacks", [])

        if not teacher_id or not week_start_str:
            return Response(
                {"error": "teacher_id va week_start majburiy maydonlar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            week_start = date.fromisoformat(week_start_str)
        except ValueError:
            return Response(
                {"error": "Noto'g'ri sana formati"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        teacher = Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            return Response(
                {"error": "O'qituvchi topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        saved_count = 0
        for item in feedbacks:
            student_id = item.get("student_id")
            performance = item.get("performance_status", "").strip()
            comment = item.get("comment", "").strip()

            if not student_id or not performance:
                continue

            student = Student.objects.filter(
                id=student_id,
                group__teacher=teacher,
                status="active",
            ).first()

            if not student:
                continue

            WeeklyFeedback.objects.update_or_create(
                student=student,
                week_start_date=week_start,
                defaults={
                    "teacher": teacher,
                    "performance_status": performance,
                    "comment": comment,
                },
            )
            saved_count += 1

        return Response(
            {
                "message": f"✅ {saved_count} ta o'quvchi uchun baholar muvaffaqiyatli saqlandi!",
                "saved_count": saved_count,
            },
            status=status.HTTP_200_OK,
        )


class TeacherCabinetDemoDataView(APIView):
    """
    POST /api/teacher/cabinet/demo-data/
    O'qituvchi kabinetini darhol sinab ko'rish uchun test o'qituvchi, guruh va talabalar yaratish.
    """

    def post(self, request):
        from django.contrib.auth.models import User
        # 1. User va Teacher
        user, _ = User.objects.get_or_create(
            username="aziz_teacher",
            defaults={
                "first_name": "Aziz",
                "last_name": "Rahimov",
                "email": "aziz@example.com",
            },
        )
        teacher, _ = Teacher.objects.get_or_create(
            user=user,
            defaults={
                "telegram_username": "aziz_py",
                "subjects": "Python, Django, AI",
                "phone": "+998 90 123 45 67",
                "is_active": True,
            },
        )

        # 2. Guruhlar
        g1, _ = Group.objects.get_or_create(
            name="Python Backend 01",
            defaults={
                "teacher": teacher,
                "schedule_days": "Du-Chor-Jum (18:30)",
                "lesson_start_time": "18:30",
                "lesson_end_time": "20:30",
                "room_number": "204",
            },
        )
        g2, _ = Group.objects.get_or_create(
            name="AI & Django Pro",
            defaults={
                "teacher": teacher,
                "schedule_days": "Se-Pay-Shan (15:00)",
                "lesson_start_time": "15:00",
                "lesson_end_time": "17:00",
                "room_number": "301",
            },
        )

        # 3. O'quvchilar
        demo_students_g1 = [
            ("Sardor Aliyev", "+998 90 111 22 33"),
            ("Madina Karimova", "+998 91 222 33 44"),
            ("Javohir Qodirov", "+998 93 333 44 55"),
            ("Dilnoza Saidova", "+998 94 444 55 66"),
        ]
        demo_students_g2 = [
            ("Bobur Mirzaev", "+998 97 555 66 77"),
            ("Shahzoda Yusupova", "+998 99 666 77 88"),
            ("Umid Rustamov", "+998 90 777 88 99"),
        ]

        created_students = 0
        for name, phone in demo_students_g1:
            _, created = Student.objects.get_or_create(
                full_name=name,
                group=g1,
                defaults={"phone": phone, "status": "active"},
            )
            if created:
                created_students += 1

        for name, phone in demo_students_g2:
            _, created = Student.objects.get_or_create(
                full_name=name,
                group=g2,
                defaults={"phone": phone, "status": "active"},
            )
            if created:
                created_students += 1

        return Response(
            {
                "message": "Demo o'qituvchi, guruhlar va o'quvchilar muvaffaqiyatli yaratildi!",
                "teacher_id": teacher.id,
                "created_students": created_students,
            },
            status=status.HTTP_201_CREATED,
        )


class SupervisorInstagramView(APIView):
    """
    GET /api/supervisor/instagram/ — Instagram konfiguratsiyasi va statistikalar.
    POST /api/supervisor/instagram/ — Konfiguratsiyani yangilash.
    """
    def get(self, request):
        config = get_or_create_default_instagram_config()
        metrics = InstagramMetric.objects.filter(account=config).order_by("-date")[:14]
        today_metric = InstagramMetric.objects.filter(account=config, date=date.today()).first()
        if not today_metric and config.auto_sync:
            try:
                today_metric = sync_instagram_metrics(config=config, target_date=date.today())
                metrics = InstagramMetric.objects.filter(account=config).order_by("-date")[:14]
            except Exception as e:
                logger.warning("Auto sync instagram error: %s", str(e))

        return Response({
            "config": InstagramConfigSerializer(config).data,
            "latest_metric": InstagramMetricSerializer(today_metric).data if today_metric else None,
            "metrics": InstagramMetricSerializer(metrics, many=True).data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        config = get_or_create_default_instagram_config()
        serializer = InstagramConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "config": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupervisorInstagramSyncView(APIView):
    """
    POST /api/supervisor/instagram/sync/ — Instagram ma'lumotlarini qo'lda darhol yangilash.
    """
    def post(self, request):
        config = get_or_create_default_instagram_config()
        try:
            metric = sync_instagram_metrics(config=config, target_date=date.today())
            return Response({
                "status": "success",
                "message": f"@{config.instagram_username} statistikasi muvaffaqiyatli yangilandi!",
                "metric": InstagramMetricSerializer(metric).data,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Instagram sync xatosi: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Sinxronizatsiya xatosi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SupervisorMarketingSendTelegramView(APIView):
    """
    POST /api/supervisor/marketing/send-telegram/
    Bugungi marketing + Instagram + AI hisobotini Telegram guruhga yuborish navbatiga kiritadi.
    """
    def post(self, request):
        target_date = date.today()
        try:
            report_text = format_marketing_telegram_report(target_date)
            marketing_group_id = getattr(settings, "MARKETING_GROUP_ID", "") or getattr(settings, "TEACHER_GROUP_ID", "")
            
            custom_chat_id = request.data.get("chat_id")
            if custom_chat_id:
                marketing_group_id = custom_chat_id

            dispatch = MarketingTelegramDispatch.objects.create(
                date=target_date,
                message_text=report_text,
                chat_id=str(marketing_group_id),
                is_sent=False,
            )

            return Response({
                "status": "success",
                "message": "Marketing hisoboti Telegram guruhga yuborish navbatiga muvaffaqiyatli joylashtirildi!",
                "dispatch_id": dispatch.id,
                "chat_id": str(marketing_group_id),
                "report_preview": report_text[:350],
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Marketing Telegram dispatch xatosi: %s", str(e), exc_info=True)
            return Response(
                {"error": f"Hisobot yuborishda xatolik: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



