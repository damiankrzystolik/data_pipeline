import structlog
from django.db import transaction
from apps.core.exceptions import BusinessLogicError
from .models import User

logger = structlog.get_logger(__name__)


class UserService:
    @staticmethod
    @transaction.atomic
    def create_user(email: str, password: str, **kwargs) -> User:
        if User.objects.filter(email=email).exists():
            raise BusinessLogicError('User with this email already exists.')
        user = User.objects.create_user(email=email, password=password, **kwargs)
        logger.info('user_created', user_id=str(user.id))
        return user