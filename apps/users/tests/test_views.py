import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserCreateView:
    url = reverse('user-create')

    def test_create_user_returns_201(self, api_client):
        payload = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'securepass123',
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'new@example.com'

    def test_create_user_duplicate_email_returns_400(self, api_client):
        UserFactory(email='existing@example.com')
        payload = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password': 'securepass123',
        }
        response = api_client.post(self.url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_missing_email_returns_400(self, api_client):
        response = api_client.post(self.url, {'username': 'nomail'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
