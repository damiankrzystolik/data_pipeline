from django.db import models

# Create your models here.
class RawRatesTable(models.Model):
    effective_date = models.DateField(unique=True)
    table_no = models.CharField(max_length=20)
    payload = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date']
        __str__ = lambda self: 'Raw Rates Table'