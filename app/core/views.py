from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Trip, TripItem, Expense, TripAttachment  
from .forms import TripForm, TripItemForm, ExpenseForm, AttachmentForm
from .utils import get_exchange_rate # Importe a função nova
from django.db.models import Sum
from collections import defaultdict # Para agrupar dados manualmente
import json # Para enviar dados ao JS

@login_required
def home(request):
    # Vamos reaproveitar a home para mostrar um resumo,
    # mas por enquanto ela renderiza o dashboard
    return render(request, 'dashboard.html')

@login_required
def trip_list(request):
    """
    Lista todas as viagens do usuário logado.
    """
    # O filtro user=request.user garante a segurança dos dados
    trips = Trip.objects.filter(user=request.user).order_by('-start_date')
    
    return render(request, 'trips/trip_list.html', {'trips': trips})

@login_required
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            # commit=False cria o objeto na memória mas não salva no banco ainda
            trip = form.save(commit=False)
            # Atribuímos o dono da viagem automaticamente
            trip.user = request.user
            # Agora sim, salvamos
            trip.save()
            return redirect('trip_list')
    else:
        form = TripForm()
    
    return render(request, 'trips/trip_form.html', {'form': form})

@login_required
def trip_detail(request, pk):
    """
    Exibe os detalhes da viagem, o mapa e a timeline de itens.
    """
    # get_object_or_404 garante que retorna erro se o ID não existir
    # e o filtro user=request.user impede que um usuário veja viagem de outro
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    # Buscamos os itens ordenados por data para a timeline
    items = trip.items.all().order_by('start_datetime')

    expenses = trip.expenses.all()
    
    # Lógica de Conversão
    total_converted_brl = 0
    # Cache simples para não bater na API várias vezes para a mesma moeda na mesma página
    rates_cache = {}

    # Iteramos sobre os gastos para calcular individualmente
    for expense in expenses:
        currency = expense.currency
        
        # Busca cotação (com cache simples para não repetir chamadas)
        if currency not in rates_cache:
            rates_cache[currency] = get_exchange_rate(currency)
        
        rate = rates_cache[currency]
        
        # Calcula o valor em BRL deste item específico
        val_brl = float(expense.amount) * rate
        
        # ATENÇÃO: Criamos um atributo temporário 'converted_value' no objeto expense
        # Isso não salva no banco, existe apenas aqui na memória para exibir na tela
        expense.converted_value = val_brl
        
        # Soma ao total geral
        total_converted_brl += val_brl
    
    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'items': items,
        'expenses': expenses, # Agora os objetos expenses têm o campo .converted_value
        'total_spent_brl': total_converted_brl,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def trip_item_create(request, trip_id):
    # Busca a viagem e garante que pertence ao usuário logado
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    if request.method == 'POST':
        form = TripItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.trip = trip # Vincula o item à viagem atual
            item.save()
            # Redireciona de volta para a tela de detalhes da viagem
            return redirect('trip_detail', pk=trip.id)
    else:
        form = TripItemForm()
    
    return render(request, 'trips/trip_item_form.html', {'form': form, 'trip': trip})

@login_required
def trip_expense_create(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, trip_id=trip.id)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = trip
            expense.save()
            return redirect('trip_detail', pk=trip.id)
    else:
        form = ExpenseForm(trip_id=trip.id)
    
    return render(request, 'trips/expense_form.html', {'form': form, 'trip': trip})

# --- VIEWS PARA VIAGEM (TRIP) ---

@login_required
def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            return redirect('trip_detail', pk=trip.id)
    else:
        form = TripForm(instance=trip)
    return render(request, 'trips/trip_form.html', {'form': form, 'edit_mode': True})

@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    if request.method == 'POST':
        trip.delete()
        return redirect('trip_list')
    return render(request, 'trips/trip_confirm_delete.html', {'trip': trip})

# --- VIEWS PARA ITENS (TRIP ITEM) ---

@login_required
def trip_item_update(request, pk):
    # Buscamos o item
    item = get_object_or_404(TripItem, pk=pk, trip__user=request.user)

    if request.method == 'POST':
        form = TripItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('trip_detail', pk=item.trip.id)
    else:
        form = TripItemForm(instance=item)
    
    # IMPORTANTE: Passar 'trip': item.trip para o template
    return render(request, 'trips/trip_item_form.html', {
        'form': form,
        'edit_mode': True,
        'trip': item.trip
        })

@login_required
def trip_item_delete(request, pk):
    item = get_object_or_404(TripItem, pk=pk, trip__user=request.user)
    trip_id = item.trip.id
    if request.method == 'POST':
        item.delete()
        return redirect('trip_detail', pk=trip_id)
    return render(request, 'trips/trip_item_confirm_delete.html', {'item': item})

@login_required
def trip_item_expense_manage(request, item_id):
    """
    Verifica se o item já tem um gasto vinculado.
    - Se TIVER: Abre o formulário de EDIÇÃO desse gasto.
    - Se NÃO TIVER: Abre o formulário de CRIAÇÃO já com o item selecionado.
    """
    item = get_object_or_404(TripItem, pk=item_id, trip__user=request.user)
    
    # Tenta pegar o primeiro gasto vinculado a este item
    # (Assumimos aqui uma relação de 1 para 1 para simplificar o botão da timeline)
    existing_expense = item.related_expenses.first()
    
    if request.method == 'POST':
        if existing_expense:
            form = ExpenseForm(request.POST, instance=existing_expense, trip_id=item.trip.id)
        else:
            form = ExpenseForm(request.POST, trip_id=item.trip.id)
            
        if form.is_valid():
            expense = form.save(commit=False)
            expense.trip = item.trip
            expense.item = item # Garante o vínculo
            expense.save()
            return redirect('trip_detail', pk=item.trip.id)
    else:
        if existing_expense:
            # Modo Edição: Carrega os dados existentes
            form = ExpenseForm(instance=existing_expense, trip_id=item.trip.id)
        else:
            # Modo Criação: Preenche o campo 'item' e sugere a data do item
            form = ExpenseForm(
                initial={'item': item, 'date': item.start_datetime.date()}, 
                trip_id=item.trip.id
            )
    
    return render(request, 'trips/expense_form.html', {
        'form': form, 
        'trip': item.trip,
        'item_name': item.name # Para mostrar no título qual item estamos gerenciando
    })

@login_required
def trip_item_attachments(request, item_id):
    item = get_object_or_404(TripItem, pk=item_id, trip__user=request.user)
    attachments = item.attachments.all() # Pega os arquivos já salvos
    
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES) # request.FILES é obrigatório para upload
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.item = item
            attachment.save()
            return redirect('trip_item_attachments', item_id=item.id)
    else:
        form = AttachmentForm()
    
    return render(request, 'trips/attachment_list.html', {
        'item': item,
        'attachments': attachments,
        'form': form,
        'trip': item.trip
    })

@login_required
def attachment_delete(request, pk):
    attachment = get_object_or_404(TripAttachment, pk=pk, item__trip__user=request.user)
    item_id = attachment.item.id
    attachment.delete()
    return redirect('trip_item_attachments', item_id=item_id)

@login_required
def financial_dashboard(request):
    # Pega todas as despesas do usuário
    expenses = Expense.objects.filter(trip__user=request.user).select_related('trip')
    
    total_global_brl = 0
    expenses_by_category = defaultdict(float)
    expenses_by_trip = defaultdict(float)
    
    rates_cache = {}

    # Processamento dos dados (Conversão e Agrupamento)
    for expense in expenses:
        currency = expense.currency
        
        # Busca cotação (usando nossa função utils)
        if currency not in rates_cache:
            rates_cache[currency] = get_exchange_rate(currency)
        
        rate = rates_cache[currency]
        val_brl = float(expense.amount) * rate
        
        # Soma Globais
        total_global_brl += val_brl
        expenses_by_category[expense.category] += val_brl
        expenses_by_trip[expense.trip.title] += val_brl

    # Prepara dados para os Gráficos (Chart.js espera listas)
    # 1. Gráfico de Categoria (Donut)
    cat_labels = list(expenses_by_category.keys())
    cat_data = [round(v, 2) for v in expenses_by_category.values()]

    # 2. Gráfico de Viagens (Barra)
    trip_labels = list(expenses_by_trip.keys())
    trip_data = [round(v, 2) for v in expenses_by_trip.values()]

    context = {
        'total_global': total_global_brl,
        'expense_count': expenses.count(),
        # Enviamos como JSON seguro para o Javascript ler
        'cat_labels': json.dumps(cat_labels),
        'cat_data': json.dumps(cat_data),
        'trip_labels': json.dumps(trip_labels),
        'trip_data': json.dumps(trip_data),
    }

    return render(request, 'financial_dashboard.html', context)