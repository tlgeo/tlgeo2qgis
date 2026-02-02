# Database Configuration Guide

**Created**: 2026-02-02  
**For**: FRMS (Forest Resource Management System) PostgreSQL/PostGIS database

## Overview

The TLGeo2QGIS plugin connects to a PostgreSQL/PostGIS database to manage forest data (plots, owners, changes). This guide explains how to configure the database connection.

---

## Quick Start

### 1. Copy Environment File

```bash
cd /path/to/tlgeo2qgis
cp .env.example .env
```

### 2. Edit `.env` File

```bash
# Open in your editor
nano .env
```

Update with your database credentials:

```env
FRMS_DB_HOST=localhost
FRMS_DB_PORT=8088
FRMS_DB_NAME=data_forest
FRMS_DB_USER=postgres
FRMS_DB_PASSWORD=newpassword
```

### 3. Test Connection

In QGIS Python Console:

```python
from config.database import DatabaseConfig

success, message = DatabaseConfig.test_connection()
if success:
    print("✅ Database connected successfully!")
else:
    print(f"❌ Connection failed: {message}")
```

---

## Configuration Files

### 1. `src/config/database.py`

**Main configuration file** with all database settings.

```python
class DatabaseConfig:
    HOST = 'localhost'      # From FRMS_DB_HOST env var
    PORT = '8088'           # From FRMS_DB_PORT env var
    DATABASE = 'data_forest'
    USER = 'postgres'
    PASSWORD = 'newpassword'
```

### 2. `.env` (NOT committed)

**Local environment variables** - overrides defaults.

```env
FRMS_DB_HOST=localhost
FRMS_DB_PORT=8088
FRMS_DB_NAME=data_forest
FRMS_DB_USER=postgres
FRMS_DB_PASSWORD=your_actual_password
```

⚠️ **Security**: This file is in `.gitignore` and will NEVER be committed.

### 3. `.env.example` (committed)

**Template file** - safe to commit with example values.

---

## Usage Examples

### Connect with QGIS

```python
from qgis.core import QgsDataSourceUri, QgsVectorLayer
from config.database import DatabaseConfig, TableNames

# Get connection parameters
params = DatabaseConfig.get_qgis_connection_params()

# Create URI
uri = QgsDataSourceUri()
uri.setConnection(
    params['host'],
    params['port'],
    params['database'],
    params['username'],
    params['password']
)

# Set table and geometry
uri.setDataSource('public', TableNames.LO_RUNG, 'geom')

# Load layer
layer = QgsVectorLayer(uri.uri(), "Lô rừng", "postgres")
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
```

### Connect with psycopg2

```python
import psycopg2
from config.database import DatabaseConfig, QueryTemplates

# Connect to database
conn = psycopg2.connect(**DatabaseConfig.get_psycopg2_params())
cursor = conn.cursor()

# Execute query
cursor.execute("SELECT COUNT(*) FROM lo_rung WHERE deleted = false")
count = cursor.fetchone()[0]
print(f"Total plots: {count}")

# Use query template
search_term = '%rừng%'
cursor.execute(
    QueryTemplates.SEARCH_PLOTS,
    (search_term, search_term, 100, 0)
)
results = cursor.fetchall()

# Close connection
cursor.close()
conn.close()
```

### Use Table Names

```python
from config.database import TableNames, FieldNames

# Build query with constants
query = f"""
    SELECT 
        {FieldNames.PLOT_CODE},
        {FieldNames.PLOT_NAME},
        {FieldNames.PLOT_AREA}
    FROM {TableNames.LO_RUNG}
    WHERE {FieldNames.DELETED} = false
"""
```

---

## Database Schema

### Main Tables

| Table | Description | Geometry |
|-------|-------------|----------|
| `lo_rung` | Forest plots | POLYGON |
| `chu_rung` | Forest owners | - |
| `dien_bien` | Forest changes | - |
| `lo_chu` | Plot-Owner relationship | - |

### Field Naming Convention

All field names use **Vietnamese snake_case**:

```
ma_lo          → Plot code
ten_lo         → Plot name
dien_tich      → Area (hectares)
ma_chu_rung    → Owner code
ten_chu_rung   → Owner name
ngay_dien_bien → Change date
```

### Geometry Fields

- **Column name**: `geom`
- **SRID**: 4326 (WGS84) or 3857 (Web Mercator) - check your schema
- **Type**: `POLYGON` for plots, `POINT` for owners (if applicable)

---

## Connection String Formats

### 1. PostgreSQL URI

```
postgresql://postgres:newpassword@localhost:8088/data_forest
```

**Get it**:
```python
conn_str = DatabaseConfig.get_connection_string()
```

### 2. QGIS Connection Parameters

```python
{
    'host': 'localhost',
    'port': '8088',
    'database': 'data_forest',
    'username': 'postgres',
    'password': 'newpassword',
    'sslmode': 'prefer'
}
```

**Get it**:
```python
params = DatabaseConfig.get_qgis_connection_params()
```

### 3. psycopg2 Parameters

```python
{
    'host': 'localhost',
    'port': 8088,  # Integer
    'database': 'data_forest',
    'user': 'postgres',
    'password': 'newpassword',
    'connect_timeout': 10,
    'sslmode': 'prefer'
}
```

**Get it**:
```python
params = DatabaseConfig.get_psycopg2_params()
```

---

## Environment Variables

All database settings can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FRMS_DB_HOST` | `localhost` | Database server hostname |
| `FRMS_DB_PORT` | `8088` | Database server port |
| `FRMS_DB_NAME` | `data_forest` | Database name |
| `FRMS_DB_USER` | `postgres` | Database username |
| `FRMS_DB_PASSWORD` | `newpassword` | Database password |
| `FRMS_DB_TIMEOUT` | `10` | Connection timeout (seconds) |
| `FRMS_DB_SSL_MODE` | `prefer` | SSL mode |

### Setting Environment Variables

**Linux/macOS**:
```bash
export FRMS_DB_HOST=production-server.example.com
export FRMS_DB_PASSWORD=secure_password_here
```

**Windows**:
```cmd
set FRMS_DB_HOST=production-server.example.com
set FRMS_DB_PASSWORD=secure_password_here
```

---

## Security Best Practices

### ✅ DO

1. **Use .env file** for local development
2. **Never commit** `.env` to git
3. **Use environment variables** for production
4. **Enable SSL** (`FRMS_DB_SSL_MODE=require`) for production
5. **Use strong passwords**
6. **Restrict database user** permissions (read-only where possible)

### ❌ DON'T

1. **Don't hardcode** passwords in code
2. **Don't commit** real credentials
3. **Don't use** `postgres` superuser in production
4. **Don't disable SSL** in production
5. **Don't share** `.env` files

---

## Troubleshooting

### Connection Refused

```
Error: could not connect to server: Connection refused
```

**Solutions**:
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Check firewall allows port 8088
3. Verify `postgresql.conf`: `listen_addresses = '*'`
4. Verify `pg_hba.conf`: Allow your IP

### Authentication Failed

```
Error: password authentication failed for user "postgres"
```

**Solutions**:
1. Verify password in `.env` file
2. Reset password: `ALTER USER postgres PASSWORD 'newpassword';`
3. Check `pg_hba.conf` authentication method

### Database Does Not Exist

```
Error: database "data_forest" does not exist
```

**Solutions**:
1. Create database: `CREATE DATABASE data_forest;`
2. Verify database name: `SELECT datname FROM pg_database;`
3. Check `FRMS_DB_NAME` in `.env`

### PostGIS Extension Missing

```
Error: type "geometry" does not exist
```

**Solutions**:
```sql
-- Connect to database
\c data_forest

-- Enable PostGIS
CREATE EXTENSION postgis;

-- Verify
SELECT PostGIS_Version();
```

### Slow Queries

**Enable query logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check indexes**:
```sql
-- Check indexes on lo_rung table
\di lo_rung*

-- Create missing indexes
CREATE INDEX idx_lo_rung_geom ON lo_rung USING GIST (geom);
CREATE INDEX idx_lo_rung_code ON lo_rung (ma_lo);
```

---

## Production Deployment

### 1. Update `.env` for Production

```env
FRMS_DB_HOST=prod-db.example.com
FRMS_DB_PORT=5432
FRMS_DB_NAME=data_forest_prod
FRMS_DB_USER=frms_app
FRMS_DB_PASSWORD=<strong-password-from-secrets-manager>
FRMS_DB_SSL_MODE=require
```

### 2. Use Read-Only User for Searches

```sql
-- Create read-only user
CREATE USER frms_readonly WITH PASSWORD 'readonly_password';

-- Grant SELECT on all tables
GRANT CONNECT ON DATABASE data_forest TO frms_readonly;
GRANT USAGE ON SCHEMA public TO frms_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO frms_readonly;
```

Update widget to use readonly connection:
```python
# For search widgets, use read-only credentials
READONLY_CONFIG = {
    'host': 'localhost',
    'port': '8088',
    'database': 'data_forest',
    'user': 'frms_readonly',
    'password': 'readonly_password'
}
```

---

## Related Files

- **Config**: `src/config/database.py`
- **Example**: `.env.example`
- **Local**: `.env` (not committed)
- **Widgets**: `src/app/tools/ui/frms_search_*_widget.py`

---

## Support

For database issues:
1. Check this guide first
2. Verify `.env` file
3. Test connection with `DatabaseConfig.test_connection()`
4. Check PostgreSQL logs: `/var/log/postgresql/`

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
