"""
QGIS Compatibility Layer.

Provides utilities for QGIS 3/4 compatibility.
"""

import logging
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)

QgsVectorFileWriter_ErrorCode = None


def qgis_version_int() -> int:
    """Get QGIS version as integer (e.g., 32800 for 3.28.0, 40000 for 4.0.0)."""
    try:
        from qgis.core import Qgis
        return Qgis.QGIS_VERSION_INT
    except ImportError:
        return 0


def is_qgis_4() -> bool:
    """Check if running on QGIS 4 or later."""
    return qgis_version_int() >= 40000


def qgis_min_version(required_version: str) -> bool:
    """Check if QGIS version meets minimum requirement (e.g., '3.34')."""
    try:
        from qgis.core import Qgis
        version_parts = required_version.split('.')
        required_int = (int(version_parts[0]) * 10000 +
                       int(version_parts[1]) * 100 +
                       int(version_parts[2]) if len(version_parts) >= 3 else 0)
        return Qgis.QGIS_VERSION_INT >= required_int
    except ImportError:
        return False


class MessageBarCompat:
    """Compatibility wrapper for messageBar operations."""

    @staticmethod
    def push_message(message_bar, title: str, message: str, level=None, duration: int = 5):
        """Push a message to the QGIS message bar.

        In QGIS 3.x uses pushMessage with level parameter.
        In QGIS 4.x pushSuccess/pushWarning may be deprecated in favor of pushMessage.
        """
        if level is None:
            from qgis.core import Qgis
            level = Qgis.Info

        try:
            message_bar.pushMessage(title, message, level, duration)
        except Exception as e:
            logger.warning(f"pushMessage failed: {e}")

    @staticmethod
    def push_success(message_bar, title: str, message: str, duration: int = 5):
        """Push a success message."""
        try:
            message_bar.pushSuccess(title, message, duration)
        except AttributeError:
            from qgis.core import Qgis
            message_bar.pushMessage(title, message, Qgis.Success, duration)
        except Exception as e:
            logger.warning(f"pushSuccess failed: {e}")

    @staticmethod
    def push_warning(message_bar, title: str, message: str, duration: int = 5):
        """Push a warning message."""
        try:
            message_bar.pushWarning(title, message, duration)
        except AttributeError:
            from qgis.core import Qgis
            message_bar.pushMessage(title, message, Qgis.Warning, duration)
        except Exception as e:
            logger.warning(f"pushWarning failed: {e}")

    @staticmethod
    def push_info(message_bar, title: str, message: str, duration: int = 5):
        """Push an info message."""
        try:
            message_bar.pushInfo(title, message, duration)
        except AttributeError:
            from qgis.core import Qgis
            message_bar.pushMessage(title, message, Qgis.Info, duration)
        except Exception as e:
            logger.warning(f"pushInfo failed: {e}")


def write_vector_format_v3(layer, path, transform_context, options):
    """Wrapper for QgsVectorFileWriter.writeAsVectorFormatV3 that handles both QGIS 3 and 4 APIs.

    QGIS 3.x returns Tuple[error_code, error_message]
    QGIS 4.x may change to exception-based or different return type

    Returns Tuple[error_code, error_message] for compatibility, or raises on critical error.
    """
    from qgis.core import QgsVectorFileWriter

    try:
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, path, transform_context, options
        )

        # QGIS 3.x returns tuple (error_code, error_message)
        if isinstance(result, tuple):
            return result

        # QGIS 4.x might return just error_code or use exceptions
        # Treat single value as error_code (0 = NoError)
        if isinstance(result, int):
            return (result, "")

        # Unknown format, return as-is wrapped
        return (0, str(result))

    except Exception as e:
        # For QGIS 4.x exception-based errors, log and return error
        logger.warning(f"writeAsVectorFormatV3 raised exception: {e}")
        return (1, str(e))


def check_writer_error(result) -> bool:
    """Check if QgsVectorFileWriter result indicates success.

    Args:
        result: Return value from writeAsVectorFormatV3

    Returns:
        True if no error, False otherwise
    """
    from qgis.core import QgsVectorFileWriter

    if isinstance(result, tuple):
        return result[0] == QgsVectorFileWriter.NoError
    elif isinstance(result, int):
        return result == QgsVectorFileWriter.NoError

    # Assume success if we can't determine
    return True