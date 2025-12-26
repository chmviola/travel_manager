from django.urls import path
from . import views

urlpatterns = [
    path('viagens/', views.trip_list, name='trip_list'),
    path('viagens/nova/', views.trip_create, name='trip_create'),
    path('viagens/<int:pk>/', views.trip_detail, name='trip_detail'),
    
    # Nova rota para adicionar item. Note que passamos o trip_id
    path('viagens/<int:trip_id>/adicionar-item/', views.trip_item_create, name='trip_item_create'),
    path('viagens/<int:trip_id>/adicionar-gasto/', views.trip_expense_create, name='trip_expense_create'),
    
    # CRUD Viagem
    path('viagens/<int:pk>/editar/', views.trip_update, name='trip_update'),
    path('viagens/<int:pk>/excluir/', views.trip_delete, name='trip_delete'),
    
    # CRUD Itens
    path('itens/<int:pk>/editar/', views.trip_item_update, name='trip_item_update'),
    path('itens/<int:pk>/excluir/', views.trip_item_delete, name='trip_item_delete'),

    path('itens/<int:item_id>/financeiro/', views.trip_item_expense_manage, name='trip_item_expense_manage'),
]