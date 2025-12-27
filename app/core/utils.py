import requests

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
