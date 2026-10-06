from django.contrib import admin
from .models import RawRatesTable

# Register your models here.
@admin.register(RawRatesTable)
class RawRatesTableAdmin(admin.ModelAdmin):
    list_display = ('effective_date', 'table_no', 'fetched_at')
    ordering = ['-effective_date']
