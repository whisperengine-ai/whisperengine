#!/usr/bin/env python3
"""
Native macOS Window Management for WhisperEngine
Provides native window controls, multi-window support, and proper macOS integration
"""

import os
import sys
import logging
import subprocess
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WindowInfo:
    """Information about a window"""
    window_id: str
    title: str
    url: str
    created_at: datetime
    last_active: datetime
    position: Tuple[int, int] = (100, 100)
    size: Tuple[int, int] = (1200, 800)
    is_minimized: bool = False
    is_fullscreen: bool = False


class MacOSWindowManager:
    """Manages native macOS windows for WhisperEngine"""
    
    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize window manager
        
        Args:
            app_instance: Reference to main app instance  
            host: Server host
            port: Server port
        """
        self.app_instance = app_instance
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        
        # Window tracking
        self.windows: Dict[str, WindowInfo] = {}
        self.active_window: Optional[str] = None
        self.window_counter = 0
        
        # Settings
        self.preferences = self._load_preferences()
        
        # Initialize main window
        self._create_main_window()
    
    def _load_preferences(self) -> Dict:
        """Load window preferences"""
        prefs_file = Path.home() / ".whisperengine" / "window_preferences.json"
        try:
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load window preferences: {e}")
        
        return {
            "default_width": 1200,
            "default_height": 800,
            "remember_positions": True,
            "auto_restore_windows": True,
            "multi_window_enabled": True,
            "minimize_to_dock": True,
            "native_fullscreen": True,
            "window_transparency": 0.95
        }
    
    def _save_preferences(self):
        """Save window preferences"""
        prefs_file = Path.home() / ".whisperengine" / "window_preferences.json"
        try:
            prefs_file.parent.mkdir(exist_ok=True)
            with open(prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save window preferences: {e}")
    
    def _create_main_window(self):
        """Create the main application window"""
        try:
            window_id = self._generate_window_id()
            
            # Create window info
            window_info = WindowInfo(
                window_id=window_id,
                title="WhisperEngine - AI Chat",
                url=self.base_url,
                created_at=datetime.now(),
                last_active=datetime.now(),
                position=(100, 100),
                size=(self.preferences.get("default_width", 1200), 
                      self.preferences.get("default_height", 800))
            )
            
            self.windows[window_id] = window_info
            self.active_window = window_id
            
            # Launch the window using system default browser
            self._launch_window(window_info)
            
            self.logger.info(f"Created main window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create main window: {e}")
    
    def _generate_window_id(self) -> str:
        """Generate unique window ID"""
        self.window_counter += 1
        return f"whisper_window_{self.window_counter}_{int(time.time())}"
    
    def _launch_window(self, window_info: WindowInfo):
        """Launch a window using native macOS capabilities"""
        try:
            # Use AppleScript to open browser with specific window properties
            script = f'''
            tell application "Safari"
                activate
                set newDocument to make new document with properties {{URL:"{window_info.url}"}}
                set windowInstance to window 1
                set bounds of windowInstance to {{{window_info.position[0]}, {window_info.position[1]}, {window_info.position[0] + window_info.size[0]}, {window_info.position[1] + window_info.size[1]}}}
                set name of newDocument to "{window_info.title}"
            end tell
            '''
            
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            if result.returncode != 0:
                # Fallback to default browser
                import webbrowser
                webbrowser.open(window_info.url)
                self.logger.warning("Fell back to default browser for window launch")
            else:
                self.logger.info(f"Launched window via Safari: {window_info.window_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to launch window: {e}")
            # Final fallback
            import webbrowser
            webbrowser.open(window_info.url)
    
    def create_new_window(self, conversation_id: Optional[str] = None) -> str:
        """Create a new conversation window"""
        try:
            window_id = self._generate_window_id()
            
            # Determine URL and title
            if conversation_id:
                url = f"{self.base_url}?conversation={conversation_id}"
                title = f"WhisperEngine - Conversation {conversation_id[:8]}"
            else:
                url = f"{self.base_url}?new=true"
                title = "WhisperEngine - New Conversation"
            
            # Calculate position (offset from main window)
            main_window = None
            if self.active_window:
                main_window = self.windows.get(self.active_window)
            
            if main_window:
                x_offset = len(self.windows) * 30
                y_offset = len(self.windows) * 30
                position = (main_window.position[0] + x_offset, main_window.position[1] + y_offset)
            else:
                position = (100, 100)
            
            # Create window info
            window_info = WindowInfo(
                window_id=window_id,
                title=title,
                url=url,
                created_at=datetime.now(),
                last_active=datetime.now(),
                position=position,
                size=(self.preferences.get("default_width", 1200), 
                      self.preferences.get("default_height", 800))
            )
            
            self.windows[window_id] = window_info
            self.active_window = window_id
            
            # Launch the window
            self._launch_window(window_info)
            
            self.logger.info(f"Created new window: {window_id}")
            return window_id
            
        except Exception as e:
            self.logger.error(f"Failed to create new window: {e}")
            return ""
    
    def minimize_window(self, window_id: str):
        """Minimize window to dock"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            # Use AppleScript to minimize Safari window
            script = f'''
            tell application "Safari"
                repeat with theWindow in windows
                    if name of current tab of theWindow is "{window_info.title}" then
                        set miniaturized of theWindow to true
                        exit repeat
                    end if
                end repeat
            end tell
            '''
            
            subprocess.run(["osascript", "-e", script], capture_output=True)
            window_info.is_minimized = True
            
            self.logger.info(f"Minimized window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to minimize window: {e}")
    
    def restore_window(self, window_id: str):
        """Restore window from dock"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            # Use AppleScript to restore Safari window
            script = f'''
            tell application "Safari"
                repeat with theWindow in windows
                    if name of current tab of theWindow is "{window_info.title}" then
                        set miniaturized of theWindow to false
                        set index of theWindow to 1
                        exit repeat
                    end if
                end repeat
                activate
            end tell
            '''
            
            subprocess.run(["osascript", "-e", script], capture_output=True)
            window_info.is_minimized = False
            window_info.last_active = datetime.now()
            self.active_window = window_id
            
            self.logger.info(f"Restored window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to restore window: {e}")
    
    def toggle_fullscreen(self, window_id: str):
        """Toggle fullscreen mode for window"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            script = f'''
            tell application "Safari"
                repeat with theWindow in windows
                    if name of current tab of theWindow is "{window_info.title}" then
                        tell theWindow
                            if not (get index is 1) then
                                set index to 1
                            end if
                        end tell
                        exit repeat
                    end if
                end repeat
            end tell
            '''
            
            subprocess.run(["osascript", "-e", script], capture_output=True)
            window_info.is_fullscreen = not window_info.is_fullscreen
            
            self.logger.info(f"Toggled fullscreen for window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to toggle fullscreen: {e}")
    
    def close_window(self, window_id: str):
        """Close a specific window"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            # Use AppleScript to close Safari tab/window
            script = f'''
            tell application "Safari"
                repeat with theWindow in windows
                    if name of current tab of theWindow is "{window_info.title}" then
                        close current tab of theWindow
                        exit repeat
                    end if
                end repeat
            end tell
            '''
            
            subprocess.run(["osascript", "-e", script], capture_output=True)
            
            # Remove from tracking
            del self.windows[window_id]
            
            # Update active window
            if self.active_window == window_id:
                if self.windows:
                    self.active_window = list(self.windows.keys())[-1]
                else:
                    self.active_window = None
            
            self.logger.info(f"Closed window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to close window: {e}")
    
    def get_window_list(self) -> List[Dict]:
        """Get list of all windows"""
        return [
            {
                "id": window_id,
                "title": info.title,
                "url": info.url,
                "created_at": info.created_at.isoformat(),
                "last_active": info.last_active.isoformat(),
                "is_minimized": info.is_minimized,
                "is_fullscreen": info.is_fullscreen,
                "is_active": window_id == self.active_window
            }
            for window_id, info in self.windows.items()
        ]
    
    def focus_window(self, window_id: str):
        """Bring window to front"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            # Restore if minimized
            if window_info.is_minimized:
                self.restore_window(window_id)
            else:
                # Just bring to front
                script = f'''
                tell application "Safari"
                    repeat with theWindow in windows
                        if name of current tab of theWindow is "{window_info.title}" then
                            set index of theWindow to 1
                            exit repeat
                        end if
                    end repeat
                    activate
                end tell
                '''
                
                subprocess.run(["osascript", "-e", script], capture_output=True)
            
            window_info.last_active = datetime.now()
            self.active_window = window_id
            
            self.logger.info(f"Focused window: {window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to focus window: {e}")
    
    def save_window_positions(self):
        """Save current window positions for restoration"""
        try:
            positions = {}
            for window_id, window_info in self.windows.items():
                positions[window_id] = {
                    "position": window_info.position,
                    "size": window_info.size,
                    "is_minimized": window_info.is_minimized,
                    "is_fullscreen": window_info.is_fullscreen,
                    "title": window_info.title,
                    "url": window_info.url
                }
            
            positions_file = Path.home() / ".whisperengine" / "window_positions.json"
            positions_file.parent.mkdir(exist_ok=True)
            
            with open(positions_file, 'w') as f:
                json.dump(positions, f, indent=2)
                
            self.logger.info("Saved window positions")
            
        except Exception as e:
            self.logger.error(f"Failed to save window positions: {e}")
    
    def restore_window_positions(self):
        """Restore saved window positions"""
        try:
            positions_file = Path.home() / ".whisperengine" / "window_positions.json"
            
            if not positions_file.exists():
                return
            
            with open(positions_file, 'r') as f:
                positions = json.load(f)
            
            for window_data in positions.values():
                if self.preferences.get("auto_restore_windows", True):
                    # Create new window with saved properties
                    window_id = self._generate_window_id()
                    window_info = WindowInfo(
                        window_id=window_id,
                        title=window_data["title"],
                        url=window_data["url"],
                        created_at=datetime.now(),
                        last_active=datetime.now(),
                        position=tuple(window_data["position"]),
                        size=tuple(window_data["size"]),
                        is_minimized=window_data.get("is_minimized", False),
                        is_fullscreen=window_data.get("is_fullscreen", False)
                    )
                    
                    self.windows[window_id] = window_info
                    self._launch_window(window_info)
            
            self.logger.info("Restored window positions")
            
        except Exception as e:
            self.logger.error(f"Failed to restore window positions: {e}")
    
    def cleanup(self):
        """Cleanup window manager"""
        try:
            # Save current positions
            if self.preferences.get("remember_positions", True):
                self.save_window_positions()
            
            # Close all windows
            for window_id in list(self.windows.keys()):
                self.close_window(window_id)
            
            self.logger.info("Window manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Window manager cleanup error: {e}")


def create_window_manager(app_instance, host: str = "127.0.0.1", port: int = 8080) -> Optional[MacOSWindowManager]:
    """
    Create macOS window manager
    
    Args:
        app_instance: Reference to main app
        host: Server host
        port: Server port
        
    Returns:
        MacOSWindowManager instance or None if not on macOS
    """
    if sys.platform != "darwin":
        logging.getLogger(__name__).warning("Window manager only available on macOS")
        return None
    
    try:
        return MacOSWindowManager(app_instance, host, port)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create window manager: {e}")
        return None


def is_window_management_available() -> bool:
    """Check if window management is available"""
    return sys.platform == "darwin"