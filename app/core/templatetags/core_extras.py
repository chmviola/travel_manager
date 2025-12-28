from django import template
import ast

register = template.Library()

@register.filter
def extract_note(value):
    """
    Tenta extrair o texto da chave 'notes' independentemente
    se o valor é um Dicionário ou uma String.
    """
    if not value:
        return ""
    
    data = value

    # Se for string (ex: "{'notes': 'texto'}"), converte para dicionário
    if isinstance(value, str):
        try:
            # ast.literal_eval é mais seguro que json.loads para strings pythonicas (aspas simples)
            data = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # Se não conseguir converter, retorna a string original limpa
            return value

    # Se agora for um dicionário, tenta pegar a nota
    if isinstance(data, dict):
        return data.get('notes', '')
    
    return str(value)

