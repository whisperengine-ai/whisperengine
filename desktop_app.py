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


class WhisperEngineDesktopApp:
    """Desktop application launcher for WhisperEngine"""
    
    def __init__(self):
        self.web_ui = None
        self.server = None  # Store server reference for graceful shutdown
        self.running = False
        self.host = "127.0.0.1"
        self.port = 8080
        self.system_tray = None
        self.enable_tray = True  # Can be controlled via env var
        
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
    
    def create_components(self):
        """Create and configure application components"""
        try:
            # Initialize configuration manager
            config_manager = AdaptiveConfigManager()
            
            # Initialize database manager (optional for desktop)
            db_manager = None
            try:
                db_manager = DatabaseIntegrationManager()
            except Exception as e:
                logging.warning(f"Database initialization failed (optional): {e}")
            
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
        """Start the web UI server"""
        try:
            # Setup async signal handlers first
            await self.setup_async_signal_handlers()
            
            if not self.check_port_availability():
                old_port = self.port
                self.find_available_port()
                logging.warning(f"Port {old_port} unavailable, using port {self.port}")
            
            # Setup system tray if available and enabled
            if self.enable_tray and is_tray_available():
                self.system_tray = create_system_tray(self, self.host, self.port)
                if self.system_tray and self.system_tray.start_background():
                    logging.info("System tray enabled - app will run in background")
                    print("✅ System tray enabled - minimize to tray available")
                else:
                    logging.warning("Failed to setup system tray")
            else:
                logging.info("System tray disabled or not available")
            
            logging.info(f"Starting WhisperEngine on http://{self.host}:{self.port}")
            
            # Only open browser automatically if no system tray (for better UX)
            auto_open = not (self.system_tray and self.system_tray.running)
            if auto_open:
                logging.info("Opening browser... (Close this terminal to quit)")
            else:
                logging.info("Access via system tray or visit http://{}:{}".format(self.host, self.port))
            
            if self.web_ui is None:
                raise RuntimeError("Web UI not initialized")
            
            self.running = True
            print(f"🚀 Starting server on http://{self.host}:{self.port}")
            if auto_open:
                print("📱 Browser will open automatically")
                print("💡 Press Ctrl+C to quit")
            else:
                print("💡 Access via system tray or press Ctrl+C to quit")
            
            await self.web_ui.start(self.host, self.port, open_browser=auto_open)
            
        except KeyboardInterrupt:
            logging.info("Received shutdown signal")
        except Exception as e:
            logging.error(f"Server error: {e}")
            raise
    
    def run(self):
        """Run the desktop application"""
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
            self.create_components()
            
            # Start server
            asyncio.run(self.start_server())
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            logging.error(f"Application error: {e}")
            print(f"\nError: {e}")
            print("Please check the logs for more details.")
            sys.exit(1)
        finally:
            # Ensure cleanup
            if self.system_tray:
                self.system_tray.stop()


def main():
    """Main entry point"""
    app = WhisperEngineDesktopApp()
    app.run()


if __name__ == "__main__":
    main()