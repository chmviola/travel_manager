"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from core import views as core_views
from django.views.static import serve

# --- IMPORTS OBRIGATÓRIOS PARA MÍDIA ---
from django.conf import settings
from django.conf.urls.static import static
# ---------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota de Login customizada
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Rota da Home (Dashboard)
    path('', core_views.home, name='home'),

    # Inclui as URLs do app Core
    path('', include('core.urls')),

    # --- SOLUÇÃO DE MÍDIA (FORÇADA) ---
    # Esta rota intercepta qualquer URL começando com /media/ e serve o arquivo
    # Funciona mesmo com DEBUG=False ou atrás do Nginx Proxy Manager
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# (Opcional) Mantém o static padrão para CSS/JS se o DEBUG funcionar um dia
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)