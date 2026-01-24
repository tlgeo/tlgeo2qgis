# TLGeo2QGIS Plugin - Documentation Index

Welcome to the TLGeo2QGIS plugin documentation!

## 📚 Quick Navigation

### For Users:
- **[QGIS Versions & Export Capabilities](QGIS_VERSIONS.md)** - Which QGIS version supports what?
- **[GDAL Upgrade Guide](GDAL_UPGRADE_GUIDE.md)** - How to upgrade GDAL for MBTiles/PMTiles
- **[Authentication Guide](AUTHENTICATION.md)** - How to login and manage authentication

### For Developers:
- **[Tasks Overview](TASKS_OVERVIEW.md)** - All tasks status and roadmap
- **[Task 012: MBTiles/PMTiles Support](02_in-progress/task_012_mbtiles_pmtiles_support.md)** - Current active task
- **[Task 010: Authentication](04_completed/task_010_authentication_jwt.md)** - Completed JWT auth

---

## 📂 Documentation Structure

```
docs/
├── README.md                          ← You are here!
├── TASKS_OVERVIEW.md                  ← All tasks summary
├── QGIS_VERSIONS.md                   ← QGIS versions guide
├── GDAL_UPGRADE_GUIDE.md              ← User upgrade guide
├── AUTHENTICATION.md                  ← Auth overview
│
├── 01_todo/                           ← Future tasks
│   └── task_011_python_code_obfuscation.md
│
├── 02_in-progress/                    ← Active tasks
│   ├── task_012_mbtiles_pmtiles_support.md
│   └── TASK_012_SUMMARY.md
│
├── 03_in-review/                      ← (empty)
│
├── 04_completed/                      ← Finished tasks
│   └── task_010_authentication_jwt.md
│
├── 05_pending/                        ← (empty)
│
└── 06_archived/                       ← (empty)
```

---

## 🎯 Current Status

**Plugin Version**: 1.0.2

**Active Development**: Task 012 - MBTiles/PMTiles Support & GDAL Auto-Update

**Next Release**: v1.1.0 (estimated 4-5 weeks)

---

## 📋 Task Status

| ID | Title | Status | Priority | Location |
|----|-------|--------|----------|----------|
| 010 | JWT Authentication | ✅ Completed | High | [04_completed/](04_completed/task_010_authentication_jwt.md) |
| 011 | Code Obfuscation | 📝 Todo | Low | [01_todo/](01_todo/task_011_python_code_obfuscation.md) |
| 012 | MBTiles/PMTiles Support | 🔄 In Progress | High | [02_in-progress/](02_in-progress/task_012_mbtiles_pmtiles_support.md) |

---

## 🚀 Quick Start Guides

### I want to export MBTiles/PMTiles but it doesn't work
→ Read: [GDAL_UPGRADE_GUIDE.md](GDAL_UPGRADE_GUIDE.md)

### I want to know which QGIS version to download
→ Read: [QGIS_VERSIONS.md](QGIS_VERSIONS.md)

### I'm getting authentication errors
→ Read: [AUTHENTICATION.md](AUTHENTICATION.md)

### I'm a developer and want to implement Task 012
→ Read: [task_012_mbtiles_pmtiles_support.md](02_in-progress/task_012_mbtiles_pmtiles_support.md)

---

## 📞 Getting Help

- **Issues**: Check documentation first, then create GitHub issue
- **Features**: Suggest in GitHub discussions or create task in `01_todo/`
- **Questions**: Check FAQ sections in each guide

---

**Last Updated**: 2024-01-24
