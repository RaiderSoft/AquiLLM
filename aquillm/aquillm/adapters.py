from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from os import getenv
class NoDefaultAccounts(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False # No email/password signups allowed

class RestrictDomains(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        user = sociallogin.user
        return user.email.split('@')[1] in getenv("ALLOWED_EMAIL_DOMAINS").split(',') or user.email in getenv("ALLOWED_EMAIL_ADDRESSES").split(',')
