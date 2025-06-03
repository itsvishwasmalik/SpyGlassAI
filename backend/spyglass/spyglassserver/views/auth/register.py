from django.contrib.auth.models import User
from spyglassserver import models
from django.shortcuts import render, redirect
from django.http import JsonResponse
from spyglassserver.views.auth import verify_email
from spyglassserver.apps.common import common_fun as cf


def register(request):
    if request.method == "POST":
        user_data = request.POST

        email = user_data["email"].lower()

        existing_user = User.objects.filter(email=email).exists()
        request_domain = request.get_host()

        if existing_user:
            return JsonResponse(
                {
                    "message": "Already Registered",
                },
                status=409,
            )

        user = User.objects.create_user(
            first_name=user_data["firstName"],
            last_name=user_data["lastName"],
            email=email,
            password=user_data["password"],
            username=email,
        )

        spyglass_user = models.SpyglassUser()
        spyglass_user.user = user
        spyglass_user.role = "ADMIN"  # admin or student
        spyglass_user.token = cf.get_random_string(36)
        spyglass_user.is_verified = False
        spyglass_user.save()

        try:
            verify_email.send_verification_email(spyglass_user, request_domain)
        except Exception:
            return JsonResponse(
                {
                    "message": "Unable to send verification email. Please try again later.",
                },
                status=500,
            )

        return JsonResponse({"message": "Email sent successfully"})

    else:
        if not request.user.is_authenticated:
            return render(request, "auth/register.html")

        return redirect("/")