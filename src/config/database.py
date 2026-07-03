"""
Database Configuration for FRMS

This module contains database connection settings for the Forest Resource
Management System (FRMS) PostgreSQL/PostGIS database.

Security Note:
    For production, override these values using environment variables or
    a .env file. Never commit actual credentials to version control.
"""

import os
from pathlib import Path

# ============================================================================
# DATABASE CONNECTION SETTINGS
# ============================================================================

class DatabaseConfig:
    """
    Database connection configuration.
    
    Values can be overridden via environment variables:
    - FRMS_DB_HOST
    - FRMS_DB_PORT
    - FRMS_DB_NAME
    - FRMS_DB_USER
    - FRMS_DB_PASSWORD
    """
    
    # Default connection parameters
    HOST = os.getenv('FRMS_DB_HOST', 'localhost')
    PORT = os.getenv('FRMS_DB_PORT', '8088')
    DATABASE = os.getenv('FRMS_DB_NAME', 'data_forest')
    USER = os.getenv('FRMS_DB_USER', 'postgres')
    PASSWORD = os.getenv('FRMS_DB_PASSWORD', 'newpassword')
    
    # Connection timeout (seconds)
    TIMEOUT = int(os.getenv('FRMS_DB_TIMEOUT', '10'))
    
    # SSL Mode (disable, allow, prefer, require, verify-ca, verify-full)
    SSL_MODE = os.getenv('FRMS_DB_SSL_MODE', 'prefer')
    
    @classmethod
    def get_connection_string(cls):
        """
        Get PostgreSQL connection string.
        
        Returns:
            str: PostgreSQL connection string in URI format
            
        """
        return (
            f"postgresql://{cls.USER}:{cls.PASSWORD}@"
            f"{cls.HOST}:{cls.PORT}/{cls.DATABASE}"
        )
    
    @classmethod
    def get_qgis_connection_params(cls):
        """
        Get connection parameters for QGIS QgsDataSourceUri.
        
        Returns:
            dict: Connection parameters for QGIS
            
        Example:
            >>> params = DatabaseConfig.get_qgis_connection_params()
            >>> uri = QgsDataSourceUri()
            >>> uri.setConnection(
            ...     params['host'],
            ...     params['port'],
            ...     params['database'],
            ...     params['username'],
            ...     params['password']
            ... )
        """
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.DATABASE,
            'username': cls.USER,
            'password': cls.PASSWORD,
            'sslmode': cls.SSL_MODE
        }
    
    @classmethod
    def get_psycopg2_params(cls):
        """
        Get connection parameters for psycopg2.
        
        Returns:
            dict: Connection parameters for psycopg2
            
        Example:
            >>> import psycopg2
            >>> conn = psycopg2.connect(**DatabaseConfig.get_psycopg2_params())
        """
        return {
            'host': cls.HOST,
            'port': int(cls.PORT),
            'database': cls.DATABASE,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'connect_timeout': cls.TIMEOUT,
            'sslmode': cls.SSL_MODE
        }
    
    @classmethod
    def test_connection(cls):
        """
        Test database connection.
        
        Returns:
            tuple: (success: bool, message: str)
            
        Example:
            >>> success, message = DatabaseConfig.test_connection()
            >>> if success:
            ...     print("Connected!")
            ... else:
            ...     print(f"Failed: {message}")
        """
        try:
            import psycopg2
            conn = psycopg2.connect(**cls.get_psycopg2_params())
            conn.close()
            return (True, "Connection successful")
        except ImportError:
            return (False, "psycopg2 not installed")
        except Exception as e:
            return (False, str(e))


# ============================================================================
# TABLE NAMES
# ============================================================================

class TableNames:
    """FRMS database table names"""
    
    # Main tables
    LO_RUNG = 'lo_rung'          # Forest plots
    CHU_RUNG = 'chu_rung'        # Forest owners
    DIEN_BIEN = 'dien_bien'      # Forest changes/evolution
    
    # Relationship tables
    LO_CHU = 'lo_chu'            # Plot-Owner relationship
    
    # Lookup tables
    LOAI_RUNG = 'loai_rung'      # Forest types
    LOAI_CHU = 'loai_chu'        # Owner types
    LOAI_DIEN_BIEN = 'loai_dien_bien'  # Change types
    
    @classmethod
    def get_all_tables(cls):
        """Get list of all table names"""
        return [
            cls.LO_RUNG,
            cls.CHU_RUNG,
            cls.DIEN_BIEN,
            cls.LO_CHU,
            cls.LOAI_RUNG,
            cls.LOAI_CHU,
            cls.LOAI_DIEN_BIEN
        ]


# ============================================================================
# FIELD NAMES
# ============================================================================

class FieldNames:
    """Standard field names for FRMS tables"""
    
    # Common fields
    ID = 'id'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    CREATED_BY = 'created_by'
    UPDATED_BY = 'updated_by'
    DELETED = 'deleted'
    
    # Lo rung (Forest Plot) fields
    PLOT_CODE = 'ma_lo'
    PLOT_NAME = 'ten_lo'
    PLOT_AREA = 'dien_tich'
    FOREST_TYPE = 'loai_rung'
    STATUS = 'trang_thai'
    NOTES = 'ghi_chu'
    GEOM = 'geom'
    
    # Chu rung (Owner) fields
    OWNER_CODE = 'ma_chu_rung'
    OWNER_NAME = 'ten_chu_rung'
    OWNER_TYPE = 'loai_chu'
    CMND = 'cmnd'
    TAX_CODE = 'ma_so_thue'
    ADDRESS = 'dia_chi'
    PHONE = 'dien_thoai'
    EMAIL = 'email'
    
    # Dien bien (Change) fields
    CHANGE_CODE = 'ma_dien_bien'
    CHANGE_DATE = 'ngay_dien_bien'
    CHANGE_TYPE = 'loai_dien_bien'
    AFFECTED_AREA = 'dien_tich_anh_huong'
    SEVERITY = 'muc_do'
    DESCRIPTION = 'mo_ta'
    PHOTO = 'anh_dinh_kem'


# ============================================================================
# QUERY TEMPLATES
# ============================================================================

class QueryTemplates:
    """SQL query templates for common operations"""
    
    # Search queries
    SEARCH_PLOTS = """
        SELECT 
            id, ma_lo, ten_lo, dien_tich, loai_rung, trang_thai,
            ST_AsText(geom) as geom_wkt,
            ST_Area(ST_Transform(geom, 3857)) / 10000 as area_ha
        FROM lo_rung
        WHERE deleted = false
            AND (
                ma_lo ILIKE %s OR
                ten_lo ILIKE %s
            )
        ORDER BY ma_lo
        LIMIT %s OFFSET %s
    """
    
    SEARCH_OWNERS = """
        SELECT 
            id, ma_chu_rung, ten_chu_rung, loai_chu, 
            cmnd, dia_chi, dien_thoai,
            (SELECT COUNT(*) FROM lo_chu WHERE ma_chu_rung = chu_rung.ma_chu_rung) as plot_count
        FROM chu_rung
        WHERE deleted = false
            AND (
                ma_chu_rung ILIKE %s OR
                ten_chu_rung ILIKE %s OR
                cmnd ILIKE %s
            )
        ORDER BY ten_chu_rung
        LIMIT %s OFFSET %s
    """
    
    SEARCH_CHANGES = """
        SELECT 
            id, ma_dien_bien, ma_lo, ngay_dien_bien, 
            loai_dien_bien, dien_tich_anh_huong, muc_do, mo_ta
        FROM dien_bien
        WHERE deleted = false
            AND (
                ma_dien_bien ILIKE %s OR
                ma_lo ILIKE %s OR
                mo_ta ILIKE %s
            )
            AND ngay_dien_bien BETWEEN %s AND %s
        ORDER BY ngay_dien_bien DESC
        LIMIT %s OFFSET %s
    """
    
    # Get by ID
    GET_PLOT_BY_ID = """
        SELECT * FROM lo_rung WHERE id = %s AND deleted = false
    """
    
    GET_OWNER_BY_CODE = """
        SELECT * FROM chu_rung WHERE ma_chu_rung = %s AND deleted = false
    """
    
    # Relationship queries
    GET_PLOTS_BY_OWNER = """
        SELECT lr.*
        FROM lo_rung lr
        INNER JOIN lo_chu lc ON lr.ma_lo = lc.ma_lo
        WHERE lc.ma_chu_rung = %s AND lr.deleted = false
    """
    
    GET_CHANGES_BY_PLOT = """
        SELECT * FROM dien_bien
        WHERE ma_lo = %s AND deleted = false
        ORDER BY ngay_dien_bien DESC
    """


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Usage Examples:

1. Get connection string:
    >>> from config.database import DatabaseConfig
    >>> conn_str = DatabaseConfig.get_connection_string()
    >>> print(conn_str)

2. Connect with QGIS:
    >>> from qgis.core import QgsDataSourceUri
    >>> params = DatabaseConfig.get_qgis_connection_params()
    >>> uri = QgsDataSourceUri()
    >>> uri.setConnection(
    ...     params['host'],
    ...     params['port'],
    ...     params['database'],
    ...     params['username'],
    ...     params['password']
    ... )
    >>> uri.setDataSource('public', 'lo_rung', 'geom')

3. Connect with psycopg2:
    >>> import psycopg2
    >>> conn = psycopg2.connect(**DatabaseConfig.get_psycopg2_params())
    >>> cursor = conn.cursor()
    >>> cursor.execute("SELECT COUNT(*) FROM lo_rung")
    >>> print(cursor.fetchone()[0])

4. Test connection:
    >>> success, message = DatabaseConfig.test_connection()
    >>> if success:
    ...     print("✅ Database connected")
    ... else:
    ...     print(f"❌ Connection failed: {message}")

5. Use table names:
    >>> from config.database import TableNames
    >>> query = f"SELECT * FROM {TableNames.LO_RUNG}"

6. Use field names:
    >>> from config.database import FieldNames
    >>> query = f"SELECT {FieldNames.PLOT_CODE}, {FieldNames.PLOT_NAME} FROM lo_rung"
"""
