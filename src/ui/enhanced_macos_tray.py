#!/usr/bin/env python3
"""
Enhanced macOS System Tray Integration for WhisperEngine
Provides advanced dock integration, badge notifications, and real-time status updates.
"""

import os
import sys
import logging
import subprocess
import threading
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    # Create mock objects for type hints
    class MockPystray:
        Menu = None
        MenuItem = None
        Icon = None
    
    class MockImage:
        Image = None
    
    pystray = MockPystray()
    Image = MockImage()
    ImageDraw = None
    ImageFont = None


@dataclass
class ConversationActivity:
    """Track conversation activity"""
    user_id: str
    last_message_time: datetime
    message_count: int
    conversation_id: str


@dataclass
class SystemStatus:
    """System status information"""
    server_running: bool = False
    active_connections: int = 0
    conversations_today: int = 0
    total_conversations: int = 0
    memory_usage_mb: float = 0.0
    uptime_seconds: int = 0
    last_activity: Optional[datetime] = None


class EnhancedMacOSTray:
    """Enhanced macOS system tray with advanced features"""
    
    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize enhanced macOS tray
        
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
        
        # Status tracking
        self.status = SystemStatus()
        self.active_conversations: Dict[str, ConversationActivity] = {}
        self.recent_activities: List[str] = []
        self.tray_icon = None
        self.running = False
        
        # Performance metrics
        self.start_time = datetime.now()
        self.last_status_update = datetime.now()
        self.update_interval = 3  # seconds
        
        # Configuration
        self.preferences = self._load_preferences()
        
        if TRAY_AVAILABLE:
            self._create_enhanced_tray()
            self._start_monitoring()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from file"""
        prefs_file = Path.home() / ".whisperengine" / "tray_preferences.json"
        try:
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load tray preferences: {e}")
        
        # Default preferences
        return {
            "show_badge_count": True,
            "show_activity_notifications": True,
            "update_interval": 3,
            "show_memory_usage": True,
            "quick_actions_enabled": True,
            "conversation_history_limit": 10
        }
    
    def _save_preferences(self):
        """Save preferences to file"""
        prefs_file = Path.home() / ".whisperengine" / "tray_preferences.json"
        try:
            prefs_file.parent.mkdir(exist_ok=True)
            with open(prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save tray preferences: {e}")
    
    def _create_enhanced_tray(self):
        """Create enhanced system tray with dynamic features"""
        if not TRAY_AVAILABLE:
            return
        
        try:
            # Create initial icon
            icon_image = self._create_status_icon()
            
            # Create dynamic menu
            menu = self._create_dynamic_menu()
            
            self.tray_icon = pystray.Icon(
                "WhisperEngine",
                icon_image,
                "WhisperEngine - AI Conversation Platform",
                menu=menu
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create enhanced tray: {e}")
    
    def _create_dynamic_menu(self):
        """Create dynamic menu that updates based on status"""
        if not TRAY_AVAILABLE:
            return None
        
        try:
            # Use local references to avoid repeated attribute access
            Menu = pystray.Menu
            MenuItem = pystray.MenuItem
            
            return Menu(
                # Header with dynamic status
                MenuItem(self._get_header_text(), None, enabled=False),
                Menu.SEPARATOR,
                
                # Quick Actions
                MenuItem("Quick Actions", Menu(
                    MenuItem("🚀 Open Chat", self._quick_open_chat),
                    MenuItem("✨ New Conversation", self._quick_new_conversation),
                    MenuItem("📋 Recent Conversations", self._show_recent_conversations),
                    MenuItem("📊 Show Statistics", self._show_statistics)
                )),
                
                # Status Information
                MenuItem("Status", Menu(
                    MenuItem(f"Server: {self._get_server_status()}", None, enabled=False),
                    MenuItem(f"Connections: {self.status.active_connections}", None, enabled=False),
                    MenuItem(f"Conversations Today: {self.status.conversations_today}", None, enabled=False),
                    MenuItem(f"Uptime: {self._get_uptime_text()}", None, enabled=False),
                    Menu.SEPARATOR,
                    MenuItem("📈 Performance Monitor", self._show_performance),
                    MenuItem("🔄 Refresh Status", self._force_status_update)
                )),
                
                # Conversation Management
                MenuItem("Conversations", Menu(
                    MenuItem("📥 Export All", self._export_conversations),
                    MenuItem("🗑️ Clear History", self._clear_conversations),
                    MenuItem("📊 View Analytics", self._show_analytics),
                    Menu.SEPARATOR,
                    MenuItem("🔍 Search Conversations", self._search_conversations)
                )),
                
                # Settings & Preferences
                MenuItem("Settings", Menu(
                    MenuItem("🔔 Notifications", self._toggle_notifications, 
                           checked=lambda item: self.preferences.get("show_activity_notifications", True)),
                    MenuItem("🏷️ Badge Count", self._toggle_badge_count, 
                           checked=lambda item: self.preferences.get("show_badge_count", True)),
                    MenuItem("💾 Memory Monitor", self._toggle_memory_monitor, 
                           checked=lambda item: self.preferences.get("show_memory_usage", True)),
                    Menu.SEPARATOR,
                    MenuItem("⚙️ Preferences...", self._show_preferences),
                    MenuItem("📁 Open Data Folder", self._open_data_folder)
                )),
                
                Menu.SEPARATOR,
                
                # System Control
                MenuItem("🔄 Restart Server", self._restart_server),
                MenuItem("ℹ️ About WhisperEngine", self._show_about),
                MenuItem("❌ Quit", self._quit_application)
            )
        except Exception as e:
            self.logger.error(f"Failed to create dynamic menu: {e}")
            return None
    
    def _create_status_icon(self, badge_count: Optional[int] = None):
        """Create status icon with optional badge"""
        if not TRAY_AVAILABLE:
            return None
        
        try:
            size = (64, 64)
            
            # Determine color based on status
            if self.status.server_running:
                if self.status.active_connections > 0:
                    color = (34, 139, 34)  # Green - active
                else:
                    color = (100, 149, 237)  # Blue - idle
            else:
                color = (220, 20, 60)  # Red - stopped
            
            # Create base icon
            image = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw main icon (brain/AI symbol)
            draw.ellipse([8, 8, 56, 56], fill=color + (255,), outline=(0, 0, 0, 255), width=2)
            
            # Neural network pattern
            for i in range(3):
                for j in range(3):
                    x = 20 + i * 8
                    y = 20 + j * 8
                    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))
            
            # Connect with lines
            draw.line([20, 20, 36, 28], fill=(255, 255, 255, 255), width=1)
            draw.line([28, 20, 44, 36], fill=(255, 255, 255, 255), width=1)
            draw.line([20, 36, 36, 28], fill=(255, 255, 255, 255), width=1)
            
            # Add badge if enabled and there's a count
            if (badge_count and badge_count > 0 and 
                self.preferences.get("show_badge_count", True)):
                self._add_badge(image, badge_count)
            
            return image
            
        except Exception as e:
            self.logger.error(f"Failed to create status icon: {e}")
            return None
    
    def _add_badge(self, image: Image.Image, count: int):
        """Add a notification badge to the icon"""
        try:
            draw = ImageDraw.Draw(image)
            
            # Badge position (top-right)
            badge_x, badge_y = 45, 8
            badge_radius = 10
            
            # Draw badge background
            draw.ellipse([
                badge_x - badge_radius, badge_y - badge_radius,
                badge_x + badge_radius, badge_y + badge_radius
            ], fill=(255, 59, 48, 255), outline=(255, 255, 255, 255), width=1)
            
            # Draw count text
            count_text = str(min(count, 99))  # Cap at 99
            if count > 99:
                count_text = "99+"
            
            # Try to load a font, fall back to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Get text size and center it
            bbox = draw.textbbox((0, 0), count_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = badge_x - text_width // 2
            text_y = badge_y - text_height // 2
            
            draw.text((text_x, text_y), count_text, fill=(255, 255, 255, 255), font=font)
            
        except Exception as e:
            self.logger.error(f"Failed to add badge: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            self.running = True
            while self.running:
                try:
                    self._update_status()
                    self._update_dock_badge()
                    self._update_tray_icon()
                    time.sleep(self.preferences.get("update_interval", 3))
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(10)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _update_status(self):
        """Update system status"""
        try:
            import requests
            import psutil
            
            # Check server health
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                self.status.server_running = response.status_code == 200
                
                # Try to get more detailed info if available
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.status.active_connections = data.get("active_connections", 0)
                        self.status.conversations_today = data.get("conversations_today", 0)
                    except:
                        pass
                        
            except Exception:
                self.status.server_running = False
                self.status.active_connections = 0
            
            # Update memory usage
            if self.preferences.get("show_memory_usage", True):
                try:
                    process = psutil.Process()
                    self.status.memory_usage_mb = process.memory_info().rss / (1024 * 1024)
                except:
                    self.status.memory_usage_mb = 0.0
            
            # Update uptime
            self.status.uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
            
            # Track activity
            if self.status.active_connections > 0:
                self.status.last_activity = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Status update failed: {e}")
    
    def _update_dock_badge(self):
        """Update dock icon badge with conversation count"""
        if not self.preferences.get("show_badge_count", True):
            return
        
        try:
            badge_count = self.status.active_connections
            
            if badge_count > 0:
                # Set dock badge
                script = f'''
                tell application "System Events"
                    try
                        set dock_item to (first dock tile whose file name = "WhisperEngine.app")
                        set badge text of dock_item to "{badge_count}"
                    end try
                end tell
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True)
            else:
                # Clear dock badge
                script = '''
                tell application "System Events"
                    try
                        set dock_item to (first dock tile whose file name = "WhisperEngine.app")
                        set badge text of dock_item to ""
                    end try
                end tell
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True)
                
        except Exception as e:
            self.logger.error(f"Failed to update dock badge: {e}")
    
    def _update_tray_icon(self):
        """Update tray icon with current status"""
        if not self.tray_icon:
            return
        
        try:
            badge_count = self.status.active_connections if self.preferences.get("show_badge_count", True) else None
            new_icon = self._create_status_icon(badge_count)
            
            if new_icon:
                self.tray_icon.icon = new_icon
                
                # Update tooltip
                uptime = self._get_uptime_text()
                tooltip = f"WhisperEngine - {self._get_server_status()}\n"
                tooltip += f"Connections: {self.status.active_connections}\n"
                tooltip += f"Uptime: {uptime}"
                
                self.tray_icon.title = tooltip
                
        except Exception as e:
            self.logger.error(f"Failed to update tray icon: {e}")
    
    # Menu action handlers
    def _get_header_text(self) -> str:
        """Get dynamic header text"""
        if self.status.server_running:
            return f"🤖 WhisperEngine • {self.status.active_connections} active"
        else:
            return "🤖 WhisperEngine • Offline"
    
    def _get_server_status(self) -> str:
        """Get server status text"""
        return "Running" if self.status.server_running else "Stopped"
    
    def _get_uptime_text(self) -> str:
        """Get formatted uptime text"""
        seconds = self.status.uptime_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    
    def _quick_open_chat(self, icon=None, item=None):
        """Quick action: Open chat interface"""
        import webbrowser
        try:
            webbrowser.open(self.server_url)
            self._notify("Chat Opened", "WhisperEngine chat interface opened in browser")
        except Exception as e:
            self.logger.error(f"Failed to open chat: {e}")
    
    def _quick_new_conversation(self, icon=None, item=None):
        """Quick action: Start new conversation"""
        import webbrowser
        try:
            webbrowser.open(f"{self.server_url}?new=true")
            self._notify("New Conversation", "Started a new conversation")
        except Exception as e:
            self.logger.error(f"Failed to start new conversation: {e}")
    
    def _show_recent_conversations(self, icon=None, item=None):
        """Show recent conversations"""
        self._notify("Recent Conversations", "Feature coming soon - will show recent conversation history")
    
    def _show_statistics(self, icon=None, item=None):
        """Show system statistics"""
        stats = f"""WhisperEngine Statistics
        
Server Status: {self._get_server_status()}
Active Connections: {self.status.active_connections}
Conversations Today: {self.status.conversations_today}
Memory Usage: {self.status.memory_usage_mb:.1f} MB
Uptime: {self._get_uptime_text()}

Last Activity: {self.status.last_activity.strftime('%H:%M:%S') if self.status.last_activity else 'None'}
"""
        
        script = f'''
        display dialog "{stats}" with title "WhisperEngine Statistics" buttons {{"OK"}} default button "OK"
        '''
        
        try:
            subprocess.run(["osascript", "-e", script])
        except Exception as e:
            self.logger.error(f"Failed to show statistics: {e}")
    
    def _show_performance(self, icon=None, item=None):
        """Show performance monitor"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            
            perf_info = f"""Performance Monitor
            
CPU Usage: {cpu_percent:.1f}%
Memory Usage: {self.status.memory_usage_mb:.1f} MB
System Memory: {memory_info.percent:.1f}% used
            
Server Response: {'Good' if self.status.server_running else 'Down'}
Update Interval: {self.preferences.get('update_interval', 3)}s
"""
            
            script = f'''
            display dialog "{perf_info}" with title "Performance Monitor" buttons {{"OK"}} default button "OK"
            '''
            subprocess.run(["osascript", "-e", script])
            
        except Exception as e:
            self.logger.error(f"Failed to show performance: {e}")
    
    def _force_status_update(self, icon=None, item=None):
        """Force immediate status update"""
        self._update_status()
        self._update_tray_icon()
        self._notify("Status Updated", "System status refreshed")
    
    # Notification helper
    def _notify(self, title: str, message: str):
        """Send system notification"""
        if self.preferences.get("show_activity_notifications", True):
            try:
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                subprocess.run(["osascript", "-e", script])
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
    
    # Settings toggles
    def _toggle_notifications(self, icon=None, item=None):
        """Toggle notification preference"""
        self.preferences["show_activity_notifications"] = not self.preferences.get("show_activity_notifications", True)
        self._save_preferences()
        status = "enabled" if self.preferences["show_activity_notifications"] else "disabled"
        self._notify("Settings", f"Notifications {status}")
    
    def _toggle_badge_count(self, icon=None, item=None):
        """Toggle badge count preference"""
        self.preferences["show_badge_count"] = not self.preferences.get("show_badge_count", True)
        self._save_preferences()
        status = "enabled" if self.preferences["show_badge_count"] else "disabled"
        
        # Clear badge if disabled
        if not self.preferences["show_badge_count"]:
            self._update_dock_badge()
        
        self._notify("Settings", f"Badge count {status}")
    
    def _toggle_memory_monitor(self, icon=None, item=None):
        """Toggle memory monitoring preference"""
        self.preferences["show_memory_usage"] = not self.preferences.get("show_memory_usage", True)
        self._save_preferences()
        status = "enabled" if self.preferences["show_memory_usage"] else "disabled"
        self._notify("Settings", f"Memory monitoring {status}")
    
    # Placeholder methods for menu items
    def _export_conversations(self, icon=None, item=None):
        """Export conversations"""
        self._notify("Export", "Conversation export feature coming soon")
    
    def _clear_conversations(self, icon=None, item=None):
        """Clear conversation history"""
        self._notify("Clear History", "Clear history feature coming soon")
    
    def _show_analytics(self, icon=None, item=None):
        """Show conversation analytics"""
        self._notify("Analytics", "Conversation analytics feature coming soon")
    
    def _search_conversations(self, icon=None, item=None):
        """Search conversations"""
        self._notify("Search", "Conversation search feature coming soon")
    
    def _show_preferences(self, icon=None, item=None):
        """Show preferences dialog"""
        self._notify("Preferences", "Advanced preferences dialog coming soon")
    
    def _open_data_folder(self, icon=None, item=None):
        """Open data folder"""
        try:
            data_dir = Path.home() / ".whisperengine"
            data_dir.mkdir(exist_ok=True)
            subprocess.run(["open", str(data_dir)])
        except Exception as e:
            self.logger.error(f"Failed to open data folder: {e}")
    
    def _restart_server(self, icon=None, item=None):
        """Restart server"""
        self._notify("Server", "Server restart feature coming soon")
    
    def _show_about(self, icon=None, item=None):
        """Show about dialog"""
        about_text = f"""WhisperEngine Desktop v2.0.0

AI Conversation Platform with Advanced Intelligence

Current Status:
• Server: {self._get_server_status()}
• Connections: {self.status.active_connections}
• Uptime: {self._get_uptime_text()}
• Memory: {self.status.memory_usage_mb:.1f} MB

Features:
• Advanced conversation memory
• Emotional intelligence integration
• Real-time performance monitoring
• Native macOS integration

© 2025 WhisperEngine AI"""
        
        script = f'''
        display dialog "{about_text}" with title "About WhisperEngine" buttons {{"OK"}} default button "OK"
        '''
        
        try:
            subprocess.run(["osascript", "-e", script])
        except Exception as e:
            self.logger.error(f"Failed to show about: {e}")
    
    def _quit_application(self, icon=None, item=None):
        """Quit application"""
        script = '''
        display dialog "Are you sure you want to quit WhisperEngine?" with title "Quit Application" buttons {"Cancel", "Quit"} default button "Cancel"
        '''
        
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            if result.returncode == 0 and "Quit" in result.stdout:
                self._notify("WhisperEngine", "Shutting down...")
                self.stop()
                if self.app_instance:
                    self.app_instance.cleanup()
        except Exception as e:
            self.logger.error(f"Failed to quit application: {e}")
    
    def run(self):
        """Run the enhanced tray"""
        if self.tray_icon and TRAY_AVAILABLE:
            self.tray_icon.run()
    
    def stop(self):
        """Stop the enhanced tray"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()


def create_enhanced_macos_tray(app_instance, host: str = "127.0.0.1", port: int = 8080) -> Optional[EnhancedMacOSTray]:
    """
    Create enhanced macOS tray integration
    
    Args:
        app_instance: Reference to main app instance
        host: Server host
        port: Server port
        
    Returns:
        EnhancedMacOSTray instance or None if not available
    """
    if not TRAY_AVAILABLE:
        logging.getLogger(__name__).warning("Enhanced tray not available - pystray/PIL not installed")
        return None
    
    if sys.platform != "darwin":
        logging.getLogger(__name__).warning("Enhanced tray only available on macOS")
        return None
    
    try:
        return EnhancedMacOSTray(app_instance, host, port)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create enhanced tray: {e}")
        return None


def is_enhanced_tray_available() -> bool:
    """Check if enhanced tray functionality is available"""
    return TRAY_AVAILABLE and sys.platform == "darwin"