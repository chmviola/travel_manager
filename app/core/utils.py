import json
import requests
import re
from django.conf import settings
from datetime import timedelta, datetime
from openai import OpenAI
from .models import APIConfiguration, Trip
from django.core.mail import get_connection


#-- Função Adicional para Buscar Dicas de Viagem AI --#
def get_travel_intel(destination):
    # 1. Busca chave no banco
    try:
        config = APIConfiguration.objects.get(key='OPENAI_API', is_active=True)
        api_key = config.value
    except APIConfiguration.DoesNotExist:
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""
    Você é um guia de viagens especialista. Crie um resumo prático sobre {destination}.
    Responda EXATAMENTE neste formato JSON, sem crases ou markdown:
    {{
        "currency": "Moeda oficial, cotação aproximada para USD e costumes de gorjeta.",
        "electricity": "Voltagem (110v/220v) e tipo de tomada (A, B, C, etc).",
        "phrases": "5 frases essenciais na língua local com tradução (Ex: Olá, Obrigado, Quanto custa).",
        "safety": "Nível de segurança, golpes comuns para turistas e zonas a evitar.",
        "food": "Cite 3 pratos ou bebidas típicas imperdíveis deste destino e o que são.",
        "curiosity": "Uma curiosidade cultural única ou fato histórico interessante e pouco conhecido sobre o local."
    }}
    Seja direto e objetivo. Responda em Português do Brasil.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo barato e rápido
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Erro OpenAI: {e}")
        return None

#-- Função Adicional para Buscar Cotação de Moeda --#
def get_exchange_rate(from_currency):
    """
    Busca a cotação atual de uma moeda para Real (BRL).
    Ex: from_currency='USD' retorna quanto vale 1 dólar em reais.
    """
    if from_currency == 'BRL':
        return 1.0
    
    try:
        # Consulta a AwesomeAPI (USD-BRL, EUR-BRL, etc)
        url = f"https://economia.awesomeapi.com.br/json/last/{from_currency}-BRL"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # O retorno é algo como: {'USDBRL': {'bid': '5.10', ...}}
        key = f"{from_currency}BRL"
        return float(data[key]['bid'])
    except Exception as e:
        print(f"Erro ao buscar cotação: {e}")
        # Valores aproximados de segurança (Fallback)
        fallback_rates = {
            'USD': 6.00, 
            'EUR': 6.30, 
            'GBP': 7.50,
            'CAD': 4.20,
            'AUD': 3.80,
            'CHF': 6.50,
            'JPY': 0.04,
            # América do Sul (Valores muito pequenos em relação ao Real)
            'CLP': 0.0063, # 1 Peso Chileno vale aprox 0.006 Reais
            'ARS': 0.0060,
            'UYU': 0.14,
            'COP': 0.0014,
            'PEN': 1.60
        }
        return fallback_rates.get(from_currency, 1.0)
    
#-- Função Adicional para Mapear Moeda por País/Cidade --#
def get_currency_by_country(country_name):
    """
    Mapeia nomes de países E CIDADES (que vêm do Google Maps) para códigos de moeda.
    """
    if not country_name:
        return None
        
    text = country_name.lower().strip()
    
    mapping = {
        # Europa (Países e Capitais Principais)
        'france': 'EUR', 'frança': 'EUR', 'paris': 'EUR',
        'germany': 'EUR', 'alemanha': 'EUR', 'berlin': 'EUR', 'berlim': 'EUR',
        'italy': 'EUR', 'itália': 'EUR', 'rome': 'EUR', 'roma': 'EUR',
        'spain': 'EUR', 'espanha': 'EUR', 'madrid': 'EUR', 'barcelona': 'EUR',
        'portugal': 'EUR', 'lisbon': 'EUR', 'lisboa': 'EUR',
        'netherlands': 'EUR', 'holanda': 'EUR', 'amsterdam': 'EUR',
        'united kingdom': 'GBP', 'reino unido': 'GBP', 'england': 'GBP', 'inglaterra': 'GBP', 'london': 'GBP', 'londres': 'GBP',
        'switzerland': 'CHF', 'suíça': 'CHF', 'zurich': 'CHF',
        
        # Américas
        'united states': 'USD', 'estados unidos': 'USD', 'usa': 'USD', 'ny': 'USD', 'miami': 'USD', 'orlando': 'USD',
        'canada': 'CAD', 'canadá': 'CAD', 'toronto': 'CAD', 'vancouver': 'CAD',
        'chile': 'CLP', 'santiago': 'CLP',
        'argentina': 'ARS', 'buenos aires': 'ARS',
        'uruguay': 'UYU', 'uruguai': 'UYU', 'montevideo': 'UYU',
        'colombia': 'COP', 'colômbia': 'COP',
        'peru': 'PEN', 'lima': 'PEN',
        
        # Ásia / Oceania
        'japan': 'JPY', 'japão': 'JPY', 'tokyo': 'JPY',
        'australia': 'AUD', 'austrália': 'AUD', 'sydney': 'AUD',
    }
    
    for key, currency in mapping.items():
        if key in text:
            return currency
            
    return None

#-- Função Adicional para Buscar Clima --#
def fetch_weather_data(location, date_obj):
    # 1. Busca a chave no Banco de Dados
    try:
        config = APIConfiguration.objects.get(key='WEATHER_API', is_active=True)
        api_key = config.value
    except APIConfiguration.DoesNotExist:
        # Se não achar no banco, pode tentar um fallback para o settings (opcional)
        # ou apenas retornar erro.
        print("ERRO: Chave WEATHER_API não cadastrada ou inativa no banco.")
        return None, None, None

    if not location or not date_obj:
        return None, None, None

    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        # Usa a api_key que veio do banco
        url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&dt={date_str}&lang=pt"        
        response = requests.get(url, timeout=5)

        # DEBUG 2: Verificando resposta da API
        if response.status_code != 200:
            print(f"Erro API: Status {response.status_code}")
            print(f"Mensagem: {response.text}")
            return None, None, None 

        data = response.json()

        if 'forecast' in data and len(data['forecast']['forecastday']) > 0:
            day_data = data['forecast']['forecastday'][0]['day']
            
            temp = round(day_data['avgtemp_c']) # Temperatura média do dia
            condition = day_data['condition']['text']
            icon = day_data['condition']['icon'] # URL do ícone (ex: //cdn.weatherapi...)
            
            # Adiciona protocolo se faltar
            if icon.startswith('//'):
                icon = f"https:{icon}"
                
            return temp, condition, icon
        else:
            print(f"JSON inesperado: {data}")
            
    except Exception as e:
        print(f"Erro ao buscar clima para {location}: {e}")
        return None, None, None
    
    return None, None, None

#-- Função Adicional para Geração de Checklist AI --#
def generate_checklist_ai(trip):
    """
    Gera uma lista de itens de viagem baseada no destino e duração usando OpenAI.
    """
    try:
        config = APIConfiguration.objects.get(key='OPENAI_API', is_active=True)
        api_key = config.value
    except APIConfiguration.DoesNotExist:
        return None

    client = OpenAI(api_key=api_key)

    # Contexto para a IA
    destination = trip.title if trip.title else "um destino turístico"
    duration = (trip.end_date - trip.start_date).days if trip.end_date and trip.start_date else 5
    
    # Prompt engenharia para garantir JSON
    prompt = f"""
    Crie um checklist de bagagem para uma viagem para {destination} com duração de {duration} dias.
    Considere o clima provável e cultura local.
    
    Retorne APENAS um JSON válido (sem markdown, sem ```json) com a seguinte estrutura:
    {{
        "Roupas": ["item 1", "item 2"],
        "Higiene": ["item 1", "item 2"],
        "Documentos": ["item 1"],
        "Eletrônicos": ["item 1"],
        "Outros": ["item 1"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo rápido e barato
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Erro OpenAI Checklist: {e}")
        return None

#-- Função Adicional para Geração de Roteiro AI --#    
def generate_itinerary_ai(trip, interests):
    """
    Gera itens de roteiro (atividades) baseados no destino e interesses.
    """
    try:
        config = APIConfiguration.objects.get(key='OPENAI_API', is_active=True)
        client = OpenAI(api_key=config.value)
    except APIConfiguration.DoesNotExist:
        return None

    destination = trip.title 
    
    # 1. Calcula a duração REAL da viagem no banco
    real_trip_duration = (trip.end_date - trip.start_date).days + 1
    if real_trip_duration < 1: real_trip_duration = 1

    # 2. Tenta encontrar um pedido explícito de dias no texto do usuário
    # Procura por números seguidos de "dias" ou "days" (ex: "12 dias", "10 days")
    match = re.search(r'(\d+)\s*(?:dias|days)', interests, re.IGNORECASE)

    if match:
        # SE o usuário pediu um número, usamos ele.
        requested_days = int(match.group(1))
        
        # Segurança: Não gera mais dias do que a viagem realmente tem
        # Ex: Se a viagem tem 20 dias e ele pede 15 -> Gera 15.
        # Ex: Se a viagem tem 5 dias e ele pede 10 -> Gera 5 (limite real).
        days = min(requested_days, real_trip_duration)
    else:
        # SE NÃO pediu, aplica a regra de economia (Max 7 dias)
        days = min(real_trip_duration, 7)

    prompt = f"""
    Crie um roteiro turístico detalhado para {destination} de {days} dias.
    O foco do viajante é: {interests}.
    
    Retorne APENAS um JSON válido com uma lista de eventos chamada "events".
    Cada evento deve ter:
    - "day": número do dia (1, 2, 3...)
    - "time": horário sugerido (formato HH:MM, ex: "09:00", "14:30")
    - "name": nome do local ou atividade
    - "location": O endereço aproximado ou nome da cidade (para geolocalização)
    - "category": use APENAS um destes valores: "ACTIVITY" (para passeios/museus), "RESTAURANT" (para comida), "HOTEL" (se for check-in)
    - "description": curta descrição (máx 100 caracteres)
    
    Exemplo de estrutura:
    {{
        "events": [
            {{ "day": 1, "time": "09:00", "name": "Museu do Louvre", "location": "Rue de Rivoli, 75001 Paris", "category": "ACTIVITY", "description": "Arte clássica." }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Erro OpenAI Roteiro: {e}")
        return None

#-- Função Adicional para Dicas de Viagem AI --#
def generate_trip_insights_ai(trip_id):
    from .models import Trip, APIConfiguration
    
    trip = Trip.objects.get(pk=trip_id)
    destination = trip.title 
    
    print(f"--- INICIANDO GERAÇÃO IA PARA: {destination} ---")

    # 1. Busca a chave
    try:
        config = APIConfiguration.objects.get(key='OPENAI_API')
        openai_key = config.value
    except APIConfiguration.DoesNotExist:
        print("ERRO: Chave OPENAI_API não encontrada.")
        return False

    prompt = f"""
    Aja como um guia local. Crie um guia sobre {destination}.
    Responda APENAS JSON válido:
    {{
        "currency_tip": "Texto sobre moeda e gorjeta",
        "electricity": "Texto sobre voltagem e tomadas",
        "phrases": "Lista de 5 frases úteis (ex: Olá, Obrigado) com tradução",
        "safety": "Dicas de segurança",
        "food": "Lista de 3 pratos típicos imperdíveis com breve descrição",
        "curiosity": "Uma curiosidade interessante"
    }}
    Responda em Português. Sem markdown.
    """

    try:
        client = OpenAI(api_key=openai_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON generator. Output raw JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"} 
        )

        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # --- FUNÇÃO DE LIMPEZA DE FORMATAÇÃO (NOVO) ---
        def format_ai_response(value):
            """Transforma listas ou dicionários em texto formatado com quebra de linha"""
            if isinstance(value, list):
                lines = []
                for item in value:
                    # Se o item for um dicionário (Ex: {'frase': 'Olá', 'trad': 'Hello'})
                    if isinstance(item, dict):
                        # Pega os valores do dicionário e junta com ": "
                        parts = list(item.values())
                        if len(parts) >= 2:
                            lines.append(f"• {parts[0]}: {parts[1]}")
                        elif len(parts) == 1:
                            lines.append(f"• {parts[0]}")
                    # Se for apenas texto na lista
                    elif isinstance(item, str):
                        lines.append(f"• {item}")
                return "\n".join(lines)
            return value
        # ----------------------------------------------

        # Monta o objeto final passando pela limpeza
        final_data = {
            'currency_tip': format_ai_response(data.get('currency_tip') or data.get('currency')),
            'electricity': format_ai_response(data.get('electricity') or data.get('plug')),
            'phrases': format_ai_response(data.get('phrases')), # AQUI ELE VAI ARRUMAR
            'safety': format_ai_response(data.get('safety')),
            'food': format_ai_response(data.get('food')),       # AQUI TAMBÉM
            'curiosity': format_ai_response(data.get('curiosity'))
        }

        trip.ai_insights = final_data
        trip.save()
        return True

    except Exception as e:
        print(f"ERRO CRÍTICO NA IA: {e}")
        return False

#-- Função Adicional para Extrair Código do País --#  
def get_country_code_from_address(address):
    """
    Recebe um endereço (string) e retorna o código ISO do país (ex: 'br', 'us').
    Retorna None se não encontrar.
    """
    if not address:
        return None
        
    address_lower = address.lower()
    
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
    'zimbábue': 'zw', 'zimbabwe': 'zw',    }

    for country_name, country_code in country_map.items():
        if country_name in address_lower:
            return country_code
            
    return None

#-- Função de envio de email --#
def get_db_mail_connection():
    print("--- DEBUG EMAIL: Iniciando busca ---")
    try:
        from .models import EmailConfiguration
        
        # Conta quantos registros existem para debug
        total_configs = EmailConfiguration.objects.count()
        print(f"--- DEBUG EMAIL: Total de registros na tabela: {total_configs} ---")
        
        config = EmailConfiguration.objects.first()

        if config:
            print(f"--- DEBUG EMAIL: Config encontrado! Host: {config.host} Port: {config.port} ---")
            return get_connection(
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                use_tls=config.use_tls,
                use_ssl=config.use_ssl,
                fail_silently=False
            )
        else:
            print("--- DEBUG EMAIL: Tabela existe mas está VAZIA. ---")
    except Exception as e:
        print(f"--- DEBUG EMAIL: ERRO CRÍTICO: {e} ---")
    
    return get_connection(fail_silently=False)

