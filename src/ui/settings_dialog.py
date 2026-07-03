from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QDialogButtonBox, QMessageBox, QLabel
from qgis.PyQt.QtCore import QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        # Import tr locally to avoid circular dependencies
        from tlgeo2qgis.util.i18n import tr, _current_locale
        
        self.setWindowTitle(tr("Settings"))
        self.resize(320, 150)
        self.setModal(True)
        
        self.settings = QSettings("TLGeo", "QGIS2Plugin")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Language Selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Tiếng Việt", "vi")
        self.lang_combo.addItem("English", "en")
        
        # Read saved setting or default to current locale
        saved_lang = self.settings.value("i18n/language", _current_locale)
        index = self.lang_combo.findData(saved_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
            
        form_layout.addRow(tr("Language:"), self.lang_combo)
        layout.addLayout(form_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Style buttons and dialog for premium look
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 13px;
                color: #333333;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                background-color: white;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #40a9ff;
            }
            QPushButton {
                padding: 6px 15px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        
        # Translate button box Save/Cancel text
        save_button = self.button_box.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setText(tr("Save"))
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if cancel_button:
            cancel_button.setText(tr("Cancel"))
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #595959;
                    border: 1px solid #d9d9d9;
                }
                QPushButton:hover {
                    color: #40a9ff;
                    border-color: #40a9ff;
                }
            """)
            
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        
    def accept(self):
        from tlgeo2qgis.util.i18n import tr, init_i18n
        
        # Save setting
        selected_lang = self.lang_combo.currentData()
        self.settings.setValue("i18n/language", selected_lang)
        
        # Trigger reload of local translation variable immediately
        init_i18n()
        
        QMessageBox.information(
            self,
            tr("Settings"),
            tr("Language changed. Please restart QGIS to apply changes completely.")
        )
        super(SettingsDialog, self).accept()
