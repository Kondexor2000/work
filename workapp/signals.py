from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import LoginLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # może zawierać listę IP oddzielonych przecinkami
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    if ip:
        LoginLog.objects.create(user=user, ip_address=ip)