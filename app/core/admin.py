from django.contrib import admin
from .models import (
    Trip, TripItem, TripAttachment, Expense, 
    APIConfiguration, Checklist, ChecklistItem, 
    EmailConfiguration, AccessLog # Adicionados aqui
)

# Registros Simples
admin.site.register(Trip)
admin.site.register(TripItem)
admin.site.register(TripAttachment)
admin.site.register(Expense)
admin.site.register(Checklist)
admin.site.register(ChecklistItem)

# Registro Customizado para Configuração de API
@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_active')
    search_fields = ('key',)

# --- NOVO: Registro para Configuração de E-mail ---
@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'username', 'use_tls', 'use_ssl')
    # Como você criou um Singleton no models.py, 
    # aqui você poderá editar a única configuração existente.

# --- NOVO: Registro para Logs de Acesso ---
@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('timestamp',) # Logs geralmente são apenas leitura