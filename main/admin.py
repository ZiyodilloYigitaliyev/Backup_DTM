from django.contrib import admin
from .models import Mapping_Data, Result_Data, Data

# Mapping_Data uchun admin sozlamalari
class Mapping_DataAdmin(admin.ModelAdmin):
    list_display = ('list_id', 'category', 'true_answer', 'order')
    list_filter = ('category',)
    search_fields = ('list_id', 'category', 'true_answer', 'order')
    ordering = ('list_id', 'order')

admin.site.register(Mapping_Data, Mapping_DataAdmin)


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
