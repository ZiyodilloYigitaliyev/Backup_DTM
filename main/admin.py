from django.contrib import admin
from .models import allCategory, ProcessedData

@admin.register(allCategory)
class AllCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category')  # Jadval ustunlarini ko‘rsatish
    search_fields = ('category',)  # Qidirish imkoniyati
    ordering = ('id',)  # ID bo‘yicha tartiblash

@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'x_coord', 'y_coord', 'data_type', 'category')  # Admin panelda ko‘rinadigan ustunlar
    list_filter = ('category', 'data_type')  # Filtrlash imkoniyati
    search_fields = ('data_type', 'category')  # Qidirish maydoni
    ordering = ('id',)  # ID bo‘yicha tartiblash
