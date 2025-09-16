#!/usr/bin/env python3
"""
WhisperEngine System Tray Integration
Provides system tray functionality for background operation with convenient access.
"""

import logging
import os
import sys
import threading
import webbrowser

try:
    import pystray
    from PIL import Image, ImageDraw

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    pystray = None
    Image = None
    ImageDraw = None


class WhisperEngineSystemTray:
    """System tray integration for WhisperEngine desktop app"""

    def __init__(self, app_instance, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize system tray

        Args:
            app_instance: Reference to the main app instance
            host: Server host address
            port: Server port number
        """
        self.app_instance = app_instance
        self.host = host
        self.port = port
        self.tray_icon = None
        self.running = False
        self.logger = logging.getLogger(__name__)

        if not TRAY_AVAILABLE:
            self.logger.warning("System tray not available - pystray/Pillow not installed")

    def create_tray_icon(self):
        """Create a simple tray icon"""
        if not TRAY_AVAILABLE or not Image or not ImageDraw:
            return None

        try:
            # Create a simple icon with "W" for WhisperEngine
            size = (64, 64)
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            # Draw a circle background
            margin = 8
            draw.ellipse(
                [margin, margin, size[0] - margin, size[1] - margin],
                fill=(45, 55, 72, 255),  # Dark gray-blue
                outline=(99, 102, 241, 255),  # Purple outline
                width=3,
            )

            # Draw "W" in the center
            text = "W"
            # Calculate text position to center it
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2 - 2

            draw.text((x, y), text, fill=(255, 255, 255, 255))

            return image

        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {e}")
            return None

    def open_whisperengine(self, icon=None, item=None):
        """Open WhisperEngine in browser"""
        try:
            url = f"http://{self.host}:{self.port}"
            webbrowser.open(url)
            self.logger.info(f"Opened WhisperEngine: {url}")
        except Exception as e:
            self.logger.error(f"Failed to open WhisperEngine: {e}")

    def show_about(self, icon=None, item=None):
        """Show about information"""
        try:
            # On macOS, we can use osascript for native dialogs
            if sys.platform == "darwin":
                os.system(
                    f"""
                osascript -e 'display dialog "WhisperEngine Desktop App\\n\\nAI Conversation Platform\\nRunning on http://{self.host}:{self.port}\\n\\nPowered by Advanced AI Intelligence" with title "About WhisperEngine" buttons {{"OK"}} default button "OK"'
                """
                )
            else:
                # For other platforms, just open in browser
                self.open_whisperengine()
        except Exception as e:
            self.logger.error(f"Failed to show about dialog: {e}")

    def quit_application(self, icon=None, item=None):
        """Quit the entire application"""
        try:
            self.logger.info("Quitting WhisperEngine...")
            self.running = False

            # Stop the tray icon
            if self.tray_icon:
                self.tray_icon.stop()

            # Stop the main application
            if hasattr(self.app_instance, "running"):
                self.app_instance.running = False

            # Force exit
            os._exit(0)

        except Exception as e:
            self.logger.error(f"Error during quit: {e}")
            os._exit(1)

    def create_menu(self):
        """Create the context menu for the tray icon"""
        if not TRAY_AVAILABLE or not pystray:
            return None

        return pystray.Menu(
            pystray.MenuItem("Open WhisperEngine", self.open_whisperengine, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About WhisperEngine", self.show_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_application),
        )

    def setup_tray(self):
        """Setup the system tray icon"""
        if not TRAY_AVAILABLE or not pystray:
            self.logger.warning("Cannot setup tray - dependencies not available")
            return False

        try:
            icon_image = self.create_tray_icon()
            menu = self.create_menu()

            self.tray_icon = pystray.Icon(
                "whisperengine", icon_image, "WhisperEngine - AI Conversation Platform", menu
            )

            self.logger.info("System tray icon created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup system tray: {e}")
            return False

    def run_tray(self):
        """Run the system tray (blocking call)"""
        if not self.tray_icon:
            self.logger.error("Tray icon not initialized")
            return

        try:
            self.running = True
            self.logger.info("Starting system tray...")
            self.tray_icon.run()
        except Exception as e:
            self.logger.error(f"System tray error: {e}")

    def start_background(self):
        """Start the tray in a background thread"""
        if not self.setup_tray():
            return False

        try:
            # Start tray in background thread
            tray_thread = threading.Thread(target=self.run_tray, daemon=True)
            tray_thread.start()

            self.logger.info("System tray started in background")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start background tray: {e}")
            return False

    def stop(self):
        """Stop the system tray"""
        try:
            self.running = False
            if self.tray_icon:
                self.tray_icon.stop()
                self.logger.info("System tray stopped")
        except Exception as e:
            self.logger.error(f"Error stopping tray: {e}")


def is_tray_available() -> bool:
    """Check if system tray functionality is available"""
    return TRAY_AVAILABLE


def create_system_tray(
    app_instance, host: str = "127.0.0.1", port: int = 8080
) -> WhisperEngineSystemTray | None:
    """
    Factory function to create system tray instance

    Args:
        app_instance: Main application instance
        host: Server host
        port: Server port

    Returns:
        WhisperEngineSystemTray instance or None if not available
    """
    if not is_tray_available():
        logging.warning("System tray not available - install pystray and Pillow")
        return None

    return WhisperEngineSystemTray(app_instance, host, port)
