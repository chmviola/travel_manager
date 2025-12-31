from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from . import views

urlpatterns = [
    # Rotas de Viagem
    path('viagens/', views.trip_list, name='trip_list'),
    path('viagens/nova/', views.trip_create, name='trip_create'),
    path('viagens/<int:pk>/', views.trip_detail, name='trip_detail'),
    path('viagens/<int:pk>/editar/', views.trip_update, name='trip_update'),
    path('viagens/<int:pk>/excluir/', views.trip_delete, name='trip_delete'),
    
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

    # Dashboard Financeiro
    path('financeiro/', views.financial_dashboard, name='financial_dashboard'),

    path('fix-locations/', views.fix_locations, name='fix_locations'),

    # Rotas de Gestão de Usuários
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
    path('usuarios/<int:pk>/excluir/', views.user_delete, name='user_delete'),

    # Rotas de Perfil do Usuário
    path('profile/', views.profile_view, name='user_profile'),
    path('profile/password/', views.change_password, name='change_password'),

    # Rotas de Configuração de API
    path('config/apis/', views.api_list, name='api_list'),
    path('config/apis/add/', views.api_update, name='api_add'),
    path('config/apis/edit/<int:pk>/', views.api_update, name='api_edit'),
    path('config/apis/delete/<int:pk>/', views.api_delete, name='api_delete'),

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
]