from django.contrib import admin
from .models import Result_Data, Data
from django.utils.html import format_html
from .models import PDFResult

# Data modeli uchun inline admin - Result_Data bilan bog'liq Data yozuvlarini bir joyda ko'rish uchun
class DataInline(admin.TabularInline):
    model = Data
    extra = 0  # Qo'shimcha bo'sh formalarni ko'rsatmaslik uchun
    fields = ('order', 'value', 'category', 'status')
    readonly_fields = ('category', 'status')  
    # Eslatma: category va status avtomatik hisoblanadigan maydonlar bo'lsa, ularni read-only qilishingiz mumkin.


# Result_Data modeli uchun admin sozlamalari
class Result_DataAdmin(admin.ModelAdmin):
    list_display = ('list_id', 'image_url', 'phone')
    list_filter = ('list_id', 'phone')
    search_fields = ('list_id', 'phone')
    inlines = [DataInline]  # Result_Data-ga tegishli Data yozuvlarini inline ko'rsatish

admin.site.register(Result_Data, Result_DataAdmin)


# Data modeli uchun admin sozlamalari
class DataAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'order', 'value', 'category', 'status')
    list_filter = ('status', 'category')
    # user_id orqali qidirish uchun, uni Result_Data dagi list_id orqali qidiramiz
    search_fields = ('user_id__list_id', 'value', 'category')
    ordering = ('user_id', 'order')

admin.site.register(Data, DataAdmin)

@admin.register(PDFResult)
class PDFResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'phone', 'pdf_link', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_id', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('pdf_url', 'created_at')

    def pdf_link(self, obj):
        """
        Agar pdf_url mavjud bo‘lsa, admin panelida bosish orqali PDF-ni ochish uchun link ko‘rsatamiz.
        """
        if obj.pdf_url:
            return format_html('<a href="{}" target="_blank">PDF-ni ochish</a>', obj.pdf_url)
        return "-"
    pdf_link.short_description = "PDF Fayl URL"