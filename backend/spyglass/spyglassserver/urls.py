from django.urls import path
from . import views_api

urlpatterns = [
    path('hello/', views_api.sayHello),
    path('get_research_paper_details/', views_api.get_research_paper_details),
]
