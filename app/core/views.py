from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone # Importante para saber o ano atual
from collections import defaultdict     # <--- Essencial para os gráficos
import json                             # <--- Essencial para os gráficos
from datetime import datetime, time, timedelta
# Seus Models e Utils (Geralmente já estavam aí)
from .utils import get_exchange_rate, get_currency_by_country, fetch_weather_data, get_travel_intel, generate_checklist_ai, generate_itinerary_ai
from .models import Trip, TripItem, Expense, TripAttachment, APIConfiguration, Checklist, ChecklistItem
from django.conf import settings
from .forms import TripForm, TripItemForm, ExpenseForm, AttachmentForm, UserProfileForm, CustomPasswordChangeForm
from django.db.models import Sum, Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from .forms import UserCreateForm, UserEditForm, APIConfigurationForm
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


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

# --- VIEWS PARA VIAGEM (TRIP) ---
@login_required
def trip_list(request):
    """
    Lista todas as viagens do usuário logado.
    """
    # O filtro user=request.user garante a segurança dos dados
    trips = Trip.objects.filter(user=request.user).order_by('-start_date')

    # --- Lógica para Identificar Bandeiras ---
    # Dicionário de mapeamento (Nome no endereço -> Código ISO)
    # Adicione mais países conforme sua necessidade
    country_map = {
        'alemanha': 'de', 'germany': 'de',
        'argentina': 'ar',
        'austrália': 'au', 'australia': 'au',
        'brasil': 'br', 'brazil': 'br',
        'canadá': 'ca', 'canada': 'ca',
        'chile': 'cl',
        'china': 'cn',
        'espanha': 'es', 'spain': 'es',
        'estados unidos': 'us', 'usa': 'us', 'united states': 'us',
        'finlândia': 'fi', 'finland': 'fi',
        'frança': 'fr', 'france': 'fr',
        'itália': 'it', 'italy': 'it',
        'japão': 'jp', 'japan': 'jp',
        'portugal': 'pt',
        'méxico': 'mx', 'mexico': 'mx',
        'reino unido': 'gb', 'uk': 'gb', 'london': 'gb',
        'uruguai': 'uy', 'uruguay': 'uy',
    }

    for trip in trips:
        trip.flags = set() # Usamos um Set para evitar bandeiras repetidas
        
        # Pega todos os itens dessa viagem que tenham endereço
        items = trip.items.exclude(location_address__isnull=True).exclude(location_address__exact='')
        
        for item in items:
            address_lower = item.location_address.lower()
            
            # Verifica se algum país do dicionário está no endereço
            for country_name, country_code in country_map.items():
                if country_name in address_lower:
                    trip.flags.add(country_code)
                    # Não damos break aqui, caso haja múltiplos países num texto estranho, 
                    # mas geralmente um endereço só tem um país.
    
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

# 1. Lógica das Bandeiras (Cópia da trip_list)
    country_map = {
        'alemanha': 'de', 'germany': 'de',
        'argentina': 'ar',
        'austrália': 'au', 'australia': 'au',
        'brasil': 'br', 'brazil': 'br',
        'canadá': 'ca', 'canada': 'ca',
        'chile': 'cl',
        'china': 'cn',
        'espanha': 'es', 'spain': 'es',
        'estados unidos': 'us', 'usa': 'us', 'united states': 'us',
        'finlândia': 'fi', 'finland': 'fi',
        'frança': 'fr', 'france': 'fr',
        'itália': 'it', 'italy': 'it',
        'japão': 'jp', 'japan': 'jp',
        'portugal': 'pt',
        'méxico': 'mx', 'mexico': 'mx',
        'reino unido': 'gb', 'uk': 'gb', 'london': 'gb',
        'uruguai': 'uy', 'uruguay': 'uy',
        'suíça': 'sw', 'switzerland': 'sw'
    }

    trip.flags = set()
    items_with_address = trip.items.exclude(location_address__isnull=True).exclude(location_address__exact='')
    
    for item in items_with_address:
        address_lower = item.location_address.lower()
        for country_name, country_code in country_map.items():
            if country_name in address_lower:
                trip.flags.add(country_code)

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

    # Verifica itens que tem endereço e data, mas não tem clima salvo
    items_changed = False
    for item in items:
        if item.location_address and item.start_datetime and not item.weather_temp:
            # Tenta buscar na API
            temp, cond, icon = fetch_weather_data(item.location_address, item.start_datetime)
            
            if temp:
                item.weather_temp = temp
                item.weather_condition = cond
                item.weather_icon = icon
                item.save() # Salva no banco para não buscar de novo
                items_changed = True
    
    # Se houve mudança, recarrega a query para garantir dados frescos
    if items_changed:
        items = trip.items.all().order_by('start_datetime')

    # BUSCAR CHAVE DO MAPA NO BANCO
    google_maps_api_key = ''
    try:
        config = APIConfiguration.objects.get(key='GOOGLE_MAPS_API', is_active=True)
        google_maps_api_key = config.value
        print(f"SUCESSO: Chave encontrada: {google_maps_api_key[:5]}...") # Debug no Log
    except APIConfiguration.DoesNotExist:
        print("ERRO: Chave GOOGLE_MAPS_API não encontrada no banco ou inativa.") # Debug no Log
    except Exception as e:
        print(f"ERRO CRÍTICO ao buscar chave: {e}")

    context = {
        'trip': trip,
        'items': items,
        'expenses': expenses,
        'total_spent_brl': round(total_converted_brl, 2),
        'trip_rates': trip_rates,
        'google_maps_api_key': google_maps_api_key # Enviando para o template
    }

    return render(request, 'trips/trip_detail.html', context)

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
def trip_generate_itinerary(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    if request.method == 'POST':
        interests = request.POST.get('interests', 'Pontos turísticos principais')
        
        # 1. Chama a IA
        data = generate_itinerary_ai(trip, interests)
        
        if data and 'events' in data:
            count = 0
            for event in data['events']:
                try:
                    # 2. Calcula a data real baseada no dia do roteiro
                    # Se Day 1, é a start_date. Se Day 2, start_date + 1 dia.
                    day_offset = int(event['day']) - 1
                    event_date = trip.start_date + timedelta(days=day_offset)
                    
                    # 3. Combina Data + Hora
                    hour, minute = map(int, event['time'].split(':'))
                    event_datetime = datetime.combine(event_date, time(hour, minute))
                    
                    # 4. Cria o item no banco
                    TripItem.objects.create(
                        trip=trip,
                        name=event['name'],
                        location_address=event.get('location', ''),
                        item_type=event['category'], # ACTIVITY, RESTAURANT
                        start_datetime=event_datetime,
                        details={'notes': event['description']} # Salvamos a descrição nas notas
                    )
                    count += 1
                except Exception as e:
                    print(f"Erro ao salvar item {event}: {e}")
                    continue
            
            if count > 0:
                messages.success(request, f"Sucesso! {count} atividades foram adicionadas ao seu roteiro.")
            else:
                messages.warning(request, "A IA respondeu, mas não conseguimos processar os itens.")
        else:
            messages.error(request, "Erro ao comunicar com a Inteligência Artificial.")
            
    return redirect('trip_detail', pk=trip.id)

# --- VIEWS PARA FINANCIAL ---
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
        
    #    # Debug no Terminal: Mostra o que está acontecendo com cada gasto
    #    print(f"Item: {expense.description} | Moeda: {expense.currency} | Valor: {expense.amount} | Taxa: {rate} | Convertido: {val_brl}")

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

# --- VIEWS GOOGLE MAPS ---
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

# --- CHECKLIST ---
@login_required
def checklist_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    # Tenta pegar ou cria um checklist vazio se não existir
    checklist, created = Checklist.objects.get_or_create(trip=trip)
    
    # Agrupa itens por categoria para facilitar o template
    items_by_category = {}
    items = checklist.items.all().order_by('category', 'item')
    
    for item in items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    context = {
        'trip': trip,
        'checklist': checklist,
        'items_by_category': items_by_category
    }
    return render(request, 'trips/checklist.html', context)

@login_required
def checklist_generate(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    # Chama a IA
    data = generate_checklist_ai(trip)
    
    if data:
        # Pega ou cria o checklist pai
        checklist, _ = Checklist.objects.get_or_create(trip=trip)
        
        # Limpa itens antigos para não duplicar (opcional, mas recomendado para "regenerar")
        checklist.items.all().delete()
        
        # Salva os novos itens
        for category, items_list in data.items():
            for item_text in items_list:
                ChecklistItem.objects.create(
                    checklist=checklist,
                    category=category,
                    item=item_text
                )
        messages.success(request, "Checklist gerado com inteligência artificial!")
    else:
        messages.error(request, "Erro ao gerar checklist. Verifique a chave da API.")
        
    return redirect('checklist_view', trip_id=trip.id)

@login_required
def checklist_toggle(request, item_id):
    # View simples para marcar/desmarcar (pode ser via AJAX futuramente)
    item = get_object_or_404(ChecklistItem, pk=item_id, checklist__trip__user=request.user)
    item.is_checked = not item.is_checked
    item.save()
    return redirect('checklist_view', trip_id=item.checklist.trip.id)

@login_required
def checklist_add_item(request, trip_id):
    if request.method == 'POST':
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        checklist, _ = Checklist.objects.get_or_create(trip=trip)
        
        category = request.POST.get('category', 'Geral')
        item_text = request.POST.get('item')
        
        if item_text:
            ChecklistItem.objects.create(
                checklist=checklist,
                category=category,
                item=item_text
            )
            messages.success(request, f"Item '{item_text}' adicionado.")
            
    return redirect('checklist_view', trip_id=trip_id)

@login_required
def checklist_delete_item(request, item_id):
    item = get_object_or_404(ChecklistItem, pk=item_id, checklist__trip__user=request.user)
    trip_id = item.checklist.trip.id
    item_text = item.item
    item.delete()
    messages.info(request, f"Item '{item_text}' removido.")
    return redirect('checklist_view', trip_id=trip_id)

@login_required
def checklist_clear_completed(request, trip_id):
    """Apaga todos os itens marcados como feitos"""
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    # Filtra itens desta viagem que estão checados (True) e deleta
    deleted_count, _ = ChecklistItem.objects.filter(
        checklist__trip=trip, 
        is_checked=True
    ).delete()
    
    if deleted_count > 0:
        messages.success(request, f"{deleted_count} itens concluídos foram removidos.")
    else:
        messages.info(request, "Nenhum item marcado para limpar.")
        
    return redirect('checklist_view', trip_id=trip.id)

@login_required
def checklist_pdf(request, trip_id):
    """Gera o PDF do Checklist"""
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    checklist, _ = Checklist.objects.get_or_create(trip=trip)
    
    # Reutilizamos a lógica de agrupar por categoria
    items_by_category = {}
    items = checklist.items.all().order_by('category', 'item')
    
    for item in items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    context = {
        'trip': trip,
        'items_by_category': items_by_category,
        'user': request.user,
    }

    # Renderiza o template HTML específico para PDF
    template_path = 'trips/checklist_pdf.html'
    template = get_template(template_path)
    html = template.render(context)

    # Cria o PDF
    response = HttpResponse(content_type='application/pdf')
    # Se quiser que baixe direto, mude 'inline' para 'attachment'
    response['Content-Disposition'] = f'inline; filename="checklist_{trip.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF <pre>' + html + '</pre>')
    
    return response

# --- VIEWS DE CONFIGURAÇÃO DE API ---
@login_required
def api_list(request):
    # Apenas superusuários podem ver isso
    if not request.user.is_superuser:
        messages.error(request, "Acesso não autorizado.")
        return redirect('home')
        
    configs = APIConfiguration.objects.all()
    return render(request, 'config/api_list.html', {'configs': configs})

@login_required
def api_update(request, pk=None):
    if not request.user.is_superuser:
        return redirect('home')

    if pk:
        config = get_object_or_404(APIConfiguration, pk=pk)
        title = "Editar API"
    else:
        config = None
        title = "Nova API"

    if request.method == 'POST':
        form = APIConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuração de API salva com sucesso!')
            return redirect('api_list')
    else:
        form = APIConfigurationForm(instance=config)

    return render(request, 'config/api_form.html', {'form': form, 'title': title})

@login_required
def api_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('home')
        
    config = get_object_or_404(APIConfiguration, pk=pk)
    config.delete()
    messages.success(request, 'Configuração removida.')
    return redirect('api_list')

# --- VIEWS DE USER PROFILE ---
@login_required
def profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        # Esta parte processa apenas os dados cadastrais (Nome, Email)
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Seus dados foram atualizados com sucesso!")
            return redirect('user_profile')
        else:
            messages.error(request, "Corrija os erros no formulário de dados.")
    else:
        form = UserProfileForm(instance=user)

    # Enviamos o form de senha vazio para ser renderizado no modal
    password_form = CustomPasswordChangeForm(user)

    context = {
        'form': form,
        'password_form': password_form,
        'user': user
    }
    return render(request, 'config/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Esta linha é CRUCIAL: mantém o usuário logado após mudar a senha
            update_session_auth_hash(request, user) 
            messages.success(request, "Sua senha foi alterada com sucesso!")
        else:
            # Se houver erro (ex: senha atual errada), mostramos via mensagem
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro na senha: {error}")
                    
    return redirect('user_profile')

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
