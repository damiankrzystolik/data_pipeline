import pytest
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_str_returns_email(self):
        user = UserFactory()
        assert str(user) == user.email

    def test_email_is_unique(self):
        UserFactory(email='unique@example.com')
        with pytest.raises(Exception):
            UserFactory(email='unique@example.com')