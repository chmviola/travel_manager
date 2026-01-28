from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.utils import get_exchange_rate
import time

class Command(BaseCommand):
    help = 'Limpa o cache e força uma nova consulta de cotações na API'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("--- INICIANDO TESTE DE COTAÇÕES ---"))
        
        # Lista de moedas para testar
        currencies = ['USD', 'EUR', 'GBP', 'CAD']

        for curr in currencies:
            # 1. Define a chave do cache (mesma lógica do utils.py)
            cache_key = f"exchange_rate_{curr}"
            
            # 2. Apaga do cache para obrigar o sistema a ir na API
            cache.delete(cache_key)
            self.stdout.write(f"Cache limpo para {curr}. Buscando na API...")
            
            # 3. Chama a função (que agora vai tentar a API obrigatoriamente)
            start_time = time.time()
            rate = get_exchange_rate(curr)
            end_time = time.time()
            
            duration = end_time - start_time

            # 4. Análise visual do resultado
            # Se for muito rápido (< 0.1s) e vier valor "redondo" (fallback), algo deu errado.
            # Se demorar um pouco e vier valor quebrado (ex: 6.1234), funcionou.
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ {curr}: R$ {rate:.4f} (Tempo: {duration:.2f}s)")
            )

        self.stdout.write(self.style.WARNING("--- FIM DO TESTE ---"))
        self.stdout.write("Nota: Se os valores forem exatos (ex: 6.1500), é o Fallback.")
        self.stdout.write("Nota: Se os valores forem quebrados (ex: 6.1243), é a API.")