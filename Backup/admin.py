from django import forms
from django.contrib import admin, messages
from django.template.response import TemplateResponse
from .models import Mapping_Data

# Foydalanuvchidan boshlang'ich va tugash list_id qiymatlarini olish uchun forma
class DeleteRangeForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    start_list_id = forms.IntegerField(label="Boshlang'ich list_id")
    end_list_id = forms.IntegerField(label="Tugash list_id")

@admin.register(Mapping_Data)
class Mapping_DataAdmin(admin.ModelAdmin):
    list_display = ('list_id', 'category', 'true_answer', 'order')
    search_fields = ('list_id', 'category', 'true_answer')
    list_filter = ('list_id',)
    actions = ['delete_selected_dates', 'delete_range_list_ids']

    # Avvalgi tanlangan elementlarni o'chirish actioni
    def delete_selected_dates(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
    delete_selected_dates.short_description = 'Tanlangan barcha malumotlarni o‘chirish'

    # Yangi: Berilgan list_id oralig'iga mos keluvchi malumotlarni o'chirish actioni
    def delete_range_list_ids(self, request, queryset):
        if 'apply' in request.POST:
            form = DeleteRangeForm(request.POST)
            if form.is_valid():
                start_list_id = form.cleaned_data['start_list_id']
                end_list_id = form.cleaned_data['end_list_id']
                # Shu oralig'idagi barcha malumotlarni tanlab olish
                qs = Mapping_Data.objects.filter(list_id__gte=start_list_id, list_id__lte=end_list_id)
                count = qs.count()
                qs.delete()
                self.message_user(request, f"{count} ta malumot muvaffaqiyatli o'chirildi.")
                return None
        else:
            form = DeleteRangeForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

        context = {
            'objects': queryset,
            'form': form,
            'title': "List_id oralig'idagi malumotlarni o'chirish",
            'action': 'delete_range_list_ids',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, "admin/delete_range.html", context)
    delete_range_list_ids.short_description = "Berilgan list_id oralig'iga mos keluvchi malumotlarni o'chirish"
