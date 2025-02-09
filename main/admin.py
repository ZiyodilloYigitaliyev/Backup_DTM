from django.contrib import admin
from .models import ProcessedData

@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ("id", "list_id", "category", "order", "answer", "status")
    list_filter = ("list_id", "category", "status")
    search_fields = ("list_id", "category", "answer")
    ordering = ("list_id", "order")
    list_per_page = 30