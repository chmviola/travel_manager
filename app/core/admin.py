from django.contrib import admin
from .models import Trip, TripItem, TripAttachment, Expense, APIConfiguration, Checklist, ChecklistItem

admin.site.register(Trip)

admin.site.register(TripItem)

admin.site.register(TripAttachment)

admin.site.register(Expense)

admin.site.register(Checklist)

admin.site.register(ChecklistItem)

@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'is_active')
    search_fields = ('key',)