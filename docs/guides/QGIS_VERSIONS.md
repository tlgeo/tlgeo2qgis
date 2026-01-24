# QGIS Versions và Export Capabilities

## Tổng Quan

Plugin TLGeo2QGIS hỗ trợ export layer ra nhiều định dạng. Tuy nhiên, khả năng export MBTiles và PMTiles phụ thuộc vào phiên bản QGIS và GDAL.

## Kiểm Tra Phiên Bản

Trong QGIS, vào menu: **TLGeo → Thông tin phiên bản**

Dialog sẽ hiển thị:
- QGIS version
- GDAL version
- Các format export có sẵn (MBTiles, PMTiles)

## Export Formats Support

### ✅ Luôn Có Sẵn (Tất Cả QGIS Versions)

| Format | Mô tả | Sử dụng |
|--------|-------|---------|
| **SQLite (.sqlite)** | Vector data trong SQLite database | Vector tiles, spatial queries |
| **SQLite 4326 (.sqlite)** | Vector data reprojected sang EPSG:4326 | Web mapping |
| **SLD (.sld)** | Style Layer Descriptor | Layer styling |
| **Metadata JSON** | Layer metadata, fields info | Documentation |

### ⚠️ Phụ Thuộc Phiên Bản

#### MBTiles Export

**MBTiles** là container format chứa vector tiles trong SQLite database.

| QGIS Version | GDAL Version | MBTiles Support | Ghi chú |
|--------------|--------------|-----------------|---------|
| **QGIS 3.14+** | GDAL 3.1+ | ✅ Có | Via processing algorithm `native:writevectortiles_mbtiles` |
| **QGIS 3.10-3.12** | GDAL 3.0+ | ⚠️ Có thể có | Qua GDAL MBTiles driver (nếu được compile) |
| **QGIS < 3.10** | GDAL 2.x | ❌ Không | Cần upgrade QGIS |

**Cách kiểm tra:**
```python
# Trong QGIS Python Console
import processing
processing.algorithmHelp('native:writevectortiles_mbtiles')
# Nếu không lỗi → có hỗ trợ MBTiles
```

#### PMTiles Export

**PMTiles** là cloud-native format cho vector tiles (single-file, HTTP range requests).

| QGIS Version | GDAL Version | PMTiles Support | Ghi chú |
|--------------|--------------|-----------------|---------|
| **QGIS 3.34+** (LTR future) | GDAL 3.8+ | ✅ Có | PMTiles driver trong GDAL 3.8.0+ |
| **QGIS 3.28-3.32** | GDAL 3.6-3.7 | ❌ Không | Chờ QGIS builds với GDAL 3.8+ |
| **QGIS < 3.28** | GDAL < 3.6 | ❌ Không | PMTiles chưa tồn tại |

**Yêu cầu:**
- GDAL 3.8.0 trở lên
- PMTiles driver được compile trong GDAL build

## Recommended QGIS Versions

### Cho Production Use

**QGIS 3.28 LTR (Long Term Release)**
- ✅ SQLite export: Hoạt động tốt
- ✅ MBTiles export: Có (via processing algorithm)
- ❌ PMTiles export: Chưa có (GDAL 3.6.x)
- **Download**: https://qgis.org/en/site/forusers/download.html

### Cho Testing/Development

**QGIS 3.34+ (Latest)**
- ✅ SQLite export: Hoạt động tốt
- ✅ MBTiles export: Có
- ✅ PMTiles export: Có (nếu GDAL 3.8+ được bundle)
- **Download**: https://qgis.org/en/site/forusers/download.html

## Workarounds Khi Không Có MBTiles/PMTiles

### Option 1: Sử dụng SQLite Export

SQLite và MBTiles đều sử dụng SQLite database format. Bạn có thể:

1. Export sang SQLite (EPSG:4326)
2. Sử dụng tool bên ngoài để convert sang MBTiles:
   - **tippecanoe**: https://github.com/felt/tippecanoe
   - **ogr2ogr** với GDAL 3.8+

```bash
# Convert SQLite to MBTiles using tippecanoe
tippecanoe -o output.mbtiles -l layer_name input_4326.sqlite

# Convert using ogr2ogr (GDAL 3.8+)
ogr2ogr -f MBTiles output.mbtiles input_4326.sqlite
```

### Option 2: Sử dụng QGIS Processing Toolbox

Nếu `native:writevectortiles_mbtiles` không có trong menu plugin nhưng có trong Processing Toolbox:

1. Mở **Processing Toolbox** (Ctrl+Alt+T)
2. Tìm "Write Vector Tiles (MBTiles)"
3. Chạy thủ công với layer

### Option 3: Upgrade QGIS

**Cách nhanh nhất**: Upgrade lên QGIS 3.28 LTR hoặc mới hơn

- **macOS**: Download DMG từ qgis.org
- **Windows**: Download installer từ qgis.org
- **Linux**: `sudo apt install qgis` (hoặc qua repository chính thức)

## GDAL Versions Timeline

| GDAL Version | Release Date | Notable Features |
|--------------|--------------|------------------|
| **GDAL 3.8.0** | Nov 2023 | ✅ PMTiles driver added |
| **GDAL 3.7.0** | May 2023 | OpenFileGDB improvements |
| **GDAL 3.6.0** | Nov 2022 | Cloud optimized formats |
| **GDAL 3.5.0** | May 2022 | STAC support |
| **GDAL 3.1.0** | May 2020 | ✅ MBTiles improvements |

## Kiểm Tra GDAL Version

### Trong QGIS Python Console:
```python
from osgeo import gdal
print(f"GDAL Version: {gdal.VersionInfo('RELEASE_NAME')}")
print(f"GDAL Version Number: {gdal.VersionInfo('VERSION_NUM')}")

# List available drivers
from osgeo import ogr
driver_count = ogr.GetDriverCount()
for i in range(driver_count):
    driver = ogr.GetDriver(i)
    print(f"{driver.GetName()}")
```

### Trong Terminal (macOS/Linux):
```bash
# Check QGIS bundled GDAL
/Applications/QGIS.app/Contents/MacOS/bin/gdal-config --version

# Check system GDAL
gdal-config --version
```

## Summary Table

| Export Format | File Extension | QGIS Version Required | GDAL Version Required | Plugin Support |
|---------------|----------------|----------------------|----------------------|----------------|
| SQLite | `.sqlite` | Any | Any | ✅ Always |
| SQLite (4326) | `.sqlite` | Any | Any | ✅ Always |
| SLD Style | `.sld` | Any | Any | ✅ Always |
| Metadata | `.json` | Any | Any | ✅ Always |
| MBTiles | `.mbtiles` | 3.14+ | 3.1+ | ⚠️ Version-dependent |
| PMTiles | `.pmtiles` | 3.34+ (future) | 3.8+ | ⚠️ Version-dependent |

## References

- **QGIS Versions**: https://qgis.org/en/site/forusers/alldownloads.html
- **GDAL Releases**: https://gdal.org/download.html
- **PMTiles Spec**: https://github.com/protomaps/PMTiles
- **MBTiles Spec**: https://github.com/mapbox/mbtiles-spec

---
*Last updated: 2024 - TLGeo2QGIS Plugin Documentation*
