#!/usr/bin/env python3
"""
Enhanced macOS System Tray Integration for WhisperEngine
Provides advanced dock integration, badge notifications, and real-time status updates.
"""

import json
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


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
    last_activity: datetime | None = None


class MacOSDockBadgeManager:
    """Manages macOS dock badge notifications and system integration"""

    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize dock badge manager

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
        self.active_conversations = {}
        self.recent_activities = []
        self.running = False

        # Performance metrics
        self.start_time = datetime.now()
        self.last_status_update = datetime.now()
        self.update_interval = 3  # seconds

        # Configuration
        self.preferences = self._load_preferences()

        # Start monitoring
        self._start_monitoring()

    def _load_preferences(self):
        """Load preferences from file"""
        prefs_file = Path.home() / ".whisperengine" / "dock_preferences.json"
        try:
            if prefs_file.exists():
                with open(prefs_file) as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load dock preferences: {e}")

        # Default preferences
        return {
            "show_badge_count": True,
            "show_activity_notifications": True,
            "update_interval": 3,
            "bounce_on_activity": True,
            "critical_notifications": True,
        }

    def _save_preferences(self):
        """Save preferences to file"""
        prefs_file = Path.home() / ".whisperengine" / "dock_preferences.json"
        try:
            prefs_file.parent.mkdir(exist_ok=True)
            with open(prefs_file, "w") as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save dock preferences: {e}")

    def _start_monitoring(self):
        """Start background monitoring thread"""

        def monitor():
            self.running = True
            while self.running:
                try:
                    self._update_status()
                    self._update_dock_badge()
                    self._update_dock_icon()
                    time.sleep(self.preferences.get("update_interval", 3))
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(10)  # Wait longer on error

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.logger.info("Started dock badge monitoring")

    def _update_status(self):
        """Update system status"""
        try:
            import psutil
            import requests

            # Check server health
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                self.status.server_running = response.status_code == 200

                # Try to get more detailed info if available
                if response.status_code == 200:
                    try:
                        data = response.json()
                        prev_connections = self.status.active_connections
                        self.status.active_connections = data.get("active_connections", 0)
                        self.status.conversations_today = data.get("conversations_today", 0)

                        # Check for new activity
                        if self.status.active_connections > prev_connections:
                            self._on_new_activity()

                    except:
                        pass

            except Exception:
                self.status.server_running = False
                self.status.active_connections = 0

            # Update memory usage
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
            self._clear_dock_badge()
            return

        try:
            badge_count = self.status.active_connections

            if badge_count > 0:
                # Set dock badge using AppleScript
                script = f"""
                tell application "System Events"
                    try
                        set frontmostApp to name of first application process whose frontmost is true
                        if frontmostApp is not "WhisperEngine" then
                            set dock_items to dock tiles of dock preferences
                            repeat with dock_item in dock_items
                                if name of dock_item contains "WhisperEngine" then
                                    set badge text of dock_item to "{badge_count}"
                                    exit repeat
                                end if
                            end repeat
                        end if
                    on error errMsg
                        -- Fallback method
                        tell application "Dock" to set badge text of (first dock tile whose name contains "WhisperEngine") to "{badge_count}"
                    end try
                end tell
                """
                subprocess.run(["osascript", "-e", script], capture_output=True)
                self.logger.debug(f"Updated dock badge to {badge_count}")
            else:
                self._clear_dock_badge()

        except Exception as e:
            self.logger.error(f"Failed to update dock badge: {e}")

    def _clear_dock_badge(self):
        """Clear dock icon badge"""
        try:
            script = """
            tell application "System Events"
                try
                    set dock_items to dock tiles of dock preferences
                    repeat with dock_item in dock_items
                        if name of dock_item contains "WhisperEngine" then
                            set badge text of dock_item to ""
                            exit repeat
                        end if
                    end repeat
                on error
                    -- Fallback method
                    tell application "Dock" to set badge text of (first dock tile whose name contains "WhisperEngine") to ""
                end try
            end tell
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)
            self.logger.debug("Cleared dock badge")
        except Exception as e:
            self.logger.error(f"Failed to clear dock badge: {e}")

    def _update_dock_icon(self):
        """Update dock icon state based on status"""
        try:
            # Update dock icon overlay or progress indicator
            if self.status.server_running:
                if self.status.active_connections > 0:
                    # Active state
                    self._set_dock_progress(
                        self.status.active_connections / 10.0
                    )  # Max 10 connections
                else:
                    # Idle state
                    self._set_dock_progress(0.0)
            else:
                # Error state
                self._set_dock_progress(-1.0)  # Error indicator

        except Exception as e:
            self.logger.error(f"Failed to update dock icon: {e}")

    def _set_dock_progress(self, progress: float):
        """Set dock icon progress indicator"""
        try:
            if progress < 0:
                # Error state - make icon bounce
                if self.preferences.get("bounce_on_activity", True):
                    script = """
                    tell application "System Events"
                        try
                            set dock_items to dock tiles of dock preferences
                            repeat with dock_item in dock_items
                                if name of dock_item contains "WhisperEngine" then
                                    -- Set error badge
                                    set badge text of dock_item to "⚠️"
                                    exit repeat
                                end if
                            end repeat
                        end try
                    end tell
                    """
                    subprocess.run(["osascript", "-e", script], capture_output=True)
            elif progress > 0:
                # Active state with progress
                percentage = min(100, int(progress * 100))
                self.logger.debug(f"Setting dock progress to {percentage}%")
            else:
                # Clear progress
                pass

        except Exception as e:
            self.logger.error(f"Failed to set dock progress: {e}")

    def _on_new_activity(self):
        """Handle new activity detection"""
        try:
            if self.preferences.get("show_activity_notifications", True):
                self._notify(
                    "New Activity",
                    f"New conversation started ({self.status.active_connections} active)",
                )

            if self.preferences.get("bounce_on_activity", True):
                self._bounce_dock_icon()

        except Exception as e:
            self.logger.error(f"Failed to handle new activity: {e}")

    def _bounce_dock_icon(self):
        """Make dock icon bounce to get attention"""
        try:
            script = """
            tell application "System Events"
                try
                    set dock_items to dock tiles of dock preferences
                    repeat with dock_item in dock_items
                        if name of dock_item contains "WhisperEngine" then
                            -- Simulate bounce by temporarily changing badge
                            set original_badge to badge text of dock_item
                            set badge text of dock_item to "•"
                            delay 0.2
                            set badge text of dock_item to original_badge
                            exit repeat
                        end if
                    end repeat
                end try
            end tell
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)
            self.logger.debug("Bounced dock icon")
        except Exception as e:
            self.logger.error(f"Failed to bounce dock icon: {e}")

    def _notify(self, title: str, message: str, critical: bool = False):
        """Send system notification"""
        try:
            sound = 'sound name "Purr"' if critical else ""
            script = f"""
            display notification "{message}" with title "{title}" {sound}
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)
            self.logger.debug(f"Sent notification: {title}")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")

    def show_quick_stats(self):
        """Show quick stats in notification"""
        uptime = self._get_uptime_text()
        stats_message = f"""Server: {'Running' if self.status.server_running else 'Stopped'}
Connections: {self.status.active_connections}
Uptime: {uptime}
Memory: {self.status.memory_usage_mb:.1f} MB"""

        self._notify("WhisperEngine Stats", stats_message)

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

    def toggle_badge_count(self):
        """Toggle badge count display"""
        self.preferences["show_badge_count"] = not self.preferences.get("show_badge_count", True)
        self._save_preferences()

        if not self.preferences["show_badge_count"]:
            self._clear_dock_badge()

        status = "enabled" if self.preferences["show_badge_count"] else "disabled"
        self._notify("Settings", f"Badge count {status}")

    def toggle_notifications(self):
        """Toggle activity notifications"""
        self.preferences["show_activity_notifications"] = not self.preferences.get(
            "show_activity_notifications", True
        )
        self._save_preferences()

        status = "enabled" if self.preferences["show_activity_notifications"] else "disabled"
        self._notify("Settings", f"Activity notifications {status}")

    def emergency_clear(self):
        """Emergency clear all dock modifications"""
        try:
            self._clear_dock_badge()
            script = """
            tell application "System Events"
                try
                    set dock_items to dock tiles of dock preferences
                    repeat with dock_item in dock_items
                        if name of dock_item contains "WhisperEngine" then
                            set badge text of dock_item to ""
                            exit repeat
                        end if
                    end repeat
                end try
            end tell
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)
            self.logger.info("Emergency dock clear completed")
        except Exception as e:
            self.logger.error(f"Emergency clear failed: {e}")

    def stop(self):
        """Stop the dock badge manager"""
        self.running = False
        self._clear_dock_badge()
        self.logger.info("Stopped dock badge monitoring")


def create_dock_badge_manager(app_instance, host: str = "127.0.0.1", port: int = 8080):
    """
    Create macOS dock badge manager

    Args:
        app_instance: Reference to main app instance
        host: Server host
        port: Server port

    Returns:
        MacOSDockBadgeManager instance or None if not on macOS
    """
    if sys.platform != "darwin":
        logging.getLogger(__name__).warning("Dock badge manager only available on macOS")
        return None

    try:
        return MacOSDockBadgeManager(app_instance, host, port)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create dock badge manager: {e}")
        return None


def is_dock_integration_available() -> bool:
    """Check if dock integration functionality is available"""
    return sys.platform == "darwin"
