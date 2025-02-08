from django.contrib import admin
from .models import *

# Register your models here.
class Mapping_DataAdmin(admin.ModelAdmin):
    actions = ['delete_selected_promos']

    # Tanlangan promolarni o'chirish funksiyasi
    def delete_selected_promos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta promo muvaffaqiyatli o'chirildi.")

    delete_selected_promos.short_description = 'Tanlangan barcha Promo kodlarni o‘chirish'

# Mapping_Data modelini Mapping_DataAdmin bilan ro'yxatga olish
admin.site.register(Mapping_Data, Mapping_DataAdmin)