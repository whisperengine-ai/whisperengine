#!/usr/bin/env python3
"""
WhisperEngine Onboarding Dialog
First-time setup and user configuration for the desktop application.
"""

import logging
import platform
import requests
import json
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import uuid
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QCheckBox,
        QComboBox,
        QTextEdit,
        QGroupBox,
        QFormLayout,
        QProgressBar,
        QMessageBox,
        QWizard,
        QWizardPage,
        QRadioButton,
        QButtonGroup,
        QSpacerItem,
        QSizePolicy,
        QFrame,
        QScrollArea,
        QListWidget,
        QListWidgetItem,
    )
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
    from PySide6.QtGui import QFont, QPixmap, QIcon, QMovie

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

if PYSIDE6_AVAILABLE:
    from .native_settings_manager import NativeSettingsManager


class LLMDetectionThread(QThread):
    """Background thread for detecting local LLM servers"""

    servers_detected = Signal(list)
    detection_progress = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Detect available LLM servers"""
        detected_servers = []

        # Common local LLM server configurations
        servers_to_check = [
            {
                "name": "LM Studio",
                "url": "http://localhost:1234",
                "health_endpoint": "/v1/models",
                "description": "LM Studio - Local LLM Server",
                "models": [],
                "status": "checking",
            },
            {
                "name": "Ollama",
                "url": "http://localhost:11434",
                "health_endpoint": "/api/tags",
                "description": "Ollama - Local LLM Server",
                "models": [],
                "status": "checking",
            },
            {
                "name": "Text Generation WebUI",
                "url": "http://localhost:5000",
                "health_endpoint": "/api/v1/models",
                "description": "Text Generation WebUI (oobabooga)",
                "models": [],
                "status": "checking",
            },
            {
                "name": "LocalAI",
                "url": "http://localhost:8080",
                "health_endpoint": "/v1/models",
                "description": "LocalAI Server",
                "models": [],
                "status": "checking",
            },
        ]

        for server in servers_to_check:
            self.detection_progress.emit(f"Checking {server['name']}...")
            try:
                # Check if server is responding
                response = requests.get(f"{server['url']}{server['health_endpoint']}", timeout=3)

                if response.status_code == 200:
                    # Try to get available models
                    models = []
                    try:
                        if server["name"] == "Ollama":
                            # Ollama uses different format
                            data = response.json()
                            models = [model["name"] for model in data.get("models", [])]
                        else:
                            # OpenAI-compatible format
                            data = response.json()
                            models = [model["id"] for model in data.get("data", [])]
                    except:
                        models = ["Unknown Model"]

                    # Update server info
                    server["models"] = models
                    server["status"] = "available"
                    detected_servers.append(server)
                    self.logger.info(f"✅ Detected {server['name']} with {len(models)} models")

            except Exception as e:
                self.logger.debug(f"Server {server['name']} not available: {e}")

        self.detection_progress.emit("Detection complete")
        self.servers_detected.emit(detected_servers)


class WelcomePage(QWizardPage):
    """Welcome page of the onboarding wizard"""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to WhisperEngine")
        self.setSubTitle("Let's set up your AI chat experience")

        layout = QVBoxLayout()

        # Welcome message
        welcome_text = QLabel(
            """
        <h2>🤖 Welcome to WhisperEngine!</h2>
        
        <p>WhisperEngine is your personal AI chat companion with advanced features:</p>
        
        <ul>
            <li><strong>🧠 Advanced Memory</strong> - Remembers your conversations and preferences</li>
            <li><strong>😊 Emotional Intelligence</strong> - Understands and responds to emotions</li>
            <li><strong>🔒 Privacy First</strong> - All data stored locally on your device</li>
            <li><strong>🎯 Personality Adaptation</strong> - Learns and adapts to your style</li>
            <li><strong>⚡ Local AI Models</strong> - Works with your local LLM servers</li>
        </ul>
        
        <p>This wizard will help you configure everything in just a few steps.</p>
        """
        )
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)

        self.setLayout(layout)


class UserSetupPage(QWizardPage):
    """User identity setup page"""

    def __init__(self):
        super().__init__()
        self.setTitle("User Profile Setup")
        self.setSubTitle("Tell us a bit about yourself")

        layout = QFormLayout()

        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your preferred username")
        self.username_edit.textChanged.connect(self.validate_page)
        layout.addRow("Username:", self.username_edit)

        # Display name
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("How should the AI address you?")
        layout.addRow("Display Name:", self.display_name_edit)

        # User preferences
        preferences_group = QGroupBox("Chat Preferences")
        prefs_layout = QVBoxLayout()

        self.casual_mode = QCheckBox("Casual conversation style")
        self.casual_mode.setChecked(True)
        prefs_layout.addWidget(self.casual_mode)

        self.memory_enabled = QCheckBox("Enable conversation memory")
        self.memory_enabled.setChecked(True)
        prefs_layout.addWidget(self.memory_enabled)

        self.emotions_enabled = QCheckBox("Enable emotional intelligence")
        self.emotions_enabled.setChecked(True)
        prefs_layout.addWidget(self.emotions_enabled)

        preferences_group.setLayout(prefs_layout)
        layout.addRow(preferences_group)

        self.setLayout(layout)

        # Generate default username
        import getpass

        default_user = getpass.getuser()
        self.username_edit.setText(default_user)
        self.display_name_edit.setText(default_user.title())

    def validate_page(self):
        """Validate the page input"""
        username = self.username_edit.text().strip()
        is_valid = len(username) >= 2 and username.isalnum()
        self.completeChanged.emit()
        return is_valid

    def isComplete(self):
        return len(self.username_edit.text().strip()) >= 2


class LLMSetupPage(QWizardPage):
    """LLM server detection and setup page"""

    def __init__(self):
        super().__init__()
        self.setTitle("AI Model Configuration")
        self.setSubTitle("Let's find and configure your AI models")

        self.detected_servers = []
        self.selected_server = None

        layout = QVBoxLayout()

        # Detection section
        detection_group = QGroupBox("Local AI Server Detection")
        detection_layout = QVBoxLayout()

        self.detection_label = QLabel("Click 'Scan for Servers' to detect local AI servers")
        detection_layout.addWidget(self.detection_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        detection_layout.addWidget(self.progress_bar)

        self.scan_button = QPushButton("🔍 Scan for Servers")
        self.scan_button.clicked.connect(self.start_detection)
        detection_layout.addWidget(self.scan_button)

        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)

        # Results section
        self.results_group = QGroupBox("Available AI Servers")
        results_layout = QVBoxLayout()

        self.servers_list = QListWidget()
        self.servers_list.itemClicked.connect(self.on_server_selected)
        results_layout.addWidget(self.servers_list)

        self.results_group.setLayout(results_layout)
        self.results_group.setVisible(False)
        layout.addWidget(self.results_group)

        # Manual configuration option
        manual_group = QGroupBox("Manual Configuration")
        manual_layout = QFormLayout()

        self.manual_url = QLineEdit()
        self.manual_url.setPlaceholderText("http://localhost:1234")
        manual_layout.addRow("Server URL:", self.manual_url)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_manual_connection)
        manual_layout.addRow(self.test_connection_button)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        self.setLayout(layout)

        # Initialize detection thread
        self.detection_thread = LLMDetectionThread()
        self.detection_thread.servers_detected.connect(self.on_servers_detected)
        self.detection_thread.detection_progress.connect(self.on_detection_progress)

    def start_detection(self):
        """Start server detection"""
        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.detection_thread.start()

    def on_detection_progress(self, message: str):
        """Update detection progress"""
        self.detection_label.setText(message)

    def on_servers_detected(self, servers: List[Dict]):
        """Handle detected servers"""
        self.detected_servers = servers
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)

        if servers:
            self.detection_label.setText(f"Found {len(servers)} available servers")
            self.results_group.setVisible(True)

            # Populate servers list
            self.servers_list.clear()
            for server in servers:
                item_text = f"{server['name']} - {server['url']}"
                if server.get("models"):
                    item_text += f" ({len(server['models'])} models)"

                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, server)
                self.servers_list.addItem(item)

            # Auto-select first server
            if self.servers_list.count() > 0:
                self.servers_list.setCurrentRow(0)
                self.on_server_selected(self.servers_list.item(0))
        else:
            self.detection_label.setText(
                "No local AI servers detected. You can configure one manually below."
            )

    def on_server_selected(self, item):
        """Handle server selection"""
        if item:
            self.selected_server = item.data(Qt.ItemDataRole.UserRole)
            self.completeChanged.emit()

    def test_manual_connection(self):
        """Test manual server connection"""
        url = self.manual_url.text().strip()
        if not url:
            return

        try:
            response = requests.get(f"{url}/v1/models", timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "Connection successful!")
                # Create manual server entry
                self.selected_server = {
                    "name": "Manual Configuration",
                    "url": url,
                    "description": "Manually configured server",
                    "models": ["Available"],
                    "status": "available",
                }
                self.completeChanged.emit()
            else:
                QMessageBox.warning(
                    self, "Error", f"Server responded with status {response.status_code}"
                )
        except Exception as e:
            QMessageBox.warning(self, "Connection Failed", f"Could not connect to server: {str(e)}")

    def isComplete(self):
        return self.selected_server is not None


class OnboardingWizard(QWizard):
    """Complete onboarding wizard for WhisperEngine"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Wizard configuration
        self.setWindowTitle("WhisperEngine Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)

        # Add pages
        self.welcome_page = WelcomePage()
        self.user_page = UserSetupPage()
        self.llm_page = LLMSetupPage()

        self.addPage(self.welcome_page)
        self.addPage(self.user_page)
        self.addPage(self.llm_page)

        # Set page IDs
        self.WELCOME_PAGE = 0
        self.USER_PAGE = 1
        self.LLM_PAGE = 2

        # Connect signals
        self.finished.connect(self.on_wizard_finished)

    def on_wizard_finished(self, result):
        """Handle wizard completion"""
        if result == QDialog.DialogCode.Accepted:
            self.logger.info("Onboarding completed successfully")
        else:
            self.logger.info("Onboarding cancelled")

    def get_user_config(self) -> Dict[str, Any]:
        """Get the user configuration from the wizard"""
        return {
            "username": self.user_page.username_edit.text().strip(),
            "display_name": self.user_page.display_name_edit.text().strip(),
            "user_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "casual_mode": self.user_page.casual_mode.isChecked(),
                "memory_enabled": self.user_page.memory_enabled.isChecked(),
                "emotions_enabled": self.user_page.emotions_enabled.isChecked(),
            },
        }

    def get_llm_config(self) -> Optional[Dict[str, Any]]:
        """Get the LLM configuration from the wizard"""
        if self.llm_page.selected_server:
            server = self.llm_page.selected_server
            return {
                "api_url": server["url"],
                "server_name": server["name"],
                "description": server.get("description", ""),
                "models": server.get("models", []),
                "default_model": server.get("models", [""])[0] if server.get("models") else "",
            }
        return None


def show_onboarding_if_needed(parent=None) -> Tuple[bool, Optional[Dict], Optional[Dict]]:
    """
    Show onboarding wizard if this is the first run
    Returns: (completed, user_config, llm_config)
    """
    # Check if onboarding was already completed
    settings_manager = NativeSettingsManager()

    # Check for existing user configuration
    user_config_path = Path.home() / ".whisperengine" / "user_config.json"
    if user_config_path.exists():
        # Already configured
        return True, None, None

    # Show onboarding wizard
    wizard = OnboardingWizard(parent)
    result = wizard.exec()

    if result == QDialog.DialogCode.Accepted:
        user_config = wizard.get_user_config()
        llm_config = wizard.get_llm_config()

        # Save user configuration
        user_config_path.parent.mkdir(exist_ok=True)
        with open(user_config_path, "w") as f:
            json.dump(user_config, f, indent=2)

        # Update settings manager with LLM config
        if llm_config:
            llm_settings = settings_manager.get_llm_config()
            llm_settings.api_url = llm_config["api_url"]
            llm_settings.model_name = llm_config.get("default_model", "auto")
            settings_manager.save_settings()

        return True, user_config, llm_config

    return False, None, None


def get_current_user_config() -> Optional[Dict[str, Any]]:
    """Get the current user configuration"""
    user_config_path = Path.home() / ".whisperengine" / "user_config.json"
    if user_config_path.exists():
        try:
            with open(user_config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load user config: {e}")
    return None
