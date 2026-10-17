from django.contrib import admin
from .models import RawRatesTable, Rate

# Register your models here.
@admin.register(RawRatesTable)
class RawRatesTableAdmin(admin.ModelAdmin):
    list_display = ('effective_date', 'table_no', 'fetched_at')
    ordering = ['-effective_date']

@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('currency_code', 'date', 'mid')
    list_filter = ('currency_code', 'date')
    search_fields = ['currency_code', 'date']