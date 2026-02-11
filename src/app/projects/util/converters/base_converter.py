"""Base Converter - Abstract base class for all layer converters."""

from abc import ABC, abstractmethod
from qgis.core import Qgis, QgsVectorLayer
from qgis.core import QgsMessageLog as MessageLog
import os
from datetime import datetime


class BaseConverter(ABC):
    """Abstract base class for layer converters.
    
    All converters inherit from this class and implement:
    - can_convert(): Check if converter is available
    - convert(): Perform the actual conversion
    
    Usage:
        converter = SomeConverter()
        if converter.can_convert():
            converter.convert(source, destination)
    """
    
    def __init__(self, name="BaseConverter"):
        self.name = name
        self._available = None
        self.log_file = None  # Set by caller if needed
    
    def _log_to_file(self, message: str):
        """Write to log file if available."""
        if self.log_file:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] [{self.name}] {message}\n")
            except:
                pass
    
    def can_convert(self) -> bool:
        """Check if this converter is available on the system."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available
    
    @abstractmethod
    def _check_availability(self) -> bool:
        """Override to check if required tools/drivers are available."""
        pass
    
    @abstractmethod
    def convert(self, layer, output_path: str, **kwargs) -> bool:
        """Perform the conversion. Returns True on success."""
        pass
    
    def log(self, message: str, level=Qgis.Info):
        """Log a message."""
        # Write to QGIS Message Log
        MessageLog.logMessage(f"[{self.name}] {message}", "TLGeo", level)
        # Also write to file if available
        self._log_to_file(f"{message}")
    
    def log_success(self, output_path: str):
        """Log successful conversion."""
        self.log(f"Exported: {output_path}")
    
    def log_error(self, error: str):
        """Log conversion error."""
        self.log(f"Error: {error}", Qgis.Warning)
    
    def log_info(self, message: str):
        """Log info message."""
        self.log(message, Qgis.Info)
