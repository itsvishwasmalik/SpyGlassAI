from django.shortcuts import redirect, render
from django.http import JsonResponse
from spyglassserver import models
from django.utils import timezone
import uuid


def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        token = request.POST.get("token", "").strip()
        password = request.POST.get("password", "")
        
        if not all([email, token, password]):
            return JsonResponse(
                {"message": "Missing required fields"}, 
                status=400
            )

        spyglass_user = models.SpyglassUser.objects.filter(user__email=email).first()

        if not spyglass_user:
            return JsonResponse(
                {"message": "Invalid or expired reset link"}, 
                status=403
            )

        # Check if token has expired (24 hour validity)
        if (timezone.now() - spyglass_user.created_at).days >= 1:
            return JsonResponse(
                {"message": "Password reset link has expired"}, 
                status=410
            )

        if spyglass_user.token != token:
            return JsonResponse(
                {"message": "Invalid or expired reset link"}, 
                status=403
            )

        # Update user password
        user = spyglass_user.user
        user.set_password(password)
        user.save()

        # Generate new token to invalidate the used reset link
        spyglass_user.token = str(uuid.uuid4())
        spyglass_user.save()

        return JsonResponse(
            {
                "message": "Password has been reset successfully",
                "redirect": "/login"
            }
        )

    # GET request
    if request.user.is_authenticated:
        return redirect("/")

    email = request.GET.get("email")
    token = request.GET.get("token")
    
    if not email or not token:
        return redirect("/forgot-password")
        
    return render(request, "auth/reset_password.html", {
        "email": email,
        "token": token
    })