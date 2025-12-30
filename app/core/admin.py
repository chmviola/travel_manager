from django.contrib import admin
from .models import Trip, TripItem, TripAttachment, Expense, APIConfiguration, Checklist, ChecklistItem

admin.site.register(Trip)

admin.site.register(TripItem)

admin.site.register(TripAttachment)

admin.site.register(Expense)

admin.site.register(Checklist)

admin.site.register(ChecklistItem)

admin.site.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('get_key_display', 'is_active', 'updated_at')
    list_filter = ('is_active', 'key')
    search_fields = ('key', 'description')
    
    # Isso melhora a visualização do nome do serviço na lista
    def get_key_display(self, obj):
        return obj.get_key_display()
    get_key_display.short_description = 'Serviço / API'