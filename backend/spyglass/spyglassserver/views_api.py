from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth.models import User

@api_view(["GET"])
def sayHello(request):
    return JsonResponse({"message": "Hello World!"})