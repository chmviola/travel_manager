from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from . import views
# --- ADICIONE ESTA LINHA ABAIXO ---
from django.contrib.auth import views as auth_views
from core.forms import CustomPasswordResetForm 
# ----------------------------------

urlpatterns = [
    # Rotas de Viagem
    path('viagens/', views.trip_list, name='trip_list'),
    path('viagens/nova/', views.trip_create, name='trip_create'),
    path('viagens/<int:pk>/', views.trip_detail, name='trip_detail'),
    path('viagens/<int:pk>/editar/', views.trip_update, name='trip_update'),
    path('viagens/<int:pk>/excluir/', views.trip_delete, name='trip_delete'),
    path('trips/<int:pk>/pdf/', views.trip_detail_pdf, name='trip_detail_pdf'),
    path('viagens/<int:pk>/calendario/', views.trip_calendar, name='trip_calendar'),
    path('sobre/', views.about_view, name='about'),
    
    # Rotas de Itens
    path('viagens/<int:trip_id>/adicionar-item/', views.trip_item_create, name='trip_item_create'),
    path('itens/<int:pk>/editar/', views.trip_item_update, name='trip_item_update'),
    path('itens/<int:pk>/excluir/', views.trip_item_delete, name='trip_item_delete'),
    
    # Rotas Financeiras
    path('viagens/<int:trip_id>/adicionar-gasto/', views.trip_expense_create, name='trip_expense_create'),
    path('itens/<int:item_id>/financeiro/', views.trip_item_expense_manage, name='trip_item_expense_manage'),

    # Rotas para Gestão de Gastos (Genéricas)
    path('gasto/<int:pk>/editar/', views.expense_update, name='expense_update'),
    path('gasto/<int:pk>/excluir/', views.expense_delete, name='expense_delete'),

    # Rotas de Anexos (Uploads)
    path('itens/<int:item_id>/anexos/', views.trip_item_attachments, name='trip_item_attachments'),
    path('anexos/<int:pk>/excluir/', views.attachment_delete, name='attachment_delete'),

    # Rota para os Links (URLs)
    path('item/<int:item_id>/link/', views.trip_item_set_link, name='trip_item_set_link'),

    # Dashboard Financeiro
    path('financeiro/', views.financial_dashboard, name='financial_dashboard'),
    path('financeiro/api/chart-data/', views.financial_chart_api, name='financial_chart_api'),
    path('fix-locations/', views.fix_locations, name='fix_locations'),
    path('gastos/<int:pk>/alternar-pagamento/', views.trip_expense_toggle_paid, name='trip_expense_toggle_paid'),

    # Rotas de Gestão de Usuários
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
    path('usuarios/<int:pk>/excluir/', views.user_delete, name='user_delete'),

    # Rotas para Importação / Exportação Google Calender
    path('viagens/<int:trip_id>/export-ics/', views.trip_export_ics, name='trip_export_ics'),
    path('viagens/<int:trip_id>/import-ics/', views.trip_import_ics, name='trip_import_ics'),

    # Rotas de Perfil do Usuário
    path('profile/', views.profile_view, name='user_profile'),
    path('profile/password/', views.change_password, name='change_password'),

    # Rotas de Configuração de API
    path('config/apis/', views.api_list, name='api_list'),
    path('config/apis/add/', views.api_update, name='api_add'),
    path('config/apis/edit/<int:pk>/', views.api_update, name='api_edit'),
    path('config/apis/delete/<int:pk>/', views.api_delete, name='api_delete'),

    # Rotas de Configuração de API
    path('config/apis/', views.config_api_list, name='config_api_list'),
    path('config/apis/new/', views.config_api_handle, name='config_api_create'), # Rota para criar
    path('config/apis/<int:pk>/edit/', views.config_api_handle, name='config_api_edit'), # Rota para editar
    path('config/apis/<int:pk>/delete/', views.config_api_delete, name='config_api_delete'),
    
    # Rota de Configuração de E-mail
    path('config/email/', views.email_settings_view, name='email_settings'),

    # Rota de Logs de Acesso
    path('config/logs/', views.access_logs_view, name='access_logs'),

    # CHECKLIST
    path('trips/<int:trip_id>/checklist/', views.checklist_view, name='checklist_view'),
    path('trips/<int:trip_id>/checklist/generate/', views.checklist_generate, name='checklist_generate'),
    path('trips/<int:trip_id>/checklist/add/', views.checklist_add_item, name='checklist_add_item'),
    path('trips/<int:trip_id>/checklist/clear/', views.checklist_clear_completed, name='checklist_clear_completed'),
    path('trips/<int:trip_id>/checklist/pdf/', views.checklist_pdf, name='checklist_pdf'),
    path('checklist/toggle/<int:item_id>/', views.checklist_toggle, name='checklist_toggle'),
    path('checklist/delete/<int:item_id>/', views.checklist_delete_item, name='checklist_delete_item'),

    # Rotas de Funcionalidades com IA
    path('trips/<int:trip_id>/generate-itinerary/', views.trip_generate_itinerary, name='trip_generate_itinerary'),
    path('trips/<int:trip_id>/generate-insights/', views.trip_generate_insights, name='trip_generate_insights'),

    # Rotas de Colaboração
    path('trips/<int:trip_id>/share/', views.trip_share, name='trip_share'),
    path('trips/<int:trip_id>/unshare/<int:user_id>/', views.trip_remove_share, name='trip_remove_share'),
    
    # Rotas de Galeria de Fotos da Viagem
    path('trips/<int:trip_id>/gallery/', views.trip_gallery, name='trip_gallery'),
    path('trips/photo/<int:photo_id>/delete/', views.trip_photo_delete, name='trip_photo_delete'),

# --- RECUPERAÇÃO DE SENHA (CORRIGIDO) ---
    
    # 1. Solicitar recuperação (Digitar E-mail)
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        form_class=CustomPasswordResetForm  # <--- IMPORTANTE: Usa seu form que lê do banco
    ), name="password_reset"),

    # 2. Aviso de e-mail enviado
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html"
    ), name="password_reset_done"),

    # 3. Link que chega no e-mail (Digitar nova senha)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html"
    ), name="password_reset_confirm"),

    # 4. Sucesso final
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html"
    ), name="password_reset_complete"),

    # Rota para o CHANGELOG
    path('changelog/', views.changelog_view, name='changelog'),
]