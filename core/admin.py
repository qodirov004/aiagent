from django.contrib import admin, messages
from django.utils.html import format_html
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
    MarketingTelegramDispatch,
    DirectorDailySummary,
)
from .gemini_services import generate_marketing_ai_analysis
from .instagram_services import sync_instagram_metrics, format_marketing_telegram_report

# Admin panel sarlavhalarini modernlashtirish
admin.site.site_header = "EduCenter Admin Boshqaruv Paneli"
admin.site.site_title = "EduCenter Admin"
admin.site.index_title = "O'quv Markazi Tizim Boshqaruvi"


@admin.register(MarketingAIInstruction)
class MarketingAIInstructionAdmin(admin.ModelAdmin):
    """AI ni o'qitish (Knowledge Base) admin paneli."""

    list_display = ("title", "category_badge", "is_active", "order", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("title", "instruction_text")
    list_editable = ("is_active", "order")
    actions = ["load_default_instructions", "activate_all", "deactivate_all"]

    @admin.display(description="Kategoriya")
    def category_badge(self, obj):
        colors = {
            "usp": "#10b981",
            "competitor": "#f43f5e",
            "budget": "#f59e0b",
            "recommendation": "#6366f1",
            "general": "#06b6d4",
        }
        color = colors.get(obj.category, "#64748b")
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_category_display(),
        )

    @admin.action(description="📚 Standart tavsiya qoidalarini bazaga yuklash")
    def load_default_instructions(self, request, queryset):
        defaults = [
            (
                "Markazimiz afzalliklari va kafolati (USP)",
                "usp",
                "1. Kurslarimiz amaliyotga yo'naltirilgan (Real loyihalar portfoliosi bilan).\n"
                "2. IT kurslarimiz narxi o'rtacha 800,000 - 1,200,000 so'm/oy.\n"
                "3. Eng yaxshi 10% bitiruvchilarga ishga joylashish kafolati yoki stajirovka taqdim etiladi.\n"
                "4. Darslar zamonaviy kompyuterlar bilan jihozlangan 204 va 301 xonalarda o'tiladi.",
                1,
            ),
            (
                "Raqobatchilar chegirma berganda qanday chora ko'rish",
                "competitor",
                "Raqobatchilar (masalan: Najot Ta'lim, PDP, Mohirdev, Astrum) katta chegirma e'lon qilganda, "
                "biz narx bo'yicha pastga tushmaymiz! Buning o'rniga:\n"
                "- Individual mentorlik va kichik guruhlar (12 kishilik) afzalligini ta'kidlaymiz.\n"
                "- Bepul sinov darsi (Open Lesson) va bepul mentor konsultasiyasi taklifini bildiramiz.\n"
                "- Har bir o'quvchiga mentor tomonidan kunlik feedback berilishini urg'ulaymiz.",
                2,
            ),
            (
                "Byudjet va 1 ta Lead narxi (CAC) mezonlari",
                "budget",
                "1. 1 ta lead narxi (CAC) 20,000 so'mdan past bo'lsa — A'lo (byudjetni 20-30% oshirish mumkin).\n"
                "2. Lead narxi 20,000 - 45,000 so'm oralig'ida bo'lsa — Yaxshi va barqaror.\n"
                "3. Agar lead narxi 50,000 so'mdan oshsa — Xavfli! Darhol target auditoriyani toraytirish, "
                "kreativlarni yangilash va 'charchagan' reklamalarni to'xtatish kerak.\n"
                "4. Agar kunlik lead 10 tadan kam bo'lsa — yangi marketing kanallari (Telegram kanallar, blogerlar) jalb qilinsin.",
                3,
            ),
            (
                "Direktor va Marketolog uchun tavsiya berish qoidalari",
                "recommendation",
                "Har bir tavsiyangiz (Action Point) aniq va o'lchanadigan bo'lsin.\n"
                "- Quruq gaplar yozmang, balki aniq nima qilish kerakligini ayting: qaysi kanaldagi reklamani to'xtatish, "
                "qanday taklif (offer) tayyorlash, qaysi guruhga tezroq qabul ochish.\n"
                "- O'zbek tilida, do'stona va professional biznes tahlil uslubida yozing.",
                4,
            ),
        ]
        created_count = 0
        for title, cat, text, order in defaults:
            obj, created = MarketingAIInstruction.objects.get_or_create(
                title=title,
                defaults={"category": cat, "instruction_text": text, "order": order, "is_active": True},
            )
            if created:
                created_count += 1
        self.message_user(request, f"{created_count} ta standart AI o'qitish qoidasi muvaffaqiyatli yuklandi!", messages.SUCCESS)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_username", "phone", "subjects", "is_active")
    list_filter = ("is_active",)
    search_fields = ("user__first_name", "user__last_name", "telegram_username", "phone")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "lesson_start_time", "lesson_end_time", "room_number")
    list_filter = ("teacher",)
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "group", "phone", "status")
    list_filter = ("status", "group")
    search_fields = ("full_name", "phone")


@admin.register(LessonSchedule)
class LessonScheduleAdmin(admin.ModelAdmin):
    list_display = ("group", "teacher", "date", "start_time", "is_notified")
    list_filter = ("is_notified", "date", "teacher")
    date_hierarchy = "date"


@admin.register(TeacherDailyReport)
class TeacherDailyReportAdmin(admin.ModelAdmin):
    list_display = ("teacher", "group", "date", "attendance_rate", "homework_rate", "topic")
    list_filter = ("date", "teacher")
    date_hierarchy = "date"
    readonly_fields = ("raw_text", "ai_summary")


@admin.register(WeeklyFeedback)
class WeeklyFeedbackAdmin(admin.ModelAdmin):
    list_display = ("student", "teacher", "week_start_date", "performance_status")
    list_filter = ("performance_status", "week_start_date", "teacher")
    search_fields = ("student__full_name",)


@admin.register(MarketingMetric)
class MarketingMetricAdmin(admin.ModelAdmin):
    list_display = ("date", "leads_count", "ad_spend_display", "cost_per_lead_display", "ai_status_badge", "updated_at")
    list_filter = ("date",)
    date_hierarchy = "date"
    readonly_fields = ("cost_per_lead", "ai_analysis_html", "ai_recommendations_html", "created_at", "updated_at")
    actions = ["generate_ai_analysis_action"]

    fieldsets = (
        ("📊 Asosiy Ko'rsatkichlar", {
            "fields": ("date", "leads_count", "ad_spend", "cost_per_lead")
        }),
        ("⚔️ Raqobatchilar Yangiliklari", {
            "fields": ("competitor_analysis_notes",),
            "description": "Raqobatchilarning bugungi aksiyalari, narxlari yoki bozor yangiliklarini kiriting."
        }),
        ("🤖 Gemini AI Tahlili va Xulosasi", {
            "fields": ("ai_analysis_html", "ai_analysis"),
            "classes": ("collapse",)
        }),
        ("💡 Gemini AI Strategik Maslahatlari (Action Points)", {
            "fields": ("ai_recommendations_html", "ai_recommendations"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Xarajat")
    def ad_spend_display(self, obj):
        return f"{obj.ad_spend:,.0f} so'm"

    @admin.display(description="Lead narxi (CAC)")
    def cost_per_lead_display(self, obj):
        if not obj.cost_per_lead or obj.cost_per_lead == 0:
            return "—"
        color = "#10b981" if obj.cost_per_lead <= 35000 else ("#f59e0b" if obj.cost_per_lead <= 50000 else "#f43f5e")
        return format_html(
            '<strong style="color: {};">{:,.0f} so\'m</strong>',
            color,
            obj.cost_per_lead,
        )

    @admin.display(description="AI Tahlil")
    def ai_status_badge(self, obj):
        if obj.ai_analysis:
            return format_html('<span style="background: #10b981; color: white; padding: 2px 7px; border-radius: 6px; font-size: 11px; font-weight: bold;">✅ Tahlil tayyor</span>')
        return format_html('<span style="background: #64748b; color: white; padding: 2px 7px; border-radius: 6px; font-size: 11px;">⏳ Tahlil qilinmagan</span>')

    @admin.display(description="AI Tahlili (Ko'rinishi)")
    def ai_analysis_html(self, obj):
        if not obj.ai_analysis:
            return "Hali AI tahlili generatsiya qilinmagan. Quyidagi saqlash tugmasini bosganda yoki action orqali yarating."
        return format_html(
            '<div style="background: #161f30; color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #6366f1; white-space: pre-wrap; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto;">{}</div>',
            obj.ai_analysis
        )

    @admin.display(description="AI Maslahatlari (Ko'rinishi)")
    def ai_recommendations_html(self, obj):
        if not obj.ai_recommendations:
            return "Hali AI maslahatlari generatsiya qilinmagan."
        return format_html(
            '<div style="background: #161f30; color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #10b981; white-space: pre-wrap; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto;">{}</div>',
            obj.ai_recommendations
        )

    @admin.action(description="🤖 Tanlangan sanalar uchun AI tahlil va maslahatlarni generatsiya qilish")
    def generate_ai_analysis_action(self, request, queryset):
        success_count = 0
        error_count = 0
        for metric in queryset:
            try:
                generate_marketing_ai_analysis(metric, auto_save=True)
                success_count += 1
            except Exception as e:
                error_count += 1
        if success_count > 0:
            self.message_user(request, f"✅ {success_count} ta sana uchun AI tahlil va tavsiyalar muvaffaqiyatli tuzildi!", messages.SUCCESS)
        if error_count > 0:
            self.message_user(request, f"⚠️ {error_count} ta yozuvda xatolik yuz berdi.", messages.ERROR)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Agar AI tahlili bo'sh bo'lsa va leadlar yoki raqobatchi kiritilgan bo'lsa, avtomatik generatsiya qilish
        if not obj.ai_analysis and (obj.leads_count > 0 or obj.competitor_analysis_notes):
            try:
                generate_marketing_ai_analysis(obj, auto_save=True)
                self.message_user(request, "🤖 Gemini AI o'qitilgan qoidalar asosida marketing tahlili va tavsiyalarni tuzib berdi!", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"⚠️ AI tahlil xatosi: {str(e)}", messages.WARNING)


@admin.register(DirectorDailySummary)
class DirectorDailySummaryAdmin(admin.ModelAdmin):
    list_display = ("date", "is_sent_to_director")
    list_filter = ("is_sent_to_director",)
    date_hierarchy = "date"
    readonly_fields = ("summary_markdown",)


@admin.register(InstagramConfig)
class InstagramConfigAdmin(admin.ModelAdmin):
    """Instagram akkaunt sozlamalari admin paneli."""

    list_display = ("account_name", "username_display", "is_active", "auto_sync", "updated_at")
    list_editable = ("is_active", "auto_sync")
    search_fields = ("account_name", "instagram_username")
    actions = ["sync_now_action"]

    @admin.display(description="Instagram Profil")
    def username_display(self, obj):
        return format_html(
            '<a href="https://instagram.com/{}" target="_blank" style="color: #ec4899; font-weight: bold; text-decoration: none;">📸 @{}</a>',
            obj.instagram_username,
            obj.instagram_username,
        )

    @admin.action(description="🔄 Tanlangan akkauntlar statistikasini hoziroq tortish")
    def sync_now_action(self, request, queryset):
        count = 0
        for config in queryset:
            try:
                sync_instagram_metrics(config=config)
                count += 1
            except Exception as e:
                self.message_user(request, f"Xatolik (@{config.instagram_username}): {str(e)}", messages.ERROR)
        if count > 0:
            self.message_user(request, f"✅ {count} ta akkaunt statistikasi yangilandi!", messages.SUCCESS)


@admin.register(InstagramMetric)
class InstagramMetricAdmin(admin.ModelAdmin):
    """Instagram kunlik statistikasi admin paneli."""

    list_display = ("date", "account", "followers_display", "growth_display", "reach_count", "media_count", "sync_source")
    list_filter = ("date", "account")
    date_hierarchy = "date"
    actions = ["refresh_sync_action"]

    @admin.display(description="Obunachilar")
    def followers_display(self, obj):
        return f"{obj.followers_count:,} ta"

    @admin.display(description="Bugungi o'sish")
    def growth_display(self, obj):
        if obj.new_followers_today > 0:
            return format_html('<span style="color: #10b981; font-weight: bold;">+{} 🟢</span>', obj.new_followers_today)
        elif obj.new_followers_today < 0:
            return format_html('<span style="color: #f43f5e; font-weight: bold;">{} 🔴</span>', obj.new_followers_today)
        return format_html('<span style="color: #94a3b8;">0</span>')

    @admin.action(description="🔄 Tanlangan kunlar statistikasini qayta yangilash")
    def refresh_sync_action(self, request, queryset):
        for metric in queryset:
            sync_instagram_metrics(config=metric.account, target_date=metric.date)
        self.message_user(request, "✅ Tanlangan kunlar statistikasi qayta sinxronlandi!", messages.SUCCESS)


@admin.register(MarketingTelegramDispatch)
class MarketingTelegramDispatchAdmin(admin.ModelAdmin):
    """Marketing hisobotini Telegram guruhga yuborish tarixi."""

    list_display = ("date", "status_display", "chat_id", "sent_at", "created_at")
    list_filter = ("is_sent", "date")
    date_hierarchy = "date"
    readonly_fields = ("date", "message_text", "chat_id", "is_sent", "sent_at", "error_message")

    @admin.display(description="Holat")
    def status_display(self, obj):
        if obj.is_sent:
            return format_html('<span style="background: #10b981; color: white; padding: 2px 7px; border-radius: 6px; font-weight: bold;">✅ Yuborilgan</span>')
        return format_html('<span style="background: #f59e0b; color: white; padding: 2px 7px; border-radius: 6px; font-weight: bold;">⏳ Kutilmoqda</span>')



