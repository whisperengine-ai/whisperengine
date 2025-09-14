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


class WhisperEngineDesktopApp:
    """Desktop application launcher for WhisperEngine"""
    
    def __init__(self):
        self.web_ui = None
        self.running = False
        self.host = "127.0.0.1"
        self.port = 8080
        
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
            print("\nShutting down WhisperEngine...")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
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
            if not self.check_port_availability():
                old_port = self.port
                self.find_available_port()
                logging.warning(f"Port {old_port} unavailable, using port {self.port}")
            
            logging.info(f"Starting WhisperEngine on http://{self.host}:{self.port}")
            logging.info("Opening browser... (Close this terminal to quit)")
            
            if self.web_ui is None:
                raise RuntimeError("Web UI not initialized")
            
            self.running = True
            await self.web_ui.start(self.host, self.port, open_browser=True)
            
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
            
            print("🤖 WhisperEngine Desktop App")
            print("=" * 40)
            print("Initializing AI conversation platform...")
            
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


def main():
    """Main entry point"""
    app = WhisperEngineDesktopApp()
    app.run()


if __name__ == "__main__":
    main()