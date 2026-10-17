"""
core/serializers.py — DRF serializerlar.

Ichki API (UserBot <-> Django) uchun serializerlar:
  - TodayScheduleSerializer: Bugungi dars jadvallarini qaytarish
  - MarkNotifiedSerializer: is_notified yangilash uchun
  - UploadReportSerializer: DOCX fayl va telegram username qabul qilish
  - DirectorSummarySerializer: Direktor xulosasini qaytarish
"""

from rest_framework import serializers
from .models import (
    Teacher,
    Group,
    Student,
    LessonSchedule,
    TeacherDailyReport,
    WeeklyFeedback,
    MarketingMetric,
    MarketingAIInstruction,
    InstagramConfig,
    InstagramMetric,
    DirectorDailySummary,
)


class TodayScheduleSerializer(serializers.ModelSerializer):
    """
    Bugungi kungi dars jadvalini UserBot uchun qaytaradi.
    Nested ma'lumotlar: o'qituvchi telegram username va guruh nomi.
    """

    teacher_telegram_username = serializers.CharField(
        source="teacher.telegram_username",
        read_only=True,
    )
    teacher_full_name = serializers.SerializerMethodField()
    group_name = serializers.CharField(
        source="group.name",
        read_only=True,
    )
    room_number = serializers.CharField(
        source="group.room_number",
        read_only=True,
    )

    class Meta:
        model = LessonSchedule
        fields = [
            "id",
            "group_name",
            "teacher_telegram_username",
            "teacher_full_name",
            "date",
            "start_time",
            "is_notified",
            "room_number",
        ]
        read_only_fields = fields

    def get_teacher_full_name(self, obj) -> str:
        return obj.teacher.user.get_full_name() or obj.teacher.telegram_username


class MarkNotifiedSerializer(serializers.Serializer):
    """
    UserBot yuborgan darslarni is_notified=True qilish uchun.
    schedule_ids — ro'yxat (list[int]).
    """

    schedule_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        help_text="Xabardor qilingan LessonSchedule ID'lari ro'yxati",
    )


class UploadReportSerializer(serializers.Serializer):
    """
    UserBot guruhdan ushlab olgan DOCX faylni yuborish uchun.
    telegram_username — faylni yuborgan o'qituvchining usernamesi.
    file — DOCX fayl.
    """

    telegram_username = serializers.CharField(
        max_length=100,
        help_text="Faylni yuborgan o'qituvchining Telegram username'i (@ belgisisiz)",
    )
    file = serializers.FileField(
        help_text=".docx formatdagi hisobot fayli",
    )

    def validate_file(self, value):
        """Faqat .docx fayllarni qabul qilish."""
        if not value.name.lower().endswith(".docx"):
            raise serializers.ValidationError(
                "Faqat .docx formatdagi fayllar qabul qilinadi."
            )

        # Maksimal fayl hajmi: 10 MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Fayl hajmi 10 MB dan oshmasligi kerak. "
                f"Joriy hajm: {value.size / 1024 / 1024:.1f} MB"
            )

        return value


class DirectorSummarySerializer(serializers.ModelSerializer):
    """Direktor xulosasini qaytarish uchun serializer."""

    class Meta:
        model = DirectorDailySummary
        fields = [
            "id",
            "date",
            "summary_markdown",
            "is_sent_to_director",
            "created_at",
        ]
        read_only_fields = fields


class TeacherDailyReportSerializer(serializers.ModelSerializer):
    """Kunlik hisobot ma'lumotlari — admin va qayta ko'rish uchun."""

    teacher_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherDailyReport
        fields = [
            "id",
            "teacher_name",
            "group_name",
            "date",
            "attendance_rate",
            "topic",
            "homework_rate",
            "issues",
            "ai_summary",
            "created_at",
        ]
        read_only_fields = fields

    def get_teacher_name(self, obj) -> str:
        return obj.teacher.user.get_full_name() or obj.teacher.telegram_username

    def get_group_name(self, obj) -> str:
        return obj.group.name if obj.group else "—"


class MarketingMetricSerializer(serializers.ModelSerializer):
    """Marketing ko'rsatkichlari uchun serializer."""

    class Meta:
        model = MarketingMetric
        fields = [
            "id",
            "date",
            "leads_count",
            "ad_spend",
            "cost_per_lead",
            "competitor_analysis_notes",
            "ai_analysis",
            "ai_recommendations",
            "created_at",
            "updated_at",
        ]


class MarketingAIInstructionSerializer(serializers.ModelSerializer):
    """AI ni o'qitish ko'rsatmalari serializeri."""

    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = MarketingAIInstruction
        fields = [
            "id",
            "title",
            "category",
            "category_display",
            "instruction_text",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        ]



class InstagramConfigSerializer(serializers.ModelSerializer):
    """Instagram akkaunt sozlamalari serializeri."""

    class Meta:
        model = InstagramConfig
        fields = [
            "id",
            "account_name",
            "instagram_username",
            "instagram_account_id",
            "access_token",
            "is_active",
            "auto_sync",
            "created_at",
            "updated_at",
        ]


class InstagramMetricSerializer(serializers.ModelSerializer):
    """Instagram statistikasi serializeri."""

    account_username = serializers.CharField(source="account.instagram_username", read_only=True)

    class Meta:
        model = InstagramMetric
        fields = [
            "id",
            "account",
            "account_username",
            "date",
            "followers_count",
            "following_count",
            "media_count",
            "new_followers_today",
            "reach_count",
            "impressions_count",
            "profile_views",
            "sync_source",
            "created_at",
            "updated_at",
        ]


class StudentSerializer(serializers.ModelSerializer):
    """O'quvchi ma'lumotlari serializeri."""

    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "full_name",
            "phone",
            "status",
            "group",
            "group_name",
            "created_at",
        ]


class GroupSerializer(serializers.ModelSerializer):
    """Guruhlar ro'yxati serializeri."""

    teacher_name = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "teacher",
            "teacher_name",
            "schedule_days",
            "lesson_start_time",
            "lesson_end_time",
            "room_number",
            "students_count",
            "created_at",
        ]

    def get_teacher_name(self, obj) -> str:
        if obj.teacher:
            return obj.teacher.user.get_full_name() or obj.teacher.telegram_username
        return "Biriktirilmagan"

    def get_students_count(self, obj) -> int:
        return obj.students.filter(status="active").count()


class TeacherSerializer(serializers.ModelSerializer):
    """O'qituvchilar serializeri."""

    full_name = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    active_students_count = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            "id",
            "full_name",
            "telegram_username",
            "telegram_chat_id",
            "phone",
            "subjects",
            "is_active",
            "groups_count",
            "active_students_count",
            "created_at",
        ]

    def get_full_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.telegram_username

    def get_groups_count(self, obj) -> int:
        return obj.groups.count()

    def get_active_students_count(self, obj) -> int:
        return Student.objects.filter(group__teacher=obj, status="active").count()


class WeeklyFeedbackSerializer(serializers.ModelSerializer):
    """Haftalik baho serializeri."""

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    group_name = serializers.CharField(source="student.group.name", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    performance_display = serializers.CharField(source="get_performance_status_display", read_only=True)

    class Meta:
        model = WeeklyFeedback
        fields = [
            "id",
            "student",
            "student_name",
            "group_name",
            "teacher",
            "teacher_name",
            "week_start_date",
            "performance_status",
            "performance_display",
            "comment",
            "created_at",
        ]

    def get_teacher_name(self, obj) -> str:
        return obj.teacher.user.get_full_name() or obj.teacher.telegram_username

