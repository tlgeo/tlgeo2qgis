# Task 012 Summary: MBTiles/PMTiles Support

## 📋 Quick Overview

**Goal**: Giúp users có thể export MBTiles và PMTiles, ngay cả khi QGIS/GDAL version cũ.

**Status**: 🔄 Specification Complete, Implementation Pending

**Timeline**: 4-5 weeks

---

## 🎯 What We're Building

### Problem:
- MBTiles cần QGIS 3.14+ hoặc GDAL 3.1+
- PMTiles cần GDAL 3.8.0+ (Nov 2023)
- Nhiều users dùng QGIS 3.10-3.22 với GDAL 3.4-3.6
- Export MBTiles/PMTiles fails hoặc không có menu

### Solution (3 Options):

#### Option 1: GDAL Auto-Installer ⭐ (Primary)
- Plugin tự động tải GDAL 3.8.3 pre-built binaries
- Cài vào user directory (không cần admin)
- Hỗ trợ macOS + Windows (Linux dùng package manager)
- Progress bar + checksum verification
- Set environment variables cho QGIS

#### Option 2: QGIS Download Links (Fallback)
- Hiển thị dialog với links tải QGIS mới
- QGIS 3.28 LTR (có MBTiles, chưa có PMTiles)
- QGIS 3.34+ (có cả MBTiles và PMTiles)
- One-click mở browser

#### Option 3: SQLite + External Tools (Alternative)
- Export sang SQLite (luôn hoạt động)
- Hướng dẫn dùng tippecanoe (SQLite → MBTiles)
- Hướng dẫn dùng pmtiles (MBTiles → PMTiles)
- Có thể bundle tools với plugin

---

## 📁 Files to Create

### New Python Modules:
```
src/
├── util/
│   ├── gdal_installer.py       # GDAL download & install (PRIMARY)
│   ├── version_checker.py      # Version detection (refactor)
│   └── external_tools.py       # Bundled tools manager
├── ui/
│   └── gdal_update_dialog.py   # User prompt dialog
```

### Documentation:
```
docs/
├── 02_in-progress/
│   ├── task_011_mbtiles_pmtiles_support.md  ✅ DONE
│   └── TASK_011_SUMMARY.md                   ✅ DONE (this file)
├── GDAL_UPGRADE_GUIDE.md                     ✅ DONE
└── QGIS_VERSIONS.md                          ✅ DONE
```

### Optional (Phase 4):
```
bundled_tools/              # External binaries (gitignored)
├── macos/
│   ├── tippecanoe         # SQLite → MBTiles
│   └── pmtiles            # MBTiles → PMTiles
├── windows/
│   ├── tippecanoe.exe
│   └── pmtiles.exe
└── linux/
    ├── tippecanoe
    └── pmtiles
```

---

## 🚀 Implementation Phases

### Phase 1: Detection & Dialog ✅ (Week 1 - DONE)
- [x] Version detection (Task 010)
- [x] Show dialog when export needs newer GDAL
- [x] Documentation (QGIS_VERSIONS.md, GDAL_UPGRADE_GUIDE.md)

### Phase 2: GDAL Installer - macOS (Week 2)
- [ ] Create `GDALInstaller` class
- [ ] Download GDAL 3.8.3 for macOS (Intel + Apple Silicon)
- [ ] SHA256 checksum verification
- [ ] Extract to `~/Library/Application Support/QGIS/GDAL/3.8.3/`
- [ ] Set environment variables
- [ ] Test on macOS 12+ (Intel + M1/M2/M3)

### Phase 3: GDAL Installer - Windows (Week 3)
- [ ] Windows download URLs (x64)
- [ ] Extract to `%APPDATA%/QGIS/GDAL/3.8.3/`
- [ ] Windows environment variable setup
- [ ] Test on Windows 10/11

### Phase 4: External Tools (Week 4 - Optional)
- [ ] Download tippecanoe binaries for all platforms
- [ ] Download pmtiles binaries for all platforms
- [ ] Add to plugin ZIP (bundled_tools/)
- [ ] Auto-convert SQLite → MBTiles using bundled tippecanoe
- [ ] Auto-convert MBTiles → PMTiles using bundled pmtiles

### Phase 5: Polish & Release (Week 5)
- [ ] Comprehensive error handling
- [ ] User testing (macOS, Windows, Linux)
- [ ] Update plugin metadata to v1.1.0
- [ ] Release notes
- [ ] Deploy to QGIS Plugin Repository

---

## 💻 Code Snippets Preview

### User Experience Flow:

```python
# User tries to export layer
def export_layer(self, layer):
    capabilities = self.check_export_capabilities()
    
    # Check if MBTiles/PMTiles needed but not available
    if needs_mbtiles and not capabilities['mbtiles']:
        dialog = GDALUpdateDialog(current_gdal_version)
        
        if dialog.exec_() == QDialog.Accepted:
            choice = dialog.get_choice()
            
            if choice == "auto_install":
                installer = GDALInstaller(self.iface)
                installer.install_gdal()  # Download + extract + configure
            
            elif choice == "download_qgis":
                open_browser("https://qgis.org/downloads")
            
            elif choice == "use_sqlite":
                show_sqlite_conversion_guide()
        
        return  # Don't export yet, wait for GDAL update
    
    # Proceed with normal export
    self.do_export(layer)
```

### GDAL Installer Core:

```python
class GDALInstaller:
    GDAL_VERSION = "3.8.3"
    
    DOWNLOAD_URLS = {
        "macos_arm64": "https://github.com/OSGeo/gdal/releases/.../gdal-3.8.3-macos-arm64.tar.gz",
        "macos_x86_64": "https://github.com/OSGeo/gdal/releases/.../gdal-3.8.3-macos-x86_64.tar.gz",
        "windows_x64": "https://github.com/OSGeo/gdal/releases/.../gdal-3.8.3-win64.zip"
    }
    
    def install_gdal(self):
        # 1. Detect platform
        platform_key = self.get_platform_key()  # "macos_arm64", etc.
        
        # 2. Download with progress
        url = self.DOWNLOAD_URLS[platform_key]
        self.download_with_progress(url, destination)
        
        # 3. Verify checksum
        if not self.verify_checksum(destination, expected_sha256):
            raise Exception("Checksum mismatch!")
        
        # 4. Extract
        self.extract_archive(destination, install_dir)
        
        # 5. Configure environment
        os.environ["GDAL_DATA"] = f"{install_dir}/share/gdal"
        os.environ["PATH"] = f"{install_dir}/bin:{os.environ['PATH']}"
        
        # 6. Notify user
        QMessageBox.information("GDAL installed! Please restart QGIS.")
```

---

## ✅ Success Criteria

### Must Have:
- [ ] Auto-detect GDAL < 3.8 when exporting MBTiles/PMTiles
- [ ] Show dialog with clear options
- [ ] GDAL auto-install works on macOS (Intel + Apple Silicon)
- [ ] GDAL auto-install works on Windows 10/11
- [ ] Linux users get clear instructions (apt/dnf commands)
- [ ] Progress bar during download
- [ ] Checksum verification
- [ ] Environment variables set correctly
- [ ] User can open QGIS download page

### Should Have:
- [ ] Cache downloaded GDAL files
- [ ] Test GDAL after installation
- [ ] Rollback if install fails
- [ ] Detailed logs for troubleshooting

### Nice to Have:
- [ ] Bundle tippecanoe + pmtiles binaries
- [ ] Auto-convert SQLite → MBTiles (fallback)
- [ ] Check for GDAL updates
- [ ] One-click QGIS upgrade (if API exists)

---

## 🧪 Testing Checklist

### Manual Tests:
- [ ] macOS 12 (Intel) - QGIS 3.22 (old) → Auto-install GDAL 3.8
- [ ] macOS 13 (M1) - QGIS 3.28 → Already has MBTiles, install for PMTiles
- [ ] macOS 14 (M2) - QGIS 3.34 → Already has everything
- [ ] Windows 10 - QGIS 3.22 → Auto-install
- [ ] Windows 11 - QGIS 3.28 → Auto-install
- [ ] Ubuntu 22.04 - Show apt commands
- [ ] Network failure during download → Show error, allow retry
- [ ] Disk full during install → Show error, cleanup partial files
- [ ] User cancels download → No corrupted files left

### Integration Tests:
- [ ] After GDAL install → Export MBTiles works
- [ ] After GDAL install → Export PMTiles works
- [ ] After QGIS restart → New GDAL recognized
- [ ] Environment variables persist across sessions

---

## 📚 Resources

### GDAL Downloads:
- GitHub Releases: https://github.com/OSGeo/gdal/releases
- OSGeo4W (Windows): https://trac.osgeo.org/osgeo4w/
- Conda-forge: https://anaconda.org/conda-forge/gdal

### Conversion Tools:
- Tippecanoe: https://github.com/felt/tippecanoe
- PMTiles: https://github.com/protomaps/go-pmtiles
- GDAL ogr2ogr: https://gdal.org/programs/ogr2ogr.html

### Platform-specific:
- macOS Homebrew GDAL: https://formulae.brew.sh/formula/gdal
- UbuntuGIS PPA: https://wiki.ubuntu.com/UbuntuGIS
- Windows GDAL builds: https://www.gisinternals.com/

---

## ⚠️ Known Challenges

### 1. GDAL Dependencies
GDAL cần nhiều libraries: PROJ, GEOS, SQLite, TIFF, JPEG, PNG, etc.
- **Solution**: Bundle pre-built GDAL với tất cả dependencies

### 2. Environment Variables
QGIS có thể override environment variables khi khởi động.
- **Solution**: Set variables trong QGIS settings (persistent)

### 3. Platform Differences
macOS/Windows/Linux có cách install GDAL khác nhau.
- **Solution**: Platform-specific installers, Linux dùng package manager

### 4. Binary Signing (macOS/Windows)
Unsigned binaries bị block bởi Gatekeeper/SmartScreen.
- **Solution**: 
  - macOS: Hướng dẫn user chạy `xattr -d com.apple.quarantine`
  - Windows: Hướng dẫn "Run anyway" hoặc sign binaries

### 5. QGIS Updates
Khi QGIS update, có thể ghi đè GDAL environment.
- **Solution**: Check GDAL version mỗi lần khởi động plugin

---

## 📊 Estimated Effort

| Phase | Tasks | Effort | Developer | 
|-------|-------|--------|-----------|
| Phase 1 | Detection & Dialog | ✅ DONE | 1 day |
| Phase 2 | macOS Installer | Code + Test | 5 days |
| Phase 3 | Windows Installer | Code + Test | 5 days |
| Phase 4 | External Tools (Optional) | Bundle + Test | 3 days |
| Phase 5 | Polish & Release | QA + Docs | 2 days |
| **Total** | | **16 days** (~3-4 weeks) | 1 FTE |

---

## 🎯 Next Actions

### Immediate (This Week):
1. ✅ Create task specification (DONE)
2. ✅ Write documentation (DONE)
3. [ ] Research GDAL pre-built binaries availability
4. [ ] Test download URLs and checksums
5. [ ] Create GDALInstaller skeleton code

### Short-term (Next 2 Weeks):
1. [ ] Implement macOS installer
2. [ ] Test on macOS Intel + Apple Silicon
3. [ ] Implement Windows installer
4. [ ] Test on Windows 10/11

### Long-term (Week 3-4):
1. [ ] Optional: Bundle external tools
2. [ ] User testing
3. [ ] Bug fixes
4. [ ] Release v1.1.0

---

## 📖 Related Documentation

- [Task 012 Full Specification](task_011_mbtiles_pmtiles_support.md)
- [QGIS Versions Guide](../QGIS_VERSIONS.md)
- [GDAL Upgrade Guide](../GDAL_UPGRADE_GUIDE.md)

---

**Created**: 2024-01-24  
**Status**: Specification Complete, Ready for Implementation  
**Assignee**: TBD
