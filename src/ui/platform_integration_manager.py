#!/usr/bin/env python3
"""
Platform Integration Manager for WhisperEngine Universal App
Handles platform-specific integrations for macOS, Windows, and Linux.
"""

import logging
import platform
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
    from PySide6.QtCore import QObject, Signal, QTimer
    from PySide6.QtGui import QIcon, QPixmap, QColor, QAction
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

class PlatformIntegrationManager(QObject):
    """Manages platform-specific integrations across operating systems"""
    
    # Signals for platform events
    tray_activated = Signal(str)  # activation type
    notification_clicked = Signal()
    dock_clicked = Signal()  # macOS only
    taskbar_progress_request = Signal(int)  # Windows only
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # Platform detection
        self.platform_name = platform.system().lower()
        self.is_macos = self.platform_name == 'darwin'
        self.is_windows = self.platform_name == 'windows'
        self.is_linux = self.platform_name == 'linux'
        
        # Platform-specific managers
        self.macos_manager: Optional['MacOSIntegration'] = None
        self.windows_manager: Optional['WindowsIntegration'] = None  
        self.linux_manager: Optional['LinuxIntegration'] = None
        
        # System tray
        self.system_tray: Optional[QSystemTrayIcon] = None
        
        self.logger.info(f"Platform integration manager initialized for {platform.system()}")
    
    def initialize(self, settings_manager=None) -> bool:
        """Initialize platform-specific integrations"""
        try:
            success = True
            
            # Initialize system tray (cross-platform)
            if self.init_system_tray():
                self.logger.info("✅ System tray initialized")
            else:
                self.logger.warning("⚠️ System tray initialization failed")
                success = False
            
            # Initialize platform-specific features
            if self.is_macos:
                success &= self.init_macos_integration(settings_manager)
            elif self.is_windows:
                success &= self.init_windows_integration(settings_manager)
            elif self.is_linux:
                success &= self.init_linux_integration(settings_manager)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize platform integrations: {e}")
            return False
    
    def init_system_tray(self) -> bool:
        """Initialize cross-platform system tray"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("System tray not available on this platform")
            return False
        
        try:
            self.system_tray = QSystemTrayIcon(self)
            
            # Create tray icon
            icon = self.create_tray_icon()
            self.system_tray.setIcon(icon)
            
            # Create context menu
            self.create_tray_menu()
            
            # Connect signals
            self.system_tray.activated.connect(self.on_tray_activated)
            self.system_tray.messageClicked.connect(self.notification_clicked.emit)
            
            # Show tray icon
            self.system_tray.show()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system tray: {e}")
            return False
    
    def create_tray_icon(self) -> QIcon:
        """Create system tray icon"""
        try:
            # Try to load icon file first
            icon_paths = [
                "assets/icon.png",
                "assets/icon.ico", 
                "src/ui/static/favicon.ico"
            ]
            
            for icon_path in icon_paths:
                if Path(icon_path).exists():
                    return QIcon(icon_path)
            
            # Create simple colored icon as fallback
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(0, 120, 212))  # WhisperEngine blue
            return QIcon(pixmap)
            
        except Exception as e:
            self.logger.warning(f"Failed to create tray icon: {e}")
            # Return empty icon as last resort
            return QIcon()
    
    def create_tray_menu(self):
        """Create system tray context menu"""
        if not self.system_tray:
            return
        
        menu = QMenu()
        
        # Show/Hide window
        show_action = QAction("Show WhisperEngine", self)
        show_action.triggered.connect(self.show_main_window)
        menu.addAction(show_action)
        
        hide_action = QAction("Hide WhisperEngine", self)
        hide_action.triggered.connect(self.hide_main_window)
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        # New chat
        new_chat_action = QAction("New Chat", self)
        new_chat_action.triggered.connect(self.new_chat)
        menu.addAction(new_chat_action)
        
        # Settings
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # About
        about_action = QAction("About WhisperEngine", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # Quit
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(menu)
    
    def on_tray_activated(self, reason):
        """Handle system tray activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.tray_activated.emit("double_click")
            self.show_main_window()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.tray_activated.emit("middle_click")
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.tray_activated.emit("left_click")
    
    def init_macos_integration(self, settings_manager=None) -> bool:
        """Initialize macOS-specific integrations"""
        try:
            self.macos_manager = MacOSIntegration(self.main_window)
            success = self.macos_manager.initialize(settings_manager)
            
            if success:
                # Connect macOS-specific signals
                self.macos_manager.dock_clicked.connect(self.dock_clicked.emit)
                self.logger.info("✅ macOS integration initialized")
            else:
                self.logger.warning("⚠️ macOS integration failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize macOS integration: {e}")
            return False
    
    def init_windows_integration(self, settings_manager=None) -> bool:
        """Initialize Windows-specific integrations"""
        try:
            self.windows_manager = WindowsIntegration(self.main_window)
            success = self.windows_manager.initialize(settings_manager)
            
            if success:
                # Connect Windows-specific signals
                self.windows_manager.taskbar_progress_changed.connect(self.taskbar_progress_request.emit)
                self.logger.info("✅ Windows integration initialized")
            else:
                self.logger.warning("⚠️ Windows integration failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Windows integration: {e}")
            return False
    
    def init_linux_integration(self, settings_manager=None) -> bool:
        """Initialize Linux-specific integrations"""
        try:
            self.linux_manager = LinuxIntegration(self.main_window)
            success = self.linux_manager.initialize(settings_manager)
            
            if success:
                self.logger.info("✅ Linux integration initialized")
            else:
                self.logger.warning("⚠️ Linux integration failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Linux integration: {e}")
            return False
    
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show system notification"""
        if self.system_tray and self.system_tray.supportsMessages():
            self.system_tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)
        else:
            self.logger.warning("System notifications not supported")
    
    def show_main_window(self):
        """Show and raise main window"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def hide_main_window(self):
        """Hide main window"""
        if self.main_window:
            self.main_window.hide()
    
    def new_chat(self):
        """Start new chat in main window"""
        if self.main_window and hasattr(self.main_window, 'new_chat'):
            self.main_window.new_chat()
    
    def show_settings(self):
        """Show settings dialog"""
        if self.main_window and hasattr(self.main_window, 'show_settings_dialog'):
            self.show_main_window()
            self.main_window.show_settings_dialog()
    
    def show_about(self):
        """Show about dialog"""
        if self.main_window and hasattr(self.main_window, 'show_about_dialog'):
            self.show_main_window()
            self.main_window.show_about_dialog()
    
    def quit_application(self):
        """Quit the application"""
        if self.main_window and hasattr(self.main_window, 'quit_application'):
            self.main_window.quit_application()
        else:
            QApplication.quit()
    
    def set_tray_tooltip(self, tooltip: str):
        """Set system tray tooltip"""
        if self.system_tray:
            self.system_tray.setToolTip(tooltip)
    
    def update_tray_icon(self, icon_path: Optional[str] = None):
        """Update system tray icon"""
        if self.system_tray:
            if icon_path and Path(icon_path).exists():
                self.system_tray.setIcon(QIcon(icon_path))
            else:
                self.system_tray.setIcon(self.create_tray_icon())
    
    def set_auto_start(self, enabled: bool) -> bool:
        """Enable/disable auto-start with system"""
        try:
            if self.is_macos and self.macos_manager:
                return self.macos_manager.set_auto_start(enabled)
            elif self.is_windows and self.windows_manager:
                return self.windows_manager.set_auto_start(enabled)
            elif self.is_linux and self.linux_manager:
                return self.linux_manager.set_auto_start(enabled)
            else:
                self.logger.warning("Auto-start not supported on this platform")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set auto-start: {e}")
            return False
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information"""
        info = {
            'platform': platform.system(),
            'version': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'system_tray_available': QSystemTrayIcon.isSystemTrayAvailable() if PYSIDE6_AVAILABLE else False,
            'features': {
                'notifications': self.system_tray.supportsMessages() if self.system_tray else False,
                'auto_start': False,
                'menu_bar': False,
                'taskbar': False,
                'dock': False
            }
        }
        
        # Platform-specific feature detection
        if self.is_macos:
            info['features'].update({
                'menu_bar': True,
                'dock': True,
                'auto_start': True
            })
        elif self.is_windows:
            info['features'].update({
                'taskbar': True,
                'auto_start': True,
                'jump_lists': True
            })
        elif self.is_linux:
            info['features'].update({
                'desktop_integration': True,
                'auto_start': True
            })
        
        return info
    
    def cleanup(self):
        """Cleanup platform integrations"""
        try:
            if self.system_tray:
                self.system_tray.hide()
                self.system_tray = None
            
            if self.macos_manager:
                self.macos_manager.cleanup()
                self.macos_manager = None
            
            if self.windows_manager:
                self.windows_manager.cleanup()
                self.windows_manager = None
            
            if self.linux_manager:
                self.linux_manager.cleanup()
                self.linux_manager = None
            
            self.logger.info("Platform integrations cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during platform integration cleanup: {e}")

# Platform-specific integration classes (placeholders for now)
class MacOSIntegration(QObject):
    """macOS-specific integration features"""
    dock_clicked = Signal()
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, settings_manager=None) -> bool:
        """Initialize macOS features"""
        # Placeholder for actual macOS integration
        self.logger.info("macOS integration placeholder initialized")
        return True
    
    def set_auto_start(self, enabled: bool) -> bool:
        """Set auto-start on macOS"""
        # Placeholder for LaunchAgents integration
        return True
    
    def cleanup(self):
        """Cleanup macOS integration"""
        pass

class WindowsIntegration(QObject):
    """Windows-specific integration features"""
    taskbar_progress_changed = Signal(int)
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, settings_manager=None) -> bool:
        """Initialize Windows features"""
        # Placeholder for actual Windows integration
        self.logger.info("Windows integration placeholder initialized")
        return True
    
    def set_auto_start(self, enabled: bool) -> bool:
        """Set auto-start on Windows"""
        # Placeholder for registry integration
        return True
    
    def cleanup(self):
        """Cleanup Windows integration"""
        pass

class LinuxIntegration(QObject):
    """Linux-specific integration features"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
    
    def initialize(self, settings_manager=None) -> bool:
        """Initialize Linux features"""
        # Placeholder for actual Linux integration
        self.logger.info("Linux integration placeholder initialized")
        return True
    
    def set_auto_start(self, enabled: bool) -> bool:
        """Set auto-start on Linux"""
        # Placeholder for .desktop file integration
        return True
    
    def cleanup(self):
        """Cleanup Linux integration"""
        pass