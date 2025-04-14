from django.urls import path
from . import views_api

urlpatterns = [
    path('hello/', views_api.sayHello),
]
