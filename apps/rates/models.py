from django.db import models

class RawRatesTable(models.Model):
    effective_date = models.DateField(unique=True)
    table_no = models.CharField(max_length=20)
    payload = models.JSONField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.effective_date} - {self.table_no}"


class Rate(models.Model):
    currency_code = models.CharField(max_length=3)
    currency_name = models.CharField(max_length=100)
    date = models.DateField()
    mid = models.DecimalField(max_digits=12, decimal_places=6)

    class Meta:
        unique_together = ('currency_code', 'date')
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.currency_code} {self.date}: {self.mid}"