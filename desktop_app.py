#!/usr/bin/env python3
"""
WhisperEngine Desktop App Entry Point
Launches the web UI server and opens browser for desktop app experience.
"""

import asyncio
import os
import sys
import logging
import signal
import threading
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.web_ui import create_web_ui
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.ui.system_tray import create_system_tray, is_tray_available
from src.ui.macos_menu_bar import create_macos_menu_bar, is_macos_menu_available
from src.ui.macos_dock_integration import create_dock_badge_manager, is_dock_integration_available
from src.ui.macos_window_manager import create_window_manager, is_window_management_available


class WhisperEngineDesktopApp:
    """Desktop application launcher for WhisperEngine"""
    
    def __init__(self):
        self.web_ui = None
        self.server = None  # Store server reference for graceful shutdown
        self.running = False
        self.host = "127.0.0.1"
        self.port = 8080
        self.system_tray = None
        self.macos_menu_bar = None
        self.dock_badge_manager = None
        self.window_manager = None
        self.enable_tray = True  # Can be controlled via env var
        self.preferences = self._load_preferences()
        
    def setup_logging(self):
        """Setup logging for desktop app"""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Suppress uvicorn access logs for cleaner output
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    def _load_preferences(self):
        """Load user preferences from file"""
        import json
        prefs_file = Path.home() / ".whisperengine" / "preferences.json"
        try:
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load preferences: {e}")
        
        # Default preferences
        return {
            "auto_open_browser": True,
            "show_notifications": True,
            "start_minimized": False
        }
    
    def _open_browser_delayed(self):
        """Open browser after a short delay"""
        import threading
        import time
        import webbrowser
        
        def delayed_open():
            time.sleep(2)  # Wait for server to fully start
            try:
                webbrowser.open(f"http://{self.host}:{self.port}")
                logging.info("Auto-opened browser for chat interface")
            except Exception as e:
                logging.error(f"Failed to auto-open browser: {e}")
        
        thread = threading.Thread(target=delayed_open, daemon=True)
        thread.start()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.system_tray:
                self.system_tray.stop()
            if self.macos_menu_bar:
                self.macos_menu_bar.stop()
            if self.dock_badge_manager:
                self.dock_badge_manager.stop()
            if self.window_manager:
                self.window_manager.cleanup()
            if self.server:
                self.server.should_exit = True
        except Exception as e:
            logging.error(f"Cleanup error: {e}")
    
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print("\nReceived shutdown signal...")
            print("Shutting down WhisperEngine gracefully...")
            self.running = False
            
            # Stop system tray immediately
            if self.system_tray:
                try:
                    self.system_tray.stop()
                    print("✅ System tray stopped")
                except Exception as e:
                    print(f"⚠️  System tray cleanup error: {e}")
            
            print("✅ WhisperEngine shutdown complete")
            print("Goodbye!")
            
            # Force exit
            os._exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def setup_async_signal_handlers(self):
        """Setup async signal handlers that work with uvicorn"""
        import asyncio
        
        def shutdown_handler():
            print("\nReceived shutdown signal...")
            print("Shutting down WhisperEngine gracefully...")
            self.running = False
            
            # Stop system tray
            if self.system_tray:
                try:
                    self.system_tray.stop()
                    print("✅ System tray stopped")
                except Exception as e:
                    print(f"⚠️  System tray cleanup error: {e}")
            
            # Stop macOS integrations
            if self.macos_menu_bar:
                try:
                    self.macos_menu_bar.stop()
                    print("✅ macOS menu bar stopped")
                except Exception as e:
                    print(f"⚠️  macOS menu bar cleanup error: {e}")
                    
            if self.dock_badge_manager:
                try:
                    self.dock_badge_manager.stop()
                    print("✅ Dock badge manager stopped")
                except Exception as e:
                    print(f"⚠️  Dock badge cleanup error: {e}")
                    
            if self.window_manager:
                try:
                    self.window_manager.cleanup()
                    print("✅ Window manager stopped")
                except Exception as e:
                    print(f"⚠️  Window manager cleanup error: {e}")
            
            print("✅ WhisperEngine shutdown complete")
            print("Goodbye!")
            
            # Create a task to exit gracefully
            asyncio.create_task(self._async_shutdown())
        
        # Set up asyncio signal handlers
        if hasattr(asyncio, 'get_running_loop'):
            try:
                loop = asyncio.get_running_loop()
                for sig in [signal.SIGINT, signal.SIGTERM]:
                    loop.add_signal_handler(sig, shutdown_handler)
            except NotImplementedError:
                # Fallback for Windows or other platforms
                signal.signal(signal.SIGINT, lambda s, f: shutdown_handler())
                signal.signal(signal.SIGTERM, lambda s, f: shutdown_handler())
    
    async def _async_shutdown(self):
        """Async shutdown helper"""
        await asyncio.sleep(0.1)  # Brief delay to let messages print
        os._exit(0)
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        self.running = False
        
        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()
        
        sys.exit(0)
    
    async def initialize_components(self):
        """Create and configure application components"""
        try:
            # Force SQLite for desktop mode
            os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
            os.environ['WHISPERENGINE_MODE'] = 'desktop'
            
            # Initialize configuration manager
            config_manager = AdaptiveConfigManager()
            
            # Initialize database manager (optional for desktop)
            db_manager = None
            try:
                db_manager = DatabaseIntegrationManager()
                logging.info("✅ Database initialized with SQLite for desktop mode")
            except Exception as e:
                logging.warning(f"Database initialization failed: {e}")
            
            # Create web UI
            self.web_ui = create_web_ui(db_manager, config_manager)
            
            logging.info("WhisperEngine components initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            raise
    
    def check_port_availability(self):
        """Check if the port is available"""
        import socket
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, self.port))
                return True
            except OSError:
                return False
    
    def find_available_port(self):
        """Find an available port starting from default"""
        for port in range(self.port, self.port + 100):
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    self.port = port
                    return port
            except OSError:
                continue
        
        raise RuntimeError("No available ports found")
    
    async def start_server(self):
        """Start the web server and system tray"""
        try:
            import uvicorn
            
            # Auto-open browser if configured
            if self.preferences.get("auto_open_browser", True):
                self._open_browser_delayed()
            
            # Create enhanced system tray/menu bar for macOS
            if self.enable_tray:
                if is_macos_menu_available():
                    print("🍎 Creating macOS enhanced menu bar...")
                    self.macos_menu_bar = create_macos_menu_bar(self, self.host, self.port)
                    if self.macos_menu_bar:
                        # Run the macOS menu bar in background thread
                        import threading
                        tray_thread = threading.Thread(target=self.macos_menu_bar.run, daemon=True)
                        tray_thread.start()
                        print("✅ macOS menu bar created")
                        
                    # Add dock badge integration
                    if is_dock_integration_available():
                        print("🏷️ Creating dock badge integration...")
                        self.dock_badge_manager = create_dock_badge_manager(self, self.host, self.port)
                        if self.dock_badge_manager:
                            print("✅ Dock badge integration enabled")
                    
                    # Add window management
                    if is_window_management_available():
                        print("🪟 Creating window management...")
                        self.window_manager = create_window_manager(self, self.host, self.port)
                        if self.window_manager:
                            print("✅ Native window management enabled")
                            
                elif is_tray_available():
                    print("🔄 Creating system tray...")
                    self.system_tray = create_system_tray(self, self.host, self.port)
                    if self.system_tray:
                        print("✅ System tray created")
            
            print(f"🌐 Starting web interface at http://{self.host}:{self.port}")
            print("📱 Check your system tray for WhisperEngine icon")
            print("💬 Open your browser to start chatting!")
            
            if not self.web_ui:
                raise RuntimeError("Web UI not initialized")
            
            # Create uvicorn config
            config = uvicorn.Config(
                self.web_ui.app,  # Use the FastAPI app from WhisperEngineWebUI
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=False  # Reduce noise
            )
            
            # Create and run server
            server = uvicorn.Server(config)
            self.server = server
            
            await server.serve()
            
        except Exception as e:
            logging.error(f"Server startup failed: {e}")
            raise
    
    async def run_async(self):
        """Run the desktop application async"""
        try:
            # Setup
            self.setup_logging()
            self.setup_signal_handlers()
            
            # Check for tray preference
            self.enable_tray = os.getenv("ENABLE_SYSTEM_TRAY", "true").lower() == "true"
            
            print("🤖 WhisperEngine Desktop App")
            print("=" * 40)
            print("Initializing AI conversation platform...")
            
            if self.enable_tray and is_tray_available():
                print("🔄 System tray integration enabled")
            elif self.enable_tray:
                print("⚠️  System tray requested but not available (missing pystray/Pillow)")
            
            # Create components
            await self.initialize_components()
            
            # Start server
            await self.start_server()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            logging.error(f"Application error: {e}")
            print(f"\nError: {e}")
            print("Please check the logs for more details.")
        finally:
            # Ensure cleanup
            if self.system_tray:
                self.system_tray.stop()
    
    def run(self):
        """Run the desktop application"""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            logging.error(f"Application error: {e}")
            print(f"\nError: {e}")
            print("Please check the logs for more details.")
            sys.exit(1)


def main():
    """Main entry point"""
    app = WhisperEngineDesktopApp()
    app.run()


if __name__ == "__main__":
    main()