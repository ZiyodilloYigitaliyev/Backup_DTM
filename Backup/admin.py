from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from .models import Mapping_Data

# ActionForm orqali qo'shimcha input maydonlarni yaratamiz
class MappingDataActionForm(ActionForm):
    start_list_id = forms.IntegerField(label="Boshlang'ich list_id", required=True)
    end_list_id = forms.IntegerField(label="Tugash list_id", required=True)

@admin.register(Mapping_Data)
class Mapping_DataAdmin(admin.ModelAdmin):
    list_display = ('list_id', 'category', 'true_answer', 'order')
    search_fields = ('list_id', 'category', 'true_answer')
    list_filter = ('list_id',)
    actions = ['delete_selected_dates', 'delete_range_list_ids']
    action_form = MappingDataActionForm

    def changelist_view(self, request, extra_context=None):
        """
        Agar POST so'rovida action 'delete_range_list_ids' deb kelayotgan bo'lsa 
        va hech qanday obyekt tanlanmagan bo'lsa, dummy (soxta) obyekt qo'shamiz.
        Bu admin actionlari uchun zarur, chunki standart holda kamida bitta obyekt tanlash talab qilinadi.
        """
        if (
            request.method == 'POST' and
            request.POST.get('action') == 'delete_range_list_ids' and
            not request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ):
            dummy = self.model.objects.all().values_list('pk', flat=True)[:1]
            if dummy:
                request.POST = request.POST.copy()
                request.POST.setlist(admin.ACTION_CHECKBOX_NAME, [str(dummy[0])])
        return super().changelist_view(request, extra_context=extra_context)

    def delete_selected_dates(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
    delete_selected_dates.short_description = 'Tanlangan barcha malumotlarni o‘chirish'

    def delete_range_list_ids(self, request, queryset):
        """
        Foydalanuvchi kiritgan start_list_id va end_list_id asosida
        shu oralig'idagi barcha Mapping_Data obyektlarini topib, ularni o'chiradi.
        """
        start_list_id = request.POST.get('start_list_id')
        end_list_id = request.POST.get('end_list_id')
        try:
            start_list_id = int(start_list_id)
            end_list_id = int(end_list_id)
        except (ValueError, TypeError):
            self.message_user(
                request,
                "Iltimos, list_id qiymatlari butun son bo'lishini ta'minlang.",
                level=messages.ERROR
            )
            return

        qs = Mapping_Data.objects.filter(list_id__gte=start_list_id, list_id__lte=end_list_id)
        count = qs.count()
        qs.delete()
        self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
    delete_range_list_ids.short_description = "Berilgan list_id oralig'idagi malumotlarni o'chirish"
