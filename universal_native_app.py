#!/usr/bin/env python3
"""
WhisperEngine Universal Native Chat Application
Cross-platform native desktop app using PySide6/Qt with platform-specific optimizations
"""

import sys
import os
import platform
import asyncio
import logging
import psutil
import threading
import time
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Set environment mode for desktop at startup
os.environ["ENV_MODE"] = "desktop"

# Load desktop environment configuration early
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from env_manager import load_environment

    load_environment()
    print("✅ Desktop environment configuration loaded")
except Exception as e:
    print(f"⚠️ Warning: Could not load environment configuration: {e}")

# Qt/PySide6 imports
try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTextEdit,
        QLineEdit,
        QPushButton,
        QLabel,
        QScrollArea,
        QFrame,
        QSizePolicy,
        QSystemTrayIcon,
        QMenu,
        QMessageBox,
        QDialog,
        QTabWidget,
    )
    from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings, QSize
    from PySide6.QtGui import (
        QFont,
        QTextCursor,
        QIcon,
        QPixmap,
        QPalette,
        QColor,
        QFontDatabase,
        QAction,
        QTextOption,
    )

    PYSIDE6_AVAILABLE = True
except ImportError:
    print("❌ PySide6 not available. Install with: pip install PySide6")
    PYSIDE6_AVAILABLE = False
    sys.exit(1)

# WhisperEngine imports
try:
    from src.core.native_ai_service import NativeAIService, AIMessage
    from src.ui.native_settings_manager import NativeSettingsManager
    from src.ui.native_settings_dialog import NativeSettingsDialog
    from src.ui.onboarding_wizard import show_onboarding_if_needed, get_current_user_config
    from src.ui.system_logs_widget import SystemLogsWidget
except ImportError as e:
    print(f"❌ Failed to import NativeAIService: {e}")
    print("Make sure you're running from the project root and all dependencies are installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PlatformAdapter:
    """Platform-specific styling and behavior adapter"""

    def __init__(self):
        self.platform = platform.system().lower()
        self.is_macos = self.platform == "darwin"
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"

    def get_platform_style(self) -> str:
        """Get platform-specific stylesheet"""

        # Platform-specific font families that Qt can properly resolve
        if self.is_macos:
            font_family = "'Helvetica Neue', Helvetica, Arial"
        elif self.is_windows:
            font_family = "'Segoe UI', 'Segoe UI Variable', 'Segoe UI Symbol'"
        else:  # Linux and others
            font_family = "'Ubuntu', 'Liberation Sans', 'DejaVu Sans'"

        base_style = (
            """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 12px;
                font-family: """
            + font_family
            + """;
                font-size: 14px;
                line-height: 1.4;
            }
            
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 12px;
                font-family: """
            + font_family
            + """;
                font-size: 14px;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            
            QLabel {
                color: #ffffff;
                font-family: """
            + font_family
            + """;
            }
            
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
        """
        )

        if self.is_macos:
            # macOS-specific styling
            return (
                base_style
                + """
                QMainWindow {
                    background-color: #1c1c1e;
                }
                QPushButton {
                    font-family: """
                + font_family
                + """;
                }
                QTextEdit, QLineEdit {
                    font-family: """
                + font_family
                + """;
                }
            """
            )
        elif self.is_windows:
            # Windows 11-specific styling
            return (
                base_style
                + """
                QMainWindow {
                    background-color: #202020;
                }
                QPushButton {
                    font-family: """
                + font_family
                + """;
                    border-radius: 4px;
                }
                QTextEdit, QLineEdit {
                    font-family: """
                + font_family
                + """;
                    border-radius: 4px;
                }
            """
            )
        else:
            # Linux styling
            return (
                base_style
                + """
                QPushButton {
                    font-family: """
                + font_family
                + """;
                }
                QTextEdit, QLineEdit {
                    font-family: """
                + font_family
                + """;
                }
            """
            )

    def get_window_title(self) -> str:
        """Get platform-appropriate window title"""
        if self.is_macos:
            return "WhisperEngine"
        elif self.is_windows:
            return "WhisperEngine"
        else:
            return "WhisperEngine"

    def get_default_size(self) -> tuple:
        """Get platform-appropriate default window size"""
        if self.is_macos:
            return (900, 700)
        elif self.is_windows:
            return (1000, 750)
        else:
            return (950, 720)


class AIWorkerThread(QThread):
    """Worker thread for AI communication"""

    response_received = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, ai_service: NativeAIService, message: str):
        super().__init__()
        self.ai_service = ai_service
        self.message = message

    def run(self):
        """Execute AI request in background thread"""
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    self.ai_service.process_message_async(self.message)
                )
                self.response_received.emit(response.content)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"AI Worker error: {e}")
            self.error_occurred.emit(f"AI Error: {str(e)}")


class WhisperEngineUniversalApp(QMainWindow):
    """Universal cross-platform WhisperEngine chat application"""

    def __init__(self):
        super().__init__()

        # Platform adapter
        self.platform_adapter = PlatformAdapter()

        # User management
        self.current_user_config: Optional[Dict[str, Any]] = None
        self.user_id: Optional[str] = None

        # AI service and settings
        self.ai_service: Optional[NativeAIService] = None
        self.ai_worker: Optional[AIWorkerThread] = None
        self.settings_manager: Optional[NativeSettingsManager] = None

        # Settings
        self.settings = QSettings("WhisperEngine", "UniversalChat")

        # Check for first-time setup
        self.handle_onboarding()

        # Initialize UI
        self.init_ui()

        # Initialize settings manager
        self.init_settings()

        # Initialize AI service
        self.init_ai_service()

        # Setup system tray if supported
        self.setup_system_tray()

        # Restore window state
        self.restore_window_state()

        logger.info(f"🚀 WhisperEngine Universal App started on {platform.system()}")

    def get_display_name(self) -> str:
        """Get the display name for the current user"""
        if self.current_user_config:
            display_name = self.current_user_config.get("display_name")
            username = self.current_user_config.get("username")
            return display_name or username or "User"
        return "User"

    def get_username(self) -> str:
        """Get the username for the current user"""
        if self.current_user_config:
            return self.current_user_config.get("username", "user")
        return "user"

    def handle_onboarding(self):
        """Handle first-time user onboarding"""
        try:
            # Check if onboarding is needed
            completed, user_config, llm_config = show_onboarding_if_needed(self)

            if completed and user_config:
                self.current_user_config = user_config
                self.user_id = user_config.get("user_id")
                logger.info(f"✅ User onboarding completed for {user_config.get('username')}")

                if llm_config:
                    logger.info(
                        f"✅ LLM configured: {llm_config.get('server_name')} at {llm_config.get('api_url')}"
                    )
            else:
                # Load existing user config
                self.current_user_config = get_current_user_config()
                if self.current_user_config:
                    self.user_id = self.current_user_config.get("user_id")
                    logger.info(
                        f"✅ Loaded existing user: {self.current_user_config.get('username')}"
                    )
                else:
                    # Create a default user if no config exists
                    import uuid
                    import getpass

                    default_username = getpass.getuser()
                    self.current_user_config = {
                        "username": default_username,
                        "display_name": default_username.title(),
                        "user_id": str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat(),
                        "preferences": {
                            "casual_mode": True,
                            "memory_enabled": True,
                            "emotions_enabled": True,
                        },
                    }
                    if self.current_user_config:
                        self.user_id = self.current_user_config["user_id"]
                        logger.info(f"✅ Created default user: {default_username}")

        except Exception as e:
            logger.error(f"❌ Onboarding error: {e}")
            # Continue with default settings
            import uuid

            self.user_id = str(uuid.uuid4())
            self.current_user_config = {"username": "user", "user_id": self.user_id}

    def load_logo(self, size: int = 64) -> Optional[QPixmap]:
        """Load the WhisperEngine logo at specified size"""
        try:
            # Look for logo in img directory
            logo_path = project_root / "img" / "whisper-engine.jpeg"
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    # Scale logo to specified size (default 64x64 for header - 2x bigger than before)
                    scaled_pixmap = pixmap.scaled(
                        size,
                        size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    return scaled_pixmap
                else:
                    logger.warning(f"Failed to load logo pixmap from {logo_path}")
            else:
                logger.warning(f"Logo file not found at {logo_path}")
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
        return None

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_chat_action = QAction("New Chat", self)
        new_chat_action.setShortcut("Ctrl+N")
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)

        file_menu.addSeparator()

        setup_action = QAction("Setup Wizard...", self)
        setup_action.triggered.connect(self.show_onboarding_wizard)
        file_menu.addAction(setup_action)

        import_action = QAction("Import Settings...", self)
        import_action.triggered.connect(self.import_settings)
        file_menu.addAction(import_action)

        export_action = QAction("Export Settings...", self)
        export_action.triggered.connect(self.export_settings)
        file_menu.addAction(export_action)

        if not self.platform_adapter.is_macos:  # macOS handles quit differently
            file_menu.addSeparator()
            quit_action = QAction("Quit", self)
            quit_action.setShortcut("Ctrl+Q")
            quit_action.triggered.connect(self.quit_application)
            file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        clear_action = QAction("Clear Chat", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_chat)
        edit_menu.addAction(clear_action)

        edit_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings_dialog)
        edit_menu.addAction(settings_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.toggle_tray_action = QAction("Show in System Tray", self)
        self.toggle_tray_action.setCheckable(True)
        self.toggle_tray_action.setChecked(True)
        view_menu.addAction(self.toggle_tray_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About WhisperEngine", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # Platform-specific menu customizations
        if self.platform_adapter.is_macos:
            # macOS-specific menu setup
            self.setup_macos_menu(menubar)

    def setup_macos_menu(self, menubar):
        """Setup macOS-specific menu items"""
        # macOS automatically creates the app menu, we just need to customize it
        try:
            # Get the app menu (first menu on macOS)
            app_menu = menubar.addMenu("WhisperEngine")

            about_action = QAction("About WhisperEngine", self)
            about_action.triggered.connect(self.show_about_dialog)
            app_menu.addAction(about_action)

            app_menu.addSeparator()

            preferences_action = QAction("Preferences...", self)
            preferences_action.setShortcut("Cmd+,")
            preferences_action.triggered.connect(self.show_settings_dialog)
            app_menu.addAction(preferences_action)

        except Exception as e:
            logger.warning(f"Failed to setup macOS menu: {e}")

    def new_chat(self):
        """Start a new chat conversation"""
        self.chat_display.clear()
        welcome_msg = f"""
        <div style='color: #888; font-size: 14px; margin: 20px 0;'>
            <strong>New conversation started!</strong><br>
            Platform: {platform.system()} {platform.release()}<br>
            <br>
            Type a message below to start chatting with the AI...
        </div>
        """
        self.chat_display.setHtml(welcome_msg)
        self.message_input.setFocus()

    def clear_chat(self):
        """Clear the current chat"""
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            "Are you sure you want to clear the current conversation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.new_chat()

    def import_settings(self):
        """Import settings from file"""
        if self.settings_manager:
            dialog = NativeSettingsDialog(self.settings_manager, self)
            dialog.import_settings()

    def export_settings(self):
        """Export settings to file"""
        if self.settings_manager:
            dialog = NativeSettingsDialog(self.settings_manager, self)
            dialog.export_settings()

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = f"""
        <h3>WhisperEngine</h3>
        <p><strong>Version:</strong> 1.0.0</p>
        <p><strong>Platform:</strong> {platform.system()} {platform.release()}</p>
        <p><strong>Python:</strong> {platform.python_version()}</p>
        <p><strong>Framework:</strong> PySide6/Qt</p>
        <br>
        <p>A privacy-first AI conversation platform with advanced memory and emotional intelligence.</p>
        <br>
        <p><strong>Features:</strong></p>
        <ul>
        <li>🧠 Advanced conversation memory</li>
        <li>💭 Emotional intelligence</li>
        <li>🔒 Privacy-focused design</li>
        <li>🖥️ Native cross-platform UI</li>
        <li>⚙️ Comprehensive settings</li>
        </ul>
        """

        QMessageBox.about(self, "About WhisperEngine", about_text)

    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle(self.platform_adapter.get_window_title())
        default_width, default_height = self.platform_adapter.get_default_size()
        self.resize(default_width, default_height)

        # Set window icon
        logo_icon = self.load_logo(32)  # Load at 32x32 for window icon
        if logo_icon:
            self.setWindowIcon(QIcon(logo_icon))

        # Apply platform-specific styling
        self.setStyleSheet(self.platform_adapter.get_platform_style())

        # Create menu bar
        self.create_menu_bar()

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        logo_pixmap = self.load_logo()  # Default 64x64 - 2x bigger than before
        if logo_pixmap:
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            logo_label.setStyleSheet("margin-right: 12px; margin-left: 4px;")  # Add some spacing
        else:
            # Fallback to emoji if logo doesn't load
            logo_label.setText("🤖")
            logo_label.setStyleSheet(
                "font-size: 32px; margin-right: 12px; margin-left: 4px;"
            )  # Bigger emoji too
        header_layout.addWidget(logo_label)

        title_label = QLabel(f"WhisperEngine ({self.get_display_name()})")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 8px;
                margin-left: 8px;
            }
        """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Create a vertical layout for upper right indicators
        upper_right_layout = QVBoxLayout()
        upper_right_layout.setSpacing(2)
        upper_right_layout.setContentsMargins(0, 0, 0, 0)

        # LLM endpoint and model indicator (upper right)
        self.llm_indicator = QLabel("� Loading LLM info...")
        self.llm_indicator.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        self.llm_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
        upper_right_layout.addWidget(self.llm_indicator)

        # Settings button (below LLM indicator)
        self.settings_button = QPushButton("Settings")
        self.settings_button.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """
        )
        self.settings_button.setMaximumHeight(24)  # Keep it small for the header
        upper_right_layout.addWidget(self.settings_button)

        # Create widget to hold the vertical layout
        upper_right_widget = QWidget()
        upper_right_widget.setLayout(upper_right_layout)
        header_layout.addWidget(upper_right_widget)

        # Try to update LLM indicator shortly after startup
        QTimer.singleShot(100, self.update_llm_indicator)

        layout.addLayout(header_layout)

        # Create tab widget to organize interface
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QTabBar::tab:selected:hover {
                background-color: #106ebe;
            }
        """
        )

        # Create chat tab
        chat_tab = self.create_chat_tab()
        self.tab_widget.addTab(chat_tab, "💬 Chat")

        # Create character prompt tab
        character_prompt_tab = self.create_character_prompt_tab()
        self.tab_widget.addTab(character_prompt_tab, "🎭 Character Prompt")

        # Create system logs tab
        self.logs_widget = SystemLogsWidget()
        self.tab_widget.addTab(self.logs_widget, "📋 System Logs")

        layout.addWidget(self.tab_widget)

        # Add system status bar at bottom
        self.create_status_bar()
        layout.addWidget(self.status_bar_widget)

        # Connect settings button
        self.settings_button.clicked.connect(self.show_settings_dialog)

        # Set focus to input
        self.message_input.setFocus()

    def create_chat_tab(self):
        """Create the chat interface tab"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setSpacing(16)
        chat_layout.setContentsMargins(16, 16, 16, 16)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_display.setWordWrapMode(QTextOption.WrapMode.WordWrap)  # Better word wrapping

        # Set minimum height
        self.chat_display.setMinimumHeight(400)

        # Configure text document for better rendering
        self.chat_display.document().setDefaultStyleSheet(
            """
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                line-height: 1.4; 
                word-wrap: break-word;
            }
            .user-message { 
                background-color: #0066cc; 
                color: white; 
                padding: 8px 12px; 
                border-radius: 15px; 
                margin: 5px 20% 5px 20%; 
                text-align: left;
                display: block;
            }
            .ai-message { 
                background-color: #2a2a2a; 
                color: white; 
                border: 1px solid #404040;
                padding: 8px 12px; 
                border-radius: 15px; 
                margin: 5px 20% 5px 0; 
                text-align: left;
                display: block;
            }
            .system-message { 
                background-color: rgba(255, 170, 0, 0.1); 
                color: #ffaa00; 
                border: 1px solid rgba(255, 170, 0, 0.3);
                padding: 6px 10px; 
                border-radius: 10px; 
                margin: 3px 30% 3px 30%; 
                text-align: center;
                display: block;
            }
            .typing-indicator { 
                background-color: #2a2a2a; 
                color: #888888; 
                border: 1px solid #404040;
                padding: 8px 12px; 
                border-radius: 15px; 
                margin: 5px 20% 5px 0; 
                text-align: left;
                display: block;
                font-style: italic;
            }
            .timestamp { 
                font-size: 10px; 
                opacity: 0.7; 
                margin-top: 2px; 
            }
        """
        )

        # Add welcome message
        welcome_msg = f"""
        <div style='color: #888; font-size: 14px; margin: 20px 0; padding: 15px; background-color: rgba(255,255,255,0.05); border-radius: 8px;'>
            <strong>Welcome to WhisperEngine!</strong><br>
            Platform: {platform.system()} {platform.release()}<br>
            Python: {sys.version.split()[0]}<br>
            Qt: PySide6 {getattr(sys.modules.get('PySide6', None), '__version__', 'Unknown')}<br>
            <br>
            Type a message below to start chatting with the AI...
        </div>
        """
        self.chat_display.setHtml(welcome_msg)

        chat_layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setMinimumWidth(100)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)

        return chat_widget

    def create_character_prompt_tab(self):
        """Create the character prompt editing tab"""
        prompt_widget = QWidget()
        prompt_layout = QVBoxLayout(prompt_widget)
        prompt_layout.setSpacing(16)
        prompt_layout.setContentsMargins(16, 16, 16, 16)

        # Header section
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("System Prompt Configuration")
        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 8px;
            }
        """
        )
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Action buttons
        self.load_prompt_button = QPushButton("📁 Load File")
        self.load_prompt_button.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """
        )
        self.load_prompt_button.clicked.connect(self.load_prompt_from_file)

        self.save_prompt_button = QPushButton("💾 Save")
        self.save_prompt_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """
        )
        self.save_prompt_button.clicked.connect(self.save_current_prompt)

        self.reset_prompt_button = QPushButton("🔄 Reset to Default")
        self.reset_prompt_button.setStyleSheet(
            """
            QPushButton {
                background-color: #d13438;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #b12a2e;
            }
        """
        )
        self.reset_prompt_button.clicked.connect(self.reset_to_default_prompt)

        header_layout.addWidget(self.load_prompt_button)
        header_layout.addWidget(self.save_prompt_button)
        header_layout.addWidget(self.reset_prompt_button)

        prompt_layout.addLayout(header_layout)

        # Info section
        info_label = QLabel(
            "Edit the system prompt that defines the AI's personality, behavior, and knowledge. Changes take effect immediately."
        )
        info_label.setStyleSheet(
            """
            QLabel {
                color: #888888;
                font-size: 12px;
                font-style: italic;
                margin-bottom: 8px;
            }
        """
        )
        prompt_layout.addWidget(info_label)

        # Character count and status
        status_layout = QHBoxLayout()
        self.char_count_label = QLabel("Characters: 0")
        self.char_count_label.setStyleSheet("color: #888888; font-size: 11px;")

        self.prompt_status_label = QLabel("Status: Not loaded")
        self.prompt_status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")

        status_layout.addWidget(self.char_count_label)
        status_layout.addStretch()
        status_layout.addWidget(self.prompt_status_label)

        prompt_layout.addLayout(status_layout)

        # Main text editor
        self.prompt_editor = QTextEdit()
        self.prompt_editor.setStyleSheet(
            """
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #0078d4;
            }
        """
        )
        self.prompt_editor.setPlaceholderText(
            "Enter your system prompt here...\n\nExample:\nYou are Dream of the Endless, the anthropomorphic personification of dreams and stories. You are ancient, wise, and speak with poetic eloquence..."
        )

        # Connect text change event to update character count
        self.prompt_editor.textChanged.connect(self.update_character_count)

        prompt_layout.addWidget(self.prompt_editor)

        # Load current system prompt
        self.load_current_system_prompt()

        return prompt_widget

    def create_status_bar(self):
        """Create system status bar with resource monitoring"""
        self.status_bar_widget = QWidget()
        self.status_bar_widget.setFixedHeight(32)
        self.status_bar_widget.setStyleSheet(
            """
            QWidget {
                background-color: #2a2a2a;
                border-top: 1px solid #404040;
                border-radius: 0px;
            }
        """
        )

        status_layout = QHBoxLayout(self.status_bar_widget)
        status_layout.setContentsMargins(12, 4, 12, 4)
        status_layout.setSpacing(8)  # Reduced spacing

        # System status icon and message
        self.system_status_icon = QLabel("🟢")
        self.system_status_icon.setFixedSize(12, 12)  # Smaller icons
        self.system_status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.system_status_icon)

        self.system_status_text = QLabel("System Ready")
        self.system_status_text.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
        self.system_status_text.setMinimumWidth(80)  # Fixed width to prevent overlap
        status_layout.addWidget(self.system_status_text)

        # Add separator
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #666666; font-size: 10px; margin: 0 4px;")
        status_layout.addWidget(separator1)

        # CPU usage
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        self.cpu_label.setMinimumWidth(50)  # Fixed width
        status_layout.addWidget(self.cpu_label)

        # Memory usage
        self.memory_label = QLabel("RAM: 0%")
        self.memory_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        self.memory_label.setMinimumWidth(55)  # Fixed width
        status_layout.addWidget(self.memory_label)

        # GPU usage (if available)
        self.gpu_label = QLabel("GPU: N/A")
        self.gpu_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.gpu_label.setMinimumWidth(60)  # Fixed width
        status_layout.addWidget(self.gpu_label)

        # Add separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #666666; font-size: 10px; margin: 0 4px;")
        status_layout.addWidget(separator2)

        # AI service status
        self.ai_status_icon = QLabel("🔄")
        self.ai_status_icon.setFixedSize(12, 12)  # Smaller icons
        self.ai_status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.ai_status_icon)

        self.ai_status_text = QLabel("Initializing AI service...")
        self.ai_status_text.setStyleSheet("color: #ffaa00; font-size: 10px;")
        self.ai_status_text.setMinimumWidth(120)  # Fixed width
        status_layout.addWidget(self.ai_status_text)

        # Spacer to push connection status to the right
        status_layout.addStretch()

        # Start resource monitoring
        self.init_resource_monitoring()

    def init_resource_monitoring(self):
        """Initialize system resource monitoring"""
        # Create timer for updating resource stats
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self.update_resource_stats)
        self.resource_timer.start(2000)  # Update every 2 seconds

        # Initialize resource monitoring in background thread
        self.resource_thread = threading.Thread(target=self.resource_monitoring_loop, daemon=True)
        self.resource_thread.start()

        # Store latest resource data
        self.latest_cpu = 0.0
        self.latest_memory = 0.0
        self.latest_gpu = "N/A"

    def resource_monitoring_loop(self):
        """Background thread for resource monitoring"""
        while True:
            try:
                # Get CPU usage
                self.latest_cpu = psutil.cpu_percent(interval=1)

                # Get memory usage
                memory = psutil.virtual_memory()
                self.latest_memory = memory.percent

                # Platform-specific GPU and VRAM detection
                try:
                    current_os = platform.system()

                    if current_os == "Darwin":  # macOS
                        gpu_info = self._detect_macos_gpu()
                        self.latest_gpu = gpu_info

                    elif current_os == "Windows":  # Windows
                        gpu_info = self._detect_windows_gpu()
                        self.latest_gpu = gpu_info

                    elif current_os == "Linux":  # Linux
                        gpu_info = self._detect_linux_gpu()
                        self.latest_gpu = gpu_info

                    else:
                        self.latest_gpu = "OS: Unsupported"

                except Exception as e:
                    logger.debug(f"GPU detection error: {e}")
                    self.latest_gpu = "GPU: Error"

            except Exception as e:
                logger.debug(f"Resource monitoring error: {e}")
                time.sleep(2)

    def _detect_macos_gpu(self) -> str:
        """Detect GPU and VRAM on macOS"""
        try:
            # Method 1: Try to get detailed GPU info using system_profiler
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                output = result.stdout

                # Parse VRAM information
                vram_info = ""
                if "VRAM" in output:
                    lines = output.split("\n")
                    for i, line in enumerate(lines):
                        if "VRAM" in line:
                            # Extract VRAM size
                            vram_line = line.strip()
                            if ":" in vram_line:
                                vram_info = vram_line.split(":")[1].strip()
                                break

                # Determine GPU type and include VRAM if available
                if "Apple" in output or "AGXAccelerator" in output:
                    gpu_type = "Apple GPU"
                elif "AMD" in output:
                    gpu_type = "AMD GPU"
                elif "NVIDIA" in output:
                    gpu_type = "NVIDIA GPU"
                elif "Intel" in output:
                    gpu_type = "Intel GPU"
                else:
                    gpu_type = "GPU"

                # Add VRAM info if found
                if vram_info:
                    return f"{gpu_type} • {vram_info}"
                else:
                    return gpu_type

            # Method 2: Try ioreg for Apple Silicon
            result = subprocess.run(
                ["ioreg", "-r", "-n", "AGXAccelerator"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and "AGXAccelerator" in result.stdout:
                return "Apple GPU"

            # Method 3: Try to get GPU via Metal (if available)
            try:
                # Check if we can detect Metal-compatible GPU
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType", "-json"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0 and "Metal" in result.stdout:
                    return "Metal GPU"
            except:
                pass

            return "GPU: Unknown"

        except Exception as e:
            logger.debug(f"macOS GPU detection error: {e}")
            return "GPU: Unknown"

    def _detect_windows_gpu(self) -> str:
        """Detect GPU and VRAM on Windows"""
        try:
            # Method 1: Try WMI (Windows Management Instrumentation)
            try:
                import wmi

                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name and gpu.AdapterRAM:
                        # Convert bytes to GB
                        vram_gb = round(int(gpu.AdapterRAM) / (1024**3), 1)
                        gpu_name = (
                            str(gpu.Name)[:20] + "..." if len(str(gpu.Name)) > 20 else str(gpu.Name)
                        )

                        # Get usage if available
                        usage_info = ""
                        if hasattr(gpu, "LoadPercentage") and gpu.LoadPercentage:
                            usage_info = f" • {gpu.LoadPercentage}%"

                        return f"{gpu_name} • {vram_gb}GB{usage_info}"

            except ImportError:
                logger.debug("WMI not available on Windows")

            # Method 2: Try NVIDIA SMI
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total,utilization.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if lines:
                        parts = lines[0].split(", ")
                        if len(parts) >= 3:
                            name = parts[0].strip()[:15] + "..."
                            memory = f"{int(parts[1].strip())/1024:.1f}GB"
                            usage = f"{parts[2].strip()}%"
                            return f"{name} • {memory} • {usage}"
            except:
                pass

            # Method 3: Basic detection via dxdiag
            try:
                result = subprocess.run(
                    ["dxdiag", "/t", "temp_dxdiag.txt"], capture_output=True, text=True, timeout=5
                )
                # This would require parsing the output file, simplified for now
                return "DirectX GPU"
            except:
                pass

            return "Windows GPU"

        except Exception as e:
            logger.debug(f"Windows GPU detection error: {e}")
            return "GPU: Unknown"

    def _detect_linux_gpu(self) -> str:
        """Detect GPU and VRAM on Linux"""
        try:
            # Method 1: NVIDIA GPU via nvidia-smi
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if lines:
                        parts = lines[0].split(", ")
                        if len(parts) >= 4:
                            name = parts[0].strip()[:12] + "..."
                            total_mem = int(parts[1].strip())
                            used_mem = int(parts[2].strip())
                            usage = parts[3].strip()

                            vram_info = f"{used_mem/1024:.1f}/{total_mem/1024:.1f}GB"
                            return f"{name} • {vram_info} • {usage}%"
            except:
                pass

            # Method 2: AMD GPU via radeontop or rocm-smi
            try:
                result = subprocess.run(
                    ["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    return "AMD GPU • ROCm"
            except:
                pass

            # Method 3: Intel GPU
            try:
                result = subprocess.run(
                    ["intel_gpu_top", "-l"], capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    return "Intel GPU"
            except:
                pass

            # Method 4: Generic lspci detection
            try:
                result = subprocess.run(["lspci", "-v"], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    output = result.stdout.lower()
                    if "nvidia" in output:
                        return "NVIDIA GPU"
                    elif "amd" in output or "radeon" in output:
                        return "AMD GPU"
                    elif "intel" in output:
                        return "Intel GPU"
                    elif "vga" in output:
                        return "Generic GPU"
            except:
                pass

            return "Linux GPU"

        except Exception as e:
            logger.debug(f"Linux GPU detection error: {e}")
            return "GPU: Unknown"

    def update_resource_stats(self):
        """Update resource stats in UI (called by timer)"""
        try:
            # Update CPU label with color coding
            cpu_color = (
                "#00ff00"
                if self.latest_cpu < 50
                else "#ffaa00" if self.latest_cpu < 80 else "#ff0000"
            )
            self.cpu_label.setText(f"CPU: {self.latest_cpu:.1f}%")
            self.cpu_label.setStyleSheet(f"color: {cpu_color}; font-size: 10px;")

            # Update memory label with color coding
            mem_color = (
                "#00ff00"
                if self.latest_memory < 60
                else "#ffaa00" if self.latest_memory < 85 else "#ff0000"
            )
            self.memory_label.setText(f"RAM: {self.latest_memory:.1f}%")
            self.memory_label.setStyleSheet(f"color: {mem_color}; font-size: 10px;")

            # Update GPU label
            if self.latest_gpu != "N/A":
                try:
                    # Check if it's a percentage value (usage monitoring)
                    if "%" in self.latest_gpu:
                        gpu_val = float(self.latest_gpu.replace("%", ""))
                        gpu_color = (
                            "#00ff00" if gpu_val < 50 else "#ffaa00" if gpu_val < 80 else "#ff0000"
                        )
                        self.gpu_label.setStyleSheet(f"color: {gpu_color}; font-size: 10px;")
                        self.gpu_label.setText(f"GPU: {self.latest_gpu}")
                    else:
                        # GPU type/name (Apple Silicon, etc.)
                        if "Apple" in self.latest_gpu:
                            gpu_color = "#00ff00"  # Green for Apple GPU (good)
                        elif "Unknown" in self.latest_gpu:
                            gpu_color = "#888888"  # Gray for unknown
                        else:
                            gpu_color = "#00ff00"  # Green for detected GPU
                        self.gpu_label.setStyleSheet(f"color: {gpu_color}; font-size: 10px;")
                        self.gpu_label.setText(f"{self.latest_gpu}")
                except Exception as e:
                    # Fallback for any parsing issues
                    logger.debug(f"GPU label update error: {e}")
                    self.gpu_label.setStyleSheet("color: #888888; font-size: 10px;")
                    self.gpu_label.setText(f"{self.latest_gpu}")
            else:
                self.gpu_label.setStyleSheet("color: #888888; font-size: 10px;")
                self.gpu_label.setText("GPU: N/A")

        except Exception as e:
            logger.debug(f"UI update error: {e}")

    def update_ai_status(self, status: str, icon: str = "🤖", color: str = "#00ff00"):
        """Update AI service status in status bar"""
        logger.debug(f"🔧 update_ai_status called: {status} (icon: {icon}, color: {color})")
        if hasattr(self, "ai_status_icon") and hasattr(self, "ai_status_text"):
            self.ai_status_icon.setText(icon)
            self.ai_status_text.setText(status)
            self.ai_status_text.setStyleSheet(f"color: {color}; font-size: 10px;")
            logger.debug(f"✅ AI status updated in UI: {status}")
        else:
            logger.debug("❌ AI status widgets not found")

    def update_system_status(self, status: str, icon: str = "🟢", color: str = "#00ff00"):
        """Update general system status in status bar"""
        if hasattr(self, "system_status_icon") and hasattr(self, "system_status_text"):
            self.system_status_icon.setText(icon)
            self.system_status_text.setText(status)
            self.system_status_text.setStyleSheet(
                f"color: {color}; font-size: 10px; font-weight: bold;"
            )

    def update_llm_indicator(self):
        """Update LLM endpoint and model information in header"""
        try:
            # Try to load environment using env_manager if not already loaded
            from env_manager import load_environment

            load_environment()

            import os

            # Get LLM configuration from environment variables
            api_url = os.getenv("LLM_CHAT_API_URL", "")
            model_name = os.getenv("LLM_CHAT_MODEL", "")

            logger.debug(f"LLM Indicator - API URL: {api_url}, Model: {model_name}")

            if api_url and model_name:
                # Extract endpoint name from URL
                endpoint_name = "Unknown"
                if "openrouter" in api_url.lower():
                    endpoint_name = "OpenRouter"
                elif "openai" in api_url.lower():
                    endpoint_name = "OpenAI"
                elif "localhost" in api_url.lower() or "127.0.0.1" in api_url.lower():
                    endpoint_name = "Local"
                elif "huggingface" in api_url.lower():
                    endpoint_name = "HuggingFace"
                elif "anthropic" in api_url.lower():
                    endpoint_name = "Anthropic"

                # Clean up model name (remove provider prefix for display)
                display_model = model_name
                if "/" in model_name:
                    display_model = model_name.split("/")[-1]

                # Shorten very long model names
                if len(display_model) > 20:
                    display_model = display_model[:17] + "..."

                self.llm_indicator.setText(f"🔗 {endpoint_name} • {display_model}")
                self.llm_indicator.setStyleSheet(
                    "color: #00aa00; font-size: 11px; font-style: normal;"
                )
                logger.debug(f"LLM Indicator updated: {endpoint_name} • {display_model}")
            else:
                self.llm_indicator.setText("🔗 LLM Not Configured")
                self.llm_indicator.setStyleSheet(
                    "color: #aa0000; font-size: 11px; font-style: italic;"
                )
                logger.debug(
                    f"LLM Indicator: Not configured (API URL: '{api_url}', Model: '{model_name}')"
                )

        except Exception as e:
            logger.debug(f"Error updating LLM indicator: {e}")
            self.llm_indicator.setText("🔗 LLM Status Unknown")
            self.llm_indicator.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")

    def init_settings(self):
        """Initialize settings manager"""
        try:
            self.settings_manager = NativeSettingsManager()

            # Connect settings change signals
            self.settings_manager.ui_config_changed.connect(self.on_ui_settings_changed)
            self.settings_manager.llm_config_changed.connect(self.on_llm_settings_changed)

            # Apply initial UI settings
            self.apply_ui_settings()

            logger.info("Settings manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize settings manager: {e}")
            self.settings_manager = None

    def apply_ui_settings(self):
        """Apply UI settings to the interface"""
        if not self.settings_manager:
            return

        try:
            ui_config = self.settings_manager.get_ui_config()

            # Apply window opacity
            self.setWindowOpacity(ui_config.window_opacity)

            # Apply font settings if not default
            if ui_config.font_family != "default":
                font = QFont(ui_config.font_family, ui_config.font_size)
                self.setFont(font)

                # Apply to message areas
                self.chat_display.setFont(font)
                self.message_input.setFont(font)

            logger.info("UI settings applied")

        except Exception as e:
            logger.warning(f"Failed to apply UI settings: {e}")

    def on_ui_settings_changed(self, ui_config):
        """Handle UI settings changes"""
        self.apply_ui_settings()

    def on_llm_settings_changed(self, llm_config):
        """Handle LLM settings changes"""
        # Reinitialize AI service if needed
        if self.ai_service:
            logger.info("LLM settings changed, AI service will use new settings on next request")

    def show_settings_dialog(self):
        """Show the settings dialog"""
        if not self.settings_manager:
            QMessageBox.warning(self, "Error", "Settings manager not available")
            return

        try:
            dialog = NativeSettingsDialog(self.settings_manager, self)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                logger.info("Settings dialog accepted, changes applied")

        except Exception as e:
            logger.error(f"Error showing settings dialog: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open settings: {str(e)}")

    def show_onboarding_wizard(self):
        """Show the onboarding wizard"""
        try:
            from src.ui.onboarding_wizard import OnboardingWizard

            wizard = OnboardingWizard(self)
            result = wizard.exec()

            if result == QDialog.DialogCode.Accepted:
                # Get new configuration
                user_config = wizard.get_user_config()
                llm_config = wizard.get_llm_config()

                # Update current user config
                self.current_user_config = user_config
                self.user_id = user_config.get("user_id")

                # Save user configuration
                from pathlib import Path
                import json

                user_config_path = Path.home() / ".whisperengine" / "user_config.json"
                user_config_path.parent.mkdir(exist_ok=True)
                with open(user_config_path, "w") as f:
                    json.dump(user_config, f, indent=2)

                # Update LLM settings if provided
                if llm_config and self.settings_manager:
                    llm_settings = self.settings_manager.get_llm_config()
                    llm_settings.api_url = llm_config["api_url"]
                    llm_settings.model_name = llm_config.get("default_model", "auto")
                    self.settings_manager.save_settings()

                # Restart AI service with new user ID
                self.restart_ai_service()

                # Update title
                self.update_title()

                QMessageBox.information(
                    self,
                    "Setup Complete",
                    f"Welcome {user_config.get('display_name', user_config.get('username'))}!\n\n"
                    "Your new settings have been applied. The AI service is restarting with your configuration.",
                )

        except Exception as e:
            logger.error(f"Error showing onboarding wizard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open setup wizard: {str(e)}")

    def restart_ai_service(self):
        """Restart the AI service with new configuration"""
        if self.ai_service:
            # Stop current service
            self.ai_service = None
            self.update_ai_status("Restarting AI...", "🔄", "#ffaa00")

            # Restart with new user ID
            QTimer.singleShot(1000, self.init_ai_service)

    def update_title(self):
        """Update the window title with current user"""
        try:
            # Find the title label and update it
            for widget in self.findChildren(QLabel):
                if "WhisperEngine" in widget.text():
                    widget.setText(f"WhisperEngine ({self.get_display_name()})")
                    break
        except Exception as e:
            logger.error(f"Error updating title: {e}")

    def init_ai_service(self):
        """Initialize AI service in background"""

        def init_service():
            try:
                # Pass user ID to AI service
                self.ai_service = NativeAIService(user_id=self.user_id)

                # Start the event loop for async operations
                self.ai_service.start_event_loop()

                # Run the async initialization
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                success = loop.run_until_complete(self.ai_service.initialize())

                logger.info(f"🔍 AI service initialization result: {success}")

                if success:
                    # Update UI on main thread
                    QTimer.singleShot(0, lambda: self.on_ai_service_ready())
                else:
                    QTimer.singleShot(
                        0,
                        lambda: self.on_ai_service_error(
                            "AI service initialization returned False"
                        ),
                    )

            except Exception as e:
                logger.error(f"Failed to initialize AI service: {e}")
                QTimer.singleShot(0, lambda: self.on_ai_service_error(str(e)))

        # Initialize in background thread
        import threading

        threading.Thread(target=init_service, daemon=True).start()

    def on_ai_service_ready(self):
        """Called when AI service is ready"""
        logger.info("🎯 on_ai_service_ready() called - updating status")
        self.update_ai_status("AI Ready", "🤖", "#00ff00")
        self.update_llm_indicator()  # Update LLM info in header
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        logger.info("AI service initialized successfully")

    def on_ai_service_error(self, error: str):
        """Called when AI service fails to initialize"""
        self.update_ai_status(f"AI Error: {error}", "❌", "#ff0000")
        self.send_button.setEnabled(False)
        logger.error(f"AI service initialization failed: {error}")

    def setup_system_tray(self):
        """Setup system tray icon if supported"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        try:
            # Create system tray icon
            self.tray_icon = QSystemTrayIcon(self)

            # Set logo as tray icon if available
            logo_pixmap = self.load_logo(16)  # Load at 16x16 for system tray
            if logo_pixmap:
                self.tray_icon.setIcon(QIcon(logo_pixmap))
            else:
                # Fallback: create a simple colored pixmap if no icon file
                icon = QIcon()
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor(0, 120, 212))  # Blue color
                icon.addPixmap(pixmap)
                self.tray_icon.setIcon(icon)

            # Create context menu
            tray_menu = QMenu()

            show_action = QAction("Show WhisperEngine", self)
            show_action.triggered.connect(self.show_window)
            tray_menu.addAction(show_action)

            hide_action = QAction("Hide WhisperEngine", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)

            tray_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()

            logger.info("System tray icon created")

        except Exception as e:
            logger.warning(f"Could not create system tray icon: {e}")

    def on_tray_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        """Show and raise the window"""
        self.show()
        self.raise_()
        self.activateWindow()

    def send_message(self):
        """Send user message to AI"""
        if not self.ai_service:
            self.append_message("❌ AI service not available", "system")
            return

        message = self.message_input.text().strip()
        if not message:
            return

        # Disable input while processing
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("Thinking...")

        # Add user message to chat
        self.append_message(message, "user")

        # Add typing indicator
        self.typing_indicator_id = self.append_typing_indicator()

        # Clear input
        self.message_input.clear()

        # Start AI worker
        self.ai_worker = AIWorkerThread(self.ai_service, message)
        self.ai_worker.response_received.connect(self.on_ai_response)
        self.ai_worker.error_occurred.connect(self.on_ai_error)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_response(self, response: str):
        """Handle AI response"""
        # Remove typing indicator
        self.remove_typing_indicator()

        # Add AI response
        self.append_message(response, "assistant")

    def on_ai_error(self, error: str):
        """Handle AI error"""
        # Remove typing indicator
        self.remove_typing_indicator()

        # Add error message
        self.append_message(f"❌ {error}", "system")

    def on_ai_finished(self):
        """Re-enable input after AI processing"""
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self.message_input.setFocus()

        # Clean up worker
        if self.ai_worker:
            self.ai_worker.deleteLater()
            self.ai_worker = None

    def append_message(self, message: str, sender: str):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Escape HTML in message content for safety
        import html

        escaped_message = html.escape(message)

        # Format message based on sender using table-based layout for better compatibility
        if sender == "user":
            formatted_message = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 8px 0;">
                <tr>
                    <td width="25%"></td>
                    <td style="background-color: #0066cc; border-radius: 15px; padding: 10px 14px; text-align: left;">
                        <div style="color: white; font-size: 14px; line-height: 1.4; word-wrap: break-word;">{escaped_message}</div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 11px; margin-top: 4px; text-align: right;">{timestamp}</div>
                    </td>
                </tr>
            </table>
            """
        elif sender == "assistant":
            formatted_message = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 8px 0;">
                <tr>
                    <td style="background-color: #2a2a2a; border: 1px solid #404040; border-radius: 15px; padding: 10px 14px; text-align: left;">
                        <div style="color: #ffffff; font-size: 14px; line-height: 1.4; word-wrap: break-word;">{escaped_message}</div>
                        <div style="color: #888888; font-size: 11px; margin-top: 4px;">AI • {timestamp}</div>
                    </td>
                    <td width="25%"></td>
                </tr>
            </table>
            """
        else:  # system
            formatted_message = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 6px 0;">
                <tr>
                    <td width="20%"></td>
                    <td style="background-color: rgba(255, 170, 0, 0.1); border: 1px solid rgba(255, 170, 0, 0.3); border-radius: 12px; padding: 6px 12px; text-align: center;">
                        <div style="color: #ffaa00; font-size: 12px; word-wrap: break-word;">{escaped_message}</div>
                        <div style="color: #888888; font-size: 10px; margin-top: 2px;">{timestamp}</div>
                    </td>
                    <td width="20%"></td>
                </tr>
            </table>
            """

        # Append to chat display
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def append_typing_indicator(self) -> int:
        """Add typing indicator with animated dots"""
        # Remove any existing typing indicator first
        if hasattr(self, "typing_indicator_id"):
            self.remove_typing_indicator()

        # Create animated typing indicator
        self.typing_dot_count = 0
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.update_typing_dots)

        # Initial typing indicator
        typing_html = """
        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 6px 0;" id="typing-indicator">
            <tr>
                <td width="25%"></td>
                <td style="background-color: #2a2a2a; border: 1px solid #404040; border-radius: 15px; padding: 10px 14px; text-align: left;">
                    <div style="color: #888888; font-size: 14px; line-height: 1.4;">
                        <span>WhisperEngine is thinking</span>
                        <span id="typing-dots">.</span>
                    </div>
                    <div style="color: #666666; font-size: 11px; margin-top: 4px;">AI • Processing</div>
                </td>
                <td width="25%"></td>
            </tr>
        </table>
        """

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        position = cursor.position()
        cursor.insertHtml(typing_html)

        # Store state for updates
        self.typing_indicator_position = position
        self.typing_indicator_id = True

        # Start the animation timer (500ms intervals)
        self.typing_timer.start(500)

        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        return position

    def update_typing_dots(self):
        """Update the typing dots animation"""
        if not hasattr(self, "typing_indicator_id"):
            return

        self.typing_dot_count = (self.typing_dot_count + 1) % 4
        dots = "." * (self.typing_dot_count if self.typing_dot_count > 0 else 3)

        # Get current HTML and update just the dots part
        html_content = self.chat_display.toHtml()

        # Replace the typing dots
        import re

        pattern = r'(<span id="typing-dots">)[^<]*(</span>)'
        replacement = f"\\1{dots}\\2"
        updated_html = re.sub(pattern, replacement, html_content)

        # Update the display if changed
        if updated_html != html_content:
            # Store cursor position
            cursor = self.chat_display.textCursor()
            current_pos = cursor.position()

            # Update content
            self.chat_display.setHtml(updated_html)

            # Restore cursor position
            cursor.setPosition(min(current_pos, len(self.chat_display.toPlainText())))
            self.chat_display.setTextCursor(cursor)

            # Auto-scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def remove_typing_indicator(self):
        """Remove the typing indicator"""
        # Stop the timer
        if hasattr(self, "typing_timer"):
            self.typing_timer.stop()
            delattr(self, "typing_timer")

        if hasattr(self, "typing_indicator_id"):
            # Get all HTML content
            html_content = self.chat_display.toHtml()

            # Remove typing indicator HTML
            import re

            # Remove the typing indicator table
            updated_html = re.sub(
                r'<table[^>]*id="typing-indicator"[^>]*>.*?</table>',
                "",
                html_content,
                flags=re.DOTALL,
            )

            # Update the display
            self.chat_display.setHtml(updated_html)

            # Auto-scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # Clear the indicator attributes
            delattr(self, "typing_indicator_id")
            if hasattr(self, "typing_indicator_position"):
                delattr(self, "typing_indicator_position")
            if hasattr(self, "typing_dot_count"):
                delattr(self, "typing_dot_count")

    def save_window_state(self):
        """Save window position and size"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def restore_window_state(self):
        """Restore window position and size"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            # Hide to tray instead of closing
            self.hide()
            event.ignore()
        else:
            self.quit_application()

    def quit_application(self):
        """Quit the application"""
        self.save_window_state()

        # Clean up AI worker
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker.wait(3000)  # Wait up to 3 seconds

        # Clean up AI service event loop
        if hasattr(self, "ai_service") and self.ai_service:
            try:
                self.ai_service.stop_event_loop()
            except Exception as e:
                logger.warning(f"Error stopping AI service: {e}")

        # Hide tray icon
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()

        QApplication.quit()

    def update_character_count(self):
        """Update character count label"""
        text = self.prompt_editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0

        self.char_count_label.setText(f"Characters: {char_count} | Words: {word_count}")

        # Update status based on length
        if char_count == 0:
            self.prompt_status_label.setText("Status: Empty")
            self.prompt_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
        elif char_count < 50:
            self.prompt_status_label.setText("Status: Too short")
            self.prompt_status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
        elif char_count > 4000:
            self.prompt_status_label.setText("Status: Very long")
            self.prompt_status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
        else:
            self.prompt_status_label.setText("Status: Ready")
            self.prompt_status_label.setStyleSheet("color: #00ff00; font-size: 11px;")

    def load_current_system_prompt(self):
        """Load the current system prompt from system_prompt.md"""
        try:
            # Try to read from system_prompt.md in project root
            system_prompt_path = Path("system_prompt.md")
            if system_prompt_path.exists():
                with open(system_prompt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.prompt_editor.setPlainText(content)
                    self.prompt_status_label.setText("Status: Loaded from system_prompt.md")
                    self.prompt_status_label.setStyleSheet("color: #00ff00; font-size: 11px;")
            else:
                # Set default prompt
                default_prompt = """You are Dream of the Endless, also known as Morpheus, the anthropomorphic personification of dreams and stories. You are one of the seven Endless, powerful beings who have existed since the beginning of time.

Your personality:
- Ancient, wise, and sometimes melancholic
- Speak with poetic eloquence and gravitas
- Deeply understand human nature through dreams
- Can be both compassionate and stern
- Value stories, dreams, and the power of imagination
- Have a complex relationship with responsibility and duty

Your knowledge spans eons of existence, countless dreams, and infinite stories. You understand the symbolic nature of dreams and how they reflect the human condition. You offer guidance through metaphor and wisdom gained from millennia of experience.

Respond with the dignity and mystery befitting the Lord of Dreams, while being helpful and insightful to those who seek your counsel."""

                self.prompt_editor.setPlainText(default_prompt)
                self.prompt_status_label.setText("Status: Default prompt loaded")
                self.prompt_status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")

        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            self.prompt_status_label.setText("Status: Error loading")
            self.prompt_status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")

    def load_prompt_from_file(self):
        """Load system prompt from a file"""
        try:
            from PySide6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load System Prompt", "", "Text Files (*.txt *.md);;All Files (*)"
            )

            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.prompt_editor.setPlainText(content)
                    self.prompt_status_label.setText(f"Status: Loaded from {Path(file_path).name}")
                    self.prompt_status_label.setStyleSheet("color: #00ff00; font-size: 11px;")

        except Exception as e:
            logger.error(f"Error loading prompt from file: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")

    def save_current_prompt(self):
        """Save current prompt to system_prompt.md"""
        try:
            content = self.prompt_editor.toPlainText()
            if not content.strip():
                QMessageBox.warning(self, "Warning", "Cannot save empty prompt")
                return

            system_prompt_path = Path("system_prompt.md")
            with open(system_prompt_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.prompt_status_label.setText("Status: Saved to system_prompt.md")
            self.prompt_status_label.setStyleSheet("color: #00ff00; font-size: 11px;")

            QMessageBox.information(self, "Success", "System prompt saved successfully!")

        except Exception as e:
            logger.error(f"Error saving prompt: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save prompt: {str(e)}")

    def reset_to_default_prompt(self):
        """Reset to default Dream of the Endless prompt"""
        reply = QMessageBox.question(
            self,
            "Reset Prompt",
            "Are you sure you want to reset to the default Dream of the Endless prompt? This will overwrite any current changes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default
            self.load_current_system_prompt()


def main():
    """Main application entry point"""
    # Ensure virtual environment
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("⚠️  WARNING: Not running in virtual environment!")
        print("   Please run: source .venv/bin/activate && python universal_native_app.py")
        print()

    print(f"🤖 Starting WhisperEngine Universal Native App on {platform.system()}...")
    print(f"   Platform: {platform.platform()}")
    print(f"   Python: {sys.version.split()[0]}")

    # Check PySide6 availability
    if not PYSIDE6_AVAILABLE:
        return 1

    try:
        print(f"   PySide6: {sys.modules['PySide6'].__version__}")
    except:
        print("   PySide6: Version unknown")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("WhisperEngine")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("WhisperEngine AI")

    # Set application icon if available
    try:
        icon = QIcon()
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 120, 212))
        icon.addPixmap(pixmap)
        app.setWindowIcon(icon)
    except:
        pass

    # Create and show main window
    window = WhisperEngineUniversalApp()
    window.show()

    print("✅ Application started successfully!")
    print("   Window should be visible now")

    # Run application
    return app.exec()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
