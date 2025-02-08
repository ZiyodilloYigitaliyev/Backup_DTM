from django.contrib import admin
from .models import Mapping_Data

@admin.register(Mapping_Data)
class Mapping_DataAdmin(admin.ModelAdmin):
    # Ro'yxatda ko'rsatiladigan ustunlar
    list_display = ('list_id', 'category', 'true_answer','order')
    # Qidiruv paneli uchun so'zlashuv maydonlari
    search_fields = ('list_id', 'category', 'true_answer')
    # Filter paneli uchun (bir xil list_id ga ega obyektlarni filtrlash)
    list_filter = ('list_id',)

    actions = ['delete_selected_promos']

    # Tanlangan promolarni o'chirish funksiyasi
    def delete_selected_promos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta promo muvaffaqiyatli o'chirildi.")

    delete_selected_promos.short_description = 'Tanlangan barcha Promo kodlarni o‘chirish'