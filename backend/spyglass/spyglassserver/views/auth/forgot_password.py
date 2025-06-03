from spyglassserver import models
from django.shortcuts import redirect, render
from django.utils import timezone
from django.http import JsonResponse
from .verify_email import send_forgot_password_email
import uuid


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        
        if not email:
            return JsonResponse(
                {"message": "Email is required"}, 
                status=400
            )

        spyglass_user = models.SpyglassUser.objects.filter(user__email=email).first()

        if not spyglass_user:
            # Use same message as success for security
            return JsonResponse(
                {"message": "If an account exists with this email, a password reset link will be sent."},
                status=200
            )

        # Update token and timestamp
        spyglass_user.token = str(uuid.uuid4())
        spyglass_user.created_at = timezone.now()
        spyglass_user.save()

        try:
            send_forgot_password_email(
                spyglass_user, 
                request.build_absolute_uri('/')[:-1]  # Get base URL without trailing slash
            )
        except Exception as e:
            return JsonResponse(
                {
                    "message": "Unable to send password reset email. Please try again later.",
                },
                status=502,
            )

        return JsonResponse(
            {
                "message": "If an account exists with this email, a password reset link will be sent.",
            }
        )

    # GET request
    if request.user.is_authenticated:
        return redirect("/")
        
    return render(request, "auth/forgot_password.html")