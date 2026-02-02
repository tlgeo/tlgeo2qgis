# Database Configuration - Setup Summary

**Created**: 2026-02-02  
**Status**: ✅ Complete

## What Was Created

### 1. Configuration Module: `src/config/`

```
src/config/
├── __init__.py              # Module exports
└── database.py              # Database configuration (350 lines)
```

**Key Classes**:
- `DatabaseConfig` - Connection settings
- `TableNames` - Table name constants
- `FieldNames` - Field name constants
- `QueryTemplates` - SQL query templates

### 2. Environment Files

```
.env.example                 # Template (committed to git)
.env                         # Local config (NOT committed - add manually)
```

### 3. Documentation

```
docs/guides/DATABASE_CONFIGURATION.md  # Complete guide (300+ lines)
docs/DATABASE_SETUP_SUMMARY.md         # This file
```

### 4. Updated Files

```
.gitignore                   # Added .env and database_local.py
```

---

## Your Database Credentials (Saved)

```
Host:     localhost
Port:     8088
Database: data_forest
User:     postgres
Password: newpassword
```

These are stored in `src/config/database.py` as defaults.

---

## Quick Usage

### 1. In Search Widgets

```python
from qgis.core import QgsDataSourceUri, QgsVectorLayer
from config.database import DatabaseConfig, TableNames

# Get connection params
params = DatabaseConfig.get_qgis_connection_params()

# Create URI
uri = QgsDataSourceUri()
uri.setConnection(
    params['host'],      # 'localhost'
    params['port'],      # '8088'
    params['database'],  # 'data_forest'
    params['username'],  # 'postgres'
    params['password']   # 'newpassword'
)

# Load forest plots layer
uri.setDataSource('public', TableNames.LO_RUNG, 'geom')
layer = QgsVectorLayer(uri.uri(), "Lô rừng", "postgres")

if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
```

### 2. Direct SQL Queries

```python
import psycopg2
from config.database import DatabaseConfig

# Connect
conn = psycopg2.connect(**DatabaseConfig.get_psycopg2_params())
cursor = conn.cursor()

# Query
cursor.execute("SELECT COUNT(*) FROM lo_rung")
count = cursor.fetchone()[0]
print(f"Total plots: {count}")

# Close
cursor.close()
conn.close()
```

### 3. Test Connection

```python
from config.database import DatabaseConfig

success, message = DatabaseConfig.test_connection()
print(message)  # "Connection successful" or error
```

---

## Constants Available

### Table Names

```python
from config.database import TableNames

TableNames.LO_RUNG          # 'lo_rung'
TableNames.CHU_RUNG         # 'chu_rung'
TableNames.DIEN_BIEN        # 'dien_bien'
TableNames.LOAI_RUNG        # 'loai_rung'
TableNames.LOAI_CHU         # 'loai_chu'
TableNames.LOAI_DIEN_BIEN   # 'loai_dien_bien'
```

### Field Names

```python
from config.database import FieldNames

# Plot fields
FieldNames.PLOT_CODE        # 'ma_lo'
FieldNames.PLOT_NAME        # 'ten_lo'
FieldNames.PLOT_AREA        # 'dien_tich'
FieldNames.FOREST_TYPE      # 'loai_rung'

# Owner fields
FieldNames.OWNER_CODE       # 'ma_chu_rung'
FieldNames.OWNER_NAME       # 'ten_chu_rung'
FieldNames.CMND             # 'cmnd'
FieldNames.ADDRESS          # 'dia_chi'

# Change fields
FieldNames.CHANGE_CODE      # 'ma_dien_bien'
FieldNames.CHANGE_DATE      # 'ngay_dien_bien'
FieldNames.CHANGE_TYPE      # 'loai_dien_bien'
```

### Query Templates

```python
from config.database import QueryTemplates

# Search plots
cursor.execute(
    QueryTemplates.SEARCH_PLOTS,
    ('%search%', '%search%', 100, 0)
)

# Get plots by owner
cursor.execute(
    QueryTemplates.GET_PLOTS_BY_OWNER,
    ('CR0001',)
)
```

---

## Override for Different Environments

### Development (default)

Uses values from `src/config/database.py`:
```python
HOST = 'localhost'
PORT = '8088'
DATABASE = 'data_forest'
```

### Production (environment variables)

Set environment variables to override:

**Linux/macOS**:
```bash
export FRMS_DB_HOST=prod-db.example.com
export FRMS_DB_PORT=5432
export FRMS_DB_NAME=data_forest_prod
export FRMS_DB_PASSWORD=prod_password
```

**Windows**:
```cmd
set FRMS_DB_HOST=prod-db.example.com
set FRMS_DB_PASSWORD=prod_password
```

### Local Override (.env file)

Create `.env` file (not committed):
```bash
cp .env.example .env
nano .env
```

Edit with your local settings:
```env
FRMS_DB_HOST=my-local-db
FRMS_DB_PORT=5433
FRMS_DB_PASSWORD=my_password
```

---

## Security ✅

### ✅ What's Safe

- `src/config/database.py` - Contains defaults, safe to commit
- `.env.example` - Template with example values, safe to commit
- `docs/` - Documentation, safe to commit

### ⚠️ What's NOT Safe

- `.env` - YOUR actual credentials, **NEVER commit**
- Any file with real passwords

### Protection

```gitignore
# Already added to .gitignore:
.env
src/config/database_local.py
```

---

## Integration with Task Files

All 12 FRMS task files (020-031) reference this configuration:

### Task 020: Search Plots

```python
# In frms_search_plots_widget.py
from config.database import DatabaseConfig, TableNames, FieldNames

def load_plots_from_database(self):
    # Use DatabaseConfig to connect
    # Use TableNames.LO_RUNG for table name
    # Use FieldNames.PLOT_CODE, etc for fields
```

### Task 021-031

Same pattern - import from `config.database` module.

---

## Next Steps

### 1. Test Connection (Recommended)

Open QGIS Python Console:

```python
from config.database import DatabaseConfig

# Test connection
success, message = DatabaseConfig.test_connection()
print(message)

# If failed, check:
# - PostgreSQL is running
# - Port 8088 is open
# - Database 'data_forest' exists
# - User 'postgres' has access
```

### 2. Load a Layer

```python
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsProject
from config.database import DatabaseConfig, TableNames

params = DatabaseConfig.get_qgis_connection_params()

uri = QgsDataSourceUri()
uri.setConnection(
    params['host'], params['port'], params['database'],
    params['username'], params['password']
)
uri.setDataSource('public', TableNames.LO_RUNG, 'geom')

layer = QgsVectorLayer(uri.uri(), "Test Layer", "postgres")
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
    print("✅ Layer loaded successfully!")
else:
    print("❌ Layer failed to load")
    print("Error:", layer.error().message())
```

### 3. Implement Task 020

Start with search functionality using this configuration.

---

## Troubleshooting

### "Connection refused"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check port
netstat -an | grep 8088
```

### "Database does not exist"

```sql
-- Connect to postgres
psql -U postgres

-- List databases
\l

-- Create if missing
CREATE DATABASE data_forest;

-- Enable PostGIS
\c data_forest
CREATE EXTENSION postgis;
```

### "Authentication failed"

```bash
# Check password in .env or database.py
cat .env

# Or reset password
psql -U postgres
ALTER USER postgres PASSWORD 'newpassword';
```

---

## Summary

✅ **Configuration module created**: `src/config/database.py`  
✅ **Constants defined**: TableNames, FieldNames, QueryTemplates  
✅ **Environment template**: `.env.example`  
✅ **Documentation**: Complete guide in `docs/guides/`  
✅ **Security**: `.env` added to `.gitignore`  
✅ **Your credentials saved**: localhost:8088/data_forest  

**Ready to use** in all FRMS widgets (Tasks 020-031)!

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
