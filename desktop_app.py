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
from src.llm.llm_client import LLMClient
from src.ui.system_tray import create_system_tray, is_tray_available


class WhisperEngineDesktopApp:
    """Desktop application launcher for WhisperEngine"""
    
    def __init__(self):
        self.web_ui = None
        self.running = False
        self.host = "127.0.0.1"
        self.port = 8080
        self.system_tray = None
        self.enable_tray = True  # Can be controlled via env var
        self.server = None
        self.shutdown_event = None
        
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
            
            # If we have an event loop running, create a task to shutdown
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.async_shutdown())
            except RuntimeError:
                # No event loop running, do synchronous shutdown
                self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def async_shutdown(self):
        """Async graceful shutdown"""
        self.running = False
        
        # Stop the server if it's running
        if self.server:
            try:
                self.server.should_exit = True
                # Signal the shutdown event
                if self.shutdown_event:
                    self.shutdown_event.set()
            except Exception as e:
                logging.warning(f"Error stopping server: {e}")
        
        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()
        
        # Stop the event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule a task to stop the loop after a brief delay
            def stop_loop():
                loop.stop()
            loop.call_later(0.1, stop_loop)
        except Exception as e:
            logging.warning(f"Error stopping event loop: {e}")
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        self.running = False
        
        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()
        
        sys.exit(0)
    
    def create_components(self):
        """Create and configure application components with WhisperEngine AI"""
        try:
            # Initialize configuration manager
            config_manager = AdaptiveConfigManager()
            
            # Initialize database manager (optional for desktop)
            db_manager = None
            try:
                db_manager = DatabaseIntegrationManager()
                logging.info("Database integration initialized for full capabilities")
            except Exception as e:
                logging.warning(f"Database initialization failed (running in basic mode): {e}")
            
            # Initialize LLM client for AI capabilities
            llm_client = None
            try:
                llm_client = LLMClient()
                logging.info("LLM client initialized for AI conversations")
            except Exception as e:
                logging.warning(f"LLM client initialization failed (demo mode): {e}")
            
            # Initialize WhisperEngine AI components (like Discord bot does)
            whisperengine_components = {}
            
            # Try to initialize memory manager
            try:
                from src.memory.memory_manager import UserMemoryManager
                memory_manager = UserMemoryManager()
                whisperengine_components['memory_manager'] = memory_manager
                logging.info("WhisperEngine memory manager initialized")
            except Exception as e:
                logging.warning(f"Memory manager initialization failed: {e}")
            
            # Try to initialize external emotion AI
            try:
                from src.emotion.external_api_emotion_ai import ExternalAPIEmotionAI
                external_emotion_ai = ExternalAPIEmotionAI()
                whisperengine_components['external_emotion_ai'] = external_emotion_ai
                logging.info("WhisperEngine external emotion AI initialized")
            except Exception as e:
                logging.warning(f"External emotion AI initialization failed: {e}")
            
            # Try to initialize Phase 2 integration
            try:
                from src.intelligence import Phase2Integration
                phase2_integration = Phase2Integration()
                whisperengine_components['phase2_integration'] = phase2_integration
                logging.info("WhisperEngine Phase 2 integration initialized")
            except Exception as e:
                logging.warning(f"Phase 2 integration initialization failed: {e}")
            
            # Add LLM client to components
            if llm_client:
                whisperengine_components['llm_client'] = llm_client
            
            # Create web UI with WhisperEngine AI components
            self.web_ui = create_web_ui(
                db_manager=db_manager, 
                config_manager=config_manager,
                llm_client=llm_client,
                whisperengine_components=whisperengine_components
            )
            
            component_count = len(whisperengine_components)
            if component_count > 0:
                logging.info(f"WhisperEngine initialized with {component_count} AI components: {list(whisperengine_components.keys())}")
            else:
                logging.info("WhisperEngine initialized in basic mode (no AI components)")
            
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
        """Start the web UI server with proper shutdown handling"""
        import uvicorn
        
        try:
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
                logging.info("Opening browser... (Press Ctrl+C to quit)")
            else:
                logging.info("Access via system tray or visit http://{}:{}".format(self.host, self.port))
            
            if self.web_ui is None:
                raise RuntimeError("Web UI not initialized")
            
            # Initialize web UI components
            await self.web_ui.initialize()
            
            # Open browser if requested
            if auto_open:
                def open_browser_delayed():
                    import time
                    time.sleep(1.5)  # Wait for server to start
                    import webbrowser
                    webbrowser.open(f"http://{self.host}:{self.port}")
                
                import threading
                threading.Thread(target=open_browser_delayed, daemon=True).start()
            
            # Create server with shutdown event
            self.shutdown_event = asyncio.Event()
            config = uvicorn.Config(
                app=self.web_ui.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=False  # Reduce log noise
            )
            self.server = uvicorn.Server(config)
            
            self.running = True
            
            # Create server task
            server_task = asyncio.create_task(self.server.serve())
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            
            # Wait for either server to exit or shutdown event
            done, pending = await asyncio.wait([server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED)
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Shutdown server if it's still running
            if not server_task.done():
                self.server.should_exit = True
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass
            
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
            
            # Start server with proper asyncio signal handling
            if sys.platform != 'win32':
                # On Unix-like systems, set up signal handlers in the event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Add signal handlers to the loop
                for sig in (signal.SIGTERM, signal.SIGINT):
                    loop.add_signal_handler(sig, self._signal_handler)
                
                try:
                    loop.run_until_complete(self.start_server())
                finally:
                    loop.close()
            else:
                # On Windows, use the existing approach
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
    
    def _signal_handler(self):
        """Signal handler for asyncio loop"""
        print("\nShutting down WhisperEngine...")
        self.running = False
        
        # Stop the server
        if self.server:
            self.server.should_exit = True
        
        # Set shutdown event to interrupt the server task
        if self.shutdown_event and not self.shutdown_event.is_set():
            self.shutdown_event.set()
        
        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()


def main():
    """Main entry point"""
    app = WhisperEngineDesktopApp()
    app.run()


if __name__ == "__main__":
    main()