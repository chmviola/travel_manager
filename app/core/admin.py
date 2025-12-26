from django.contrib import admin
from .models import Trip, TripItem, Expense

admin.site.register(Trip)
admin.site.register(TripItem)
admin.site.register(Expense)