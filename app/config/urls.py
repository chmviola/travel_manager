from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from core import views as core_views
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- [IMPORTANTE] MÍDIA EM PRIMEIRO LUGAR ---
    # Colocamos no topo para garantir que nenhuma outra rota intercepte
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),

    # Admin
    path('admin/', admin.site.urls),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Home
    path('', core_views.home, name='home'),

    # Core Apps (Isso tem que ficar por último pois pode ter rotas genéricas)
    path('', include('core.urls')),
]