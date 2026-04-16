import pytest
from django.test import RequestFactory
from unittest.mock import MagicMock

from apps.base.user_api_secret_mgmt.views import _get_loader, _parse_current_team
from apps.core.utils.loader import LanguageLoader


@pytest.mark.unit
class TestParseCurrentTeam:
    def _make_request(self, cookies=None):
        factory = RequestFactory()
        request = factory.get("/fake-url")
        if cookies:
            request.COOKIES = cookies
        return request

    def _make_loader(self):
        return LanguageLoader(app="core", default_lang="en")

    def test_valid_integer_cookie(self):
        request = self._make_request({"current_team": "5"})
        loader = self._make_loader()
        team, error = _parse_current_team(request, loader)
        assert team == 5
        assert error is None

    def test_zero_value_cookie(self):
        request = self._make_request({"current_team": "0"})
        loader = self._make_loader()
        team, error = _parse_current_team(request, loader)
        assert team == 0
        assert error is None

    def test_invalid_cookie_value(self):
        request = self._make_request({"current_team": "abc"})
        loader = self._make_loader()
        team, error = _parse_current_team(request, loader)
        assert team is None
        assert error is not None
        assert error.status_code == 400

    def test_missing_cookie_uses_default(self):
        request = self._make_request({})
        loader = self._make_loader()
        team, error = _parse_current_team(request, loader)
        assert team == 0
        assert error is None


@pytest.mark.unit
class TestGetLoader:
    def test_returns_loader_with_user_locale(self):
        request = MagicMock()
        request.user.locale = "zh-CN"
        loader = _get_loader(request)
        assert isinstance(loader, LanguageLoader)

    def test_defaults_to_en_when_no_user(self):
        request = MagicMock()
        request.user = None
        loader = _get_loader(request)
        assert isinstance(loader, LanguageLoader)
