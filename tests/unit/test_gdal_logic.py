import pytest
import os
import hashlib
from unittest.mock import MagicMock, patch
from src.util.gdal_installer import GDALInstaller

class TestGDALLogic:
    
    @pytest.fixture
    def installer(self):
        mock_iface = MagicMock()
        return GDALInstaller(mock_iface)

    def test_platform_detection_macos_arm64(self, installer):
        with patch('platform.system', return_value="Darwin"), \
             patch('platform.machine', return_value="arm64"):
            assert installer.get_platform_key() == "macos_arm64"

    def test_platform_detection_macos_intel(self, installer):
        with patch('platform.system', return_value="Darwin"), \
             patch('platform.machine', return_value="x86_64"):
            assert installer.get_platform_key() == "macos_x86_64"

    def test_platform_detection_windows(self, installer):
        with patch('platform.system', return_value="Windows"), \
             patch('platform.machine', return_value="AMD64"):
            assert installer.get_platform_key() == "windows_x64"

    def test_checksum_verification(self, installer, tmp_path):
        # Create a dummy file
        test_file = tmp_path / "test.zip"
        content = b"This is test content"
        test_file.write_bytes(content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Test verify
        assert installer.verify_checksum(str(test_file), expected_hash) is True
        assert installer.verify_checksum(str(test_file), "wrong_hash") is False
        
    def test_checksum_missing_file(self, installer):
        assert installer.verify_checksum("/non/existent/file", "hash") is False
