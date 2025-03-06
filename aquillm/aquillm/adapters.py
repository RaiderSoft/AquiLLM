from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from os import getenv
from .models import EmailWhitelist
class NoDefaultAccounts(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False # No email/password signups allowed

class RestrictDomains(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        user = sociallogin.user
        allowed_domains = getenv("ALLOWED_EMAIL_DOMAINS")
        if allowed_domains is None:
            return False
        allowed_emails = getenv("ALLOWED_EMAIL_ADDRESSES")
        if allowed_emails is None:
            return False
        return (user.email.split('@')[1] in allowed_domains.split(',') or
                user.email in allowed_emails.split(",") or 
                user.email in EmailWhitelist.objects.values_list('email', flat=True))
