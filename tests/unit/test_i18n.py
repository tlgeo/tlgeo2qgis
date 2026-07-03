import pytest
from unittest.mock import patch, MagicMock

# Import the translation functions
from util.i18n import init_i18n, tr, _translations

class TestI18n:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Save original state of i18n variables if needed
        import util.i18n as i18n_mod
        orig_locale = getattr(i18n_mod, "_current_locale", "en")
        yield
        # Restore original locale
        i18n_mod._current_locale = orig_locale

    def test_translation_vietnamese(self):
        import util.i18n as i18n_mod
        i18n_mod._current_locale = "vi"
        
        # Test exact match
        assert tr("Connect mobile device (QR Code)") == "Kết nối thiết bị di động (QR Code)"
        assert tr("Logout") == "Đăng xuất"
        
        # Test formatting wrapper
        assert tr("You are logged in as:\n{}").format("test@gmail.com") == "Bạn đã đăng nhập với tài khoản:\ntest@gmail.com"
        
        # Test fallback when key doesn't exist
        assert tr("Nonexistent key here") == "Nonexistent key here"

    def test_translation_english(self):
        import util.i18n as i18n_mod
        i18n_mod._current_locale = "en"
        
        # Test matches
        assert tr("Connect mobile device (QR Code)") == "Connect mobile device (QR Code)"
        assert tr("Logout") == "Logout"
        
        # Test fallback
        assert tr("Nonexistent key here") == "Nonexistent key here"

    def test_init_i18n_vietnamese_locale(self):
        with patch("util.i18n.QgsApplication") as mock_qgs, \
             patch("util.i18n.QSettings") as mock_settings:
            mock_qgs.locale.return_value = "vi_VN"
            
            init_i18n()
            
            import util.i18n as i18n_mod
            assert i18n_mod._current_locale == "vi"

    def test_init_i18n_english_locale(self):
        with patch("util.i18n.QgsApplication") as mock_qgs, \
             patch("util.i18n.QSettings") as mock_settings:
            mock_qgs.locale.return_value = "en_US"
            
            init_i18n()
            
            import util.i18n as i18n_mod
            assert i18n_mod._current_locale == "en"

    def test_init_i18n_fallback_qsettings(self):
        with patch("util.i18n.QgsApplication") as mock_qgs, \
             patch("util.i18n.QSettings") as mock_settings:
            # QgsApplication.locale() returns empty string/None
            mock_qgs.locale.return_value = ""
            
            mock_settings_inst = MagicMock()
            def mock_value(key, default=None):
                if key == "i18n/language":
                    return None
                elif key == "locale/userLocale":
                    return "vi"
                return default
            mock_settings_inst.value.side_effect = mock_value
            mock_settings.return_value = mock_settings_inst
            
            init_i18n()
            
            import util.i18n as i18n_mod
            assert i18n_mod._current_locale == "vi"
            mock_settings_inst.value.assert_any_call('locale/userLocale', 'en')

    def test_init_i18n_custom_override(self):
        with patch("util.i18n.QSettings") as mock_settings:
            mock_settings_inst = MagicMock()
            # Simulate custom language set to 'vi'
            mock_settings_inst.value.return_value = "vi"
            mock_settings.return_value = mock_settings_inst
            
            init_i18n()
            
            import util.i18n as i18n_mod
            assert i18n_mod._current_locale == "vi"
            mock_settings_inst.value.assert_called_with("i18n/language", None)
