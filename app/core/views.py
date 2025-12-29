from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone # Importante para saber o ano atual
from collections import defaultdict     # <--- Essencial para os gráficos
import json                             # <--- Essencial para os gráficos
# Seus Models e Utils (Geralmente já estavam aí)
from .models import Trip, Expense, TripItem
from .utils import get_exchange_rate, get_currency_by_country
from .models import Trip, TripItem, Expense, TripAttachment 
from django.conf import settings
from .forms import TripForm, TripItemForm, ExpenseForm, AttachmentForm
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from .forms import UserCreateForm, UserEditForm


@login_required
def home(request):
    # 1. Busca as viagens
    trips = Trip.objects.filter(user=request.user).order_by('-start_date')
    
    # 2. Cálculo Financeiro
    total_spent = 0
    rates_cache = {}
    all_expenses = Expense.objects.filter(trip__user=request.user)
    
    for expense in all_expenses:
        if expense.currency not in rates_cache:
            rates_cache[expense.currency] = get_exchange_rate(expense.currency)
        # ARREDONDAMENTO AQUI:
        val_converted = float(expense.amount) * rates_cache[expense.currency]
        total_spent += round(val_converted, 2)

    # 3. Cotações de Referência (Dólar e Euro) para os Widgets
    # Se já tivermos buscado no loop acima, usamos do cache. Se não, buscamos agora.
    usd_rate = rates_cache.get('USD') or get_exchange_rate('USD')
    eur_rate = rates_cache.get('EUR') or get_exchange_rate('EUR')

    # 4. Dados para o Mapa (CORREÇÃO AQUI)
    # Buscamos os itens com coordenadas
    raw_locations = TripItem.objects.filter(
        trip__user=request.user
    ).exclude(
        location_lat__isnull=True
    ).exclude(
        location_lng__isnull=True
    ).values('name', 'location_lat', 'location_lng', 'trip__title')

    # Lista limpa para o Javascript
    map_locations = []
    for loc in raw_locations:
        map_locations.append({
            'name': loc['name'],
            'trip__title': loc['trip__title'],
            # Convertendo Decimal do Python para Float do JS
            'location_lat': float(loc['location_lat']), 
            'location_lng': float(loc['location_lng']),
        })

    context = {
        'trips': trips,
        'total_spent': total_spent,
        'trip_count': trips.count(),
        # Passamos as taxas para o template
        'usd_rate': usd_rate,
        'eur_rate': eur_rate,
        # Usamos json.dumps para garantir que vá como texto JSON válido
        'map_locations': json.dumps(map_locations), 
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }

    return render(request, 'index.html', context)

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
        if expense.currency not in rates_cache:
            rates_cache[expense.currency] = get_exchange_rate(expense.currency)
        expense.converted_value = round(float(expense.amount) * rates_cache[expense.currency], 2)
        total_converted_brl += expense.converted_value
    
    # --- NOVA LÓGICA: COTAÇÕES POR PAÍS DOS ITENS ---
    detected_currencies = set() # Usamos set para não repetir moedas (ex: 2 hoteis na frança = 1 Euro)
    
    for item in items:
        if item.location_address:
            # Tenta descobrir a moeda baseada no endereço do item
            currency_code = get_currency_by_country(item.location_address)
            if currency_code and currency_code != 'BRL': # Ignora Real
                detected_currencies.add(currency_code)

    # Agora buscamos a cotação de HOJE para essas moedas encontradas
    trip_rates = []
    for currency in detected_currencies:
        # Reutiliza do cache se já tivermos buscado para os gastos
        rate = rates_cache.get(currency) or get_exchange_rate(currency)
        trip_rates.append({
            'code': currency,
            'rate': rate
        })

    return render(request, 'trips/trip_detail.html', {
        'trip': trip,
        'items': items,
        'expenses': expenses,
        'total_spent_brl': round(total_converted_brl, 2),
        'trip_rates': trip_rates, # <--- ENVIAMOS AS COTAÇÕES AQUI
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
    # 1. Busca ÚNICA e Otimizada
    # Trazemos 'trip' e 'item' para não travar o banco na hora de gerar a tabela
    all_expenses = Expense.objects.filter(
        trip__user=request.user
    ).select_related('trip', 'item').order_by('-date')
    
    # 2. Inicialização de Variáveis
    total_global_brl = 0
    total_year_brl = 0  # Variável para o novo Widget

    # Garante que pegamos o ano certo (inteiro)
    current_year = timezone.now().year # Pega o ano atual (ex: 2025)
    
    expenses_by_category = defaultdict(float)
    expenses_by_trip = defaultdict(float)
    rates_cache = {}

    # 3. Loop Único (Processa Tabela, Gráficos e Widgets ao mesmo tempo)
    for expense in all_expenses:
        # --- Conversão de Moeda ---
        if expense.currency not in rates_cache:
            rates_cache[expense.currency] = get_exchange_rate(expense.currency)
            
        rate = rates_cache[expense.currency]
        
        # CÁLCULO CRÍTICO: Valor * Taxa
        val_brl = float(expense.amount) * rate
        val_brl = round(val_brl, 2)
        
        # Debug no Terminal: Mostra o que está acontecendo com cada gasto
        print(f"Item: {expense.description} | Moeda: {expense.currency} | Valor: {expense.amount} | Taxa: {rate} | Convertido: {val_brl}")

        # Salva no objeto para exibir na Tabela (coluna R$)
        expense.converted_value = val_brl
        
        # --- SOMAS (Acumuladores) ---
        
        # 1. Soma Global (Tudo desde sempre)
        total_global_brl += val_brl
        
        # Total do Ano Atual (NOVO)
        if expense.date.year == current_year:
            total_year_brl += val_brl

        # Dados para Gráficos
        expenses_by_category[expense.category] += val_brl
        expenses_by_trip[expense.trip.title] += val_brl

    # 4. Preparação dos Gráficos
    cat_labels = list(expenses_by_category.keys())
    cat_data = [round(v, 2) for v in expenses_by_category.values()]

    trip_labels = list(expenses_by_trip.keys())
    trip_data = [round(v, 2) for v in expenses_by_trip.values()]

    context = {
        # Widgets / KPIs
        'total_global': total_global_brl,
        'expense_count': all_expenses.count(),
        'total_year': total_year_brl,      # <--- Dado Novo
        'current_year': current_year,      # <--- Para mostrar no label
        
        # Tabela
        'all_expenses': all_expenses,
        
        # Gráficos (JSON)
        'cat_labels': json.dumps(cat_labels),
        'cat_data': json.dumps(cat_data),
        'trip_labels': json.dumps(trip_labels),
        'trip_data': json.dumps(trip_data),
    }
    
    return render(request, 'financial_dashboard.html', context)

@login_required
def expense_update(request, pk):
    """
    Edita um gasto existente (seja ele vinculado a um item ou solto).
    """
    expense = get_object_or_404(Expense, pk=pk, trip__user=request.user)
    
    if request.method == 'POST':
        # Passamos trip_id para o form saber filtrar os itens corretamente
        form = ExpenseForm(request.POST, instance=expense, trip_id=expense.trip.id)
        if form.is_valid():
            form.save()
            return redirect('trip_detail', pk=expense.trip.id)
    else:
        form = ExpenseForm(instance=expense, trip_id=expense.trip.id)
    
    return render(request, 'trips/expense_form.html', {
        'form': form,
        'trip': expense.trip,
        'item_name': expense.item.name if expense.item else None # Mostra no título se tiver item
    })

@login_required
def expense_delete(request, pk):
    """
    Exclui o gasto. Se ele estava vinculado a um item, o vínculo some
    e o ícone da timeline volta a ficar cinza automaticamente.
    """
    expense = get_object_or_404(Expense, pk=pk, trip__user=request.user)
    trip_id = expense.trip.id # Guarda o ID para voltar para a página certa
    expense.delete()
    return redirect('trip_detail', pk=trip_id)

@login_required
def fix_locations(request):
    # Pega todos os itens que têm endereço mas não têm latitude
    items = TripItem.objects.filter(location_address__isnull=False, location_lat__isnull=True)

    count = 0
    for item in items:
        # Ao chamar .save(), a lógica nova do models.py será executada automaticamente
        item.save()
        count += 1

    print(f"{count} itens atualizados com coordenadas.")
    return redirect('home')

# --- VERIFICAÇÃO DE SEGURANÇA ---
def is_admin(user):
    # Retorna True se for Superuser (root) OU se pertencer ao grupo 'admin'
    return user.is_superuser or user.groups.filter(name='admin').exists()

@login_required
@user_passes_test(is_admin) # Só passa se for admin
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'users/user_form.html', {'form': form, 'title': 'Novo Usuário'})

@login_required
@user_passes_test(is_admin)
def user_update(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user_obj)
    return render(request, 'users/user_form.html', {'form': form, 'title': f'Editar: {user_obj.username}'})

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        # Impede que o usuário se delete
        return redirect('user_list')
    
    user_obj.delete()
    return redirect('user_list')
