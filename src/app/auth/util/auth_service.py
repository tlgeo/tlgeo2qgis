"""
Authentication Service for TLGeo2QGIS Plugin
Handles JWT authentication with GEOADMIN Strapi backend
"""

import os
import requests
from typing import Optional, Dict, Any
from PyQt5.QtCore import QSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AuthService:
    """
    Authentication service for managing JWT tokens and user sessions
    """
    
    def __init__(self):
        """Initialize AuthService with QSettings for token storage"""
        self.settings = QSettings("TLGeo", "QGIS2Plugin")
        self.strapi_url = os.getenv("GEOADMIN_STRAPI_URL", "http://localhost:11000")
        
        # Ensure URL doesn't have trailing slash
        if self.strapi_url.endswith('/'):
            self.strapi_url = self.strapi_url[:-1]
    
    def login(self, identifier: str, password: str) -> Dict[str, Any]:
        """
        Login to GEOADMIN Strapi using auth-ext API
        
        Args:
            identifier: Username or email
            password: User password
            
        Returns:
            dict: Response with 'success', 'jwt', 'user', and optional 'error'
            
        Example:
            result = auth.login("user@example.com", "password123")
            if result['success']:
                print(f"Logged in as {result['user']['email']}")
        """
        try:
            url = f"{self.strapi_url}/api/auth-ext/login"
            payload = {
                "identifier": identifier,
                "password": password
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Save token and user info
                self.save_token(data.get('jwt'), data.get('user'))
                return {
                    'success': True,
                    'jwt': data.get('jwt'),
                    'user': data.get('user')
                }
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Thông tin đăng nhập không hợp lệ')
                return {
                    'success': False,
                    'error': error_msg
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Email hoặc mật khẩu không đúng'
                }
            else:
                return {
                    'success': False,
                    'error': f'Lỗi server: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Kết nối đến server quá thời gian chờ'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': f'Không thể kết nối đến server {self.strapi_url}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Lỗi không xác định: {str(e)}'
            }
    
    def save_token(self, jwt: str, user: Optional[Dict[str, Any]] = None):
        """
        Store JWT token and user information in QSettings
        
        Args:
            jwt: JWT token string
            user: User information dictionary (optional)
        """
        if jwt:
            self.settings.setValue("auth/jwt_token", jwt)
        
        if user:
            self.settings.setValue("auth/user_id", user.get('id'))
            self.settings.setValue("auth/user_email", user.get('email'))
            self.settings.setValue("auth/user_username", user.get('username'))
    
    def get_token(self) -> Optional[str]:
        """
        Retrieve stored JWT token from QSettings
        
        Returns:
            str: JWT token or None if not found
        """
        return self.settings.value("auth/jwt_token", None)
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get stored user information from QSettings
        
        Returns:
            dict: User info or None if not found
        """
        user_id = self.settings.value("auth/user_id", None)
        if user_id is None:
            return None
            
        return {
            'id': user_id,
            'email': self.settings.value("auth/user_email"),
            'username': self.settings.value("auth/user_username")
        }
    
    def validate_token(self) -> bool:
        """
        Validate stored token by calling /api/users-ext/me endpoint
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        token = self.get_token()
        if not token:
            return False
        
        try:
            url = f"{self.strapi_url}/api/users-ext/me"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Token is valid, optionally update user info
                user_data = response.json()
                self.save_token(token, user_data)
                return True
            else:
                # Token is invalid or expired
                return False
                
        except Exception:
            # Network error or other issue - assume invalid
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user information from server using stored token
        
        Returns:
            dict: User data from server or None if request fails
        """
        token = self.get_token()
        if not token:
            return None
        
        try:
            url = f"{self.strapi_url}/api/users-ext/me"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    def logout(self):
        """
        Clear stored token and user data from QSettings
        """
        self.settings.remove("auth/jwt_token")
        self.settings.remove("auth/user_id")
        self.settings.remove("auth/user_email")
        self.settings.remove("auth/user_username")
    
    def is_authenticated(self) -> bool:
        """
        Check if user has a stored token (doesn't validate it)
        
        Returns:
            bool: True if token exists, False otherwise
        """
        token = self.get_token()
        return token is not None and token != ""
    
    def check_https_security(self) -> Optional[str]:
        """
        Check if connection is using HTTPS for non-localhost URLs
        
        Returns:
            str: Warning message if using HTTP in production, None otherwise
        """
        if not self.strapi_url.startswith("https://") and "localhost" not in self.strapi_url and "127.0.0.1" not in self.strapi_url:
            return (
                "Cảnh báo bảo mật:\n\n"
                f"Bạn đang kết nối đến server qua HTTP không mã hóa ({self.strapi_url}).\n\n"
                "Khuyến nghị sử dụng HTTPS trong môi trường production để bảo vệ thông tin đăng nhập."
            )
        return None
