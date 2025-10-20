from django.urls import path
from . import views

urlpatterns = [
    path('', views.FrontendView.as_view(), name='frontend'),
]