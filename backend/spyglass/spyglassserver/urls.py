from django.urls import path
from . import views_api
from spyglassserver.views.chat import chat
from spyglassserver.views.auth import (
    login,
    register,
    social_authentication,
    reset_password,
    forgot_password,
    verify_email,
)

urlpatterns = [
    path('', chat.chat_page, name='chat_page'),
    path("login/", login.login_user, name="login_user"),
    path("logout/", login.logout_user, name="logout_user"),
    path("register/", register.register, name="register"),
    path("linkedin/", social_authentication.linkedin, name="linkedin"),
    path("reset-password/", reset_password.reset_password, name="reset_password"),
    path(
        "email-verification/",
        verify_email.verify_email,
        name="email_verification",
    ),
    path(
        "forgot-password/",
        forgot_password.forgot_password,
        name="forgot_password",
    ),
    path('api/hello/', views_api.sayHello),
    path('api/get_research_paper_details/', views_api.get_research_paper_details),
    path('api/generate_query_response/', views_api.generate_query_response),
]
