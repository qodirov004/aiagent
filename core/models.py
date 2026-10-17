"""
core/models.py — O'quv markazi boshqaruv tizimi modellari.

Barcha modellar:
  - Teacher: O'qituvchilar profili (Telegram, telefon, fanlar)
  - Group: Guruhlar (jadval, xona, o'qituvchi)
  - Student: O'quvchilar (guruh, holat)
  - LessonSchedule: Kunlik dars jadvallari
  - TeacherDailyReport: O'qituvchi kunlik hisoboti (docx → AI tahlil)
  - WeeklyFeedback: Haftalik o'quvchi bahosi
  - MarketingMetric: Marketing kunlik ko'rsatkichlari
  - DirectorDailySummary: Direktor uchun AI xulosasi
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ===========================================================================
# Abstrakt baza model — barcha modellarda created_at / updated_at bo'ladi
# ===========================================================================

class TimeStampedModel(models.Model):
    """Barcha modellar uchun created_at va updated_at maydonlarini qo'shuvchi abstrakt model."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqti",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqti",
    )

    class Meta:
        abstract = True


# ===========================================================================
# 1. Teacher — O'qituvchi profili
# ===========================================================================

class Teacher(TimeStampedModel):
    """O'qituvchi profili — Django User modeliga OneToOne bog'lanadi."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="Foydalanuvchi",
    )
    telegram_username = models.CharField(
        max_length=100,
        unique=True,
        help_text="@ belgisisiz username (masalan: teacher_ali)",
        verbose_name="Telegram username",
    )
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram Chat ID",
        help_text="Shaxsiy xabar yuborish uchun chat ID",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Telefon raqami",
    )
    subjects = models.CharField(
        max_length=255,
        help_text="Masalan: Python Backend, Foundation",
        verbose_name="Fanlar",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faolmi?",
    )

    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.telegram_username} ({self.subjects})"


# ===========================================================================
# 2. Group — O'quv guruhi
# ===========================================================================

class Group(TimeStampedModel):
    """O'quv guruhi — o'qituvchi, jadval va xona ma'lumotlari."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Guruh nomi",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        related_name="groups",
        verbose_name="O'qituvchi",
    )
    schedule_days = models.JSONField(
        default=list,
        help_text="Hafta kunlari: ['mon', 'wed', 'fri']",
        verbose_name="Dars kunlari",
    )
    lesson_start_time = models.TimeField(
        verbose_name="Dars boshlanish vaqti",
    )
    lesson_end_time = models.TimeField(
        verbose_name="Dars tugash vaqti",
    )
    room_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Xona raqami",
    )

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ===========================================================================
# 3. Student — O'quvchi
# ===========================================================================

class Student(TimeStampedModel):
    """O'quvchi — guruhga biriktirilgan, holat boshqaruvi."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("frozen", "Frozen"),
        ("left", "Left"),
    ]

    full_name = models.CharField(
        max_length=255,
        verbose_name="To'liq ismi",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name="Guruh",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefon raqami",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="Holati",
    )

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} — {self.group.name}"


# ===========================================================================
# 4. LessonSchedule — Kunlik dars jadvali
# ===========================================================================

class LessonSchedule(TimeStampedModel):
    """Kunlik dars jadvali — har bir guruh/sana/vaqt kombinatsiyasi uchun yagona yozuv."""

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Guruh",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="O'qituvchi",
    )
    date = models.DateField(
        db_index=True,
        verbose_name="Sana",
    )
    start_time = models.TimeField(
        verbose_name="Boshlanish vaqti",
    )
    is_notified = models.BooleanField(
        default=False,
        help_text="Userbot guruhda ogohlantirdimi?",
        verbose_name="Xabardor qilindimi?",
    )

    class Meta:
        verbose_name = "Dars jadvali"
        verbose_name_plural = "Dars jadvallari"
        unique_together = ("group", "date", "start_time")
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.group.name} — {self.date} {self.start_time}"


# ===========================================================================
# 5. TeacherDailyReport — Kunlik DOCX hisobot (AI tahlil)
# ===========================================================================

class TeacherDailyReport(TimeStampedModel):
    """
    O'qituvchi kunlik hisoboti.
    DOCX fayldan olingan matn Gemini AI orqali tahlil qilinadi.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="daily_reports",
        verbose_name="O'qituvchi",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_reports",
        verbose_name="Guruh",
    )
    date = models.DateField(
        db_index=True,
        verbose_name="Hisobot sanasi",
    )
    raw_file = models.FileField(
        upload_to="reports/docx/%Y/%m/%d/",
        verbose_name="DOCX fayl",
    )
    raw_text = models.TextField(
        help_text="Docx fayldan ajratib olingan sof matn",
        verbose_name="Sof matn",
    )
    attendance_rate = models.FloatField(
        default=0.0,
        help_text="Qatnashish foizi: 0-100",
        verbose_name="Qatnashish (%)",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    topic = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Mavzu",
    )
    homework_rate = models.FloatField(
        default=0.0,
        help_text="Uyga vazifa topshirganlar foizi",
        verbose_name="Uyga vazifa (%)",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    issues = models.JSONField(
        default=list,
        help_text="Darsda yuzaga kelgan muammolar ro'yxati",
        verbose_name="Muammolar",
    )
    ai_summary = models.TextField(
        blank=True,
        help_text="Gemini AI xulosasi",
        verbose_name="AI xulosasi",
    )

    class Meta:
        verbose_name = "Kunlik hisobot"
        verbose_name_plural = "Kunlik hisobotlar"
        ordering = ["-date", "teacher__user__first_name"]

    def __str__(self):
        teacher_name = self.teacher.user.get_full_name() or self.teacher.telegram_username
        return f"{teacher_name} — {self.date}"


# ===========================================================================
# 6. WeeklyFeedback — Haftalik o'quvchi bahosi
# ===========================================================================

class WeeklyFeedback(TimeStampedModel):
    """
    O'qituvchi tomonidan har bir o'quvchiga beriladigan haftalik baho.
    Har bir o'quvchi uchun bir haftada faqat bitta yozuv.
    """

    PERFORMANCE_CHOICES = [
        ("excellent", "A'lo"),
        ("good", "Yaxshi"),
        ("average", "O'rtacha"),
        ("bad", "Yomon"),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="weekly_feedbacks",
        verbose_name="O'qituvchi",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="weekly_feedbacks",
        verbose_name="O'quvchi",
    )
    week_start_date = models.DateField(
        db_index=True,
        help_text="Dushanba sanasi",
        verbose_name="Hafta boshi (Dushanba)",
    )
    performance_status = models.CharField(
        max_length=20,
        choices=PERFORMANCE_CHOICES,
        verbose_name="O'zlashtirish darajasi",
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Qisqa izoh",
    )

    class Meta:
        verbose_name = "Haftalik baho"
        verbose_name_plural = "Haftalik baholar"
        unique_together = ("student", "week_start_date")
        ordering = ["-week_start_date", "student__full_name"]

    def __str__(self):
        return (
            f"{self.student.full_name} — {self.week_start_date} — "
            f"{self.get_performance_status_display()}"
        )


# ===========================================================================
# 7. MarketingMetric — Kunlik marketing ko'rsatkichlari & AI Tahlili
# ===========================================================================

class MarketingMetric(TimeStampedModel):
    """Kunlik marketing ko'rsatkichlari — leadlar, reklama xarajati, raqobatchilar va AI tahlili."""

    date = models.DateField(
        unique=True,
        db_index=True,
        verbose_name="Sana",
    )
    leads_count = models.IntegerField(
        default=0,
        verbose_name="Leadlar soni",
    )
    ad_spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Reklama xarajati (so'm)",
    )
    cost_per_lead = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="1 ta lead narxi (CAC)",
        help_text="Avtomatik hisoblanadi (Xarajat / Leadlar)",
    )
    competitor_analysis_notes = models.TextField(
        blank=True,
        help_text="Raqobatchilar yangiliklari, aksiyalari yoki narxlari haqida ma'lumot",
        verbose_name="Raqobatchilar haqida ma'lumot",
    )
    ai_analysis = models.TextField(
        blank=True,
        verbose_name="AI Marketing Tahlili va Xulosasi",
        help_text="O'qitilgan qoidalar asosida Gemini chiqargan tahlil",
    )
    ai_recommendations = models.TextField(
        blank=True,
        verbose_name="AI Strategik Maslahatlari va Harakat Rejasi",
        help_text="Direktor va marketolog uchun aniq amaliy maslahatlar (Action Points)",
    )

    class Meta:
        verbose_name = "Marketing ko'rsatkich"
        verbose_name_plural = "Marketing ko'rsatkichlar"
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        if self.leads_count and self.leads_count > 0 and self.ad_spend:
            self.cost_per_lead = round(float(self.ad_spend) / float(self.leads_count), 2)
        else:
            self.cost_per_lead = 0.00
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Marketing — {self.date} (Leadlar: {self.leads_count}, CAC: {self.cost_per_lead:,.0f} so'm)"


# ===========================================================================
# 7.1. MarketingAIInstruction — AI ni o'qitish va strategik bilimlar bazasi
# ===========================================================================

class MarketingAIInstruction(TimeStampedModel):
    """
    Marketing AI Agentini o'qitish bazasi (Prompt Knowledge Base).
    Admin panel orqali o'quv markazning afzalliklari, narxlari,
    raqobatchilarga qarshi strategiyalari va tavsiya berish qoidalari kiritiladi.
    Gemini barcha xulosalarni ushbu qoidalar asosida shakllantiradi.
    """

    CATEGORY_CHOICES = [
        ("usp", "🎯 Markazimiz afzalliklari va Kurslarimiz (USP)"),
        ("competitor", "⚔️ Raqobatchilarga qarshi strategiya va qoidalar"),
        ("budget", "💰 Byudjet va Xarajat mezonlari (CAC / ROI)"),
        ("recommendation", "💡 Maslahat va Tavsiya berish talablari"),
        ("general", "📋 Umumiy marketing ko'rsatmalari"),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="Ko'rsatma / Qoida mavzusi",
        help_text="Masalan: 'Markazimiz kurslari narxlari va kafolati' yoki 'Najot Ta'lim aksiyasiga javob'",
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="usp",
        verbose_name="Kategoriya",
    )
    instruction_text = models.TextField(
        verbose_name="AI ga o'rgatiladigan qoida va bilimlar matni",
        help_text="Gemini ushbu matnni to'liq o'rganib oladi va xulosa chiqarishda unga amal qiladi.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faolmi?",
        help_text="O'chirilgan qoidalar AI ga yuborilmaydi.",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Tartib raqami",
    )

    class Meta:
        verbose_name = "AI ni o'qitish ko'rsatmasi"
        verbose_name_plural = "AI ni o'qitish (Marketing Qoidalari)"
        ordering = ["order", "-created_at"]

    def __str__(self):
        status = "🟢" if self.is_active else "⚪"
        return f"{status} [{self.get_category_display().split()[0]}] {self.title}"



# ===========================================================================
# 8. DirectorDailySummary — Supervayzer (Gemini) xulosasi
# ===========================================================================

class DirectorDailySummary(TimeStampedModel):
    """
    Direktor uchun tayyorlangan kunlik xulosa.
    Gemini AI tuzadi, Userbot Telegram orqali direktorga yuboradi.
    """

    date = models.DateField(
        unique=True,
        db_index=True,
        verbose_name="Sana",
    )
    summary_markdown = models.TextField(
        help_text="Direktor uchun tayyorlangan Markdown hisobot",
        verbose_name="Xulosa (Markdown)",
    )
    is_sent_to_director = models.BooleanField(
        default=False,
        verbose_name="Direktorga yuborilganmi?",
    )

    class Meta:
        verbose_name = "Direktor xulosasi"
        verbose_name_plural = "Direktor xulosalari"
        ordering = ["-date"]

    def __str__(self):
        status = "✅ Yuborilgan" if self.is_sent_to_director else "⏳ Kutilmoqda"
        return f"Xulosa — {self.date} [{status}]"


# ===========================================================================
# 9. InstagramConfig — Instagram akkaunt integratsiyasi va sozlamalari
# ===========================================================================

class InstagramConfig(TimeStampedModel):
    """
    Instagram akkaunt sozlamalari (Meta Graph API / Web Sync).
    O'quv markazining Instagram akkauntini ulaydi va statistikani tortadi.
    """

    account_name = models.CharField(
        max_length=150,
        default="EduCenter Asosiy Sahifasi",
        verbose_name="Profil nomi / Izoh",
        help_text="Masalan: 'EduCenter Asosiy Sahifasi'",
    )
    instagram_username = models.CharField(
        max_length=100,
        default="diamond_academy_uz",
        verbose_name="Instagram Username (@ belgisisiz)",
        help_text="Masalan: 'diamond_academy_uz'",
    )
    instagram_account_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Meta Instagram Account ID",
        help_text="Meta Graph API Business Account ID (ixtiyoriy)",
    )
    access_token = models.TextField(
        blank=True,
        verbose_name="Meta Access Token (Graph API)",
        help_text="Uzoq muddatli Meta Graph API tokeni (agar bo'lmasa, web sync ishlatiladi)",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faolmi?",
    )
    auto_sync = models.BooleanField(
        default=True,
        verbose_name="Avtomatik kunlik sinxronizatsiya?",
        help_text="Har kuni avtomatik ravishda statistika tortilsinmi?",
    )

    class Meta:
        verbose_name = "Instagram akkaunt sozlamasi"
        verbose_name_plural = "Instagram akkaunt sozlamalari"

    def __str__(self):
        return f"@{self.instagram_username} ({self.account_name})"


# ===========================================================================
# 10. InstagramMetric — Kunlik Instagram statistikasi
# ===========================================================================

class InstagramMetric(TimeStampedModel):
    """
    Instagram akkauntining kunlik ko'rsatkichlari:
    obunachilar, o'sish, postlar, qamrov (reach), profil ko'rishlar.
    """

    account = models.ForeignKey(
        InstagramConfig,
        on_delete=models.CASCADE,
        related_name="metrics",
        null=True,
        blank=True,
        verbose_name="Instagram Akkaunt",
    )
    date = models.DateField(
        unique=True,
        db_index=True,
        verbose_name="Sana",
    )
    followers_count = models.IntegerField(
        default=0,
        verbose_name="Jami Obunachilar soni",
    )
    following_count = models.IntegerField(
        default=0,
        verbose_name="Kuzatilayotganlar soni",
    )
    media_count = models.IntegerField(
        default=0,
        verbose_name="Jami Postlar / Reels soni",
    )
    new_followers_today = models.IntegerField(
        default=0,
        verbose_name="Bugungi yangi obunachilar o'sishi",
        help_text="Kechagi kunga nisbatan o'sish (+/-)",
    )
    reach_count = models.IntegerField(
        default=0,
        verbose_name="Kunlik Qamrov (Reach)",
        help_text="Profil va postlarni ko'rgan noyob foydalanuvchilar soni",
    )
    impressions_count = models.IntegerField(
        default=0,
        verbose_name="Kunlik Ko'rishlar (Impressions)",
    )
    profile_views = models.IntegerField(
        default=0,
        verbose_name="Profilga tashriflar (Profile views)",
    )
    sync_source = models.CharField(
        max_length=50,
        default="Avtomatik Sinxronizatsiya",
        verbose_name="Sinxronizatsiya usuli",
    )

    class Meta:
        verbose_name = "Instagram statistikasi"
        verbose_name_plural = "Instagram statistikasi"
        ordering = ["-date"]

    def __str__(self):
        sign = "+" if self.new_followers_today >= 0 else ""
        return f"Instagram — {self.date} ({self.followers_count:,} obunachi, {sign}{self.new_followers_today} bugun)"


# ===========================================================================
# 11. MarketingTelegramDispatch — Telegram Marketing guruhiga xabar yuborish
# ===========================================================================

class MarketingTelegramDispatch(TimeStampedModel):
    """
    Marketing hisobotlarini Telegram guruhiga jo'natish logi va navbati.
    Dashboard orqali yoki avtomatik scheduler orqali yuborilganda qayd qilinadi.
    """
    date = models.DateField(default=timezone.now, verbose_name="Sana")
    message_text = models.TextField(verbose_name="Hisobot matni (Markdown)")
    chat_id = models.CharField(max_length=100, blank=True, verbose_name="Telegram Guruh ID")
    is_sent = models.BooleanField(default=False, verbose_name="Yuborildimi?")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Yuborilgan vaqt")
    error_message = models.TextField(blank=True, verbose_name="Xatolik xabari")

    class Meta:
        verbose_name = "Marketing Telegram yuborish"
        verbose_name_plural = "Marketing Telegram yuborishlar"
        ordering = ["-created_at"]

    def __str__(self):
        status_icon = "✅" if self.is_sent else "⏳"
        return f"{status_icon} Marketing xabar — {self.date} ({self.created_at.strftime('%H:%M')})"


