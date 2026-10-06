from django.db.models import QuerySet
from .models import User


class UserSelector:
    @staticmethod
    def get_active_users() -> QuerySet:
        return User.objects.filter(is_active=True).order_by('-date_joined')

    @staticmethod
    def get_by_email(email: str):
        return User.objects.filter(email=email).first()