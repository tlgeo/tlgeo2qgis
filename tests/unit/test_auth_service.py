import pytest
from unittest.mock import MagicMock, patch
from src.util.auth_service import AuthService

# Use the mocked QSettings from conftest
from PyQt5.QtCore import QSettings

class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        # Reset settings before each test
        settings = QSettings("TLGeo", "QGIS2Plugin")
        settings.store = {}
        return AuthService()

    def test_login_success(self, auth_service):
        """Test successful login with JWT return"""
        with patch('requests.post') as mock_post:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jwt": "fake_token_123",
                "user": {
                    "id": 1,
                    "email": "test@example.com",
                    "username": "tester"
                }
            }
            mock_post.return_value = mock_response
            
            # Call login
            result = auth_service.login("test@example.com", "password")
            
            # Assertions
            assert result['success'] is True
            assert result['jwt'] == "fake_token_123"
            assert auth_service.get_token() == "fake_token_123"
            
            # Verify correct endpoint was called
            expected_url = f"{auth_service.strapi_url}/api/auth-ext/login"
            mock_post.assert_called_with(
                expected_url, 
                json={"identifier": "test@example.com", "password": "password"},
                timeout=10
            )

    def test_login_failure(self, auth_service):
        """Test login failure (401)"""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response
            
            result = auth_service.login("wrong", "pass")
            
            assert result['success'] is False
            assert auth_service.get_token() is None

    def test_validate_token_success(self, auth_service):
        """Test token validation via /api/users-ext/me"""
        # Set initial token
        auth_service.save_token("valid_token", {"id": 1})
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "email": "updated@example.com"}
            mock_get.return_value = mock_response
            
            is_valid = auth_service.validate_token()
            
            assert is_valid is True
            mock_get.assert_called_with(
                f"{auth_service.strapi_url}/api/users-ext/me",
                headers={"Authorization": "Bearer valid_token"},
                timeout=10
            )

    def test_validate_token_failure(self, auth_service):
        """Test token validation failure (expired)"""
        auth_service.save_token("expired_token", {"id": 1})
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            is_valid = auth_service.validate_token()
            
            assert is_valid is False

    def test_logout(self, auth_service):
        """Test logout clears storage"""
        auth_service.save_token("token", {"id": 1})
        assert auth_service.get_token() == "token"
        
        auth_service.logout()
        assert auth_service.get_token() is None
