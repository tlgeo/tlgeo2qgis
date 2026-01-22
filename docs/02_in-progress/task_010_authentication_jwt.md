# Task 010: Implement Authentication & JWT Token Management

## Description
Implement user authentication system for tlgeo2qgis plugin with login screen and JWT token management. The plugin will validate the JWT token on startup and prompt for login if the token is invalid or expired.

## Objectives
- [ ] Create login dialog UI with username/password fields
- [ ] Implement secure JWT token storage (QSettings or keychain)
- [ ] Add authentication service to handle login/logout
- [ ] Implement token validation via `/api/users/me` endpoint
- [ ] Add automatic token check on plugin load
- [ ] Show login dialog when token is invalid/expired
- [ ] Store authenticated user information
- [ ] Add logout functionality
- [ ] Handle authentication errors gracefully

## Technical Requirements

### 1. Login Dialog UI
**File**: `src/ui/login_dialog.py`

**Features**:
- Username/email field
- Password field (masked input)
- Login button
- Cancel button
- "Remember me" checkbox (optional)
- Error message display area
- GEOADMIN logo/branding
- Loading indicator during authentication

**Design**:
```python
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        # UI setup with QFormLayout
        # Email/username input
        # Password input (QLineEdit with EchoMode.Password)
        # Login/Cancel buttons
        # Error label
    
    def on_login_clicked(self):
        # Validate inputs
        # Call authentication service
        # Handle response
        # Close dialog if successful
```

### 2. Authentication Service
**File**: `src/util/auth_service.py`

**Features**:
```python
class AuthService:
    def __init__(self):
        self.settings = QSettings("TLGeo", "QGIS2Plugin")
        self.strapi_url = os.getenv("GEOADMIN_STRAPI_URL", "http://localhost:1337")
        
    def login(self, identifier: str, password: str) -> dict:
        """
        Login to GEOADMIN Strapi
        POST /api/auth/local
        Returns: {"jwt": "...", "user": {...}}
        """
        
    def save_token(self, jwt: str, user: dict):
        """Store JWT token securely in QSettings"""
        
    def get_token(self) -> str:
        """Retrieve stored JWT token"""
        
    def validate_token(self) -> bool:
        """
        Validate token via GET /api/users/me
        Returns: True if valid, False if expired/invalid
        """
        
    def get_current_user(self) -> dict:
        """Get user info from /api/users/me"""
        
    def logout(self):
        """Clear stored token and user data"""
        
    def is_authenticated(self) -> bool:
        """Check if user has valid token"""
```

### 3. Token Storage Strategy

**Option A: QSettings** (Recommended for cross-platform)
```python
settings = QSettings("TLGeo", "QGIS2Plugin")
settings.setValue("auth/jwt_token", jwt_token)
settings.setValue("auth/user_id", user_id)
settings.setValue("auth/user_email", user_email)
```

**Option B: Keychain** (More secure, platform-specific)
- macOS: Keychain Access
- Windows: Credential Manager
- Linux: Secret Service API
- Requires additional dependency: `keyring`

**Decision**: Use QSettings for simplicity and cross-platform compatibility.

### 4. Plugin Lifecycle Integration
**File**: `src/main.py`

**Changes**:
```python
class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.auth_service = AuthService()
        
    def initGui(self):
        # Check authentication before initializing UI
        if not self.auth_service.is_authenticated():
            self.show_login_dialog()
        else:
            # Validate token
            if not self.auth_service.validate_token():
                self.show_login_dialog()
            else:
                # Initialize plugin UI
                self.init_provider()
                
    def show_login_dialog(self):
        """Show login dialog and handle result"""
        dialog = LoginDialog(self.iface.mainWindow())
        if dialog.exec_() == QDialog.Accepted:
            # User logged in successfully
            self.init_provider()
        else:
            # User cancelled - show message
            QMessageBox.warning(
                self.iface.mainWindow(),
                "TLGeo2QGIS",
                "Bạn cần đăng nhập để sử dụng plugin này."
            )
```

### 5. API Endpoints

**GEOADMIN Strapi Auth Endpoints**:

**Login**:
```
POST /api/auth/local
Body: {
  "identifier": "user@example.com",
  "password": "password123"
}
Response: {
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    ...
  }
}
```

**Validate Token**:
```
GET /api/users/me
Headers: {
  "Authorization": "Bearer {jwt_token}"
}
Response: {
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  ...
}
Error (401): {
  "error": {
    "status": 401,
    "name": "UnauthorizedError",
    "message": "Invalid token"
  }
}
```

### 6. Error Handling

**Network Errors**:
- Connection timeout
- Server unreachable
- Show user-friendly error messages

**Authentication Errors**:
- Invalid credentials (401)
- Account disabled/blocked
- Token expired
- Show specific error messages in Vietnamese

**Token Storage Errors**:
- Permission denied
- Disk full
- Fallback to session-only authentication

### 7. Security Considerations

**Best Practices**:
- ✅ Never log JWT tokens
- ✅ Clear password field after login attempt
- ✅ Use HTTPS in production (check URL scheme)
- ✅ Handle token refresh if API supports it
- ✅ Clear token on logout
- ✅ Mask password input
- ⚠️ QSettings is NOT encrypted (consider keyring for production)

**HTTPS Check**:
```python
if not self.strapi_url.startswith("https://") and "localhost" not in self.strapi_url:
    QMessageBox.warning(
        None,
        "Cảnh báo bảo mật",
        "Bạn đang kết nối đến server qua HTTP không mã hóa.\n"
        "Khuyến nghị sử dụng HTTPS trong môi trường production."
    )
```

## Acceptance Criteria

### UI/UX
- [ ] Login dialog appears on plugin load if not authenticated
- [ ] Login dialog has clean, professional design with GEOADMIN branding
- [ ] Password field is masked
- [ ] Loading indicator shows during authentication
- [ ] Error messages are clear and in Vietnamese
- [ ] Dialog can be cancelled (with warning message)

### Authentication Flow
- [ ] User can login with email/username and password
- [ ] JWT token is stored securely after successful login
- [ ] Token is validated on plugin load via `/api/users/me`
- [ ] Invalid/expired token triggers login dialog
- [ ] Valid token allows plugin to initialize normally
- [ ] User information is accessible throughout plugin

### Token Management
- [ ] Token is stored persistently (survives QGIS restart)
- [ ] Token is sent with all API requests (Authorization header)
- [ ] Token is cleared on logout
- [ ] Token validation handles 401 errors gracefully

### Error Handling
- [ ] Network errors show user-friendly messages
- [ ] Invalid credentials show specific error message
- [ ] Server unreachable shows appropriate message
- [ ] Timeout errors are handled gracefully
- [ ] All errors are displayed in Vietnamese

### Security
- [ ] Password is never logged or stored
- [ ] JWT token is not logged
- [ ] HTTPS warning shown for non-localhost HTTP connections
- [ ] Token is cleared from memory on logout

## Implementation Plan

### Phase 1: Core Authentication (Priority: High)
1. Create `AuthService` class with basic login/logout
2. Implement JWT storage using QSettings
3. Add token validation via `/api/users/me`
4. Test authentication flow

### Phase 2: UI Development (Priority: High)
1. Create `LoginDialog` UI
2. Add form validation
3. Integrate with `AuthService`
4. Add loading indicators
5. Test UI interactions

### Phase 3: Plugin Integration (Priority: High)
1. Update `main.py` to check auth on load
2. Show login dialog when needed
3. Handle login success/failure
4. Test full plugin lifecycle

### Phase 4: Error Handling & UX (Priority: Medium)
1. Add comprehensive error handling
2. Improve error messages (Vietnamese)
3. Add HTTPS security warning
4. Add logout functionality
5. Test edge cases

### Phase 5: Documentation & Testing (Priority: Medium)
1. Update user documentation
2. Update developer documentation
3. Add usage examples
4. Test on Windows/macOS/Linux

## Files to Create/Modify

### New Files
- `src/ui/login_dialog.py` - Login dialog UI
- `src/util/auth_service.py` - Authentication service

### Modified Files
- `src/main.py` - Add auth check on plugin load
- `src/__init__.py` - May need to add requests dependency (already added)
- `src/layer_menu_provider.py` - Use auth token for upload API calls
- `docs/README.md` - Add authentication documentation
- `docs/CONFIGURATION.md` - Add auth settings documentation

## Testing Checklist

### Unit Tests
- [ ] Test `AuthService.login()` with valid credentials
- [ ] Test `AuthService.login()` with invalid credentials
- [ ] Test `AuthService.validate_token()` with valid token
- [ ] Test `AuthService.validate_token()` with expired token
- [ ] Test token storage/retrieval from QSettings
- [ ] Test logout clears token

### Integration Tests
- [ ] Test plugin load with no stored token
- [ ] Test plugin load with valid stored token
- [ ] Test plugin load with expired stored token
- [ ] Test login dialog submission
- [ ] Test login dialog cancellation
- [ ] Test token refresh on API calls

### Manual Tests
- [ ] Test on Windows
- [ ] Test on macOS
- [ ] Test on Linux
- [ ] Test with production Strapi server
- [ ] Test with localhost Strapi server
- [ ] Test network disconnection scenarios
- [ ] Test server timeout scenarios

## Dependencies

**Already Available**:
- ✅ `requests` - HTTP client
- ✅ `python-dotenv` - Environment variables
- ✅ `PyQt5` (via QGIS) - UI framework

**May Need**:
- ⚠️ `keyring` - For more secure token storage (optional)

## References

- Strapi Authentication: https://docs.strapi.io/dev-docs/plugins/users-permissions
- QSettings Documentation: https://doc.qt.io/qt-5/qsettings.html
- QGIS Python API: https://qgis.org/pyqgis/

## Notes

### Token Expiration
- Strapi JWT tokens typically expire after 30 days (configurable)
- Consider adding token refresh mechanism if Strapi supports it
- For now, user will be prompted to re-login when token expires

### Multi-User Support
- Current implementation supports single user per QGIS instance
- If multi-user support needed, consider user profile switching

### Offline Mode
- Plugin should handle offline scenarios gracefully
- Consider cached credentials or offline mode flag
- Show appropriate message when server unreachable

## Status
- **Current**: Planning
- **Started**: Not yet
- **Target Completion**: TBD

## Related Tasks
- Task 009: Layer Export & Upload (requires authentication for upload)
