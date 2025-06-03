from django.core.mail import send_mail
import uuid
import string
import secrets
import json
import base64
from spyglassserver import models


def get_random_string(length=36, include_digits=True):
    """Generate a random string of given length"""
    # For tokens and secure identifiers, use UUID
    if length <= 36 and not include_digits:
        return str(uuid.uuid4())[:length]
    
    # For passwords and other strings that need specific requirements
    alphabet = string.ascii_letters + string.digits if include_digits else string.ascii_letters
    while True:
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        if not include_digits or sum(c.isdigit() for c in token) >= 1:
            break
    return token


def send_email_ide(email_body_html, subject, from_email, to_email, cc=None, bcc=None):
    """Send email using Django's send_mail"""
    return send_mail(
        subject=subject,
        message='',  # Empty for HTML emails
        from_email=from_email,
        recipient_list=list(to_email) if isinstance(to_email, (list, set, tuple)) else [to_email],
        html_message=email_body_html,
        fail_silently=False
    )


def get_user_info(spyglass_user):
    """Get encoded user information"""
    user_info = {
        "id": spyglass_user.id,
        "first_name": spyglass_user.user.first_name,
        "last_name": spyglass_user.user.last_name,
        "username": spyglass_user.user.username,
        "email": spyglass_user.user.email,
        "role": spyglass_user.role,
    }
    return b64e(json.dumps(user_info))


def b64e(s):
    """Base64 encode a string"""
    return base64.b64encode(s.encode()).decode()


def b64d(s):
    """Base64 decode a string"""
    return base64.b64decode(s).decode()


def get_valid_participant(test_id, user_token, is_admin=False):
    """Validate and return a participant for a test"""
    if is_admin:
        admin_user = models.SpyglassUser.objects.filter(token=user_token).first()
        if admin_user and models.Test.objects.filter(
            id=test_id, created_by=admin_user
        ).exists():
            return admin_user
    else:
        spyglass_user = models.SpyglassUser.objects.filter(token=user_token).first()
        if spyglass_user and models.UserAssignedTest.objects.filter(
            test_id=test_id, spyglass_user=spyglass_user
        ).exists():
            return spyglass_user
    return None