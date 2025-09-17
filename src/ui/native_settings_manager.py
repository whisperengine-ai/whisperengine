#!/usr/bin/env python3
"""
Native Settings Manager for WhisperEngine Universal App
Handles configuration, preferences, and platform-specific settings.
"""

import json
import logging
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from PySide6.QtCore import QSettings, QObject, Signal
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
        QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
        QSpinBox, QSlider, QTextEdit, QGroupBox, QFormLayout,
        QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
        QPushButton, QProgressBar, QFrame
    )
    from PySide6.QtCore import Qt
except ImportError:
    print("PySide6 not available for settings manager")

# Configuration dataclasses
@dataclass
class LLMConfig:
    """LLM configuration settings"""
    api_url: str = "http://127.0.0.1:1234/v1"
    model_name: str = "llama-3.2-3b-instruct"
    api_key: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    system_prompt_file: str = "prompts/default.md"
    timeout_seconds: int = 30

@dataclass
class UIConfig:
    """UI configuration settings"""
    theme: str = "dark"
    font_family: str = "default"
    font_size: int = 14
    window_opacity: float = 1.0
    auto_scroll: bool = True
    show_timestamps: bool = True
    markdown_rendering: bool = True
    auto_save_conversations: bool = True

@dataclass
class PlatformConfig:
    """Platform-specific configuration"""
    system_tray_enabled: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    auto_start: bool = False
    notifications_enabled: bool = True
    platform_integration: bool = True

@dataclass
class PrivacyConfig:
    """Privacy and security settings"""
    store_conversations: bool = True
    encryption_enabled: bool = False
    auto_delete_after_days: int = 30
    share_analytics: bool = False
    local_mode_only: bool = False

@dataclass
class AdvancedConfig:
    """Advanced configuration options"""
    debug_mode: bool = False
    log_level: str = "INFO"
    memory_limit_mb: int = 512
    cache_enabled: bool = True
    experimental_features: bool = False
    custom_plugins_path: str = ""

class SettingsCategory(Enum):
    """Settings categories for organization"""
    LLM = "LLM Configuration"
    UI = "User Interface"
    PLATFORM = "Platform Integration"
    PRIVACY = "Privacy & Security"
    ADVANCED = "Advanced Options"

class NativeSettingsManager(QObject):
    """Comprehensive settings manager for native app"""
    
    # Signals for settings changes
    settings_changed = Signal(str, object)  # category, new_config
    llm_config_changed = Signal(object)
    ui_config_changed = Signal(object)
    
    def __init__(self, app_name: str = "WhisperEngine"):
        super().__init__()
        self.app_name = app_name
        self.logger = logging.getLogger(__name__)
        
        # Qt settings for persistence
        self.qt_settings = QSettings("WhisperEngine", "UniversalApp")
        
        # Configuration objects
        self.llm_config = LLMConfig()
        self.ui_config = UIConfig()
        self.platform_config = PlatformConfig()
        self.privacy_config = PrivacyConfig()
        self.advanced_config = AdvancedConfig()
        
        # Platform detection
        self.platform_name = platform.system().lower()
        self.is_macos = self.platform_name == 'darwin'
        self.is_windows = self.platform_name == 'windows'
        self.is_linux = self.platform_name == 'linux'
        
        # Load existing settings
        self.load_settings()
        
        self.logger.info(f"Settings manager initialized for {platform.system()}")
    
    def get_config_file_path(self) -> Path:
        """Get platform-appropriate config file path"""
        if self.is_macos:
            config_dir = Path.home() / "Library" / "Application Support" / self.app_name
        elif self.is_windows:
            config_dir = Path.home() / "AppData" / "Roaming" / self.app_name
        else:  # Linux
            config_dir = Path.home() / ".config" / self.app_name
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "settings.json"
    
    def load_settings(self):
        """Load settings from persistent storage"""
        try:
            # Load from JSON file first (primary)
            config_file = self.get_config_file_path()
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                # Update configuration objects
                if 'llm' in data:
                    self.llm_config = LLMConfig(**data['llm'])
                if 'ui' in data:
                    self.ui_config = UIConfig(**data['ui'])
                if 'platform' in data:
                    self.platform_config = PlatformConfig(**data['platform'])
                if 'privacy' in data:
                    self.privacy_config = PrivacyConfig(**data['privacy'])
                if 'advanced' in data:
                    self.advanced_config = AdvancedConfig(**data['advanced'])
                
                self.logger.info("Settings loaded from JSON file")
            else:
                # Fallback to Qt settings
                self._load_from_qt_settings()
                
        except Exception as e:
            self.logger.warning(f"Error loading settings: {e}, using defaults")
            self._load_defaults()
    
    def _load_from_qt_settings(self):
        """Load settings from Qt settings as fallback"""
        try:
            # LLM settings
            self.llm_config.api_url = str(self.qt_settings.value("llm/api_url", self.llm_config.api_url))
            self.llm_config.model_name = str(self.qt_settings.value("llm/model_name", self.llm_config.model_name))
            
            # Safe temperature conversion
            try:
                temp_val = self.qt_settings.value("llm/temperature", self.llm_config.temperature)
                self.llm_config.temperature = float(str(temp_val)) if temp_val is not None else self.llm_config.temperature
            except (ValueError, TypeError):
                self.llm_config.temperature = 0.7  # default
            
            # UI settings
            self.ui_config.theme = str(self.qt_settings.value("ui/theme", self.ui_config.theme))
            
            # Safe font size conversion
            try:
                font_size_val = self.qt_settings.value("ui/font_size", self.ui_config.font_size)
                self.ui_config.font_size = int(str(font_size_val)) if font_size_val is not None else self.ui_config.font_size
            except (ValueError, TypeError):
                self.ui_config.font_size = 14  # default
            
            # Platform settings
            try:
                tray_val = self.qt_settings.value("platform/system_tray", True)
                self.platform_config.system_tray_enabled = str(tray_val).lower() == 'true' if tray_val is not None else True
            except (ValueError, TypeError):
                self.platform_config.system_tray_enabled = True
            
            self.logger.info("Settings loaded from Qt settings")
            
        except Exception as e:
            self.logger.warning(f"Error loading Qt settings: {e}")
    
    def _load_defaults(self):
        """Load default settings"""
        self.llm_config = LLMConfig()
        self.ui_config = UIConfig()
        self.platform_config = PlatformConfig()
        self.privacy_config = PrivacyConfig()
        self.advanced_config = AdvancedConfig()
        
        # Platform-specific defaults
        if self.is_macos:
            self.ui_config.font_family = "-apple-system"
        elif self.is_windows:
            self.ui_config.font_family = "Segoe UI"
        else:
            self.ui_config.font_family = "system-ui"
        
        self.logger.info("Default settings loaded")
    
    def save_settings(self):
        """Save settings to persistent storage"""
        try:
            # Save to JSON file (primary)
            config_file = self.get_config_file_path()
            data = {
                'llm': asdict(self.llm_config),
                'ui': asdict(self.ui_config),
                'platform': asdict(self.platform_config),
                'privacy': asdict(self.privacy_config),
                'advanced': asdict(self.advanced_config),
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'platform': platform.platform(),
                    'version': '1.2.0'
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Also save to Qt settings as backup
            self._save_to_qt_settings()
            
            self.logger.info(f"Settings saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def _save_to_qt_settings(self):
        """Save settings to Qt settings as backup"""
        try:
            # LLM settings
            self.qt_settings.setValue("llm/api_url", self.llm_config.api_url)
            self.qt_settings.setValue("llm/model_name", self.llm_config.model_name)
            self.qt_settings.setValue("llm/temperature", self.llm_config.temperature)
            
            # UI settings
            self.qt_settings.setValue("ui/theme", self.ui_config.theme)
            self.qt_settings.setValue("ui/font_size", self.ui_config.font_size)
            
            # Platform settings
            self.qt_settings.setValue("platform/system_tray", self.platform_config.system_tray_enabled)
            
            self.qt_settings.sync()
            
        except Exception as e:
            self.logger.warning(f"Error saving Qt settings: {e}")
    
    def get_llm_config(self) -> LLMConfig:
        """Get current LLM configuration"""
        return self.llm_config
    
    def update_llm_config(self, **kwargs):
        """Update LLM configuration"""
        for key, value in kwargs.items():
            if hasattr(self.llm_config, key):
                setattr(self.llm_config, key, value)
        
        self.save_settings()
        self.llm_config_changed.emit(self.llm_config)
        self.settings_changed.emit("llm", self.llm_config)
    
    def get_ui_config(self) -> UIConfig:
        """Get current UI configuration"""
        return self.ui_config
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.ui_config, key):
                setattr(self.ui_config, key, value)
        
        self.save_settings()
        self.ui_config_changed.emit(self.ui_config)
        self.settings_changed.emit("ui", self.ui_config)
    
    def get_platform_config(self) -> PlatformConfig:
        """Get current platform configuration"""
        return self.platform_config
    
    def update_platform_config(self, **kwargs):
        """Update platform configuration"""
        for key, value in kwargs.items():
            if hasattr(self.platform_config, key):
                setattr(self.platform_config, key, value)
        
        self.save_settings()
        self.settings_changed.emit("platform", self.platform_config)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configuration objects"""
        return {
            'llm': self.llm_config,
            'ui': self.ui_config,
            'platform': self.platform_config,
            'privacy': self.privacy_config,
            'advanced': self.advanced_config
        }
    
    def reset_to_defaults(self, category: Optional[str] = None):
        """Reset settings to defaults"""
        if category == "llm" or category is None:
            self.llm_config = LLMConfig()
        if category == "ui" or category is None:
            self.ui_config = UIConfig()
        if category == "platform" or category is None:
            self.platform_config = PlatformConfig()
        if category == "privacy" or category is None:
            self.privacy_config = PrivacyConfig()
        if category == "advanced" or category is None:
            self.advanced_config = AdvancedConfig()
        
        self.save_settings()
        self.logger.info(f"Settings reset to defaults: {category or 'all'}")
    
    def export_settings(self, file_path: str) -> bool:
        """Export settings to file"""
        try:
            data = {
                'llm': asdict(self.llm_config),
                'ui': asdict(self.ui_config),
                'platform': asdict(self.platform_config),
                'privacy': asdict(self.privacy_config),
                'advanced': asdict(self.advanced_config),
                'export_metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'platform': platform.platform(),
                    'app_version': '1.2.0'
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Settings exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Import settings from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate and import each category
            if 'llm' in data:
                self.llm_config = LLMConfig(**data['llm'])
            if 'ui' in data:
                self.ui_config = UIConfig(**data['ui'])
            if 'platform' in data:
                self.platform_config = PlatformConfig(**data['platform'])
            if 'privacy' in data:
                self.privacy_config = PrivacyConfig(**data['privacy'])
            if 'advanced' in data:
                self.advanced_config = AdvancedConfig(**data['advanced'])
            
            self.save_settings()
            self.logger.info(f"Settings imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False
    
    def validate_llm_connection(self) -> Tuple[bool, str]:
        """Validate LLM connection with current settings"""
        try:
            import requests
            import time
            
            url = f"{self.llm_config.api_url.rstrip('/')}/models"
            
            start_time = time.time()
            response = requests.get(url, timeout=self.llm_config.timeout_seconds)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                model_names = [model.get('id', '') for model in models]
                
                if self.llm_config.model_name in model_names:
                    return True, f"✅ Connected successfully in {response_time:.2f}s. Model '{self.llm_config.model_name}' is available."
                else:
                    available_models = ", ".join(model_names[:3])
                    return False, f"⚠️ Connected but model '{self.llm_config.model_name}' not found. Available: {available_models}"
            else:
                return False, f"❌ Connection failed: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, f"❌ Connection timeout after {self.llm_config.timeout_seconds}s"
        except requests.exceptions.ConnectionError:
            return False, f"❌ Cannot connect to {self.llm_config.api_url}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from LLM server"""
        try:
            import requests
            
            url = f"{self.llm_config.api_url.rstrip('/')}/models"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                return [model.get('id', '') for model in models]
            else:
                self.logger.warning(f"Failed to get models: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.warning(f"Error getting available models: {e}")
            return []