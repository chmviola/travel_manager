from django import template
import re
import ast

register = template.Library()

@register.filter
def extract_note(value):
    if not value:
        return ""
    
    # Se já for dicionário, retorna direto
    if isinstance(value, dict):
        return value.get('notes', '')

    val_str = str(value)

    # Tenta o método elegante (Python)
    try:
        data = ast.literal_eval(val_str)
        if isinstance(data, dict):
            return data.get('notes', '')
    except:
        pass

    # Se falhar (por causa de \r\n ou caracteres estranhos), usa FORÇA BRUTA (Regex)
    # Procura por: 'notes': 'PEGAR TUDO AQUI' ou "notes": "PEGAR TUDO AQUI"
    # O regex abaixo pega o conteúdo entre as aspas após 'notes':
    match = re.search(r"['\"]notes['\"]\s*:\s*['\"](.*?)['\"]\s*}?$", val_str, re.DOTALL)
    if match:
        # Remove caracteres de escape de Python se sobrarem
        clean_text = match.group(1).replace('\\r\\n', '\n').replace('\\n', '\n')
        return clean_text
    
    return val_str
