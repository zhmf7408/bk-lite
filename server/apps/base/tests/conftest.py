import pytest
from rest_framework.test import APIClient

from apps.base.models import User
from apps.base.tests.factories import UserAPISecretFactory, UserFactory


@pytest.fixture
def user_with_permissions(db):
    """Create a user with API secret permissions."""
    user = UserFactory(
        username="permuser",
        group_list=[{"id": 1, "name": "Team Alpha"}, {"id": 2, "name": "Team Beta"}],
        roles=["admin"],
        is_superuser=True,
    )
    return user


@pytest.fixture
def api_client_with_team(user_with_permissions):
    """Return an APIClient authenticated with team cookie set."""
    client = APIClient()
    client.force_authenticate(user=user_with_permissions)
    client.cookies["current_team"] = "1"
    return client


@pytest.fixture
def user_api_secret(db, user_with_permissions):
    """Create a UserAPISecret for the default test user."""
    return UserAPISecretFactory(
        username=user_with_permissions.username,
        domain=user_with_permissions.domain,
        team=1,
    )
