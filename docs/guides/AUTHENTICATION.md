# TLGeo2QGIS - Authentication

## Overview

TLGeo2QGIS plugin requires authentication with GEOADMIN Strapi backend. The plugin uses JWT (JSON Web Token) for secure API communication.

## Features

- **Automatic Login**: Login dialog appears on plugin load if not authenticated
- **Token Persistence**: Login credentials are remembered across QGIS sessions
- **Token Validation**: Token is validated on startup via `/api/users/me` endpoint
- **Secure Upload**: All layer uploads include JWT authentication
- **Easy Logout**: Logout option available in TLGeo menu

## Configuration

Set your GEOADMIN Strapi URL in `.env` file:

```bash
GEOADMIN_STRAPI_URL=http://localhost:11000
```

For production, use HTTPS:

```bash
GEOADMIN_STRAPI_URL=https://your-domain.com
```

## Usage

### First Time Login

1. Install and activate the plugin in QGIS
2. Login dialog will appear automatically
3. Enter your GEOADMIN email/username and password
4. Click "Đăng nhập" (Login)
5. Plugin will initialize after successful authentication

### Subsequent Sessions

The plugin remembers your login:
- Token is stored securely in QGIS settings
- No need to login again unless token expires
- Token is validated on each plugin load

### Logout

To logout:
1. Open TLGeo menu in QGIS menu bar
2. Click "Đăng xuất" (Logout)
3. Restart the plugin to login with different credentials

## Token Storage

Tokens are stored using Qt's QSettings:
- **Organization**: TLGeo
- **Application**: QGIS2Plugin
- **Keys**: 
  - `auth/jwt_token` - JWT token string
  - `auth/user_id` - User ID
  - `auth/user_email` - User email
  - `auth/user_username` - Username

### Manual Token Cleanup (if needed)

On macOS/Linux:
```bash
# View stored settings
defaults read com.TLGeo.QGIS2Plugin

# Delete all settings
defaults delete com.TLGeo.QGIS2Plugin
```

On Windows:
- Settings are stored in Windows Registry
- Path: `HKEY_CURRENT_USER\Software\TLGeo\QGIS2Plugin`

## Security Considerations

### HTTPS Warning

If you connect to a non-localhost server via HTTP (not HTTPS), the plugin will show a security warning. This is normal for development but should use HTTPS in production.

### Password Security

- Passwords are never logged or stored
- Passwords are cleared from memory after login attempt
- Only JWT tokens are stored, not passwords

### Token Security

- Tokens are stored in QSettings (not encrypted)
- For higher security in production, consider using OS keychain (requires `keyring` package)
- Tokens expire after 30 days (Strapi default, configurable)

## Troubleshooting

### "Không thể kết nối đến server"

**Problem**: Cannot connect to Strapi server

**Solutions**:
1. Check if Strapi server is running
2. Verify `GEOADMIN_STRAPI_URL` in `.env` file
3. Check network connectivity
4. Check firewall settings

### "Email hoặc mật khẩu không đúng"

**Problem**: Invalid credentials

**Solutions**:
1. Verify your GEOADMIN account credentials
2. Check if account is active (not blocked)
3. Try resetting password if forgotten

### "Phiên đăng nhập đã hết hạn"

**Problem**: Token expired

**Solutions**:
1. Click "OK" and login again with credentials
2. Token typically expires after 30 days

### Plugin doesn't ask for login

**Problem**: Plugin loads without authentication

**Solutions**:
1. Check if you have a valid token stored
2. Manually clear QSettings (see "Manual Token Cleanup")
3. Restart QGIS

## API Endpoints Used

### Login
```
POST /api/auth-ext/login
Body: {
  "identifier": "user@example.com",
  "password": "password123"
}
Response: {
  "jwt": "eyJhbGci...",
  "user": { ... }
}
```

### Validate Token
```
GET /api/users-ext/me
Headers: {
  "Authorization": "Bearer {jwt_token}"
}
Response: {
  "id": 1,
  "email": "user@example.com",
  ...
}
```

### Logout (Optional)
```
POST /api/auth-ext/logout
Headers: {
  "Authorization": "Bearer {jwt_token}"
}
```

### Upload Layer
```
POST /api/upload
Headers: {
  "Authorization": "Bearer {jwt_token}"
}
Body: multipart/form-data with files
```

## Development

### AuthService API

```python
from util.auth_service import AuthService

# Initialize
auth = AuthService()

# Login
result = auth.login("user@example.com", "password")
if result['success']:
    print(f"Logged in as {result['user']['email']}")

# Check if authenticated
if auth.is_authenticated():
    print("User has token")

# Validate token
if auth.validate_token():
    print("Token is valid")

# Get current user
user = auth.get_current_user()

# Get token for API calls
token = auth.get_token()

# Logout
auth.logout()
```

## Related Documentation

- [Task 010: Authentication Implementation](./04_completed/task_010_authentication_jwt.md)
- [Strapi Authentication Docs](https://docs.strapi.io/dev-docs/plugins/users-permissions)
- [QSettings Documentation](https://doc.qt.io/qt-5/qsettings.html)
