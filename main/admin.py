from django.contrib import admin
from .models import ImageData, Coordinate

class CoordinateInline(admin.TabularInline):
    model = Coordinate
    extra = 0

class ImageDataAdmin(admin.ModelAdmin):
    list_display = ("image_url", "get_coordinates", "created_at")  # `created_at` maydoni mavjud
    search_fields = ("image_url",)
    list_filter = ("created_at",)  # `created_at`ni filter sifatida qo‘shamiz
    inlines = [CoordinateInline]

    def get_coordinates(self, obj):
        return ", ".join([f"({coord.x}, {coord.y})" for coord in obj.coordinates.all()])
    
    get_coordinates.short_description = "Koordinatalar"

    def save_model(self, request, obj, form, change):
        # Eski image va koordinatalarni o‘chiramiz
        ImageData.objects.all().delete()
        super().save_model(request, obj, form, change)

admin.site.register(ImageData, ImageDataAdmin)

from .models import result
@admin.register(result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'phone', 'total_score', 'file')
    search_fields = ('student_id', 'phone')