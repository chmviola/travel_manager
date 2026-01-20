from multiprocessing import context
from decimal import Decimal
from django.core.mail import send_mail, get_connection
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone # Importante para saber o ano atual
from django.urls import reverse
from collections import defaultdict
import json
import googlemaps
import ast
import markdown
import os
import traceback
import sys
from datetime import datetime, time, timedelta
from .utils import get_exchange_rate, get_currency_by_country, fetch_weather_data, get_travel_intel, generate_checklist_ai, generate_itinerary_ai, generate_trip_insights_ai, get_country_code_from_address
from .models import Trip, TripItem, Expense, TripAttachment, APIConfiguration, Checklist, ChecklistItem, TripCollaborator, TripPhoto, EmailConfiguration, AccessLog
from django.conf import settings
from .forms import TripForm, TripItemForm, ExpenseForm, AttachmentForm, UserProfileForm, CustomPasswordChangeForm, APIConfigurationForm, UserCreateForm, UserEditForm, APIConfigurationForm, ShareTripForm, TripPhotoForm, EmailConfigurationForm, ICSImportForm
from django.db.models import Sum, Q, Case, When, F, DecimalField
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from icalendar import Calendar, Event as ICalEvent
import pytz
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder


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
            'location_lat': float(loc['location_lat']), 
            'location_lng': float(loc['location_lng']),
        })
    
    # --- CORREÇÃO AQUI: BUSCA A CHAVE NO BANCO ---
    google_maps_api_key = None
    try:
        # Tenta pegar a chave salva no banco
        config = APIConfiguration.objects.get(key='GOOGLE_MAPS_API')
        google_maps_api_key = config.value
    except APIConfiguration.DoesNotExist:
        print("AVISO: Chave GOOGLE_MAPS_API não encontrada no banco.")
    # ---------------------------------------------

    context = {
        'trips': trips,
        'total_spent': total_spent,
        'trip_count': trips.count(),
        # Passamos as taxas para o template
        'usd_rate': usd_rate,
        'eur_rate': eur_rate,
        # Usamos json.dumps para garantir que vá como texto JSON válido
        'map_locations': json.dumps(map_locations), 
        'google_maps_api_key': google_maps_api_key
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
        # trip.flags = set() 
        
        # # Pega todos os itens dessa viagem que tenham endereço
        # items = trip.items.exclude(location_address__isnull=True).exclude(location_address__exact='')
        
        # for item in items:
        #     address_lower = item.location_address.lower()
            
        #     for country_name, country_code in country_map.items():
        #         if country_name in address_lower:
        #             trip.flags.add(country_code)
        
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

#--- VIEW PARA DETALHES DA VIAGEM ITENS---
@login_required
def trip_detail(request, pk):
    # 1. Busca a Viagem e Permissões
    trip = get_object_or_404(
        Trip, 
        Q(pk=pk) & (Q(user=request.user) | Q(collaborators__user=request.user))
    )

    user_role = trip.get_user_role(request.user)
    can_edit = (user_role == 'owner' or user_role == 'editor')

    # 1. Busca TODOS os itens apenas para extrair as datas disponíveis
    all_items = trip.items.all().order_by('start_datetime')
    available_dates = trip.items.dates('start_datetime', 'day')

    # 2. Determina qual data exibir (Filtro)
    selected_date_str = request.GET.get('date')
    selected_date = None

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Se não tem data selecionada, pega a primeira disponível
    if not selected_date and available_dates:
        selected_date = available_dates[0]

    # 3. Filtra os itens para a timeline e mapa (AQUI ESTAVA O ERRO, AGORA ESTÁ CERTO)
    if selected_date:
        items = all_items.filter(start_datetime__date=selected_date)
    else:
        items = all_items

    # --- REMOVIDA A LINHA QUE SOBRESCREVIA 'items' COM TUDO DE NOVO ---

    # 4. Processamento de Itens (Flags e Clima) - Aplica nos itens FILTRADOS
    # trip.flags = set() 
    items_changed = False

    # --- LIMPEZA DE DADOS PARA EXIBIÇÃO (Sua lógica original mantida) ---
    import ast
    for item in items:
        # # Lógica de Bandeira
        item.flag_code = get_country_code_from_address(item.location_address)
        # if item.flag_code:
        #     trip.flags.add(item.flag_code)

        # Lógica de Limpeza das Notas 
        if item.details:
            raw = item.details
            if isinstance(raw, str):
                try:
                    raw = ast.literal_eval(raw)
                except:
                    pass
            
            if isinstance(raw, dict):
                notes = raw.get('notes', '')
                if isinstance(notes, str) and notes.strip().startswith("{'notes'"):
                    try:
                        inner = ast.literal_eval(notes)
                        if isinstance(inner, dict):
                            notes = inner.get('notes', notes)
                    except:
                        pass
                item.details = {'notes': notes}
        
        # B. Detectar Clima (Se tiver endereço, data e ainda não tiver clima)
        if item.location_address and item.start_datetime and not item.weather_temp:
            temp, cond, icon = fetch_weather_data(item.location_address, item.start_datetime)
            if temp:
                item.weather_temp = temp
                item.weather_condition = cond
                item.weather_icon = icon
                item.save()
                items_changed = True
    
    # Se atualizamos o clima, recarregamos MANTENDO O FILTRO DA DATA
    if items_changed:
        if selected_date:
            items = trip.items.filter(start_datetime__date=selected_date).order_by('start_datetime')
        else:
            items = trip.items.all().order_by('start_datetime')

    # 5. Processamento Financeiro (Mantém global da viagem ou filtra? Geralmente financeiro é global)
    # Aqui mantemos expenses global (trip.expenses) para o resumo financeiro mostrar o total da viagem
    # --- LÓGICA FINANCEIRA ATUALIZADA ---
    expenses = trip.expenses.all()
    
    total_planned_brl = Decimal('0.00')
    total_paid_brl = Decimal('0.00')
    rates_cache = {}

    for expense in expenses:
        # Obtém a taxa de câmbio (com cache)
        if expense.currency not in rates_cache:
            rates_cache[expense.currency] = get_exchange_rate(expense.currency)

        rate = Decimal(str(rates_cache[expense.currency]))  # Converte para Decimal para precisão

        # Calcula o valor convertido para BRL
        converted = Decimal(expense.amount) * rate
        converted = converted.quantize(Decimal('0.01'))  # Arredonda para 2 casas decimais

        # Atribui ao atributo temporário (padronizado para 'converted_amount')
        expense.converted_amount = converted

        # Acumula nos totais convertidos
        total_planned_brl += converted
        if expense.is_paid:
            total_paid_brl += converted

    to_pay_brl = total_planned_brl - total_paid_brl

    # 6. Cotações para Exibição (Baseado nos itens filtrados do dia)
    detected_currencies = set()
    for item in items:
        if item.location_address:
            currency_code = get_currency_by_country(item.location_address)
            if currency_code and currency_code != 'BRL':
                detected_currencies.add(currency_code)
    
    trip_rates = []
    for currency in detected_currencies:
        rate = rates_cache.get(currency) or get_exchange_rate(currency)
        trip_rates.append({'code': currency, 'rate': rate})

    # 7. Chave do Google Maps
    google_maps_api_key = ''
    try:
        config = APIConfiguration.objects.filter(key='GOOGLE_MAPS_API', is_active=True).first()
        if config:
            google_maps_api_key = config.value
    except Exception as e:
        print(f"Erro ao buscar API Key: {e}")

    context = {
        'trip': trip,
        'total_planned': total_planned_brl,
        'total_paid': total_paid_brl,
        'to_pay': to_pay_brl,
        'items': items,
        'available_dates': available_dates,
        'selected_date': selected_date,
        'expenses': expenses,
        'can_edit': can_edit,
        'user_role': user_role,
        #'total_spent_brl': round(total_converted_brl, 2),
        'trip_rates': trip_rates,
        'google_maps_api_key': google_maps_api_key
    }

    return render(request, 'trips/trip_detail.html', context)

#--- VIEW PARA DETALHES DA VIAGEM CALENDÁRIO --
@login_required
def trip_calendar(request, pk):
    try:
        print(f"--- INICIANDO VIEW TRIP_CALENDAR (PK={pk}) ---")
        
        # 1. Busca a Viagem
        trip = get_object_or_404(
            Trip, 
            Q(pk=pk) & (Q(user=request.user) | Q(collaborators__user=request.user))
        )
        user_role = trip.get_user_role(request.user)
        can_edit = (user_role == 'owner' or user_role == 'editor')
        
        print("--- VIAGEM ENCONTRADA, BUSCANDO ITENS ---")

        # 2. Busca Itens
        items = trip.items.all().order_by('start_datetime')
        
        # Prepara eventos JSON
        calendar_events = []
        for item in items:
            # Cor baseada no tipo (com proteção caso item.type seja None)
            color = '#3c8dbc' 
            try:
                if hasattr(item, 'type'):
                    if item.type == 'FLIGHT': color = '#dc3545'
                    elif item.type == 'LODGING': color = '#28a745'
                    elif item.type == 'FOOD': color = '#ffc107'
            except: pass
            
            # Tenta gerar a URL de edição (AQUI É UM PONTO CRÍTICO DE ERRO)
            url_edit = '#'
            if can_edit:
                try:
                    # Se o nome da rota no urls.py não for 'trip_item_update', vai dar erro aqui
                    # url_edit = reverse('trip_item_update', args=[item.id]) 
                    # Vou deixar comentado e colocar '#' para testar se é isso que está quebrando
                    # Descomente a linha abaixo se tiver certeza do nome da rota:
                     url_edit = reverse('trip_item_update', args=[item.id])
                except Exception as e:
                    print(f"AVISO: Não foi possível gerar URL para item {item.id}: {e}")
                    url_edit = '#'

            event = {
                'title': item.name,
                'start': item.start_datetime.isoformat() if item.start_datetime else '',
                'backgroundColor': color,
                'borderColor': color,
                'url': url_edit
            }
            
            if item.end_datetime:
                event['end'] = item.end_datetime.isoformat()
                
            calendar_events.append(event)
        
        print(f"--- ITENS PROCESSADOS: {len(calendar_events)} ---")
        
        events_json = json.dumps(calendar_events, cls=DjangoJSONEncoder)

        # 3. Financeiro (Mesma lógica blindada da trip_detail)
        print("--- INICIANDO FINANCEIRO ---")
        expenses = list(trip.expenses.all().order_by('-date'))
        total_planned = Decimal(0)
        total_paid = Decimal(0)
        rates_cache = {}

        for expense in expenses:
            rate = 1
            if expense.currency and expense.currency != 'BRL':
                if expense.currency in rates_cache:
                    rate = rates_cache[expense.currency]
                else:
                    try:
                        r = get_exchange_rate(expense.currency)
                        rate = Decimal(str(r)) if r else 1
                        rates_cache[expense.currency] = rate
                    except: rate = 1
            
            try:
                val_amount = Decimal(str(expense.amount)) if expense.amount else Decimal(0)
                val_rate = Decimal(str(rate))
                val_converted = val_amount * val_rate
            except: val_converted = Decimal(0)

            expense.converted_value = val_converted
            total_planned += val_converted
            if expense.is_paid: total_paid += val_converted

        to_pay = total_planned - total_paid
        print("--- FINANCEIRO CONCLUÍDO ---")

        # 4. Cotações
        trip_rates = []
        try:
            cur_set = set()
            for item in items:
                if item.location_address:
                    c = get_currency_by_country(item.location_address)
                    if c and c != 'BRL': cur_set.add(c)
            for c in cur_set:
                r = rates_cache.get(c) or get_exchange_rate(c)
                if r: trip_rates.append({'code': c, 'rate': r})
        except: pass

        # API Key
        google_maps_api_key = ''
        try:
            from .models import APIConfiguration
            c = APIConfiguration.objects.filter(key='GOOGLE_MAPS_API', is_active=True).first()
            if c: google_maps_api_key = c.value
        except: pass

        print("--- RENDERIZANDO TEMPLATE ---")
        context = {
            'trip': trip,
            'events_json': events_json,
            'items': items,
            'expenses': expenses,
            'total_planned': total_planned,
            'total_paid': total_paid,
            'to_pay': to_pay,
            'trip_rates': trip_rates,
            'can_edit': can_edit,
            'google_maps_api_key': google_maps_api_key,
            'show_calendar_nav': True
        }

        return render(request, 'trips/trip_calendar.html', context)

    except Exception:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERRO CRÍTICO NA VIEW TRIP_CALENDAR:")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.stdout.flush()
        raise

    
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
    # Nota: A query abaixo restringe apenas ao dono. Se quiser permitir editores, 
    # use get_object_or_404(Trip, pk=trip_id) e faça a verificação de role depois.
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    if request.method == 'POST':
        form = TripItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.trip = trip
            
            # --- TRATAMENTO DO JSON ---
            raw_notes = form.cleaned_data.get('details', '')
            if isinstance(raw_notes, dict):
                item.details = raw_notes
            else:
                item.details = {'notes': raw_notes}
            # --------------------------

            # --- INÍCIO DA CORREÇÃO (GEOCODING NA CRIAÇÃO) ---
            if item.location_address:
                try:
                    # 1. Busca a chave no Banco de Dados
                    config = APIConfiguration.objects.get(key='GOOGLE_MAPS_API')
                    
                    # 2. Conecta no Google Maps
                    gmaps = googlemaps.Client(key=config.value)
                    
                    # 3. Converte Endereço -> Lat/Lng
                    geocode_result = gmaps.geocode(item.location_address)
                    
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        item.location_lat = location['lat']
                        item.location_lng = location['lng']
                        print(f"Geocoding Create Sucesso: {item.location_lat}, {item.location_lng}")
                        
                except APIConfiguration.DoesNotExist:
                    print("ERRO: Chave GOOGLE_MAPS_API não cadastrada no banco.")
                except Exception as e:
                    print(f"Erro no Geocoding (Create): {e}")
            # --- FIM DA CORREÇÃO ---

            item.save()
            messages.success(request, "Item adicionado com sucesso!")
            
            # --- Redireciona para a data do item ---
            base_url = reverse('trip_detail', args=[trip.id])
            if item.start_datetime:
                date_str = item.start_datetime.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
            return redirect(base_url)
            # ---------------------------------------
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
            messages.success(request, "Despesa registrada com sucesso.")
            # --- MUDANÇA AQUI: Redireciona para a data da despesa ---
            base_url = reverse('trip_detail', args=[trip.id])
            if expense.date: # Assumindo que seu campo se chama 'date'
                date_str = expense.date.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
            return redirect(base_url)
            # --------------------------------------------------------
    else:
        # Dica: Se quiser pré-preencher a data vinda da URL na criação
        initial_date = request.GET.get('date')
        form = ExpenseForm(initial={'date': initial_date} if initial_date else None)

    return render(request, 'trips/expense_form.html', {'form': form, 'trip': trip})

#--- VIEW PARA CALCULAR O QUE JÁ FOI PAGO ---
@require_POST
def trip_expense_toggle_paid(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.is_paid = not expense.is_paid # Inverte o status
    expense.save()
    
    # Recalcula os totais da viagem para atualizar a tela dinamicamente
    trip = expense.trip
    expenses = trip.expenses.all()
    
    total_planned_brl = Decimal('0.00')
    total_paid_brl = Decimal('0.00')
    rates_cache = {}
    
    for exp in expenses:
        if exp.currency not in rates_cache:
            rates_cache[exp.currency] = get_exchange_rate(exp.currency)

        rate = Decimal(str(rates_cache[exp.currency]))
        converted = Decimal(exp.amount) * rate
        converted = converted.quantize(Decimal('0.01'))

        total_planned_brl += converted
        if exp.is_paid:
            total_paid_brl += converted

    to_pay_brl = total_planned_brl - total_paid_brl
    
    return JsonResponse({
        'is_paid': expense.is_paid,
        'total_paid': float(total_paid_brl),  # Converte para float para JSON (ou use str)
        'to_pay': float(to_pay_brl),
        'total_planned': float(total_planned_brl)
    })

#--- VIEW PARA EDITAR VIAGEM ---
@login_required
def trip_update(request, pk):
    """
    Edita os dados principais da viagem (Título, Datas, Status).
    """
    trip = get_object_or_404(Trip, pk=pk)
    
    # Segurança: Apenas o dono pode editar as configurações gerais da viagem
    if trip.user != request.user:
         messages.error(request, "Você não tem permissão para editar esta viagem.")
         return redirect('trip_list')

    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Viagem atualizada com sucesso.")
            return redirect('trip_detail', pk=trip.id)
    else:
        form = TripForm(instance=trip)

    return render(request, 'trips/trip_form.html', {
        'form': form, 
        'title': 'Editar Viagem'
    })

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
    item = get_object_or_404(TripItem, pk=pk)
    trip = item.trip
    
    # Verifica permissão
    if trip.user != request.user and trip.get_user_role(request.user) != 'editor':
         messages.error(request, "Sem permissão para editar este item.")
         return redirect('trip_detail', pk=trip.id)

    # --- FUNÇÃO AUXILIAR INTERNA PARA LIMPAR O JSON ---
    def extract_notes_text(data):
        """Extrai apenas o texto, removendo camadas de JSON/Dict"""
        if data is None:
            return ""
        
        # Se for dicionário, pega a chave 'notes'
        if isinstance(data, dict):
            return extract_notes_text(data.get('notes', ''))
            
        # Se for string, verifica se é um dicionário disfarçado
        if isinstance(data, str):
            data = data.strip()
            if data.startswith("{") and "notes" in data:
                try:
                    # Tenta converter string em dict
                    parsed = ast.literal_eval(data)
                    # Chama recursivamente para limpar o resultado
                    return extract_notes_text(parsed)
                except:
                    pass
        return data # Retorna o texto puro
    # --------------------------------------------------

    if request.method == 'POST':
        form = TripItemForm(request.POST, instance=item)
        if form.is_valid():
            updated_item = form.save(commit=False)
            
            # 1. Pega o que o usuário digitou
            user_input = form.cleaned_data.get('details', '')
            
            # 2. Garante que pegamos só o texto limpo (caso haja sujeira)
            clean_text = extract_notes_text(user_input)
            
            # 3. Salva no formato JSON correto
            updated_item.details = {'notes': clean_text}
            
            # --- INÍCIO DA CORREÇÃO (GEOCODING NA EDIÇÃO) ---
            # Pegamos o item original do banco para comparar se o endereço mudou
            original_item = TripItem.objects.get(pk=pk)
            
            address_changed = updated_item.location_address != original_item.location_address
            missing_coords = not updated_item.location_lat or not updated_item.location_lng
            
            # Só consome a API se o endereço mudou ou se não tem coordenadas salvas
            if updated_item.location_address and (address_changed or missing_coords):
                try:
                    # 1. Busca a chave no Banco de Dados
                    config = APIConfiguration.objects.get(key='GOOGLE_MAPS_API')
                    
                    # 2. Conecta no Google Maps
                    gmaps = googlemaps.Client(key=config.value)
                    
                    # 3. Converte Endereço -> Lat/Lng
                    geocode_result = gmaps.geocode(updated_item.location_address)
                    
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        updated_item.location_lat = location['lat']
                        updated_item.location_lng = location['lng']
                        print(f"Geocoding Update Sucesso: {updated_item.location_lat}, {updated_item.location_lng}")
                        
                except APIConfiguration.DoesNotExist:
                    print("ERRO: Chave GOOGLE_MAPS_API não cadastrada no banco.")
                except Exception as e:
                    print(f"Erro no Geocoding (Update): {e}")
            # --- FIM DA CORREÇÃO ---

            updated_item.save()
            messages.success(request, "Item atualizado com sucesso.")
            
            # --- Redireciona para a data do item atualizado ---
            base_url = reverse('trip_detail', args=[trip.id])
            if updated_item.start_datetime:
                # Pega a data nova (caso o usuário tenha mudado o dia)
                date_str = updated_item.start_datetime.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
            return redirect(base_url)
            # --------------------------------------------------
            
    else:
        # --- PREPARAÇÃO PARA EXIBIÇÃO (GET) ---
        original_details = item.details
        item.details = extract_notes_text(original_details)
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
            
            # --- CORREÇÃO AQUI: Redirecionamento Inteligente ---
            base_url = reverse('trip_detail', args=[item.trip.id])
            
            if expense.date:
                date_str = expense.date.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
            
            return redirect(base_url)
            # ---------------------------------------------------
    else:
        if existing_expense:
            # Modo Edição
            form = ExpenseForm(instance=existing_expense, trip_id=item.trip.id)
        else:
            # Modo Criação: Preenche item e data sugerida
            form = ExpenseForm(
                initial={'item': item, 'date': item.start_datetime.date()}, 
                trip_id=item.trip.id
            )
    
    return render(request, 'trips/expense_form.html', {
        'form': form, 
        'trip': item.trip,
        # INCLUÍMOS ESTA VARIÁVEL PARA O BOTÃO CANCELAR FUNCIONAR NA CRIAÇÃO
        'target_date': item.start_datetime.date() if item.start_datetime else None,
        'item_name': item.name
    })

@login_required
def trip_item_attachments(request, item_id):
    item = get_object_or_404(TripItem, pk=item_id, trip__user=request.user)
    attachments = item.attachments.all()
    
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.item = item
            attachment.save()
            messages.success(request, "Arquivo anexado com sucesso.")

            # --- CORREÇÃO: Redireciona para a timeline na data do item ---
            base_url = reverse('trip_detail', args=[item.trip.id])
            
            if item.start_datetime:
                date_str = item.start_datetime.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
            
            return redirect(base_url)
            # -------------------------------------------------------------
            
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
def trip_item_set_link(request, item_id):
    item = get_object_or_404(TripItem, pk=item_id, trip__user=request.user)
    
    if request.method == 'POST':
        # Pega o link do formulário
        link_url = request.POST.get('link_url')
        
        # Salva (ou limpa se estiver vazio)
        item.link = link_url if link_url else None
        item.save()
        
        messages.success(request, "Link atualizado com sucesso!")
        
        # --- REDIRECIONAMENTO INTELIGENTE ---
        base_url = reverse('trip_detail', args=[item.trip.id])
        if item.start_datetime:
            date_str = item.start_datetime.strftime('%Y-%m-%d')
            return redirect(f"{base_url}?date={date_str}")
            
        return redirect(base_url)
    
    # Se tentar acessar via GET, manda de volta
    return redirect('trip_detail', pk=item.trip.id)

#--- VIEW PARA GERAR ITINERÁRIO USANDO IA ---
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

#--- VIEW PARA GERAR DICAS DE VIAGEM USANDO IA ---
@login_required
def trip_generate_insights(request, trip_id): # 
    # Busca a viagem usando o trip_id recebido da URL
    trip = get_object_or_404(Trip, pk=trip_id)
    
    # Verifica permissão
    if trip.user != request.user and trip.get_user_role(request.user) != 'editor':
        messages.error(request, "Você não tem permissão para atualizar as dicas.")
        # Redireciona usando pk=trip_id (pois a url de detalhe provavelmente espera pk)
        return redirect('trip_detail', pk=trip_id)

    # Chama a função de IA passando o ID numérico
    success = generate_trip_insights_ai(trip.id)

    if success:
        messages.success(request, "Guia de Bolso (IA) atualizado com sucesso!")
    else:
        messages.error(request, "Erro ao conectar com a IA. Verifique sua chave de API.")

    return redirect('trip_detail', pk=trip_id)

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

    # Adicione esta linha para popular o dropdown
    all_trips = Trip.objects.filter(user=request.user).order_by('-start_date')

    # --- [NOVO] Adicione esta linha para pegar a cotação ---
    try:
        usd_rate = get_exchange_rate('USD')
    except:
        usd_rate = 0.0
    # -------------------------------------------------------

    context = {
        # Widgets / KPIs
        'total_global': total_global_brl,
        'expense_count': all_expenses.count(),
        'total_year': total_year_brl,
        'current_year': current_year,
        
        # --- [NOVO] Adicione esta linha aqui dentro ---
        'usd_rate': usd_rate,
        # ----------------------------------------------
        
        'all_trips': all_trips,
        'all_expenses': all_expenses,
        
        # Gráficos (JSON)
        'cat_labels': json.dumps(cat_labels),
        'cat_data': json.dumps(cat_data),
        'trip_labels': json.dumps(trip_labels),
        'trip_data': json.dumps(trip_data),
    }
    
    return render(request, 'financial_dashboard.html', context)

# --- VIEW PARA O GRÁFICO DONUT NO FINANCIAL DASHBOARD ---
@login_required
def financial_chart_api(request):
    trip_id = request.GET.get('trip_id')
    
    # 1. Filtra despesas
    expenses = Expense.objects.filter(trip__user=request.user)
    
    if trip_id and trip_id != 'all':
        try:
            expenses = expenses.filter(trip_id=int(trip_id))
        except ValueError:
            pass 
            
    stats = defaultdict(float)
    
    # --- CORREÇÃO BLINDADA AQUI ---
    # Tenta pegar as escolhas do campo. Se não tiver, cria um dicionário vazio.
    choices = {}
    try:
        field_object = Expense._meta.get_field('category')
        if field_object.choices:
            choices = dict(field_object.choices)
    except:
        # Se der qualquer erro ao tentar pegar choices, seguimos sem elas
        choices = {}
    # ------------------------------
    
    for expense in expenses:
        # Tratamento de erro na conversão de moeda
        try:
            rate = get_exchange_rate(expense.currency)
        except:
            rate = 1.0
            
        val_brl = float(expense.amount) * rate
        stats[expense.category] += val_brl

    # Ordena
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    labels = []
    data = []
    
    for cat_code, val in sorted_stats:
        # Se existir no dicionário de choices, usa o nome bonito.
        # Se não existir (ou choices for vazio), usa o próprio código/texto salvo.
        cat_name = str(choices.get(cat_code, cat_code))
        
        labels.append(cat_name)
        data.append(round(val, 2))
        
    return JsonResponse({
        'labels': labels,
        'data': data
    })

@login_required
def expense_update(request, pk):
    # Sua query original
    expense = get_object_or_404(Expense, pk=pk, trip__user=request.user)
    
    if request.method == 'POST':
        # Mantendo sua lógica de trip_id no form
        form = ExpenseForm(request.POST, instance=expense, trip_id=expense.trip.id)
        
        if form.is_valid():
            updated_expense = form.save() # Salva e guarda o objeto
            
            # --- CORREÇÃO DO REDIRECIONAMENTO ---
            base_url = reverse('trip_detail', args=[expense.trip.id])
            
            if updated_expense.date:
                date_str = updated_expense.date.strftime('%Y-%m-%d')
                return redirect(f"{base_url}?date={date_str}")
                
            return redirect(base_url)
            # ------------------------------------
            
    else:
        form = ExpenseForm(instance=expense, trip_id=expense.trip.id)
    
    return render(request, 'trips/expense_form.html', {
        'form': form,
        'trip': expense.trip,
        'item_name': expense.item.name if expense.item else None 
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

# --- VIEW DE IMPORTAÇÃO/ EXPORTAÇÃO GOOGLE CALENDER ---
# --- EXPORTAR PARA CALENDAR (.ICS) ---
@login_required
def trip_export_ics(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    
    # Cria o Calendário
    cal = Calendar()
    cal.add('prodid', '-//Travel Manager//carlosviola.com//')
    cal.add('version', '2.0')
    
    items = trip.items.all()
    
    for item in items:
        if item.start_datetime:
            event = ICalEvent()
            event.add('summary', f"✈️ {item.name}")
            
            # Descrição: Junta notas e link
            description = ""
            if item.link:
                description += f"Link: {item.link}\n"
            
            # Tenta extrair texto limpo das notas (usando sua função ou acessando direto)
            notes = item.details.get('notes', '') if isinstance(item.details, dict) else str(item.details)
            if notes:
                description += f"Notas: {notes}"
                
            event.add('description', description)
            
            # Localização
            if item.location_address:
                event.add('location', item.location_address)
            
            # Data de Início
            event.add('dtstart', item.start_datetime)
            
            # Data de Fim (Se não tiver, assume 1 hora de duração)
            if item.end_datetime:
                event.add('dtend', item.end_datetime)
            else:
                event.add('dtend', item.start_datetime + timedelta(hours=1))
            
            event.add('dtstamp', datetime.now())
            cal.add_component(event)

    # Gera o arquivo para download
    response = HttpResponse(cal.to_ical(), content_type="text/calendar")
    response['Content-Disposition'] = f'attachment; filename="trip_{trip.id}.ics"'
    return response

# --- IMPORTAR DO CALENDAR (.ICS) ---
@login_required
def trip_import_ics(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    
    if request.method == 'POST':
        form = ICSImportForm(request.POST, request.FILES)
        if form.is_valid():
            ics_file = request.FILES['ics_file']
            
            try:
                # Lê o arquivo
                cal = Calendar.from_ical(ics_file.read())
                count = 0
                
                for component in cal.walk():
                    if component.name == "VEVENT":
                        # Extrai dados básicos
                        summary = str(component.get('summary', 'Evento Importado'))
                        dtstart = component.get('dtstart').dt
                        dtend = component.get('dtend')
                        location = str(component.get('location', ''))
                        description = str(component.get('description', ''))
                        
                        # Tratamento de Fuso Horário e Tipos de Data
                        # Se for data pura (dia todo), converte para datetime
                        if not isinstance(dtstart, datetime):
                            dtstart = datetime.combine(dtstart, time(0,0))
                        
                        # Se tiver timezone info, converte ou remove para salvar no banco (depende da sua config)
                        # Assumindo que seu banco salva tz-aware ou naive, o Django costuma lidar bem,
                        # mas é bom garantir.
                        
                        # Cria o Item
                        TripItem.objects.create(
                            trip=trip,
                            name=summary,
                            item_type='ACTIVITY', # Tipo padrão
                            start_datetime=dtstart,
                            end_datetime=dtend.dt if dtend else None,
                            location_address=location,
                            details={'notes': description}
                        )
                        count += 1
                
                messages.success(request, f"{count} itens importados com sucesso!")
                
            except Exception as e:
                messages.error(request, f"Erro ao processar arquivo: {str(e)}")
                
            return redirect('trip_detail', pk=trip.id)
            
    return redirect('trip_detail', pk=trip.id)

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

    # 2. LÓGICA DAS BANDEIRAS (NOVO)
    # Buscamos todas as viagens do usuário e já trazemos os itens juntos (prefetch) para ser rápido
    user_trips = Trip.objects.filter(user=request.user).prefetch_related('items')
    
    visited_flags = set() # Usamos um Set para não repetir bandeiras
    
    for trip in user_trips:
        for item in trip.items.all():
            if item.location_address:
                # Reutiliza sua função existente que extrai 'br', 'us', 'fr' do endereço
                code = get_country_code_from_address(item.location_address)
                if code:
                    visited_flags.add(code)
    
    # Ordena as bandeiras alfabeticamente para ficar bonito na tela
    visited_flags = sorted(list(visited_flags))

    context = {
        'form': form if 'form' in locals() else None, # Ajuste conforme sua view
        'visited_flags': visited_flags, # <--- Passamos as bandeiras aqui
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

#--- VIEW para o CHANGELOG ---
def changelog_view(request):
    # Caminho do arquivo. 
    # settings.BASE_DIR geralmente aponta para a pasta onde está o manage.py
    file_path = os.path.join(settings.BASE_DIR, 'CHANGELOG.md')
    
    changelog_html = ""
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            # Converte Markdown para HTML com algumas extensões úteis
            # 'fenced_code' permite blocos de código
            # 'nl2br' transforma quebras de linha em <br>
            changelog_html = markdown.markdown(text, extensions=['fenced_code', 'nl2br'])
    else:
        changelog_html = """
        <div class="alert alert-warning">
            Arquivo CHANGELOG.md não encontrado no servidor.
        </div>
        """

    return render(request, 'config/changelog.html', {
        'changelog_html': changelog_html, 
        'title': 'Histórico de Versões'
    })

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

# --- VIEW DE CONFIGURAÇÃO DE E-MAIL (SOMENTE ADMIN) ---
@login_required
@user_passes_test(is_admin)
def email_settings_view(request):
    # Tenta pegar a configuração existente ou cria uma vazia
    config = EmailConfiguration.objects.first()
    
    if request.method == 'POST':
        # Verifica se é uma ação de salvar ou de testar
        action = request.POST.get('action')
        
        form = EmailConfigurationForm(request.POST, instance=config)
        
        if form.is_valid():
            config_instance = form.save()
            
            if action == 'test':
                # --- LÓGICA DE TESTE DE ENVIO ---
                try:
                    # Cria a conexão manualmente usando os dados salvos
                    connection = get_connection(
                        host=config_instance.host,
                        port=config_instance.port,
                        username=config_instance.username,
                        password=config_instance.password,
                        use_tls=config_instance.use_tls,
                        use_ssl=config_instance.use_ssl
                    )
                    
                    # Tenta enviar um e-mail simples
                    send_mail(
                        subject='Teste de Configuração - TravelManager',
                        message='Se você recebeu este e-mail, a configuração SMTP está funcionando corretamente!',
                        from_email=config_instance.default_from_email,
                        recipient_list=[request.user.email],
                        connection=connection,
                        fail_silently=False,
                    )
                    messages.success(request, f"Configurações salvas e e-mail de teste enviado para {request.user.email}!")
                except Exception as e:
                    messages.error(request, f"Configuração salva, mas o teste falhou: {str(e)}")
            else:
                messages.success(request, "Configurações de e-mail salvas com sucesso.")
            
            return redirect('email_settings')
    else:
        form = EmailConfigurationForm(instance=config)

    return render(request, 'config/email_settings.html', {'form': form, 'title': 'Configuração de E-mail'})

# --- VIEW DE LOGS DE ACESSO (SOMENTE ADMIN) ---
@login_required
@user_passes_test(is_admin)
def access_logs_view(request):
    logs = AccessLog.objects.all()
    
    # --- FILTRO POR USUÁRIO (NOVO) ---
    target_user_id = request.GET.get('user_id')
    target_user = None

    if target_user_id:
        try:
            # Filtra os logs apenas daquele ID
            logs = logs.filter(user_id=target_user_id)
            # Busca o objeto User só para mostrar o nome na tela (opcional)
            from django.contrib.auth.models import User
            target_user = User.objects.get(pk=target_user_id)
        except Exception:
            pass # Se o ID for inválido, ignora e mostra tudo
            
    # Pega os últimos 200 registros (após filtrar)
    logs = logs[:200]
    
    context = {
        'logs': logs,
        'target_user': target_user # Enviamos para o template saber que está filtrado
    }
    
    return render(request, 'config/access_logs.html', context)

