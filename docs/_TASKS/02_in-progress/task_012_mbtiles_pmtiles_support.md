# Task 012: MBTiles/PMTiles Export Support & GDAL Auto-Update

**Status**: 🔄 In Progress  
**Priority**: High  
**Assigned**: Development Team  
**Created**: 2024-01-24  
**Category**: Feature Enhancement

---

## 📋 Overview

Hiện tại plugin export layer ra nhiều format, nhưng **MBTiles** và **PMTiles** chỉ hoạt động trên QGIS/GDAL versions mới:
- **MBTiles**: Yêu cầu QGIS 3.14+ hoặc GDAL với MBTiles driver
- **PMTiles**: Yêu cầu GDAL 3.8.0+ (released Nov 2023)

**Vấn đề**: Nhiều users dùng QGIS cũ (3.10-3.22) với GDAL 3.4-3.6, không export được MBTiles/PMTiles.

**Mục tiêu**: 
1. ✅ Phát hiện QGIS/GDAL version (ĐÃ XONG - Task 010)
2. 🔄 Cung cấp giải pháp tự động cài GDAL mới
3. 🔄 Hoặc hướng dẫn user download QGIS mới

---

## 🎯 Requirements

### 1. Version Detection (✅ COMPLETED)

- [x] Hiển thị QGIS version
- [x] Hiển thị GDAL version
- [x] Check MBTiles support (Processing algorithm + GDAL driver)
- [x] Check PMTiles support (GDAL 3.8+ driver)
- [x] Menu item: "TLGeo > Thông tin phiên bản"

**Implementation**: `src/main.py:show_version_info()`

### 2. GDAL Auto-Update Options

#### Option A: Tự động tải GDAL Build mới (Recommended)

**Concept**: Plugin tự download pre-built GDAL binaries

**Platforms**:

##### macOS:
```python
# Download from conda-forge or OSGeo
GDAL_DOWNLOAD_URLS = {
    "macos_arm64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-macos-arm64.tar.gz",
    "macos_x86_64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-macos-x86_64.tar.gz"
}

# Install location
install_path = ~/Library/Application Support/QGIS/GDAL/3.8.3/
```

##### Windows:
```python
GDAL_DOWNLOAD_URLS = {
    "windows_x64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-win64.zip"
}

# Install location
install_path = %APPDATA%/QGIS/GDAL/3.8.3/
```

##### Linux:
```python
# Use system package manager
# Ubuntu/Debian: apt install gdal-bin libgdal-dev
# Fedora: dnf install gdal gdal-devel
```

**Features**:
- Auto-detect OS and architecture
- Download progress bar
- Verify checksum (SHA256)
- Install to user directory (no admin needed)
- Set GDAL environment variables for QGIS to use

#### Option B: Hướng dẫn tải QGIS mới

**Concept**: Show dialog với link tải QGIS 3.28+ LTR

**Dialog content**:
```
❌ GDAL {current_version} không hỗ trợ MBTiles/PMTiles

📥 GIẢI PHÁP:

[Option 1] Cài đặt GDAL 3.8+ tự động (Recommended)
  → Plugin sẽ tải và cài đặt GDAL 3.8.3
  → Không cần quyền admin
  → Thời gian: ~5-10 phút
  
  [Cài đặt ngay]

[Option 2] Nâng cấp QGIS (Ổn định nhất)
  → Tải QGIS 3.28 LTR (Long Term Release)
  → Đi kèm GDAL 3.6+ (hỗ trợ MBTiles)
  → Chờ QGIS 3.34+ để có PMTiles
  
  [Tải QGIS 3.28 LTR] [Tải QGIS 3.34+]

[Option 3] Sử dụng SQLite thay thế
  → Export sang SQLite (hoạt động trên mọi version)
  → Dùng tool bên ngoài convert sang MBTiles
  → Tools: tippecanoe, ogr2ogr
  
  [Xem hướng dẫn]
```

#### Option C: External Tool Integration

**Concept**: Bundle conversion tools với plugin

**Tools to bundle**:
- **tippecanoe**: SQLite → MBTiles converter
- **pmtiles**: MBTiles → PMTiles converter
- **ogr2ogr** (GDAL 3.8+): Universal converter

**Workflow**:
```python
# 1. Export to SQLite (always works)
export_to_sqlite(layer, "output_4326.sqlite")

# 2. If MBTiles requested but not supported:
if export_mbtiles and not has_mbtiles_support():
    # Use bundled tippecanoe
    tippecanoe_bin = get_bundled_tool("tippecanoe")
    subprocess.run([
        tippecanoe_bin,
        "-o", "output.mbtiles",
        "-l", layer_name,
        "output_4326.sqlite"
    ])

# 3. If PMTiles requested but not supported:
if export_pmtiles and not has_pmtiles_support():
    # Convert MBTiles → PMTiles using bundled tool
    pmtiles_bin = get_bundled_tool("pmtiles")
    subprocess.run([
        pmtiles_bin, "convert",
        "output.mbtiles",
        "output.pmtiles"
    ])
```

---

## 📐 Technical Design

### 1. File Structure

```
src/
├── util/
│   ├── gdal_installer.py       # GDAL download & install logic (NEW)
│   ├── version_checker.py      # Version detection (refactor from main.py)
│   └── external_tools.py       # Bundled tools management (NEW)
├── ui/
│   └── gdal_update_dialog.py   # GDAL update dialog (NEW)
└── main.py                      # Updated to use new modules

bundled_tools/                   # External binaries (NEW, gitignored)
├── macos/
│   ├── tippecanoe
│   └── pmtiles
├── windows/
│   ├── tippecanoe.exe
│   └── pmtiles.exe
└── linux/
    ├── tippecanoe
    └── pmtiles
```

### 2. GDAL Installer Module

**File**: `src/util/gdal_installer.py`

```python
import os
import platform
import urllib.request
import hashlib
import tarfile
import zipfile
from PyQt5.QtWidgets import QProgressDialog
from qgis.core import QgsMessageLog, Qgis

class GDALInstaller:
    """Handle GDAL download and installation"""
    
    GDAL_VERSION = "3.8.3"
    
    DOWNLOAD_URLS = {
        "macos_arm64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-macos-arm64.tar.gz",
        "macos_x86_64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-macos-x86_64.tar.gz",
        "windows_x64": "https://github.com/OSGeo/gdal/releases/download/v3.8.3/gdal-3.8.3-win64.zip",
        "linux_x86_64": None  # Use package manager
    }
    
    SHA256_CHECKSUMS = {
        "macos_arm64": "abc123...",
        "macos_x86_64": "def456...",
        "windows_x64": "ghi789..."
    }
    
    def __init__(self, iface):
        self.iface = iface
        self.install_dir = self.get_install_directory()
    
    def get_install_directory(self):
        """Get GDAL install directory based on OS"""
        if platform.system() == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/QGIS/GDAL")
        elif platform.system() == "Windows":
            return os.path.expanduser("~/AppData/Roaming/QGIS/GDAL")
        else:  # Linux
            return os.path.expanduser("~/.local/share/QGIS/GDAL")
    
    def get_platform_key(self):
        """Detect platform and architecture"""
        system = platform.system()
        machine = platform.machine()
        
        if system == "Darwin":  # macOS
            if machine == "arm64":
                return "macos_arm64"
            else:
                return "macos_x86_64"
        elif system == "Windows":
            return "windows_x64"
        else:  # Linux
            return "linux_x86_64"
    
    def is_gdal_installed(self):
        """Check if GDAL 3.8+ is already installed"""
        gdal_bin = os.path.join(self.install_dir, self.GDAL_VERSION, "bin", "gdal-config")
        if platform.system() == "Windows":
            gdal_bin = os.path.join(self.install_dir, self.GDAL_VERSION, "bin", "gdal-config.exe")
        
        return os.path.exists(gdal_bin)
    
    def download_with_progress(self, url, destination, progress_dialog):
        """Download file with progress bar"""
        def reporthook(blocknum, blocksize, totalsize):
            downloaded = blocknum * blocksize
            if totalsize > 0:
                percent = int((downloaded / totalsize) * 100)
                progress_dialog.setValue(percent)
        
        urllib.request.urlretrieve(url, destination, reporthook)
    
    def verify_checksum(self, filepath, expected_hash):
        """Verify SHA256 checksum"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        actual_hash = sha256.hexdigest()
        return actual_hash == expected_hash
    
    def extract_archive(self, filepath, extract_to):
        """Extract tar.gz or zip archive"""
        if filepath.endswith('.tar.gz'):
            with tarfile.open(filepath, 'r:gz') as tar:
                tar.extractall(extract_to)
        elif filepath.endswith('.zip'):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
    
    def install_gdal(self):
        """Main installation workflow"""
        platform_key = self.get_platform_key()
        
        # Check if Linux (use package manager)
        if platform_key == "linux_x86_64":
            return self.show_linux_instructions()
        
        # Get download URL
        url = self.DOWNLOAD_URLS.get(platform_key)
        if not url:
            QgsMessageLog.logMessage(f"No download URL for platform: {platform_key}", "TLGeo", Qgis.Warning)
            return False
        
        # Create progress dialog
        progress = QProgressDialog("Đang tải GDAL 3.8.3...", "Hủy", 0, 100, self.iface.mainWindow())
        progress.setWindowTitle("Cài đặt GDAL")
        progress.show()
        
        try:
            # Download
            download_path = os.path.join(self.install_dir, "downloads", os.path.basename(url))
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            self.download_with_progress(url, download_path, progress)
            
            # Verify checksum
            progress.setLabelText("Đang kiểm tra file tải về...")
            expected_hash = self.SHA256_CHECKSUMS.get(platform_key)
            if expected_hash and not self.verify_checksum(download_path, expected_hash):
                QgsMessageLog.logMessage("Checksum verification failed!", "TLGeo", Qgis.Critical)
                return False
            
            # Extract
            progress.setLabelText("Đang giải nén GDAL...")
            extract_to = os.path.join(self.install_dir, self.GDAL_VERSION)
            os.makedirs(extract_to, exist_ok=True)
            self.extract_archive(download_path, extract_to)
            
            # Set environment variables
            self.configure_environment()
            
            progress.close()
            
            QgsMessageLog.logMessage(f"GDAL {self.GDAL_VERSION} installed successfully!", "TLGeo", Qgis.Success)
            return True
            
        except Exception as e:
            progress.close()
            QgsMessageLog.logMessage(f"GDAL installation failed: {str(e)}", "TLGeo", Qgis.Critical)
            return False
    
    def configure_environment(self):
        """Set GDAL environment variables for QGIS"""
        gdal_path = os.path.join(self.install_dir, self.GDAL_VERSION)
        
        # Set PATH
        bin_path = os.path.join(gdal_path, "bin")
        current_path = os.environ.get("PATH", "")
        if bin_path not in current_path:
            os.environ["PATH"] = f"{bin_path}:{current_path}"
        
        # Set GDAL_DATA
        data_path = os.path.join(gdal_path, "share", "gdal")
        os.environ["GDAL_DATA"] = data_path
        
        # Set LD_LIBRARY_PATH (Linux/macOS)
        lib_path = os.path.join(gdal_path, "lib")
        if platform.system() != "Windows":
            current_ld = os.environ.get("LD_LIBRARY_PATH", "")
            os.environ["LD_LIBRARY_PATH"] = f"{lib_path}:{current_ld}"
        
        QgsMessageLog.logMessage(f"GDAL environment configured: {gdal_path}", "TLGeo", Qgis.Info)
    
    def show_linux_instructions(self):
        """Show instructions for Linux users"""
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox(self.iface.mainWindow())
        msg.setWindowTitle("Cài đặt GDAL trên Linux")
        msg.setText(
            "Để cài đặt GDAL 3.8+ trên Linux, vui lòng chạy lệnh sau trong Terminal:\n\n"
            "Ubuntu/Debian:\n"
            "  sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable\n"
            "  sudo apt update\n"
            "  sudo apt install gdal-bin libgdal-dev\n\n"
            "Fedora:\n"
            "  sudo dnf install gdal gdal-devel\n\n"
            "Arch:\n"
            "  sudo pacman -S gdal\n"
        )
        msg.exec_()
        return False
```

### 3. GDAL Update Dialog

**File**: `src/ui/gdal_update_dialog.py`

```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt

class GDALUpdateDialog(QDialog):
    """Dialog to prompt user for GDAL update"""
    
    def __init__(self, current_gdal_version, parent=None):
        super().__init__(parent)
        self.current_version = current_gdal_version
        self.user_choice = None
        
        self.setWindowTitle("Cập nhật GDAL")
        self.setMinimumSize(600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"❌ GDAL {self.current_version} không hỗ trợ MBTiles/PMTiles")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        layout.addWidget(title)
        
        # Description
        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setMaximumHeight(150)
        desc.setHtml("""
        <p><b>MBTiles</b> và <b>PMTiles</b> là các format tối ưu cho vector tiles:</p>
        <ul>
            <li><b>MBTiles</b>: Yêu cầu GDAL 3.1+ (khuyến nghị 3.6+)</li>
            <li><b>PMTiles</b>: Yêu cầu GDAL 3.8.0+ (Nov 2023)</li>
        </ul>
        <p>Vui lòng chọn một trong các giải pháp sau:</p>
        """)
        layout.addWidget(desc)
        
        # Option 1: Auto install
        btn_auto = QPushButton("📥 [Khuyến nghị] Cài đặt GDAL 3.8.3 tự động")
        btn_auto.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_auto.clicked.connect(lambda: self.set_choice("auto_install"))
        layout.addWidget(btn_auto)
        
        auto_note = QLabel("  → Tải và cài đặt GDAL 3.8.3 vào thư mục người dùng\n  → Không cần quyền admin\n  → Thời gian: ~5-10 phút")
        auto_note.setStyleSheet("color: #666; margin-left: 20px;")
        layout.addWidget(auto_note)
        
        # Option 2: Download QGIS
        btn_layout = QHBoxLayout()
        
        btn_qgis_ltr = QPushButton("📥 Tải QGIS 3.28 LTR")
        btn_qgis_ltr.clicked.connect(lambda: self.set_choice("download_qgis_ltr"))
        btn_layout.addWidget(btn_qgis_ltr)
        
        btn_qgis_latest = QPushButton("📥 Tải QGIS 3.34+")
        btn_qgis_latest.clicked.connect(lambda: self.set_choice("download_qgis_latest"))
        btn_layout.addWidget(btn_qgis_latest)
        
        layout.addLayout(btn_layout)
        
        qgis_note = QLabel("  → Nâng cấp toàn bộ QGIS lên version mới\n  → QGIS 3.28: có MBTiles, chưa có PMTiles\n  → QGIS 3.34+: có cả MBTiles và PMTiles")
        qgis_note.setStyleSheet("color: #666; margin-left: 20px;")
        layout.addWidget(qgis_note)
        
        # Option 3: Use SQLite
        btn_sqlite = QPushButton("📄 Xem hướng dẫn dùng SQLite thay thế")
        btn_sqlite.clicked.connect(lambda: self.set_choice("use_sqlite"))
        layout.addWidget(btn_sqlite)
        
        sqlite_note = QLabel("  → Export sang SQLite (hoạt động trên mọi version)\n  → Dùng tool bên ngoài convert sang MBTiles/PMTiles")
        sqlite_note.setStyleSheet("color: #666; margin-left: 20px;")
        layout.addWidget(sqlite_note)
        
        # Cancel button
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        self.setLayout(layout)
    
    def set_choice(self, choice):
        """Set user choice and close dialog"""
        self.user_choice = choice
        self.accept()
    
    def get_choice(self):
        """Get user's choice after dialog closes"""
        return self.user_choice
```

### 4. Integration vào Plugin

**File**: `src/main.py` (update)

```python
def export_layer_with_gdal_check(self, layer):
    """Export layer, check GDAL version first"""
    
    # Check capabilities
    capabilities = self.check_export_capabilities()
    
    # If user wants MBTiles/PMTiles but not supported
    needs_mbtiles = True  # From export settings
    needs_pmtiles = True  # From export settings
    
    if needs_mbtiles and not (capabilities['mbtiles_processing'] or capabilities['mbtiles_gdal']):
        self.show_gdal_update_prompt()
        return
    
    if needs_pmtiles and not capabilities['pmtiles']:
        self.show_gdal_update_prompt()
        return
    
    # Proceed with export
    layer_menu_provider.export_layer(layer)

def show_gdal_update_prompt(self):
    """Show GDAL update dialog"""
    from osgeo import gdal
    from .ui.gdal_update_dialog import GDALUpdateDialog
    from .util.gdal_installer import GDALInstaller
    
    gdal_version = gdal.VersionInfo("RELEASE_NAME")
    
    dialog = GDALUpdateDialog(gdal_version, self.iface.mainWindow())
    
    if dialog.exec_() == QDialog.Accepted:
        choice = dialog.get_choice()
        
        if choice == "auto_install":
            # Auto install GDAL
            installer = GDALInstaller(self.iface)
            if installer.install_gdal():
                QMessageBox.information(
                    self.iface.mainWindow(),
                    "Cài đặt thành công",
                    "GDAL 3.8.3 đã được cài đặt!\n\n"
                    "Vui lòng khởi động lại QGIS để sử dụng GDAL mới."
                )
            else:
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    "Cài đặt thất bại",
                    "Không thể cài đặt GDAL tự động.\n"
                    "Vui lòng thử tải QGIS mới hoặc cài GDAL thủ công."
                )
        
        elif choice == "download_qgis_ltr":
            # Open QGIS download page
            QDesktopServices.openUrl(QUrl("https://qgis.org/en/site/forusers/download.html"))
        
        elif choice == "download_qgis_latest":
            # Open QGIS latest download
            QDesktopServices.openUrl(QUrl("https://qgis.org/en/site/forusers/download.html"))
        
        elif choice == "use_sqlite":
            # Show SQLite guide
            self.show_sqlite_conversion_guide()

def show_sqlite_conversion_guide(self):
    """Show guide for converting SQLite to MBTiles/PMTiles"""
    guide = """
<h3>Hướng dẫn chuyển đổi SQLite sang MBTiles/PMTiles</h3>

<h4>Bước 1: Export sang SQLite</h4>
<p>Plugin đã export layer sang SQLite (EPSG:4326). File này hoạt động trên mọi version QGIS.</p>

<h4>Bước 2: Cài đặt công cụ chuyển đổi</h4>

<b>Tippecanoe (SQLite → MBTiles):</b>
<pre>
# macOS (Homebrew)
brew install tippecanoe

# Linux (build from source)
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe && make && sudo make install
</pre>

<b>pmtiles (MBTiles → PMTiles):</b>
<pre>
# Download từ GitHub
https://github.com/protomaps/go-pmtiles/releases
</pre>

<h4>Bước 3: Chuyển đổi</h4>
<pre>
# SQLite → MBTiles
tippecanoe -o output.mbtiles -l layer_name input_4326.sqlite

# MBTiles → PMTiles
pmtiles convert output.mbtiles output.pmtiles
</pre>

<h4>Tài liệu tham khảo:</h4>
<ul>
<li><a href="https://github.com/felt/tippecanoe">Tippecanoe Documentation</a></li>
<li><a href="https://github.com/protomaps/PMTiles">PMTiles Documentation</a></li>
</ul>
"""
    
    dialog = QDialog(self.iface.mainWindow())
    dialog.setWindowTitle("Hướng dẫn chuyển đổi")
    dialog.resize(700, 500)
    
    layout = QVBoxLayout()
    
    text = QTextEdit()
    text.setReadOnly(True)
    text.setHtml(guide)
    layout.addWidget(text)
    
    btn_close = QPushButton("Đóng")
    btn_close.clicked.connect(dialog.accept)
    layout.addWidget(btn_close)
    
    dialog.setLayout(layout)
    dialog.exec_()
```

---

## ✅ Acceptance Criteria

### Must Have:
- [ ] Phát hiện GDAL version < 3.8 khi export MBTiles/PMTiles
- [ ] Hiển thị dialog với 3 options (auto install, download QGIS, use SQLite)
- [ ] GDAL auto-installer hoạt động trên macOS
- [ ] GDAL auto-installer hoạt động trên Windows
- [ ] Hiển thị hướng dẫn cho Linux users
- [ ] Download progress bar khi tải GDAL
- [ ] Verify checksum của file tải về
- [ ] Set environment variables sau khi cài GDAL
- [ ] Link tải QGIS hoạt động (mở browser)
- [ ] Hướng dẫn convert SQLite → MBTiles/PMTiles

### Should Have:
- [ ] Cache downloaded GDAL files (không tải lại nếu đã có)
- [ ] Rollback nếu cài GDAL thất bại
- [ ] Test GDAL sau khi cài xong
- [ ] Log chi tiết quá trình cài đặt
- [ ] Export settings: cho phép user chọn formats muốn export

### Nice to Have:
- [ ] Bundle tippecanoe và pmtiles binaries với plugin
- [ ] Auto-convert SQLite → MBTiles nếu GDAL không hỗ trợ
- [ ] Notification khi có QGIS/GDAL version mới
- [ ] One-click QGIS upgrade (nếu có API)

---

## 📊 Testing Plan

### Unit Tests:
```python
def test_detect_platform():
    installer = GDALInstaller(mock_iface)
    platform = installer.get_platform_key()
    assert platform in ["macos_arm64", "macos_x86_64", "windows_x64", "linux_x86_64"]

def test_checksum_verification():
    installer = GDALInstaller(mock_iface)
    # Create test file
    test_file = "/tmp/test_gdal.tar.gz"
    with open(test_file, 'wb') as f:
        f.write(b"test data")
    
    # Calculate expected hash
    expected = hashlib.sha256(b"test data").hexdigest()
    
    # Verify
    assert installer.verify_checksum(test_file, expected) == True
    assert installer.verify_checksum(test_file, "wrong_hash") == False

def test_gdal_already_installed():
    installer = GDALInstaller(mock_iface)
    # Mock installed GDAL
    os.makedirs(installer.install_dir + "/3.8.3/bin", exist_ok=True)
    open(installer.install_dir + "/3.8.3/bin/gdal-config", 'a').close()
    
    assert installer.is_gdal_installed() == True
```

### Integration Tests:
- [ ] Test full GDAL installation workflow (download → verify → extract → configure)
- [ ] Test dialog flow (show → user clicks option → action executes)
- [ ] Test export workflow with GDAL check
- [ ] Test QGIS restart after GDAL install

### Manual Tests:
- [ ] Test on macOS (Intel + Apple Silicon)
- [ ] Test on Windows 10/11
- [ ] Test on Ubuntu 22.04 LTS
- [ ] Test with QGIS 3.22 (old, no MBTiles)
- [ ] Test with QGIS 3.28 LTR (has MBTiles, no PMTiles)
- [ ] Test network failure during download
- [ ] Test disk full during installation
- [ ] Test user cancels download

---

## 🚀 Implementation Phases

### Phase 1: Detection & Dialog (Week 1)
- [x] Version detection (DONE - Task 010)
- [ ] Create `GDALUpdateDialog`
- [ ] Show dialog when export requires newer GDAL
- [ ] Link to QGIS downloads
- [ ] SQLite conversion guide

### Phase 2: GDAL Installer - macOS (Week 2)
- [ ] Create `GDALInstaller` class
- [ ] Download GDAL 3.8.3 for macOS
- [ ] Verify checksum
- [ ] Extract to user directory
- [ ] Set environment variables
- [ ] Test on macOS Intel + Apple Silicon

### Phase 3: GDAL Installer - Windows (Week 3)
- [ ] Windows-specific download logic
- [ ] Windows environment variable setup
- [ ] Test on Windows 10/11

### Phase 4: External Tools (Week 4 - Optional)
- [ ] Bundle tippecanoe binaries
- [ ] Bundle pmtiles binaries
- [ ] Auto-convert SQLite → MBTiles using bundled tools
- [ ] Test bundled tools on all platforms

### Phase 5: Polish & Deploy (Week 5)
- [ ] Error handling improvements
- [ ] User feedback collection
- [ ] Documentation update
- [ ] Release v1.1.0 with GDAL auto-installer

---

## 📚 Resources

### GDAL Downloads:
- **Official Releases**: https://github.com/OSGeo/gdal/releases
- **Conda-forge**: https://anaconda.org/conda-forge/gdal
- **OSGeo4W (Windows)**: https://trac.osgeo.org/osgeo4w/

### Conversion Tools:
- **Tippecanoe**: https://github.com/felt/tippecanoe
- **PMTiles**: https://github.com/protomaps/go-pmtiles
- **GDAL ogr2ogr**: https://gdal.org/programs/ogr2ogr.html

### QGIS Downloads:
- **QGIS 3.28 LTR**: https://qgis.org/en/site/forusers/download.html
- **QGIS 3.34+**: https://qgis.org/en/site/forusers/download.html

---

## 📝 Notes

### Challenges:
1. **GDAL Dependencies**: GDAL có nhiều dependencies (PROJ, GEOS, etc.). Cần bundle tất cả.
2. **Environment Variables**: QGIS có thể override environment variables. Cần set đúng cách.
3. **Platform Differences**: macOS/Windows/Linux có cách cài khác nhau.
4. **Binary Signing**: macOS/Windows có thể block unsigned binaries.

### Alternatives Considered:
- **Use Docker**: Too heavy for plugin
- **Use Conda**: Requires conda installation
- **Use System Package Manager**: Requires admin rights
- **Current Approach (Download pre-built)**: Best balance

### Future Enhancements:
- Tích hợp với QGIS Plugin Repository để auto-update
- Hỗ trợ offline installation (bundle GDAL trong plugin ZIP)
- Cloud-based conversion service (upload SQLite → convert online → download MBTiles)

---

**Last Updated**: 2024-01-24
**Status**: Ready for Implementation
