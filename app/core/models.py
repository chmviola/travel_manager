from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Trip(models.Model):
    """
    Representa a Viagem como um todo.
    Agrupa todos os itens, gastos e configurações.
    """
    STATUS_CHOICES = [
        ('PLANNING', 'Planejamento'),
        ('CONFIRMED', 'Confirmada'),
        ('COMPLETED', 'Concluída'),
        ('CANCELED', 'Cancelada'),
    ]

    # Vínculo com o Usuário (Isolamento de dados)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    
    title = models.CharField(max_length=200, verbose_name="Nome da Viagem")
    start_date = models.DateField(null=True, blank=True, verbose_name="Início")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fim")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class TripItem(models.Model):
    """
    Tabela Polimórfica (Modular).
    Armazena Voos, Hotéis, Passeios e Restaurantes na mesma tabela
    diferenciando pelo 'type' e usando JSON para detalhes específicos.
    """
    TYPE_CHOICES = [
        ('FLIGHT', 'Voo'),
        ('HOTEL', 'Hospedagem'),
        ('ACTIVITY', 'Atração/Passeio'),
        ('RENTAL', 'Aluguel de Carro'),
        ('RESTAURANT', 'Restaurante'),
        ('NOTE', 'Anotação'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='items')
    
    # Informações Básicas
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=200, verbose_name="Nome do Item")
    
    # Agenda (Essencial para montar a timeline)
    start_datetime = models.DateTimeField(verbose_name="Início/Check-in")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Fim/Check-out")
    
    # Geolocalização (Para o Google Maps)
    # DecimalField é melhor que Float para coordenadas para manter precisão
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Endereço")

    # A MÁGICA DA MODULARIDADE: Campo JSON
    # Aqui guardamos: gate do voo, número do quarto, confirmação de reserva, etc.
    details = models.JSONField(default=dict, blank=True, verbose_name="Detalhes Específicos")

    class Meta:
        ordering = ['start_datetime']
        verbose_name = "Item da Viagem"
        verbose_name_plural = "Itens da Viagem"

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.name}"


class Expense(models.Model):
    """
    Controle Financeiro.
    Pode ser ligado apenas à viagem (gasto genérico) 
    ou a um item específico (ex: pagamento do Hotel X).
    """
    CURRENCY_CHOICES = [
        ('BRL', 'Real (BRL)'),
        ('USD', 'Dólar Americano (USD)'),
        ('EUR', 'Euro (EUR)'),
        # América do Sul
        ('CLP', 'Peso Chileno (CLP)'),
        ('ARS', 'Peso Argentino (ARS)'),
        ('UYU', 'Peso Uruguaio (UYU)'),
        ('COP', 'Peso Colombiano (COP)'),
        ('PEN', 'Sol Peruano (PEN)'),
        # América do Norte e outros
        ('CAD', 'Dólar Canadense (CAD)'),
        ('GBP', 'Libra Esterlina (GBP)'),
        ('CHF', 'Franco Suíço (CHF)'),
        ('AUD', 'Dólar Australiano (AUD)'),
        ('JPY', 'Iene Japonês (JPY)'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses')
    
    # Opcional: Ligar o gasto a um item (ex: Gasto do item "Hotel Ibis")
    item = models.ForeignKey(TripItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_expenses')
    
    description = models.CharField(max_length=200, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='BRL')
    
    category = models.CharField(max_length=50, verbose_name="Categoria") # Ex: Alimentação, Transporte
    date = models.DateField(default=models.functions.Now)

    class Meta:
        ordering = ['date']
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"

    def __str__(self):
        return f"{self.description} - {self.currency} {self.amount}"