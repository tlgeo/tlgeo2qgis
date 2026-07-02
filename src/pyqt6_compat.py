"""
PyQt6 / Qt6 Compatibility Layer for QGIS 4.
This module dynamically patches qgis.PyQt modules to support PyQt5-style unscoped enums
(e.g., Qt.AlignCenter instead of Qt.AlignmentFlag.AlignCenter).
"""
import sys

def apply_compat_patches():
    try:
        import qgis.PyQt
        from qgis.PyQt import QtCore
        
        # Detect QGIS 4 or PyQt6 presence robustly
        is_qgis4 = False
        try:
            from qgis.core import Qgis
            version_int = getattr(Qgis, 'QGIS_VERSION_INT', 0)
            if isinstance(version_int, int):
                is_qgis4 = version_int >= 40000
        except ImportError:
            pass
            
        is_pyqt6 = False
        try:
            import PyQt6
            is_pyqt6 = True
        except ImportError:
            pass
            
        if is_qgis4 or is_pyqt6:
            from qgis.PyQt import QtGui, QtWidgets
            
            class CompatMeta(type):
                def __getattr__(cls, name):
                    orig = getattr(cls, '_original_class', None)
                    if orig:
                        # 1. Try to get attribute from original class
                        try:
                            return getattr(orig, name)
                        except AttributeError:
                            pass
                        
                        # 2. Search nested classes/enums of original class
                        for attr_name in dir(orig):
                            if attr_name.startswith('_'):
                                continue
                            try:
                                attr = getattr(orig, attr_name)
                            except AttributeError:
                                continue
                            if isinstance(attr, type):
                                try:
                                    if hasattr(attr, name):
                                        return getattr(attr, name)
                                except AttributeError:
                                    continue
                    raise AttributeError(f"type object '{cls.__name__}' has no attribute '{name}'")

                def __instancecheck__(cls, instance):
                    orig = getattr(cls, '_original_class', None)
                    if orig:
                        return isinstance(instance, orig)
                    return super().__instancecheck__(instance)

                def __subclasscheck__(cls, subclass):
                    orig = getattr(cls, '_original_class', None)
                    if orig:
                        if hasattr(subclass, '_original_class'):
                            subclass = getattr(subclass, '_original_class')
                        return issubclass(subclass, orig)
                    return super().__subclasscheck__(subclass)

                def __call__(cls, *args, **kwargs):
                    orig = getattr(cls, '_original_class', None)
                    if orig:
                        return orig(*args, **kwargs)
                    return super().__call__(*args, **kwargs)

            def make_compat_class(orig_class, name):
                try:
                    return CompatMeta(name, (orig_class,), {'_original_class': orig_class})
                except TypeError:
                    # Final/non-subclassable class (e.g. Qt)
                    return CompatMeta(name, (object,), {'_original_class': orig_class})

            class ModuleCompatWrapper:
                def __init__(self, original_module):
                    self._original_module = original_module
                    self._wrapped_cache = {}

                def __getattr__(self, name):
                    if name in self._wrapped_cache:
                        return self._wrapped_cache[name]
                    
                    orig_attr = getattr(self._original_module, name)
                    if name in ('pyqtSignal', 'pyqtSlot', 'pyqtProperty'):
                        return orig_attr
                        
                    if isinstance(orig_attr, type):
                        wrapped = make_compat_class(orig_attr, name)
                        self._wrapped_cache[name] = wrapped
                        return wrapped
                    return orig_attr

            # Wrap modules and replace in sys.modules
            sys.modules['qgis.PyQt.QtCore'] = ModuleCompatWrapper(sys.modules['qgis.PyQt.QtCore'])
            sys.modules['qgis.PyQt.QtGui'] = ModuleCompatWrapper(sys.modules['qgis.PyQt.QtGui'])
            sys.modules['qgis.PyQt.QtWidgets'] = ModuleCompatWrapper(sys.modules['qgis.PyQt.QtWidgets'])

            # Update parent module references
            qgis.PyQt.QtCore = sys.modules['qgis.PyQt.QtCore']
            qgis.PyQt.QtGui = sys.modules['qgis.PyQt.QtGui']
            qgis.PyQt.QtWidgets = sys.modules['qgis.PyQt.QtWidgets']
            
            print("Successfully applied QGIS 4 / PyQt6 compatibility shim")
            
    except Exception as e:
        print(f"Failed to apply PyQt6 compatibility patches: {e}")

# Apply patches immediately on import
apply_compat_patches()
