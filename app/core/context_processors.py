from django.conf import settings

def export_version(request):
    """Torna a versão do app disponível em todos os templates."""
    return {
        'app_version': settings.APP_VERSION
    }