from django.contrib import admin, messages
from django import forms
from django.contrib.admin.helpers import ActionForm
from .models import Mapping_Data

# Django adminining standart ActionForm-ni kengaytiramiz
class MappingDataActionForm(ActionForm):
    start_list_id = forms.IntegerField(label="Boshlang'ich list_id", required=False)
    end_list_id = forms.IntegerField(label="Tugash list_id", required=False)

@admin.register(Mapping_Data)
class Mapping_DataAdmin(admin.ModelAdmin):
    list_display = ('list_id', 'category', 'true_answer', 'order')
    search_fields = ('list_id', 'category', 'true_answer')
    list_filter = ('list_id',)
    actions = ['delete_selected_dates', 'delete_range_list_ids']
    action_form = MappingDataActionForm  # Standart ActionForm asosida forma

    def delete_selected_dates(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
    delete_selected_dates.short_description = 'Tanlangan barcha malumotlarni o‘chirish'

    def delete_range_list_ids(self, request, queryset):
        start_list_id = request.POST.get('start_list_id')
        end_list_id = request.POST.get('end_list_id')
        if not start_list_id or not end_list_id:
            self.message_user(
                request,
                "Iltimos, boshlang'ich va tugash list_id qiymatlarini kiriting.",
                level=messages.ERROR
            )
            return
        try:
            start_list_id = int(start_list_id)
            end_list_id = int(end_list_id)
        except ValueError:
            self.message_user(
                request,
                "List_id qiymatlari butun son bo'lishi kerak.",
                level=messages.ERROR
            )
            return

        qs = Mapping_Data.objects.filter(list_id__gte=start_list_id, list_id__lte=end_list_id)
        count = qs.count()
        qs.delete()
        self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
    delete_range_list_ids.short_description = "Berilgan list_id oralig'idagi malumotlarni o'chirish"
