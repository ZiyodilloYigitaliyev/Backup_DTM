from django.contrib import admin
from .models import *


@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'x_coord', 'y_coord', 'data_type', 'category')  # Admin panelda ko‘rinadigan ustunlar
    list_filter = ('category', 'data_type')  # Filtrlash imkoniyati
    search_fields = ('data_type', 'category')  # Qidirish maydoni
    ordering = ('id',)  # ID bo‘yicha tartiblash
# ProcessedTest uchun admin klassi
class ProcessedTestAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'phone_number', 'file_url', 'uploaded_at', 'total_score')  # Qaysi ustunlarni ko'rsatishni tanlang
    search_fields = ('student_id', 'phone_number')  # Qidiruv uchun ustunlar
    list_filter = ('uploaded_at', 'total_score')  # Filtrlar
    ordering = ('-uploaded_at',)  # Tartiblash (so'nggi qo'shilganlar birinchi bo'ladi)

# ProcessedTestResult uchun admin klassi
class ProcessedTestResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'student_answer', 'is_correct', 'processed_at', 'score')  # Qaysi ustunlarni ko'rsatishni tanlang
    search_fields = ('student__student_id', 'student_answer')  # Qidiruv uchun ustunlar
    list_filter = ('is_correct', 'processed_at')  # Filtrlar
    ordering = ('-processed_at',)  # Tartiblash (so'nggi qo'shilganlar birinchi bo'ladi)

# Modellarni admin paneliga qo'shish
admin.site.register(ProcessedTest, ProcessedTestAdmin)
admin.site.register(ProcessedTestResult, ProcessedTestResultAdmin)