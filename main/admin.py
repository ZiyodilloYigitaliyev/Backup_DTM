from django.contrib import admin
from .models import ProcessedData


@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'x_coord', 'y_coord', 'data_type', 'category')  # Admin panelda ko‘rinadigan ustunlar
    list_filter = ('category', 'data_type')  # Filtrlash imkoniyati
    search_fields = ('data_type', 'category')  # Qidirish maydoni
    ordering = ('id',)  # ID bo‘yicha tartiblash
