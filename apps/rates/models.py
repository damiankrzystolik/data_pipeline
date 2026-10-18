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
        constraints = [
            models.UniqueConstraint(fields=['currency_code', 'date'], name='currency_code_date_unique')
        ]
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.currency_code} {self.date}: {self.mid}"


class MonthlyRatesStats(models.Model):
    currency_code = models.CharField(max_length=3)
    month = models.DateField()
    avg_mid = models.DecimalField(max_digits=12, decimal_places=6)
    min_mid = models.DecimalField(max_digits=12, decimal_places=6)
    max_mid = models.DecimalField(max_digits=12, decimal_places=6)
    stddev_mid = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['currency_code', 'month'], name='unique_currency_month'),
        ]
        ordering = ['month']

    def __str__(self):
        return f"{self.currency_code} {self.month:%Y-%m} {self.avg_mid}"