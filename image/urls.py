from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recommend_imgs/', views.recommend_imgs, name='recommend'),
]
