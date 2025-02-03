from django.urls import path
from .views import ProcessImageView

urlpatterns = [
    path('upload/', ProcessImageView.as_view(), name='process_image'),
]