from django.urls import path
from .views import *

urlpatterns = [
    path('upload/', ListIDAPIView.as_view(), name='process_image'),
]