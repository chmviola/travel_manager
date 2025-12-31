import json
import requests
from django.conf import settings
from datetime import timedelta, datetime
from openai import OpenAI
from .models import APIConfiguration, Trip

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
    Você é um guia de viagem especialista. Para o destino '{destination}', forneça um resumo JSON com:
    - currency_tip: Dica sobre moeda e se deve dar gorjeta.
    - plug_type: Tipo de tomada usada.
    - safety_tip: Uma dica rápida de segurança.
    - basic_phrases: Uma string com 3 frases essenciais na lingua local (Olá, Obrigado, Quanto custa).
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

    destination = trip.title # Ou trip.location se tiver mudado
    days = (trip.end_date - trip.start_date).days + 1
    if days < 1: days = 1
    if days > 7: days = 7 # Limite para não gastar muitos tokens

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
def generate_trip_insights_ai(destination):
    """
    Gera dicas culturais e práticas sobre o destino.
    """
    try:
        config = APIConfiguration.objects.get(key='OPENAI_API', is_active=True)
        client = OpenAI(api_key=config.value)
    except APIConfiguration.DoesNotExist:
        return None

    prompt = f"""
    Estou viajando para: {destination}.
    Gere um JSON com dicas práticas e curtas (máximo 1 frase longa cada).
    Campos obrigatórios:
    - "currency_tip": Sobre a moeda local e se deve dar gorjeta.
    - "plug": Tipo de tomada (ex: Tipo G) e voltagem.
    - "phrases": 3 frases essenciais na língua local (Olá, Obrigado, Quanto custa).
    - "safety": Uma dica de segurança importante ou região a evitar.
    - "curiosity": Uma curiosidade cultural rápida.

    Responda em Português do Brasil.
    Retorne APENAS o JSON.
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
        print(f"Erro OpenAI Insights: {e}")
        return None