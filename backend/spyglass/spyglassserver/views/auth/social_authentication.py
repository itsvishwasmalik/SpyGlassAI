from spyglassserver import models
from django.contrib.auth.models import User
from django.conf import settings
import requests
from django.contrib.auth import login
from django.http import HttpResponseRedirect, JsonResponse
from spyglassserver.apps.common import common_fun as cf


def linkedin(request):
    if request.method == "GET":
        auth_code = request.GET.get("code")

        if auth_code is not None:
            access_token_link = (
                "https://www.linkedin.com/oauth/v2/accessToken?code="
                + auth_code
                + "&grant_type=authorization_code&client_id="
                + settings.LINKEDIN_AUTH["CLIENT_ID"]
                + "&client_secret="
                + settings.LINKEDIN_AUTH["CLIENT_SECRET"]
                + "&redirect_uri="
                + settings.LINKEDIN_AUTH["REDIRECT_URI"]
                + "&scope=r_liteprofile+r_emailaddress"
            )
            response = requests.get(access_token_link).json()

            access_token = response["access_token"]

            basic_profile_generation_link = (
                "https://api.linkedin.com/v2/me?projection=(id,firstName,lastName,emailAddress,profilePicture(displayImage~:playableStreams))&oauth2_access_token="
                + access_token
            )
            response = requests.get(basic_profile_generation_link).json()

            first_name, last_name = (
                response["firstName"]["localized"]["en_US"],
                response["lastName"]["localized"]["en_US"],
            )

            # Saved for future Use
            response["profilePicture"]["displayImage~"]["elements"][3]["identifiers"][
                0
            ]["identifier"]

            email_generation_link = (
                "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))&oauth2_access_token="
                + access_token
            )
            email = (
                requests.get(email_generation_link)
                .json()["elements"][0]["handle~"]["emailAddress"]
                .lower()
            )

            response = register_social_user(
                request, first_name=first_name, last_name=last_name, email=email
            )

            return HttpResponseRedirect("/")

        else:
            return HttpResponseRedirect("/login/")

    else:
        scopes = "%20".join(settings.LINKEDIN_AUTH["SCOPE"])
        link = (
            "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id="
            + settings.LINKEDIN_AUTH["CLIENT_ID"]
            + "&redirect_uri="
            + settings.LINKEDIN_AUTH["REDIRECT_URI"]
            + "&state=foobar&scope="
            + scopes
        )
        return JsonResponse({"redirectURL": link})


def register_social_user(request, first_name, last_name, email):
    existing_user = User.objects.filter(email=email).first()
    user = existing_user

    if not user:
        new_user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email,
            password=cf.get_random_string(16),
        )

        spyglass_user = models.SpyglassUser()
        spyglass_user.user = new_user
        spyglass_user.role = "ADMIN"
        spyglass_user.token = cf.get_random_string(36)
        spyglass_user.is_verified = True
        spyglass_user.save()

        user = new_user

    # Log in the user
    login(request, user)

    return JsonResponse({"message": "Login Successful"})