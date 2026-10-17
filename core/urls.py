"""
core/urls.py — URL konfiguratsiyasi.

Endpointlar:
  A) /api/internal/ — UserBot uchun ichki API (Header Token bilan himoyalangan)
  B) /teacher/cabinet/ — O'qituvchilar veb-kabineti (Login required)
"""

from django.urls import path
from .views import (
    DailySummaryForDirectorView,
    MarkNotifiedView,
    TeacherCabinetView,
    TodaySchedulesView,
    UploadReportView,
    SupervisorStatsView,
    SupervisorSummariesView,
    SupervisorReportsView,
    SupervisorMarketingView,
    SupervisorTeachersView,
    SupervisorGroupsView,
    SupervisorFeedbacksView,
    TeacherCabinetApiView,
    TeacherCabinetDemoDataView,
    SupervisorMarketingAIAnalyzeView,
    SupervisorMarketingInstructionsView,
    InternalMarketingReportView,
    InternalQuickStatsView,
    InternalPendingMarketingDispatchesView,
    SupervisorInstagramView,
    SupervisorInstagramSyncView,
    SupervisorMarketingSendTelegramView,
)

app_name = "core"

urlpatterns = [
    # =======================================================================
    # A) USERBOT UCHUN ICHKI API
    # =======================================================================

    # Bugungi darslar va xabardor qilinmagan o'qituvchilar
    path(
        "api/internal/today-schedules/",
        TodaySchedulesView.as_view(),
        name="today-schedules",
    ),

    # Xabar yuborilgan darslarni belgilash
    path(
        "api/internal/mark-notified/",
        MarkNotifiedView.as_view(),
        name="mark-notified",
    ),

    # DOCX hisobot yuklash va AI tahlil
    path(
        "api/internal/upload-report/",
        UploadReportView.as_view(),
        name="upload-report",
    ),

    # Direktor uchun AI xulosa
    path(
        "api/internal/daily-summary-for-director/",
        DailySummaryForDirectorView.as_view(),
        name="daily-summary-for-director",
    ),

    # Marketing guruhi uchun Telegram hisobot matni
    path(
        "api/internal/marketing-telegram-report/",
        InternalMarketingReportView.as_view(),
        name="internal-marketing-telegram-report",
    ),

    # Tezkor statistika (KPI) hisobot matni (/stats buyrug'i uchun)
    path(
        "api/internal/quick-stats/",
        InternalQuickStatsView.as_view(),
        name="internal-quick-stats",
    ),

    # Navbatdagi Telegram marketing xabarlarini boshqarish
    path(
        "api/internal/pending-marketing-dispatches/",
        InternalPendingMarketingDispatchesView.as_view(),
        name="internal-pending-marketing-dispatches",
    ),

    # =======================================================================
    # B) O'QITUVCHILAR VEB-KABINETI (Django Template)
    # =======================================================================

    path(
        "teacher/cabinet/",
        TeacherCabinetView.as_view(),
        name="teacher-cabinet",
    ),

    # =======================================================================
    # C) REACT O'QITUVCHI KABINETI API
    # =======================================================================

    path(
        "api/teacher/cabinet/",
        TeacherCabinetApiView.as_view(),
        name="api-teacher-cabinet",
    ),
    path(
        "api/teacher/cabinet/demo-data/",
        TeacherCabinetDemoDataView.as_view(),
        name="api-teacher-cabinet-demo",
    ),

    # =======================================================================
    # D) SUPERVAYZER DASHBOARD API (React Frontend)
    # =======================================================================

    path(
        "api/supervisor/stats/",
        SupervisorStatsView.as_view(),
        name="supervisor-stats",
    ),
    path(
        "api/supervisor/summaries/",
        SupervisorSummariesView.as_view(),
        name="supervisor-summaries",
    ),
    path(
        "api/supervisor/reports/",
        SupervisorReportsView.as_view(),
        name="supervisor-reports",
    ),
    path(
        "api/supervisor/marketing/",
        SupervisorMarketingView.as_view(),
        name="supervisor-marketing",
    ),
    path(
        "api/supervisor/marketing/ai-analyze/",
        SupervisorMarketingAIAnalyzeView.as_view(),
        name="supervisor-marketing-ai-analyze",
    ),
    path(
        "api/supervisor/marketing/instructions/",
        SupervisorMarketingInstructionsView.as_view(),
        name="supervisor-marketing-instructions",
    ),
    path(
        "api/supervisor/marketing/send-telegram/",
        SupervisorMarketingSendTelegramView.as_view(),
        name="supervisor-marketing-send-telegram",
    ),
    path(
        "api/supervisor/instagram/",
        SupervisorInstagramView.as_view(),
        name="supervisor-instagram",
    ),
    path(
        "api/supervisor/instagram/sync/",
        SupervisorInstagramSyncView.as_view(),
        name="supervisor-instagram-sync",
    ),
    path(
        "api/supervisor/teachers/",
        SupervisorTeachersView.as_view(),
        name="supervisor-teachers",
    ),
    path(
        "api/supervisor/groups/",
        SupervisorGroupsView.as_view(),
        name="supervisor-groups",
    ),
    path(
        "api/supervisor/feedbacks/",
        SupervisorFeedbacksView.as_view(),
        name="supervisor-feedbacks",
    ),
]

