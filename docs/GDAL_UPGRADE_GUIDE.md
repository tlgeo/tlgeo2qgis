# Quick Guide: Upgrading GDAL for MBTiles/PMTiles Support

## 🎯 Mục Đích

Hướng dẫn nhanh để upgrade GDAL nhằm hỗ trợ export **MBTiles** và **PMTiles** trong TLGeo2QGIS plugin.

---

## ✅ Kiểm Tra Version Hiện Tại

### Trong QGIS:
1. Menu → **TLGeo → Thông tin phiên bản**
2. Xem thông tin:
   - **QGIS Version**: (ví dụ: 3.28.1)
   - **GDAL Version**: (ví dụ: 3.6.2)
   - **Export Capabilities**:
     - MBTiles: ✅ hoặc ❌
     - PMTiles: ✅ hoặc ❌

---

## 🔧 Các Giải Pháp

### Option 1: Nâng Cấp QGIS (Khuyến Nghị - Dễ Nhất)

#### ✅ QGIS 3.28 LTR (Long Term Release)
- **Hỗ trợ**: MBTiles ✅, PMTiles ❌
- **GDAL**: 3.6.x
- **Ổn định**: Cao (LTR)
- **Download**: https://qgis.org/en/site/forusers/download.html

**Cách cài**:
1. Tải QGIS 3.28 LTR
2. Cài đặt (ghi đè version cũ)
3. Restart QGIS
4. Export MBTiles hoạt động! ✅

#### ✅ QGIS 3.34+ (Latest - Khi Release)
- **Hỗ trợ**: MBTiles ✅, PMTiles ✅
- **GDAL**: 3.8.x
- **Ổn định**: Testing
- **Download**: https://qgis.org/en/site/forusers/download.html

**Ghi chú**: PMTiles cần GDAL 3.8+, hiện chưa có trong QGIS builds chính thức. Chờ update.

---

### Option 2: Cài GDAL 3.8 Riêng (Nâng Cao)

⚠️ **Cảnh báo**: Cách này phức tạp hơn, cần kiến thức Terminal/Command line.

#### macOS (Homebrew):
```bash
# Cài Homebrew (nếu chưa có)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Cài GDAL 3.8
brew install gdal

# Kiểm tra version
gdal-config --version
# Output: 3.8.x
```

**Cấu hình QGIS để dùng Homebrew GDAL**:
```bash
# Thêm vào ~/.zshrc hoặc ~/.bash_profile:
export GDAL_DATA=/opt/homebrew/share/gdal
export PATH=/opt/homebrew/bin:$PATH

# Restart Terminal và QGIS
```

#### Windows:

**Cách 1: OSGeo4W**
1. Tải OSGeo4W: https://trac.osgeo.org/osgeo4w/
2. Chạy installer
3. Chọn "Advanced Install"
4. Chọn packages:
   - `gdal` (latest)
   - `gdal-python`
5. Install
6. Cấu hình QGIS:
   - Settings → Options → System
   - Environment variables:
     - `GDAL_DATA`: `C:\OSGeo4W\share\gdal`
     - `PATH`: `C:\OSGeo4W\bin;...`

**Cách 2: Conda**
```bash
# Cài Miniconda
# Download: https://docs.conda.io/en/latest/miniconda.html

# Tạo environment mới
conda create -n gdal_env python=3.9 gdal=3.8

# Activate
conda activate gdal_env

# Kiểm tra
python -c "from osgeo import gdal; print(gdal.VersionInfo())"
```

#### Linux (Ubuntu/Debian):
```bash
# Thêm UbuntuGIS repository
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt update

# Cài GDAL 3.8+
sudo apt install gdal-bin libgdal-dev python3-gdal

# Kiểm tra version
gdal-config --version
```

---

### Option 3: Sử dụng SQLite + External Tools (Luôn Hoạt Động)

Nếu không muốn upgrade QGIS/GDAL, sử dụng SQLite export + công cụ chuyển đổi.

#### Bước 1: Export SQLite từ Plugin
1. Right-click layer → **TLGeo > Tải lên**
2. Plugin tự động export:
   - `layer_sqlite_4326.sqlite` ← Dùng file này
   - `layer_sqlite.sqlite`
   - `layer.metadata.json`
   - `layer.sld`

#### Bước 2: Cài Conversion Tools

**Tippecanoe** (SQLite → MBTiles):
```bash
# macOS
brew install tippecanoe

# Linux (build from source)
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe
make -j
sudo make install

# Windows: Download pre-built từ GitHub releases
# https://github.com/felt/tippecanoe/releases
```

**pmtiles** (MBTiles → PMTiles):
```bash
# Download binary từ GitHub
# https://github.com/protomaps/go-pmtiles/releases

# macOS
wget https://github.com/protomaps/go-pmtiles/releases/download/v1.11.0/pmtiles_1.11.0_Darwin_arm64.tar.gz
tar -xzf pmtiles_*.tar.gz
sudo mv pmtiles /usr/local/bin/

# Windows: Download .exe và thêm vào PATH
```

#### Bước 3: Convert

**SQLite → MBTiles**:
```bash
cd ~/TLGeo_Exports/{UUID}/

tippecanoe -o output.mbtiles \
  --layer=layer_name \
  --minimum-zoom=0 \
  --maximum-zoom=14 \
  layer_sqlite_4326.sqlite
```

**MBTiles → PMTiles**:
```bash
pmtiles convert output.mbtiles output.pmtiles
```

**Kết quả**:
- `output.mbtiles` - Vector tiles (MBTiles format)
- `output.pmtiles` - Vector tiles (PMTiles format, cloud-native)

---

## 🚀 So Sánh Các Giải Pháp

| Giải pháp | Độ khó | Thời gian | MBTiles | PMTiles | Ổn định |
|-----------|--------|-----------|---------|---------|---------|
| **Upgrade QGIS 3.28 LTR** | ⭐ Dễ | 10 phút | ✅ | ❌ | ⭐⭐⭐⭐⭐ |
| **Upgrade QGIS 3.34+** | ⭐ Dễ | 10 phút | ✅ | ✅ | ⭐⭐⭐ (testing) |
| **Cài GDAL riêng (macOS)** | ⭐⭐⭐ Khó | 30 phút | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Cài GDAL riêng (Windows)** | ⭐⭐⭐⭐ Rất khó | 1 giờ | ✅ | ✅ | ⭐⭐⭐ |
| **Cài GDAL riêng (Linux)** | ⭐⭐ Trung bình | 20 phút | ✅ | ✅ | ⭐⭐⭐⭐ |
| **SQLite + External Tools** | ⭐⭐ Trung bình | 15 phút | ✅ | ✅ | ⭐⭐⭐⭐⭐ |

---

## 💡 Khuyến Nghị Theo Use Case

### Nếu bạn là Beginner:
→ **Upgrade QGIS 3.28 LTR** (Option 1)
- Dễ nhất, ổn định nhất
- MBTiles đủ cho hầu hết use cases

### Nếu bạn cần PMTiles ngay:
→ **SQLite + External Tools** (Option 3)
- Không cần upgrade QGIS/GDAL
- Tippecanoe + pmtiles rất nhanh và reliable

### Nếu bạn là Developer/Advanced User:
→ **Cài GDAL 3.8 riêng** (Option 2)
- Control đầy đủ
- Có thể dùng GDAL mới nhất
- Tích hợp tốt với command line workflows

### Nếu bạn làm Production:
→ **QGIS 3.28 LTR + External Tools** (Option 1 + 3)
- Ổn định cao (LTR)
- Fallback bằng external tools nếu cần PMTiles

---

## 🐛 Troubleshooting

### "GDAL not found" sau khi cài:
```bash
# macOS/Linux: Check PATH
echo $PATH
which gdal-config

# Add to PATH nếu thiếu
export PATH=/usr/local/bin:$PATH  # macOS
export PATH=/usr/bin:$PATH        # Linux

# Windows: Check Environment Variables
# System Properties → Advanced → Environment Variables → Path
```

### "PMTiles driver not available" trong QGIS mới:
- PMTiles driver được thêm vào GDAL 3.8.0 (Nov 2023)
- Hầu hết QGIS builds hiện tại dùng GDAL 3.6.x
- Chờ QGIS builds mới hoặc dùng Option 3 (external tools)

### QGIS không nhận GDAL mới sau khi cài:
1. **Restart QGIS hoàn toàn** (không chỉ reload plugin)
2. Check QGIS settings:
   - Settings → Options → System → Environment
   - Verify `GDAL_DATA` và `PATH`
3. macOS: QGIS có thể bundle GDAL riêng trong `.app`
   - QGIS sẽ dùng bundled GDAL, không dùng system GDAL
   - Cần cài QGIS mới để có GDAL mới

### Tippecanoe/pmtiles không chạy:
```bash
# macOS: Permission denied
chmod +x tippecanoe
chmod +x pmtiles

# macOS: "unverified developer" error
xattr -d com.apple.quarantine tippecanoe
xattr -d com.apple.quarantine pmtiles

# Windows: Add to PATH
# System Properties → Environment Variables → Path → Edit → New
# C:\path\to\tippecanoe\
```

---

## 📚 Tài Liệu Tham Khảo

- **QGIS Downloads**: https://qgis.org/en/site/forusers/download.html
- **GDAL Releases**: https://gdal.org/download.html
- **Tippecanoe**: https://github.com/felt/tippecanoe
- **PMTiles**: https://github.com/protomaps/PMTiles
- **OSGeo4W (Windows)**: https://trac.osgeo.org/osgeo4w/
- **UbuntuGIS (Linux)**: https://wiki.ubuntu.com/UbuntuGIS

---

## ❓ FAQ

**Q: Có cần PMTiles không? MBTiles có đủ không?**  
A: MBTiles đủ cho hầu hết use cases. PMTiles tối ưu hơn cho cloud storage (S3, GCS) với HTTP range requests.

**Q: Sau khi upgrade QGIS, data cũ có mất không?**  
A: Không. QGIS projects và data không bị ảnh hưởng khi upgrade.

**Q: Có thể dùng cả QGIS 3.22 và 3.28 cùng lúc không?**  
A: Có (macOS/Linux), nhưng Windows phức tạp hơn. Rename `.app` hoặc install vào thư mục khác.

**Q: Plugin auto-installer khi nào ra?**  
A: Task 012 đang phát triển. Dự kiến v1.1.0 (2-3 tuần).

---

**Last Updated**: 2024-01-24  
**Version**: 1.0
