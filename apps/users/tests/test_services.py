import pytest
from apps.users.services import UserService
from apps.core.exceptions import BusinessLogicError


@pytest.mark.django_db
class TestUserService:
    def test_create_user_success(self):
        user = UserService.create_user(
            email='new@example.com',
            password='securepass123',
            username='newuser',
        )
        assert user.email == 'new@example.com'
        assert user.check_password('securepass123')

    def test_duplicate_email_raises(self):
        UserService.create_user(email='dup@example.com', password='pass', username='u1')
        with pytest.raises(BusinessLogicError):
            UserService.create_user(email='dup@example.com', password='pass', username='u2')