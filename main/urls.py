from django.urls import path

from . import views

urlpatterns = [
    path('send_email/<int:settings_id>/', views.send_email, name='send_email'),
]