from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import AccessLog

# Função auxiliar para pegar o IP real (mesmo atrás do Docker/Proxy)
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Sinal para logar o login do usuário
@receiver(user_logged_in)
def log_login(sender, user, request, **kwargs):
    if request:
        AccessLog.objects.create(
            user=user,
            action='LOGIN',
            ip_address=get_client_ip(request),
            session_key=request.session.session_key
        )

# Sinal para logar o logout do usuário
@receiver(user_logged_out)
def log_logout(sender, user, request, **kwargs):
    if request:
        AccessLog.objects.create(
            user=user,
            action='LOGOUT',
            ip_address=get_client_ip(request),
            session_key=request.session.session_key
        )