from django.urls import path

from . import views

urlpatterns = [
	path('virtual-card', views.virtual_card, name='virtual_card'),
]

