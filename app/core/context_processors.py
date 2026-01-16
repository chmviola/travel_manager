from django.conf import settings

def export_version(request):
    """Torna a versão do app disponível em todos os templates."""
    # print(f"--- DEBUG CONTEXT: Enviando versão {settings.APP_VERSION} para o template ---")
    return {
        'app_version': settings.APP_VERSION
    }