#!/usr/bin/env python3
"""
Native Settings Dialog for WhisperEngine Universal App
Comprehensive settings UI with tabbed interface and real-time validation.
"""

import logging
import platform

try:
    from PySide6.QtCore import QSize, Qt, QThread, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QSplitter,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

if PYSIDE6_AVAILABLE:
    from .native_settings_manager import NativeSettingsManager


class LLMTestThread(QThread):
    """Background thread for testing LLM connection"""

    test_completed = Signal(bool, str)

    def __init__(self, settings_manager: "NativeSettingsManager"):
        super().__init__()
        self.settings_manager = settings_manager

    def run(self):
        """Test LLM connection in background"""
        try:
            success, message = self.settings_manager.validate_llm_connection()
            self.test_completed.emit(success, message)
        except Exception as e:
            self.test_completed.emit(False, f"Test failed: {str(e)}")


class ModelFetchThread(QThread):
    """Background thread for fetching available models"""

    models_fetched = Signal(list)

    def __init__(self, settings_manager: "NativeSettingsManager"):
        super().__init__()
        self.settings_manager = settings_manager

    def run(self):
        """Fetch available models in background"""
        try:
            models = self.settings_manager.get_available_models()
            self.models_fetched.emit(models)
        except Exception as e:
            logging.error(f"Error fetching models: {e}")
            self.models_fetched.emit([])


class NativeSettingsDialog(QDialog):
    """Comprehensive native settings dialog"""

    def __init__(self, settings_manager: NativeSettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(__name__)

        # Track changes
        self.has_changes = False
        self.test_thread: LLMTestThread | None = None
        self.model_fetch_thread: ModelFetchThread | None = None

        self.init_ui()
        self.load_current_settings()
        self.connect_signals()

        # Apply platform-specific styling
        self.apply_platform_styling()

        self.logger.info("Settings dialog initialized")

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WhisperEngine Settings")
        self.setModal(True)
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_llm_tab()
        self.create_ui_tab()
        self.create_platform_tab()
        self.create_privacy_tab()
        self.create_advanced_tab()

        # Button bar
        button_layout = QHBoxLayout()

        # Import/Export buttons
        self.import_btn = QPushButton("Import Settings")
        self.export_btn = QPushButton("Export Settings")
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()

        # Main action buttons
        self.reset_btn = QPushButton("Reset to Defaults")
        self.cancel_btn = QPushButton("Cancel")
        self.apply_btn = QPushButton("Apply")
        self.ok_btn = QPushButton("OK")

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

        # Set default button
        self.ok_btn.setDefault(True)

    def create_llm_tab(self):
        """Create LLM configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Server Configuration Group
        server_group = QGroupBox("LLM Server Configuration")
        server_form = QFormLayout(server_group)

        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("http://127.0.0.1:1234/v1")
        server_form.addRow("API URL:", self.api_url_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Optional API key")
        server_form.addRow("API Key:", self.api_key_edit)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(" seconds")
        server_form.addRow("Timeout:", self.timeout_spin)

        layout.addWidget(server_group)

        # Model Configuration Group
        model_group = QGroupBox("Model Configuration")
        model_layout = QVBoxLayout(model_group)

        # Model selection
        model_form = QFormLayout()

        model_row = QHBoxLayout()
        self.model_name_combo = QComboBox()
        self.model_name_combo.setEditable(True)
        self.refresh_models_btn = QPushButton("🔄")
        self.refresh_models_btn.setMaximumWidth(30)
        self.refresh_models_btn.setToolTip("Refresh available models")
        model_row.addWidget(self.model_name_combo)
        model_row.addWidget(self.refresh_models_btn)

        model_form.addRow("Model Name:", model_row)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setSingleStep(100)
        model_form.addRow("Max Tokens:", self.max_tokens_spin)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(2)
        model_form.addRow("Temperature:", self.temperature_spin)

        model_layout.addLayout(model_form)
        layout.addWidget(model_group)

        # Connection Test Group
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)

        test_button_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        test_button_layout.addWidget(self.test_connection_btn)
        test_button_layout.addWidget(self.test_progress)
        test_button_layout.addStretch()
        test_layout.addLayout(test_button_layout)

        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        test_layout.addWidget(self.test_result_label)

        layout.addWidget(test_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "🤖 LLM")

    def create_ui_tab(self):
        """Create UI configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Theme and Appearance Group
        appearance_group = QGroupBox("Theme and Appearance")
        appearance_form = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "auto"])
        appearance_form.addRow("Theme:", self.theme_combo)

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(
            [
                "default",
                "-apple-system",
                "Segoe UI",
                "system-ui",
                "Arial",
                "Helvetica",
                "Roboto",
                "Source Sans Pro",
            ]
        )
        appearance_form.addRow("Font Family:", self.font_family_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        appearance_form.addRow("Font Size:", self.font_size_spin)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(100)
        self.opacity_label = QLabel("100%")
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        appearance_form.addRow("Window Opacity:", opacity_layout)

        layout.addWidget(appearance_group)

        # Chat Interface Group
        chat_group = QGroupBox("Chat Interface")
        chat_layout = QVBoxLayout(chat_group)

        self.auto_scroll_check = QCheckBox("Auto-scroll to new messages")
        self.show_timestamps_check = QCheckBox("Show message timestamps")
        self.markdown_rendering_check = QCheckBox("Enable markdown rendering")
        self.auto_save_check = QCheckBox("Auto-save conversations")

        chat_layout.addWidget(self.auto_scroll_check)
        chat_layout.addWidget(self.show_timestamps_check)
        chat_layout.addWidget(self.markdown_rendering_check)
        chat_layout.addWidget(self.auto_save_check)

        layout.addWidget(chat_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "🎨 Interface")

    def create_platform_tab(self):
        """Create platform-specific configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Platform Info
        info_group = QGroupBox("Platform Information")
        info_layout = QFormLayout(info_group)

        platform_name = platform.system()
        platform_version = platform.release()
        info_layout.addRow("Operating System:", QLabel(f"{platform_name} {platform_version}"))
        info_layout.addRow("Architecture:", QLabel(platform.machine()))

        layout.addWidget(info_group)

        # System Integration Group
        integration_group = QGroupBox("System Integration")
        integration_layout = QVBoxLayout(integration_group)

        self.system_tray_check = QCheckBox("Enable system tray icon")
        self.start_minimized_check = QCheckBox("Start minimized to tray")
        self.minimize_to_tray_check = QCheckBox("Minimize to tray instead of closing")
        self.auto_start_check = QCheckBox("Start with system (auto-start)")
        self.notifications_check = QCheckBox("Enable system notifications")
        self.platform_integration_check = QCheckBox("Enable platform-specific features")

        integration_layout.addWidget(self.system_tray_check)
        integration_layout.addWidget(self.start_minimized_check)
        integration_layout.addWidget(self.minimize_to_tray_check)
        integration_layout.addWidget(self.auto_start_check)
        integration_layout.addWidget(self.notifications_check)
        integration_layout.addWidget(self.platform_integration_check)

        layout.addWidget(integration_group)

        # Platform-specific features
        if platform.system() == "Darwin":  # macOS
            macos_group = QGroupBox("macOS Features")
            macos_layout = QVBoxLayout(macos_group)

            self.menu_bar_check = QCheckBox("Show menu bar integration")
            self.dock_integration_check = QCheckBox("Enable Dock integration")

            macos_layout.addWidget(self.menu_bar_check)
            macos_layout.addWidget(self.dock_integration_check)

            layout.addWidget(macos_group)

        elif platform.system() == "Windows":  # Windows
            windows_group = QGroupBox("Windows Features")
            windows_layout = QVBoxLayout(windows_group)

            self.taskbar_integration_check = QCheckBox("Enable taskbar integration")
            self.jump_lists_check = QCheckBox("Enable jump lists")

            windows_layout.addWidget(self.taskbar_integration_check)
            windows_layout.addWidget(self.jump_lists_check)

            layout.addWidget(windows_group)

        elif platform.system() == "Linux":  # Linux
            linux_group = QGroupBox("Linux Features")
            linux_layout = QVBoxLayout(linux_group)

            self.desktop_integration_check = QCheckBox("Enable desktop environment integration")
            self.freedesktop_check = QCheckBox("Follow FreeDesktop standards")

            linux_layout.addWidget(self.desktop_integration_check)
            linux_layout.addWidget(self.freedesktop_check)

            layout.addWidget(linux_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "🖥️ Platform")

    def create_privacy_tab(self):
        """Create privacy and security configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Data Storage Group
        storage_group = QGroupBox("Data Storage")
        storage_layout = QVBoxLayout(storage_group)

        self.store_conversations_check = QCheckBox("Store conversation history")
        self.encryption_check = QCheckBox("Encrypt stored data")

        storage_layout.addWidget(self.store_conversations_check)
        storage_layout.addWidget(self.encryption_check)

        # Auto-delete settings
        delete_layout = QHBoxLayout()
        delete_layout.addWidget(QLabel("Auto-delete conversations after:"))
        self.auto_delete_spin = QSpinBox()
        self.auto_delete_spin.setRange(1, 365)
        self.auto_delete_spin.setSuffix(" days")
        delete_layout.addWidget(self.auto_delete_spin)
        delete_layout.addStretch()
        storage_layout.addLayout(delete_layout)

        layout.addWidget(storage_group)

        # Privacy Group
        privacy_group = QGroupBox("Privacy Settings")
        privacy_layout = QVBoxLayout(privacy_group)

        self.share_analytics_check = QCheckBox("Share anonymous usage analytics")
        self.local_mode_check = QCheckBox("Local mode only (no external connections)")

        privacy_layout.addWidget(self.share_analytics_check)
        privacy_layout.addWidget(self.local_mode_check)

        layout.addWidget(privacy_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "🔒 Privacy")

    def create_advanced_tab(self):
        """Create advanced configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Development Group
        dev_group = QGroupBox("Development & Debugging")
        dev_layout = QVBoxLayout(dev_group)

        self.debug_mode_check = QCheckBox("Enable debug mode")

        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addWidget(self.log_level_combo)
        log_layout.addStretch()

        dev_layout.addWidget(self.debug_mode_check)
        dev_layout.addLayout(log_layout)

        layout.addWidget(dev_group)

        # Performance Group
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)

        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory Limit:"))
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(128, 2048)
        self.memory_limit_spin.setSuffix(" MB")
        memory_layout.addWidget(self.memory_limit_spin)
        memory_layout.addStretch()

        self.cache_enabled_check = QCheckBox("Enable caching")

        perf_layout.addLayout(memory_layout)
        perf_layout.addWidget(self.cache_enabled_check)

        layout.addWidget(perf_group)

        # Experimental Group
        exp_group = QGroupBox("Experimental Features")
        exp_layout = QVBoxLayout(exp_group)

        self.experimental_check = QCheckBox("Enable experimental features")

        plugins_layout = QHBoxLayout()
        self.plugins_path_edit = QLineEdit()
        self.browse_plugins_btn = QPushButton("Browse...")
        plugins_layout.addWidget(QLabel("Custom Plugins Path:"))
        plugins_layout.addWidget(self.plugins_path_edit)
        plugins_layout.addWidget(self.browse_plugins_btn)

        exp_layout.addWidget(self.experimental_check)
        exp_layout.addLayout(plugins_layout)

        layout.addWidget(exp_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "⚡ Advanced")

    def load_current_settings(self):
        """Load current settings into UI"""
        configs = self.settings_manager.get_all_configs()

        # LLM settings
        llm = configs["llm"]
        self.api_url_edit.setText(llm.api_url)
        self.api_key_edit.setText(llm.api_key)
        self.timeout_spin.setValue(llm.timeout_seconds)
        self.model_name_combo.setCurrentText(llm.model_name)
        self.max_tokens_spin.setValue(llm.max_tokens)
        self.temperature_spin.setValue(llm.temperature)

        # UI settings
        ui = configs["ui"]
        self.theme_combo.setCurrentText(ui.theme)
        self.font_family_combo.setCurrentText(ui.font_family)
        self.font_size_spin.setValue(ui.font_size)
        self.opacity_slider.setValue(int(ui.window_opacity * 100))
        self.auto_scroll_check.setChecked(ui.auto_scroll)
        self.show_timestamps_check.setChecked(ui.show_timestamps)
        self.markdown_rendering_check.setChecked(ui.markdown_rendering)
        self.auto_save_check.setChecked(ui.auto_save_conversations)

        # Platform settings
        platform_cfg = configs["platform"]
        self.system_tray_check.setChecked(platform_cfg.system_tray_enabled)
        self.start_minimized_check.setChecked(platform_cfg.start_minimized)
        self.minimize_to_tray_check.setChecked(platform_cfg.minimize_to_tray)
        self.auto_start_check.setChecked(platform_cfg.auto_start)
        self.notifications_check.setChecked(platform_cfg.notifications_enabled)
        self.platform_integration_check.setChecked(platform_cfg.platform_integration)

        # Privacy settings
        privacy = configs["privacy"]
        self.store_conversations_check.setChecked(privacy.store_conversations)
        self.encryption_check.setChecked(privacy.encryption_enabled)
        self.auto_delete_spin.setValue(privacy.auto_delete_after_days)
        self.share_analytics_check.setChecked(privacy.share_analytics)
        self.local_mode_check.setChecked(privacy.local_mode_only)

        # Advanced settings
        advanced = configs["advanced"]
        self.debug_mode_check.setChecked(advanced.debug_mode)
        self.log_level_combo.setCurrentText(advanced.log_level)
        self.memory_limit_spin.setValue(advanced.memory_limit_mb)
        self.cache_enabled_check.setChecked(advanced.cache_enabled)
        self.experimental_check.setChecked(advanced.experimental_features)
        self.plugins_path_edit.setText(advanced.custom_plugins_path)

        # Update opacity label
        self.update_opacity_label()

    def connect_signals(self):
        """Connect UI signals to handlers"""
        # Button connections
        self.ok_btn.clicked.connect(self.accept_changes)
        self.apply_btn.clicked.connect(self.apply_changes)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_to_defaults)

        # Import/Export
        self.import_btn.clicked.connect(self.import_settings)
        self.export_btn.clicked.connect(self.export_settings)

        # LLM tab connections
        self.test_connection_btn.clicked.connect(self.test_llm_connection)
        self.refresh_models_btn.clicked.connect(self.refresh_models)

        # UI tab connections
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)

        # Advanced tab connections
        self.browse_plugins_btn.clicked.connect(self.browse_plugins_path)

        # Change tracking
        self.connect_change_tracking()

    def connect_change_tracking(self):
        """Connect change tracking to all inputs"""
        # This is a simplified version - in practice you'd connect all inputs
        self.api_url_edit.textChanged.connect(self.mark_changes)
        self.model_name_combo.currentTextChanged.connect(self.mark_changes)
        self.theme_combo.currentTextChanged.connect(self.mark_changes)

    def mark_changes(self):
        """Mark that settings have changed"""
        self.has_changes = True
        self.apply_btn.setEnabled(True)

    def update_opacity_label(self):
        """Update opacity percentage label"""
        value = self.opacity_slider.value()
        self.opacity_label.setText(f"{value}%")

    def test_llm_connection(self):
        """Test LLM connection in background"""
        if self.test_thread and self.test_thread.isRunning():
            return

        # Update settings temporarily for test
        self.apply_llm_settings_for_test()

        # Start test
        self.test_connection_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate
        self.test_result_label.setText("Testing connection...")

        self.test_thread = LLMTestThread(self.settings_manager)
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()

    def apply_llm_settings_for_test(self):
        """Apply current LLM settings temporarily for testing"""
        self.settings_manager.update_llm_config(
            api_url=self.api_url_edit.text(),
            model_name=self.model_name_combo.currentText(),
            api_key=self.api_key_edit.text(),
            timeout_seconds=self.timeout_spin.value(),
        )

    def on_test_completed(self, success: bool, message: str):
        """Handle test completion"""
        self.test_connection_btn.setEnabled(True)
        self.test_progress.setVisible(False)
        self.test_result_label.setText(message)

        # Clean up thread
        if self.test_thread:
            self.test_thread.deleteLater()
            self.test_thread = None

    def refresh_models(self):
        """Refresh available models list"""
        if self.model_fetch_thread and self.model_fetch_thread.isRunning():
            return

        # Apply current URL for fetching
        self.apply_llm_settings_for_test()

        self.refresh_models_btn.setEnabled(False)
        self.refresh_models_btn.setText("...")

        self.model_fetch_thread = ModelFetchThread(self.settings_manager)
        self.model_fetch_thread.models_fetched.connect(self.on_models_fetched)
        self.model_fetch_thread.start()

    def on_models_fetched(self, models: list[str]):
        """Handle fetched models"""
        current_text = self.model_name_combo.currentText()

        self.model_name_combo.clear()
        if models:
            self.model_name_combo.addItems(models)
            # Restore previous selection if it exists
            index = self.model_name_combo.findText(current_text)
            if index >= 0:
                self.model_name_combo.setCurrentIndex(index)
            else:
                self.model_name_combo.setCurrentText(current_text)
        else:
            self.model_name_combo.setCurrentText(current_text)

        self.refresh_models_btn.setEnabled(True)
        self.refresh_models_btn.setText("🔄")

        # Clean up thread
        if self.model_fetch_thread:
            self.model_fetch_thread.deleteLater()
            self.model_fetch_thread = None

    def browse_plugins_path(self):
        """Browse for plugins directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Plugins Directory")
        if dir_path:
            self.plugins_path_edit.setText(dir_path)
            self.mark_changes()

    def import_settings(self):
        """Import settings from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON files (*.json);;All files (*)"
        )
        if file_path:
            success = self.settings_manager.import_settings(file_path)
            if success:
                self.load_current_settings()
                QMessageBox.information(self, "Success", "Settings imported successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to import settings.")

    def export_settings(self):
        """Export settings to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "whisperengine_settings.json", "JSON files (*.json)"
        )
        if file_path:
            success = self.settings_manager.export_settings(file_path)
            if success:
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to export settings.")

    def reset_to_defaults(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_current_settings()
            self.has_changes = False
            self.apply_btn.setEnabled(False)

    def apply_changes(self):
        """Apply current settings"""
        try:
            # Collect all settings
            llm_settings = {
                "api_url": self.api_url_edit.text(),
                "model_name": self.model_name_combo.currentText(),
                "api_key": self.api_key_edit.text(),
                "max_tokens": self.max_tokens_spin.value(),
                "temperature": self.temperature_spin.value(),
                "timeout_seconds": self.timeout_spin.value(),
            }

            ui_settings = {
                "theme": self.theme_combo.currentText(),
                "font_family": self.font_family_combo.currentText(),
                "font_size": self.font_size_spin.value(),
                "window_opacity": self.opacity_slider.value() / 100.0,
                "auto_scroll": self.auto_scroll_check.isChecked(),
                "show_timestamps": self.show_timestamps_check.isChecked(),
                "markdown_rendering": self.markdown_rendering_check.isChecked(),
                "auto_save_conversations": self.auto_save_check.isChecked(),
            }

            platform_settings = {
                "system_tray_enabled": self.system_tray_check.isChecked(),
                "start_minimized": self.start_minimized_check.isChecked(),
                "minimize_to_tray": self.minimize_to_tray_check.isChecked(),
                "auto_start": self.auto_start_check.isChecked(),
                "notifications_enabled": self.notifications_check.isChecked(),
                "platform_integration": self.platform_integration_check.isChecked(),
            }

            # Apply all settings
            self.settings_manager.update_llm_config(**llm_settings)
            self.settings_manager.update_ui_config(**ui_settings)
            self.settings_manager.update_platform_config(**platform_settings)

            self.has_changes = False
            self.apply_btn.setEnabled(False)

            QMessageBox.information(self, "Success", "Settings applied successfully!")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply settings: {str(e)}")

    def accept_changes(self):
        """Apply changes and close dialog"""
        if self.has_changes:
            self.apply_changes()
        self.accept()

    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Save:
                self.apply_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def apply_platform_styling(self):
        """Apply platform-specific styling with theme awareness"""
        # Get current theme from settings
        ui_config = self.settings_manager.get_ui_config()
        theme = ui_config.theme

        # Determine if we should use dark theme
        is_dark_theme = theme == "dark" or (theme == "auto" and self.is_system_dark_theme())

        # Base colors based on theme
        if is_dark_theme:
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            border_color = "#555555"
            tab_bg = "#333333"
            group_bg = "#383838"
            input_bg = "#404040"
            input_border = "#666666"
        else:
            bg_color = "#f0f0f0"
            text_color = "#000000"
            border_color = "#cccccc"
            tab_bg = "#ffffff"
            group_bg = "#f8f8f8"
            input_bg = "#ffffff"
            input_border = "#cccccc"

        # Platform-specific styling with theme support
        platform_name = platform.system()

        base_style = f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QTabWidget::pane {{
                border: 1px solid {border_color};
                background-color: {tab_bg};
                color: {text_color};
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background-color: {group_bg};
                color: {text_color};
                border: 1px solid {border_color};
                padding: 8px 12px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_bg};
                border-bottom: 1px solid {tab_bg};
            }}
            QTabBar::tab:hover {{
                background-color: {input_bg};
            }}
            QGroupBox {{
                font-weight: bold;
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                margin-top: 1ex;
                background-color: {group_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid #0078d4;
            }}
            QCheckBox, QRadioButton {{
                color: {text_color};
            }}
            QPushButton {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
            }}
            QPushButton:pressed {{
                background-color: {input_border};
            }}
            QListWidget {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 4px;
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 4px;
                text-align: center;
                color: {text_color};
            }}
            QProgressBar::chunk {{
                background-color: #0078d4;
                border-radius: 3px;
            }}
        """

        if platform_name == "Darwin":  # macOS
            # macOS-specific enhancements
            self.setStyleSheet(
                base_style
                + """
                QGroupBox {
                    border-radius: 10px;
                }
                QPushButton {
                    border-radius: 6px;
                }
            """
            )
        elif platform_name == "Windows":  # Windows
            # Windows-specific enhancements
            self.setStyleSheet(
                base_style
                + """
                QTabBar::tab {
                    border-radius: 0px;
                }
                QPushButton {
                    border-radius: 2px;
                }
            """
            )
        else:  # Linux
            self.setStyleSheet(base_style)

    def is_system_dark_theme(self) -> bool:
        """Detect if system is using dark theme"""
        try:
            app = QApplication.instance()
            if app and hasattr(app, "palette"):
                palette = app.palette()
                # Check if window color is darker than text color
                window_color = palette.color(QPalette.ColorRole.Window)
                text_color = palette.color(QPalette.ColorRole.WindowText)
                return window_color.lightness() < text_color.lightness()
        except Exception:
            pass
        return False
