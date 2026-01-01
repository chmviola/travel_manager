from multiprocessing import context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone # Importante para saber o ano atual
from collections import defaultdict     # <--- Essencial para os gráficos
import json                             # <--- Essencial para os gráficos
from datetime import datetime, time, timedelta
# Seus Models e Utils (Geralmente já estavam aí)
from .utils import get_exchange_rate, get_currency_by_country, fetch_weather_data, get_travel_intel, generate_checklist_ai, generate_itinerary_ai, generate_trip_insights_ai, get_country_code_from_address
from .models import Trip, TripItem, Expense, TripAttachment, APIConfiguration, Checklist, ChecklistItem, TripCollaborator, TripPhoto
from django.conf import settings
from .forms import TripForm, TripItemForm, ExpenseForm, AttachmentForm, UserProfileForm, CustomPasswordChangeForm, APIConfigurationForm, UserCreateForm, UserEditForm, APIConfigurationForm, ShareTripForm, TripPhotoForm
from django.db.models import Sum, Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

#--- VIEW PARA A PÁGINA INICIAL (DASHBOARD) ---
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
def trip_list(request):
    """
    Lista todas as viagens (próprias e compartilhadas) do usuário logado.
    """
    
    # --- MUDANÇA AQUI ---
    # Buscamos viagens onde o usuário é o DONO (user=request.user)
    # OU (|) onde ele é um COLABORADOR (collaborators__user=request.user)
    # O .distinct() é importante para evitar duplicatas caso haja algum conflito no join
    trips = Trip.objects.filter(
        Q(user=request.user) | Q(collaborators__user=request.user)
    ).distinct().order_by('-start_date')

    # --- Lógica para Identificar Bandeiras (MANTIDA IGUAL) ---
    country_map = {
        # A
        'afeganistão': 'af', 'afghanistan': 'af',
        'áfrica do sul': 'za', 'south africa': 'za',
        'albânia': 'al', 'albania': 'al',
        'alemanha': 'de', 'germany': 'de',
        'andorra': 'ad',
        'angola': 'ao',
        'antígua e barbuda': 'ag', 'antigua and barbuda': 'ag',
        'arábia saudita': 'sa', 'saudi arabia': 'sa',
        'argélia': 'dz', 'algeria': 'dz',
        'argentina': 'ar',
        'armênia': 'am', 'armenia': 'am',
        'austrália': 'au', 'australia': 'au',
        'áustria': 'at', 'austria': 'at',
        'azerbaijão': 'az', 'azerbaijan': 'az',

        # B
        'bahamas': 'bs',
        'bangladesh': 'bd',
        'barbados': 'bb',
        'barein': 'bh', 'bahrain': 'bh',
        'bélgica': 'be', 'belgium': 'be',
        'belize': 'bz',
        'benin': 'bj',
        'bolívia': 'bo', 'bolivia': 'bo',
        'bósnia e herzegovina': 'ba', 'bosnia and herzegovina': 'ba',
        'botswana': 'bw',
        'brasil': 'br', 'brazil': 'br',
        'brunei': 'bn',
        'bulgária': 'bg', 'bulgaria': 'bg',

        # C
        'cabo verde': 'cv', 'cape verde': 'cv',
        'camarões': 'cm', 'cameroon': 'cm',
        'canadá': 'ca', 'canada': 'ca',
        'catar': 'qa', 'qatar': 'qa',
        'cazaquistão': 'kz', 'kazakhstan': 'kz',
        'chile': 'cl',
        'china': 'cn',
        'chipre': 'cy', 'cyprus': 'cy',
        'colômbia': 'co', 'colombia': 'co',
        'coreia do norte': 'kp', 'north korea': 'kp',
        'coreia do sul': 'kr', 'south korea': 'kr',
        'costa rica': 'cr',
        'croácia': 'hr', 'croatia': 'hr',
        'cuba': 'cu',

        # D
        'dinamarca': 'dk', 'denmark': 'dk',
        'dominica': 'dm',

        # E
        'egito': 'eg', 'egypt': 'eg',
        'el salvador': 'sv',
        'emirados árabes unidos': 'ae', 'united arab emirates': 'ae',
        'equador': 'ec',
        'eritrea': 'er',
        'eslováquia': 'sk', 'slovakia': 'sk',
        'eslovênia': 'si', 'slovenia': 'si',
        'espanha': 'es', 'spain': 'es',
        'estados unidos': 'us', 'usa': 'us', 'united states': 'us',
        'estônia': 'ee', 'estonia': 'ee',
        'etiópia': 'et', 'ethiopia': 'et',

        # F
        'finlândia': 'fi', 'finland': 'fi',
        'frança': 'fr', 'france': 'fr',

        # G
        'gabão': 'ga', 'gabon': 'ga',
        'gana': 'gh', 'ghana': 'gh',
        'geórgia': 'ge', 'georgia': 'ge',
        'grécia': 'gr', 'greece': 'gr',
        'guatemala': 'gt',

        # H
        'haiti': 'ht',
        'holanda': 'nl', 'netherlands': 'nl',
        'honduras': 'hn',
        'hungria': 'hu', 'hungary': 'hu',

        # I
        'índia': 'in', 'india': 'in',
        'indonésia': 'id', 'indonesia': 'id',
        'irã': 'ir', 'iran': 'ir',
        'iraque': 'iq', 'iraq': 'iq',
        'irlanda': 'ie', 'ireland': 'ie',
        'islândia': 'is', 'iceland': 'is',
        'israel': 'il',
        'itália': 'it', 'italy': 'it',

        # J
        'jamaica': 'jm',
        'japão': 'jp', 'japan': 'jp',

        # K
        'kenya': 'ke',
        'kuwait': 'kw',

        # L
        'letonia': 'lv', 'latvia': 'lv',
        'líbano': 'lb', 'lebanon': 'lb',
        'lituânia': 'lt', 'lithuania': 'lt',
        'luxemburgo': 'lu', 'luxembourg': 'lu',

        # M
        'malásia': 'my', 'malaysia': 'my',
        'marrocos': 'ma', 'morocco': 'ma',
        'méxico': 'mx', 'mexico': 'mx',
        'moçambique': 'mz', 'mozambique': 'mz',

        # N
        'namíbia': 'na', 'namibia': 'na',
        'nepal': 'np',
        'nigéria': 'ng', 'nigeria': 'ng',
        'noruega': 'no', 'norway': 'no',
        'nova zelândia': 'nz', 'new zealand': 'nz',

        # P
        'paquistão': 'pk', 'pakistan': 'pk',
        'paraguai': 'py', 'paraguay': 'py',
        'peru': 'pe',
        'polônia': 'pl', 'poland': 'pl',
        'portugal': 'pt',

        # R
        'reino unido': 'gb', 'uk': 'gb', 'united kingdom': 'gb',
        'romênia': 'ro', 'romania': 'ro',
        'rússia': 'ru', 'russia': 'ru',

        # S
        'senegal': 'sn',
        'sérvia': 'rs', 'serbia': 'rs',
        'singapura': 'sg', 'singapore': 'sg',
        'síria': 'sy', 'syria': 'sy',
        'suécia': 'se', 'sweden': 'se',
        'suíça': 'ch', 'switzerland': 'ch',

        # T
        'tailândia': 'th', 'thailand': 'th',
        'tunísia': 'tn', 'tunisia': 'tn',
        'turquia': 'tr', 'turkey': 'tr',

        # U
        'ucrânia': 'ua', 'ukraine': 'ua',
        'uruguai': 'uy', 'uruguay': 'uy',

        # V
        'venezuela': 've',
        'vietnã': 'vn', 'vietnam': 'vn',

        # Z
        'zâmbia': 'zm', 'zambia': 'zm',
        'zimbábue': 'zw', 'zimbabwe': 'zw',
    }

    for trip in trips:
        trip.flags = set() 
        
        # Pega todos os itens dessa viagem que tenham endereço
        items = trip.items.exclude(location_address__isnull=True).exclude(location_address__exact='')
        
        for item in items:
            address_lower = item.location_address.lower()
            
            for country_name, country_code in country_map.items():
                if country_name in address_lower:
                    trip.flags.add(country_code)
        
        trip.current_user_role = trip.get_user_role(request.user)

    return render(request, 'trips/trip_list.html', {'trips': trips})

#--- VIEW PARA CRIAR NOVA VIAGEM ---
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

#-- VIEW PARA COMPARTILHAR VIAGEM ---
@login_required
def trip_share(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user) # Só o dono compartilha
    
    if request.method == 'POST':
        form = ShareTripForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            target_user = User.objects.get(email=email)
            
            if target_user == request.user:
                messages.error(request, "Você não pode compartilhar consigo mesmo.")
            else:
                obj, created = TripCollaborator.objects.update_or_create(
                    trip=trip, user=target_user,
                    defaults={'role': role}
                )
                if created:
                    messages.success(request, f"Viagem compartilhada com {target_user.get_full_name()}!")
                else:
                    messages.info(request, f"Permissão de {target_user.get_full_name()} atualizada.")
            return redirect('trip_list') # Ou volta para o dashboard
    
    return redirect('trip_list')

#--- VIEW PARA REMOVER COLABORADOR ---
@login_required
def trip_remove_share(request, trip_id, user_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    TripCollaborator.objects.filter(trip=trip, user_id=user_id).delete()
    messages.success(request, "Acesso revogado.")
    return redirect('trip_list') # O ideal seria redirecionar para um modal de gestão

#--- VIEW PARA DETALHES DA VIAGEM ---
@login_required
def trip_detail(request, pk):
    # 1. Busca a Viagem e Permissões
    trip = get_object_or_404(
        Trip, 
        Q(pk=pk) & (Q(user=request.user) | Q(collaborators__user=request.user))
    )

    user_role = trip.get_user_role(request.user)
    can_edit = (user_role == 'owner' or user_role == 'editor')

    # 2. Busca os Itens (ORDEM CORRIGIDA: Isso tem que vir antes dos loops)
    items = trip.items.all().order_by('start_datetime')

    # --- LIMPEZA DE DADOS PARA EXIBIÇÃO ---
    import ast
    for item in items:
        # Lógica de Bandeira (Mantenha a sua existente)
        item.flag_code = get_country_code_from_address(item.location_address)
        
        # Lógica de Limpeza das Notas (NOVO)
        if item.details:
            raw = item.details
            
            # Se for string, tenta converter pra dict
            if isinstance(raw, str):
                try:
                    raw = ast.literal_eval(raw)
                except:
                    pass # É string pura
            
            # Se agora é dict, tenta pegar 'notes'
            if isinstance(raw, dict):
                notes = raw.get('notes', '')
                
                # VERIFICAÇÃO RECURSIVA (O problema do {'notes': "{'notes': ...}"})
                # Se o conteúdo da nota PARECE outro dicionário, limpamos de novo
                if isinstance(notes, str) and notes.strip().startswith("{'notes'"):
                    try:
                        inner = ast.literal_eval(notes)
                        if isinstance(inner, dict):
                            notes = inner.get('notes', notes)
                    except:
                        pass
                
                # Salva no objeto TEMPORÁRIO (memória) para o template ler certo
                # O template lê item.details.notes. Vamos garantir que item.details seja um dict limpo
                item.details = {'notes': notes}

    # 3. Processamento de Itens (Flags e Clima)
    trip.flags = set() # Inicializa o conjunto de bandeiras da viagem (cabeçalho)
    items_changed = False # Flag para saber se precisamos salvar algo

    for item in items:
        # A. Detectar Bandeira (Usa a função do utils.py)
        code = get_country_code_from_address(item.location_address)
        item.flag_code = code # Para o ícone na timeline
        if code:
            trip.flags.add(code) # Para as bandeiras no topo da página

        # B. Detectar Clima (Se tiver endereço, data e ainda não tiver clima)
        if item.location_address and item.start_datetime and not item.weather_temp:
            # Tenta buscar na API
            temp, cond, icon = fetch_weather_data(item.location_address, item.start_datetime)
            if temp:
                item.weather_temp = temp
                item.weather_condition = cond
                item.weather_icon = icon
                item.save()
                items_changed = True
    
    # Se atualizamos o clima de algum item, recarregamos a lista para garantir dados frescos
    if items_changed:
        items = trip.items.all().order_by('start_datetime')

    # 4. Processamento Financeiro
    expenses = trip.expenses.all()
    total_converted_brl = 0
    rates_cache = {} # Cache local para não chamar a função get_exchange_rate repetidamente

    # Calcula totais e converte gastos
    for expense in expenses:
        if expense.currency == 'BRL':
            expense.converted_value = expense.amount
            total_converted_brl += expense.amount
        else:
            # Se não tá no cache, busca
            if expense.currency not in rates_cache:
                rates_cache[expense.currency] = get_exchange_rate(expense.currency)
            
            rate = rates_cache[expense.currency]
            expense.converted_value = round(float(expense.amount) * rate, 2)
            total_converted_brl += expense.converted_value

    # 5. Cotações para Exibição (Baseado nos países visitados)
    detected_currencies = set()
    for item in items:
        if item.location_address:
            # Tenta descobrir a moeda do país
            currency_code = get_currency_by_country(item.location_address)
            if currency_code and currency_code != 'BRL':
                detected_currencies.add(currency_code)
    
    # Monta a lista de cotações para o rodapé do card financeiro
    trip_rates = []
    for currency in detected_currencies:
        rate = rates_cache.get(currency) or get_exchange_rate(currency)
        trip_rates.append({'code': currency, 'rate': rate})

    # 6. Chave do Google Maps
    google_maps_api_key = ''
    try:
        config = APIConfiguration.objects.filter(key='GOOGLE_MAPS_API', is_active=True).first()
        if config:
            google_maps_api_key = config.value
    except Exception as e:
        print(f"Erro ao buscar API Key: {e}")

    # 7. Contexto Final
    context = {
        'trip': trip,
        'items': items,
        'expenses': expenses,
        'can_edit': can_edit,
        'user_role': user_role,
        'total_spent_brl': round(total_converted_brl, 2),
        'trip_rates': trip_rates,
        'google_maps_api_key': google_maps_api_key
    }

    return render(request, 'trips/trip_detail.html', context)

#--- VIEW PARA GERAR PDF DO ROTEIRO ---
@login_required
def trip_detail_pdf(request, pk):
    trip = get_object_or_404(Trip, pk=pk, user=request.user)
    
    # Busca itens ordenados
    items = trip.items.all().order_by('start_datetime')
    
    # Busca e calcula gastos (para mostrar o total no PDF)
    expenses = trip.expenses.all()
    total_brl = 0
    for expense in expenses:
        # Cálculo simplificado para o PDF (idealmente usaria o cache como na view principal)
        rate = get_exchange_rate(expense.currency)
        total_brl += float(expense.amount) * rate

    context = {
        'trip': trip,
        'items': items,
        'expenses': expenses,
        'total_brl': round(total_brl, 2),
        'user': request.user,
        'now': datetime.now()
    }

    # Renderiza o template PDF
    template_path = 'trips/trip_pdf.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    # 'attachment' baixa o arquivo, 'inline' abre no navegador
    response['Content-Disposition'] = f'inline; filename="roteiro_{trip.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF')
    
    return response

#--- VIEWS PARA CRIAR ITENS DE VIAGEM (TRIP ITEM) ---
@login_required
def trip_item_create(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    if request.method == 'POST':
        form = TripItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            
            # --- LÓGICA DE LIMPEZA DEFINITIVA ---
            raw_text = form.cleaned_data.get('details', '')
            
            # Se o texto digitado parecer um dicionário Python (ex: {'notes': ...})
            # Isso acontece se o usuário copiou e colou, ou se o form carregou errado.
            # Vamos descascar essa string até sobrar só o texto.
            import ast
            
            # Loop de segurança: Enquanto parecer um dicionário, tente extrair o miolo
            # Isso resolve casos de dupla ou tripla recursividade
            while isinstance(raw_text, str) and raw_text.strip().startswith("{'notes'"):
                try:
                    parsed = ast.literal_eval(raw_text)
                    if isinstance(parsed, dict):
                        raw_text = parsed.get('notes', raw_text)
                    else:
                        break
                except:
                    break

            # Agora temos certeza que raw_text é o texto limpo
            item.details = {'notes': raw_text}
            # ------------------------------------

            item.save()
            # ... resto do código (messages, redirect)
    else:
        form = TripItemForm()

    return render(request, 'trips/trip_item_form.html', {'form': form, 'trip': trip, 'title': 'Novo Item'})

#--- VIEW PARA CRIAR GASTOS DE VIAGEM ---
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

#--- VIEW PARA EDITAR VIAGEM ---
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

#--- VIEW PARA DELETAR VIAGEM ---
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
    # 1. Busca o item e a viagem
    item = get_object_or_404(TripItem, pk=pk)
    trip = item.trip
    
    # 2. Verifica permissão (Dono ou Editor)
    # Nota: get_user_role deve estar funcionando no model Trip
    if trip.user != request.user and trip.get_user_role(request.user) != 'editor':
         messages.error(request, "Sem permissão para editar este item.")
         return redirect('trip_detail', pk=trip.id)

    if request.method == 'POST':
        form = TripItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            
            # --- LÓGICA DE LIMPEZA DEFINITIVA ---
            raw_text = form.cleaned_data.get('details', '')
            
            # Se o texto digitado parecer um dicionário Python (ex: {'notes': ...})
            # Isso acontece se o usuário copiou e colou, ou se o form carregou errado.
            # Vamos descascar essa string até sobrar só o texto.
            import ast
            
            # Loop de segurança: Enquanto parecer um dicionário, tente extrair o miolo
            # Isso resolve casos de dupla ou tripla recursividade
            while isinstance(raw_text, str) and raw_text.strip().startswith("{'notes'"):
                try:
                    parsed = ast.literal_eval(raw_text)
                    if isinstance(parsed, dict):
                        raw_text = parsed.get('notes', raw_text)
                    else:
                        break
                except:
                    break

            # Agora temos certeza que raw_text é o texto limpo
            item.details = {'notes': raw_text}
            # ------------------------------------

            item.save()
            # ... resto do código (messages, redirect)
            
    else:
        # --- LÓGICA DE EXIBIÇÃO (GET) ---
        # Aqui está o truque: Modificamos o objeto 'item' APENAS NA MEMÓRIA
        # para que o formulário receba o texto limpo, não o JSON.
        
        # Fazemos uma cópia ou alteramos o atributo temporariamente
        if item.details and isinstance(item.details, dict):
            # Substituímos o dict pela string apenas para exibir no form
            item.details = item.details.get('notes', '')
        
        # Agora passamos o instance modificado. O form vai ler 'item.details' 
        # que agora é uma string simples ("Almoço no lugar X").
        form = TripItemForm(instance=item)

    return render(request, 'trips/trip_item_form.html', {
        'form': form, 
        'trip': trip, 
        'title': 'Editar Item'
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

@login_required
def trip_generate_insights(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    # Chama a IA usando o título da viagem como destino
    # (Pode melhorar usando trip.location se tiver esse campo específico)
    insights = generate_trip_insights_ai(trip.title)
    
    if insights:
        trip.ai_insights = insights
        trip.save()
        messages.success(request, "Dicas de viagem geradas com sucesso!")
    else:
        messages.error(request, "Não foi possível gerar as dicas no momento.")
        
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

# --- VIEWS DE CONFIGURAÇÃO DE API ---
@login_required
def config_api_list(request):
    """Lista todas as configurações de API."""
    # Buscamos TUDO, ordenado por chave. Isso deve resolver o problema da chave não aparecer.
    configs = APIConfiguration.objects.all().order_by('key')
    context = {
        'configs': configs
    }
    return render(request, 'config/api_list.html', context)

@login_required
def config_api_handle(request, pk=None):
    """View única para CRIAR (pk=None) ou EDITAR (pk com valor) uma API."""
    if pk:
        # Modo Edição: busca a instância existente
        config = get_object_or_404(APIConfiguration, pk=pk)
        title = f"Editar API: {config.key}"
    else:
        # Modo Criação: nova instância
        config = None
        title = "Nova Configuração de API"

    if request.method == 'POST':
        form = APIConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            action = "atualizada" if pk else "criada"
            messages.success(request, f"Configuração de API {action} com sucesso.")
            return redirect('config_api_list')
    else:
        form = APIConfigurationForm(instance=config)

    context = {
        'form': form,
        'title': title,
        'is_edit': pk is not None
    }
    # Vamos usar um template genérico para o formulário
    return render(request, 'config/api_form.html', context)

#--- View para Deletar ---
@login_required
def config_api_delete(request, pk):
    config = get_object_or_404(APIConfiguration, pk=pk)
    if request.method == 'POST':
        key_name = config.key
        config.delete()
        messages.success(request, f"Chave {key_name} removida.")
        return redirect('config_api_list')
    # Se tentar acessar via GET, redireciona para a lista por segurança
    return redirect('config_api_list')

#--- VIEWS PARA GALERIA DE FOTOS DA VIAGEM ---
@login_required
def trip_gallery(request, trip_id):
    # ... (busca da trip e permissões mantém igual) ...
    trip = get_object_or_404(Trip, pk=trip_id) # simplificado para leitura
    
    # DEBUG: Verifique se isso aparece no 'docker logs -f'
    print("--- ACESSOU A VIEW GALLERY ---")

    if request.method == 'POST':
        print(f"FILES recebidos: {request.FILES}") # DEBUG CRÍTICO

        # 1. Pegamos os arquivos DIRETAMENTE do request, ignorando o form
        files = request.FILES.getlist('image')
        
        caption = request.POST.get('caption', '') # Pegamos a legenda direto também

        if not files:
            messages.error(request, "Nenhum arquivo chegou ao servidor.")
        else:
            count = 0
            for f in files:
                try:
                    TripPhoto.objects.create(
                        trip=trip,
                        image=f,
                        caption=caption
                    )
                    count += 1
                except Exception as e:
                    print(f"Erro ao salvar: {e}")
            
            messages.success(request, f"{count} fotos enviadas!")
            return redirect('trip_gallery', trip_id=trip.id)

    # GET request
    form = TripPhotoForm()
    photos = trip.photos.all().order_by('-uploaded_at')

    context = {
        'trip': trip,
        'photos': photos,
        'form': form,
        'can_edit': True # Simplificado para teste
    }
    return render(request, 'trips/trip_gallery.html', context)

@login_required
def trip_photo_delete(request, photo_id):
    photo = get_object_or_404(TripPhoto, pk=photo_id)
    trip = photo.trip
    
    # Segurança: Só permite deletar se tiver acesso à trip
    if trip.user != request.user and trip.get_user_role(request.user) != 'editor':
        messages.error(request, "Sem permissão.")
        return redirect('trip_gallery', trip_id=trip.id)

    photo.delete()
    messages.success(request, "Foto removida.")
    return redirect('trip_gallery', trip_id=trip.id)


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
