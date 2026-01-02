import requests # Para chamar a API do Google pelo Python
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# --- MODELO DE VIAGEM ---
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

    # Campo para guardar as dicas da IA (Moeda, Tomada, etc)
    ai_insights = models.JSONField(blank=True, null=True, default=dict)

    def get_user_role(self, user):
        if user == self.user:
            return 'owner'
        try:
            collaborator = self.collaborators.get(user=user)
            return collaborator.role
        except TripCollaborator.DoesNotExist:
            return None

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# --- MODELO DE ITENS DA VIAGEM ---
class TripItem(models.Model):
    """
    Tabela Polimórfica (Modular).
    Armazena Voos, Hotéis, Passeios e Restaurantes na mesma tabela
    diferenciando pelo 'type' e usando JSON para detalhes específicos.
    """
    TYPE_CHOICES = [
        ('FLIGHT', 'Voo'),
        ('BUS', 'Ônibus'),
        ('TRAIN', 'Trem'),
        ('CRUISE', 'Cruzeiro'),
        ('HOTEL', 'Hospedagem'),
        ('ACTIVITY', 'Atração/Passeio'),
        ('TOUR', 'Tour Guiado'),
        ('WINARY', 'Atração/Vinícola'),
        ('MUSEUM', 'Atração/Museu'),
        ('RENTAL', 'Aluguel de Carro'),
        ('RESTAURANT', 'Restaurante'),
        ('TRANSPORT', 'Transporte Local'),
        ('BUYING', 'Compras'),
        ('INSURANCE', 'Seguro Viagem'),
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

    # NOVOS CAMPOS DE CLIMA
    weather_temp = models.CharField(max_length=10, blank=True, null=True) # Ex: 24
    weather_condition = models.CharField(max_length=100, blank=True, null=True) # Ex: Nublado
    weather_icon = models.CharField(max_length=255, blank=True, null=True) # URL do ícone

    # A MÁGICA DA MODULARIDADE: Campo JSON
    # Aqui guardamos: gate do voo, número do quarto, confirmação de reserva, etc.
    details = models.JSONField(default=dict, blank=True, verbose_name="Detalhes Específicos")

    class Meta:
        ordering = ['start_datetime']
        verbose_name = "Item da Viagem"
        verbose_name_plural = "Itens da Viagem"

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.name}"

    def save(self, *args, **kwargs):
        # Verifica se tem endereço mas NÃO tem coordenada salva
        if self.location_address and (not self.location_lat or not self.location_lng):
            try:
                # Chama a API de Geocoding do Google (Server-Side)
                api_key = settings.GOOGLE_MAPS_API_KEY
                base_url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "address": self.location_address,
                    "key": api_key
                }

                response = requests.get(base_url, params=params)
                data = response.json()

                if data['status'] == 'OK':
                    location = data['results'][0]['geometry']['location']
                    self.location_lat = location['lat']
                    self.location_lng = location['lng']
                    print(f"Coordenadas encontradas para {self.name}: {self.location_lat}, {self.location_lng}")
                else:
                    print(f"Google não encontrou o endereço: {self.location_address}")

            except Exception as e:
                print(f"Erro ao geocodificar: {e}")

        super().save(*args, **kwargs)

# --- MODELO DE GASTOS ---
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

# --- MODELO DE ANEXOS DE ARQUIVOS ---
class TripAttachment(models.Model):
    item = models.ForeignKey(TripItem, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='trip_files/', verbose_name="Arquivo (PDF/Img)")
    description = models.CharField(max_length=100, blank=True, verbose_name="Descrição (Opcional)")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Anexo de {self.item.name}"

# --- MODELO DE COLABORAÇÃO ---
class TripCollaborator(models.Model):
    ROLE_CHOICES = [
        ('viewer', 'Somente Leitura'),
        ('editor', 'Acesso Total (Editar/Excluir)'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_trips')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'user') # Impede compartilhar 2x com a mesma pessoa

    def __str__(self):
        return f"{self.user.username} - {self.trip.title} ({self.role})"

# --- MODELO DE CONFIGURAÇÕES DE API ---
class APIConfiguration(models.Model):
    KEY_CHOICES = [
        ('WEATHER_API', 'WeatherAPI (Clima)'),
        ('GOOGLE_MAPS', 'Google Maps API'),
        ('OPENAI_API', 'OpenAI API'),
        # Futuramente você pode adicionar outras aqui (OpenAI, AWS, etc)
    ]

    key = models.CharField(max_length=50, choices=KEY_CHOICES, unique=True, verbose_name="Serviço/API")
    value = models.CharField(max_length=255, verbose_name="Chave de Acesso (Key)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição/Notas")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_key_display()

    class Meta:
        verbose_name = "Configuração de API"
        verbose_name_plural = "Configurações de API"

# --- MODELO DE CHECKLIST ---
class Checklist(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='checklist')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checklist - {self.trip.title}"

# --- MODELO ITENS DO CHECKLIST ---
class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=50, default="Geral") # Ex: Roupas, Higiene, Documentos
    item = models.CharField(max_length=200)
    is_checked = models.BooleanField(default=False)

    def __str__(self):
        return self.item

#--- MODELO DE FOTOS DA VIAGEM ---
class TripPhoto(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='trip_photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.trip.title}"

    # Opcional: Deleta o arquivo físico ao deletar o objeto do banco
    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

# --- MODELO DE CONFIGURAÇÕES DE E-MAIL ---
class EmailConfiguration(models.Model):
    backend = models.CharField(max_length=100, default='django.core.mail.backends.smtp.EmailBackend', verbose_name="Backend")
    host = models.CharField(max_length=255, verbose_name="Servidor SMTP (Host)")
    port = models.IntegerField(default=587, verbose_name="Porta")
    username = models.CharField(max_length=255, verbose_name="Usuário/E-mail", blank=True, null=True)
    password = models.CharField(max_length=255, verbose_name="Senha", blank=True, null=True)
    use_tls = models.BooleanField(default=True, verbose_name="Usar TLS")
    use_ssl = models.BooleanField(default=False, verbose_name="Usar SSL")
    default_from_email = models.EmailField(verbose_name="E-mail de Envio (Remetente)")

    class Meta:
        verbose_name = "Configuração de E-mail"
        verbose_name_plural = "Configuração de E-mail"

    def __str__(self):
        return f"SMTP: {self.host}:{self.port}"

    # Método para garantir que só exista 1 configuração no banco (Singleton)
    def save(self, *args, **kwargs):
        if not self.pk and EmailConfiguration.objects.exists():
            # Se já existe, atualiza o primeiro em vez de criar novo
            self.pk = EmailConfiguration.objects.first().pk
        super().save(*args, **kwargs)