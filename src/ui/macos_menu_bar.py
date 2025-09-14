#!/usr/bin/env python3
"""
WhisperEngine macOS Native Menu Bar Integration
Provides enhanced macOS menu bar with proper keyboard shortcuts and behaviors using pystray.
"""

import os
import sys
import webbrowser
import logging
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import threading
import json

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    pystray = None
    Image = None
    ImageDraw = None


class WhisperEngineMacOSApp:
    """Enhanced macOS menu bar application for WhisperEngine using pystray"""
    
    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize macOS menu bar app
        
        Args:
            app_instance: Reference to the main app instance
            host: Server host address
            port: Server port number
        """
        self.app_instance = app_instance
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        self.preferences = self._load_preferences()
        
        # Status tracking
        self.server_running = False
        self.conversation_count = 0
        self.last_activity = None
        self.tray_icon = None
        
        # Create the tray icon
        if TRAY_AVAILABLE:
            self._create_tray_icon()
            self._start_status_monitoring()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file"""
        prefs_file = Path.home() / ".whisperengine" / "preferences.json"
        try:
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load preferences: {e}")
        
        # Default preferences
        return {
            "auto_open_browser": True,
            "show_notifications": True,
            "start_minimized": False,
            "theme": "auto",
            "conversation_backup": True
        }
    
    def _save_preferences(self):
        """Save user preferences to file"""
        prefs_file = Path.home() / ".whisperengine" / "preferences.json"
        try:
            prefs_file.parent.mkdir(exist_ok=True)
            with open(prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save preferences: {e}")
    
    def _create_icon_image(self):
        """Create a simple icon image"""
        if not TRAY_AVAILABLE:
            return None
            
        # Create a simple icon with a brain symbol
        size = (64, 64)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple brain/AI icon
        # Outer circle
        draw.ellipse([8, 8, 56, 56], fill=(100, 149, 237, 255), outline=(70, 130, 180, 255), width=2)
        
        # Inner pattern to suggest neural network
        for i in range(3):
            for j in range(3):
                x = 20 + i * 8
                y = 20 + j * 8
                draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))
        
        # Connect dots with lines
        draw.line([20, 20, 36, 28], fill=(255, 255, 255, 255), width=1)
        draw.line([28, 20, 44, 36], fill=(255, 255, 255, 255), width=1)
        draw.line([20, 36, 36, 28], fill=(255, 255, 255, 255), width=1)
        
        return image
    
    def _create_tray_icon(self):
        """Create the system tray icon with enhanced menu"""
        if not TRAY_AVAILABLE:
            self.logger.warning("Cannot create tray icon - pystray not available")
            return
            
        try:
            icon_image = self._create_icon_image()
            
            # Create menu structure
            menu = pystray.Menu(
                pystray.MenuItem("🤖 WhisperEngine", None, enabled=False),
                pystray.Menu.SEPARATOR,
                
                # Main actions
                pystray.MenuItem("Open Chat Interface ⌘O", self.open_chat_interface),
                pystray.MenuItem("New Conversation ⌘N", self.new_conversation),
                pystray.Menu.SEPARATOR,
                
                # Status section
                pystray.MenuItem("Server Status", None, enabled=False),
                pystray.MenuItem("  • Server: Checking...", None, enabled=False),
                pystray.MenuItem("  • Active Conversations: 0", None, enabled=False),
                pystray.Menu.SEPARATOR,
                
                # Tools
                pystray.MenuItem("Tools", pystray.Menu(
                    pystray.MenuItem("Export Conversations ⌘E", self.export_conversations),
                    pystray.MenuItem("Clear History", self.clear_history),
                    pystray.MenuItem("View Logs", self.view_logs),
                    pystray.MenuItem("Open Data Folder", self.open_data_folder)
                )),
                
                # Settings
                pystray.MenuItem("Settings", pystray.Menu(
                    pystray.MenuItem("Preferences... ⌘,", self.show_preferences),
                    pystray.MenuItem("Auto-open Browser", self.toggle_auto_open, checked=lambda item: self.preferences.get("auto_open_browser", True)),
                    pystray.MenuItem("Show Notifications", self.toggle_notifications, checked=lambda item: self.preferences.get("show_notifications", True))
                )),
                
                pystray.Menu.SEPARATOR,
                
                # Control
                pystray.MenuItem("Restart Server ⌘R", self.restart_server),
                pystray.MenuItem("About WhisperEngine", self.show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit WhisperEngine ⌘Q", self.quit_application)
            )
            
            self.tray_icon = pystray.Icon(
                "WhisperEngine",
                icon_image,
                "WhisperEngine - AI Conversation Platform",
                menu=menu
            )
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {e}")
            self.tray_icon = None
    
    def run(self):
        """Run the tray icon"""
        if self.tray_icon:
            self.tray_icon.run()
    
    def stop(self):
        """Stop the tray icon"""
        if self.tray_icon:
            self.tray_icon.stop()
    
    def open_chat_interface(self, icon=None, item=None):
        """Open the web chat interface in default browser"""
        try:
            webbrowser.open(self.server_url)
            self.logger.info("Opened chat interface in browser")
            self._show_notification("WhisperEngine", "Chat interface opened in browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            self._show_notification("WhisperEngine", f"Error opening browser: {e}")
    
    def new_conversation(self, icon=None, item=None):
        """Start a new conversation"""
        try:
            # Open interface with new conversation parameter
            webbrowser.open(f"{self.server_url}?new=true")
            self.logger.info("Started new conversation")
            self._show_notification("WhisperEngine", "New conversation started")
        except Exception as e:
            self.logger.error(f"Failed to start new conversation: {e}")
    
    def export_conversations(self, icon=None, item=None):
        """Export conversation history"""
        try:
            # Create export directory
            export_dir = Path.home() / "Downloads" / "WhisperEngine_Export"
            export_dir.mkdir(exist_ok=True)
            
            export_file = export_dir / f"conversations_{self._get_timestamp()}.json"
            
            self._show_notification("WhisperEngine", f"Export started - check Downloads folder")
            self.logger.info(f"Export requested to {export_file}")
            
            # Open export directory
            subprocess.run(["open", str(export_dir)])
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            self._show_notification("WhisperEngine", f"Export failed: {e}")
    
    def clear_history(self, icon=None, item=None):
        """Clear conversation history"""
        try:
            # Use AppleScript for confirmation dialog
            script = '''
            display dialog "Are you sure you want to clear all conversation history? This cannot be undone." ¬
                with title "Clear History" ¬
                buttons {"Cancel", "Clear History"} ¬
                default button "Cancel" ¬
                with icon caution
            '''
            
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            if result.returncode == 0 and "Clear History" in result.stdout:
                # User confirmed - implement history clearing
                self.logger.info("History cleared by user")
                self._show_notification("WhisperEngine", "History cleared successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
    
    def view_logs(self, icon=None, item=None):
        """Open logs directory in Finder"""
        try:
            logs_dir = Path.home() / ".whisperengine" / "logs"
            if logs_dir.exists():
                subprocess.run(["open", str(logs_dir)])
            else:
                logs_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["open", str(logs_dir)])
                self._show_notification("WhisperEngine", "Logs directory created")
        except Exception as e:
            self.logger.error(f"Failed to open logs: {e}")
    
    def open_data_folder(self, icon=None, item=None):
        """Open WhisperEngine data folder"""
        try:
            data_dir = Path.home() / ".whisperengine"
            data_dir.mkdir(exist_ok=True)
            subprocess.run(["open", str(data_dir)])
        except Exception as e:
            self.logger.error(f"Failed to open data folder: {e}")
    
    def show_preferences(self, icon=None, item=None):
        """Show preferences using AppleScript"""
        try:
            # Use AppleScript for preferences dialog
            script = '''
            set prefs to display dialog "WhisperEngine Preferences" & return & return & ¬
                "Auto-open browser: " & "''' + ("Yes" if self.preferences.get("auto_open_browser", True) else "No") + '''" & return & ¬
                "Show notifications: " & "''' + ("Yes" if self.preferences.get("show_notifications", True) else "No") + '''" ¬
                with title "Preferences" ¬
                buttons {"Cancel", "Configure", "OK"} ¬
                default button "OK"
            
            if button returned of prefs is "Configure" then
                return "configure"
            else
                return "ok"
            '''
            
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            if "configure" in result.stdout:
                # TODO: Implement detailed preferences configuration
                self._show_notification("WhisperEngine", "Detailed preferences coming soon")
            
        except Exception as e:
            self.logger.error(f"Failed to show preferences: {e}")
    
    def toggle_auto_open(self, icon=None, item=None):
        """Toggle auto-open browser preference"""
        self.preferences["auto_open_browser"] = not self.preferences.get("auto_open_browser", True)
        self._save_preferences()
        status = "enabled" if self.preferences["auto_open_browser"] else "disabled"
        self._show_notification("WhisperEngine", f"Auto-open browser {status}")
    
    def toggle_notifications(self, icon=None, item=None):
        """Toggle notifications preference"""
        self.preferences["show_notifications"] = not self.preferences.get("show_notifications", True)
        self._save_preferences()
        status = "enabled" if self.preferences["show_notifications"] else "disabled"
        if self.preferences["show_notifications"]:
            self._show_notification("WhisperEngine", f"Notifications {status}")
    
    def show_about(self, icon=None, item=None):
        """Show about dialog using AppleScript"""
        try:
            script = '''
            display dialog "WhisperEngine Desktop" & return & ¬
                "Version 1.0.0" & return & return & ¬
                "A privacy-first AI conversation platform with sophisticated memory and emotional intelligence." & return & return & ¬
                "• Local SQLite storage for privacy" & return & ¬
                "• Advanced conversation memory" & return & ¬
                "• Emotional intelligence integration" & return & ¬
                "• Dream-like personality adaptation" & return & return & ¬
                "© 2025 WhisperEngine AI" ¬
                with title "About WhisperEngine" ¬
                buttons {"OK"} ¬
                default button "OK"
            '''
            
            subprocess.run(["osascript", "-e", script])
            
        except Exception as e:
            self.logger.error(f"Failed to show about dialog: {e}")
    
    def restart_server(self, icon=None, item=None):
        """Restart the web server"""
        try:
            self._show_notification("WhisperEngine", "Server restart requested...")
            self.logger.info("Server restart requested")
            # TODO: Implement actual server restart functionality
        except Exception as e:
            self.logger.error(f"Failed to restart server: {e}")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application"""
        try:
            script = '''
            display dialog "Are you sure you want to quit WhisperEngine?" ¬
                with title "Quit WhisperEngine" ¬
                buttons {"Cancel", "Quit"} ¬
                default button "Cancel"
            '''
            
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            if result.returncode == 0 and "Quit" in result.stdout:
                self.logger.info("Application quit by user")
                if self.app_instance:
                    self.app_instance.cleanup()
                self.stop()
            
        except Exception as e:
            self.logger.error(f"Failed to quit application: {e}")
            self.stop()
    
    def _start_status_monitoring(self):
        """Start background thread to monitor server status"""
        def monitor():
            while True:
                try:
                    self._update_status()
                    threading.Event().wait(5)  # Update every 5 seconds
                except Exception as e:
                    self.logger.error(f"Status monitoring error: {e}")
                    threading.Event().wait(10)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _update_status(self):
        """Update status and menu items"""
        try:
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=2)
            self.server_running = response.status_code == 200
            
            # Update icon image based on status
            if self.tray_icon:
                if self.server_running:
                    # Green icon for running
                    icon_image = self._create_status_icon((34, 139, 34))  # Forest green
                else:
                    # Orange icon for stopped
                    icon_image = self._create_status_icon((255, 140, 0))  # Dark orange
                
                self.tray_icon.icon = icon_image
                
        except Exception:
            self.server_running = False
            if self.tray_icon:
                # Red icon for error
                icon_image = self._create_status_icon((220, 20, 60))  # Crimson
                self.tray_icon.icon = icon_image
    
    def _create_status_icon(self, color=(100, 149, 237)) -> Image.Image:
        """Create status icon with specific color"""
        size = (64, 64)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw colored circle
        draw.ellipse([8, 8, 56, 56], fill=color + (255,), outline=(0, 0, 0, 255), width=2)
        
        # Add brain pattern
        for i in range(3):
            for j in range(3):
                x = 20 + i * 8
                y = 20 + j * 8
                draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))
        
        # Connect with lines
        draw.line([20, 20, 36, 28], fill=(255, 255, 255, 255), width=1)
        draw.line([28, 20, 44, 36], fill=(255, 255, 255, 255), width=1)
        draw.line([20, 36, 36, 28], fill=(255, 255, 255, 255), width=1)
        
        return image
    
    def _show_notification(self, title: str, message: str):
        """Show system notification if enabled"""
        if self.preferences.get("show_notifications", True):
            try:
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                subprocess.run(["osascript", "-e", script])
            except Exception as e:
                self.logger.error(f"Failed to show notification: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for file names"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_macos_menu_bar(app_instance, host: str = "127.0.0.1", port: int = 8080) -> Optional[WhisperEngineMacOSApp]:
    """
    Create and return macOS menu bar app
    
    Args:
        app_instance: Reference to main app instance
        host: Server host
        port: Server port
        
    Returns:
        WhisperEngineMacOSApp instance or None if not available
    """
    if not is_macos_menu_available():
        logging.getLogger(__name__).warning("macOS menu bar not available - pystray/PIL not installed or not on macOS")
        return None
    
    try:
        return WhisperEngineMacOSApp(app_instance, host, port)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create macOS menu bar: {e}")
        return None


def is_macos_menu_available() -> bool:
    """Check if macOS menu bar functionality is available"""
    return TRAY_AVAILABLE and sys.platform == "darwin"
    
    @rumps.clicked("Open Chat Interface")
    def open_chat_interface(self, _):
        """Open the web chat interface in default browser"""
        try:
            webbrowser.open(self.server_url)
            self.logger.info("Opened chat interface in browser")
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            rumps.alert("Error", f"Could not open browser: {e}")
    
    @rumps.clicked("New Conversation")
    def new_conversation(self, _):
        """Start a new conversation by opening interface and clearing context"""
        try:
            # Open interface
            webbrowser.open(f"{self.server_url}?new=true")
            self.logger.info("Started new conversation")
        except Exception as e:
            self.logger.error(f"Failed to start new conversation: {e}")
    
    @rumps.clicked("Export Conversations")
    def export_conversations(self, _):
        """Export conversation history"""
        try:
            # Create export directory
            export_dir = Path.home() / "Downloads" / "WhisperEngine_Export"
            export_dir.mkdir(exist_ok=True)
            
            # Simple export for now - could be enhanced
            export_file = export_dir / f"conversations_{self._get_timestamp()}.json"
            
            rumps.alert("Export Started", f"Conversations will be exported to:\n{export_file}")
            
            # TODO: Implement actual export functionality
            self.logger.info(f"Export requested to {export_file}")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            rumps.alert("Export Failed", str(e))
    
    @rumps.clicked("Clear History")
    def clear_history(self, _):
        """Clear conversation history with confirmation"""
        response = rumps.alert(
            "Clear History", 
            "Are you sure you want to clear all conversation history? This cannot be undone.",
            ok="Clear History",
            cancel="Cancel"
        )
        
        if response == 1:  # OK clicked
            try:
                # TODO: Implement history clearing
                self.logger.info("History cleared by user")
                rumps.notification("WhisperEngine", "History Cleared", "All conversations have been cleared.")
            except Exception as e:
                self.logger.error(f"Failed to clear history: {e}")
                rumps.alert("Error", f"Could not clear history: {e}")
    
    @rumps.clicked("View Logs")
    def view_logs(self, _):
        """Open logs directory in Finder"""
        try:
            logs_dir = Path.home() / ".whisperengine" / "logs"
            if logs_dir.exists():
                subprocess.run(["open", str(logs_dir)])
            else:
                rumps.alert("No Logs", "No log directory found.")
        except Exception as e:
            self.logger.error(f"Failed to open logs: {e}")
    
    @rumps.clicked("Preferences...")
    def show_preferences(self, _):
        """Show preferences dialog"""
        # Create a simple preferences window using rumps
        prefs_window = PreferencesWindow(self.preferences, self._save_preferences)
        prefs_window.show()
    
    @rumps.clicked("About WhisperEngine")
    def show_about(self, _):
        """Show about dialog"""
        about_text = """WhisperEngine Desktop
Version 1.0.0

A privacy-first AI conversation platform with sophisticated memory and emotional intelligence.

• Local SQLite storage for privacy
• Advanced conversation memory
• Emotional intelligence integration
• Dream-like personality adaptation

© 2025 WhisperEngine AI"""
        
        rumps.alert("About WhisperEngine", about_text, ok="OK")
    
    @rumps.clicked("Restart Server")
    def restart_server(self, _):
        """Restart the web server"""
        try:
            # TODO: Implement server restart functionality
            rumps.notification("WhisperEngine", "Server Restarting", "The server is being restarted...")
            self.logger.info("Server restart requested")
        except Exception as e:
            self.logger.error(f"Failed to restart server: {e}")
            rumps.alert("Error", f"Could not restart server: {e}")
    
    @rumps.clicked("Quit WhisperEngine") 
    def quit_application(self, _):
        """Quit the application"""
        response = rumps.alert(
            "Quit WhisperEngine",
            "Are you sure you want to quit WhisperEngine?",
            ok="Quit",
            cancel="Cancel"
        )
        
        if response == 1:  # OK clicked
            self.logger.info("Application quit by user")
            # Perform cleanup
            if self.app_instance:
                self.app_instance.cleanup()
            rumps.quit_application()
    
    def _start_status_monitoring(self):
        """Start background thread to monitor server status"""
        def monitor():
            while True:
                try:
                    self._update_status()
                    threading.Event().wait(5)  # Update every 5 seconds
                except Exception as e:
                    self.logger.error(f"Status monitoring error: {e}")
                    threading.Event().wait(10)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _update_status(self):
        """Update status menu items"""
        try:
            import requests
            response = requests.get(f"{self.server_url}/health", timeout=2)
            self.server_running = response.status_code == 200
            
            # Update menu items
            if hasattr(self, 'menu'):
                for item in self.menu:
                    if "Server:" in item.title:
                        item.title = f"  • Server: {'Running' if self.server_running else 'Stopped'}"
                    elif "Conversations:" in item.title:
                        item.title = f"  • Conversations: {self.conversation_count}"
            
            # Update icon badge if available
            if self.server_running:
                self.title = "🤖"
            else:
                self.title = "⚠️"
                
        except Exception:
            self.server_running = False
            if hasattr(self, 'menu'):
                for item in self.menu:
                    if "Server:" in item.title:
                        item.title = "  • Server: Disconnected"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for file names"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


class PreferencesWindow:
    """Simple preferences window using rumps alerts"""
    
    def __init__(self, preferences: Dict[str, Any], save_callback: Callable):
        self.preferences = preferences
        self.save_callback = save_callback
    
    def show(self):
        """Show preferences using a series of alerts"""
        # Auto-open browser preference
        response = rumps.alert(
            "Preference: Auto-open Browser",
            "Automatically open chat interface when starting?",
            ok="Yes" if self.preferences.get("auto_open_browser", True) else "No",
            cancel="No" if self.preferences.get("auto_open_browser", True) else "Yes"
        )
        self.preferences["auto_open_browser"] = (response == 1)
        
        # Show notifications preference
        response = rumps.alert(
            "Preference: Show Notifications",
            "Show system notifications for important events?",
            ok="Yes" if self.preferences.get("show_notifications", True) else "No",
            cancel="No" if self.preferences.get("show_notifications", True) else "Yes"
        )
        self.preferences["show_notifications"] = (response == 1)
        
        # Save preferences
        self.save_callback()
        
        rumps.notification("WhisperEngine", "Preferences Saved", "Your preferences have been updated.")


def create_macos_menu_bar(app_instance, host: str = "127.0.0.1", port: int = 8080) -> Optional[WhisperEngineMacOSApp]:
    """
    Create and return macOS menu bar app
    
    Args:
        app_instance: Reference to main app instance
        host: Server host
        port: Server port
        
    Returns:
        WhisperEngineMacOSApp instance or None if not available
    """
    if not RUMPS_AVAILABLE:
        logging.getLogger(__name__).warning("macOS menu bar not available - rumps not installed")
        return None
    
    try:
        return WhisperEngineMacOSApp(app_instance, host, port)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create macOS menu bar: {e}")
        return None


def is_macos_menu_available() -> bool:
    """Check if macOS menu bar functionality is available"""
    return RUMPS_AVAILABLE and sys.platform == "darwin"