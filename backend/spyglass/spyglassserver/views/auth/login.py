from spyglassserver import models
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.http import JsonResponse
from django.shortcuts import render
from spyglassserver.views.auth import verify_email
from django.db.models import Q
from django.contrib.auth.models import User


def login_user(request):
    if request.method == "POST":
        user_data = request.POST
        username = user_data.get("username", "").lower().strip()
        password = user_data.get("password", "")
        request_domain = request.get_host()

        if not username or not password:
            return JsonResponse({"message": "Username and password are required"}, status=400)

        user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        if not user:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

        authenticated_user = authenticate(
            username=user.username,
            password=password,
        )

        if not authenticated_user:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

        spyglass_user = models.SpyglassUser.objects.filter(user=user).first()
        if not spyglass_user:
            return JsonResponse({"message": "Account not found"}, status=404)

        if not spyglass_user.is_verified:
            try:
                verify_email.send_verification_email(spyglass_user, request_domain)
            except Exception:
                return JsonResponse(
                    {"message": "Unable to send verification email. Please try again later."},
                    status=500,
                )
            return JsonResponse(
                {"message": "Account not verified. Verification email has been sent."},
                status=403
            )

        login(request, authenticated_user)
        return JsonResponse({
            "message": "Login successful",
            "redirectURL": "/"
        })

    # GET request
    if request.user.is_authenticated:
        return redirect("/")

    return render(request, "auth/login.html")


def logout_user(request):
    login_url = "/login/"
    logout(request)
    return redirect(login_url)