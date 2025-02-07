from django.urls import path
from .views import *

urlpatterns = [
    path('upload/', ResultAPIView.as_view(), name='process_image'),
]