from django.http import JsonResponse, HttpResponseRedirect
from spyglassserver.apps.common import common_fun as cf
from django.template.loader import render_to_string
from django.conf import settings
from spyglassserver import models
from django.utils.http import urlencode
from django.urls import reverse
from django.utils import timezone


def verify_email(request):
    email = request.GET.get("email")
    token = request.GET.get("token")

    if not email or not token:
        return JsonResponse(
            {
                "message": "Invalid request parameters",
                "status": 400,
            }
        )

    spyglass_user = models.SpyglassUser.objects.filter(user__email=email).first()

    if not spyglass_user:
        return JsonResponse(
            {
                "message": "User not found",
                "status": 404,
            }
        )

    # Check if token is expired (tokens valid for 24 hours)
    if (timezone.now() - spyglass_user.created_at).days >= 1:
        return JsonResponse(
            {
                "message": "Verification link expired",
                "status": 410,
            }
        )

    if spyglass_user.token != token:
        return JsonResponse(
            {
                "message": "Invalid verification token",
                "status": 401,
            }
        )

    if spyglass_user.is_verified:
        response = {
            "message": "Email already verified",
            "status": 409,
        }
    else:
        spyglass_user.is_verified = True
        spyglass_user.save()
        response = {
            "message": "Email verification completed",
            "status": 200,
        }

    # Safely construct the redirect URL
    params = {
        'email': email,
        'message': response['message'],
        'status': str(response['status'])
    }
    redirect_url = f"{reverse('login')}?{urlencode(params)}"
    return HttpResponseRedirect(redirect_url)


def send_verification_email(spyglass_user, base_url):
    """Send email verification link to user"""
    token = spyglass_user.token
    verification_url = f"{base_url}/email-verification/?email={spyglass_user.user.email}&token={token}"

    email_body_html = render_to_string(
        "mail/verification_email.html",
        {
            "user": spyglass_user.user,
            "verification_url": verification_url,
            "expiry_hours": 24,
        },
    )

    from django.core.mail import send_mail
    send_mail(
        subject="Verify your SpyGlass AI account",
        message="",  # Empty string as we're sending HTML email
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[spyglass_user.user.email],
        html_message=email_body_html,
        fail_silently=False,
    )


def send_forgot_password_email(spyglass_user, base_url):
    """Send password reset link to user"""
    token = spyglass_user.token
    reset_url = f"{base_url}/reset-password/?email={spyglass_user.user.email}&token={token}"

    email_body_html = render_to_string(
        "mail/forgot_password.html",
        {
            "user": spyglass_user.user,
            "reset_url": reset_url,
            "expiry_hours": 24,
        },
    )

    from django.core.mail import send_mail
    send_mail(
        subject="Reset your SpyGlass AI password",
        message="",  # Empty string as we're sending HTML email
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[spyglass_user.user.email],
        html_message=email_body_html,
        fail_silently=False,
    )