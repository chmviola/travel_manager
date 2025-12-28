from django.conf import settings

def version_context(request):
    """
    Disponibiliza a variável {{ app_version }} em todos os templates.
    """
    return {
        'app_version': getattr(settings, 'APP_VERSION', '1.0.0')
    }