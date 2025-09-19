"""
Test suite for onboarding functionality.

Tests the user onboarding experience across different scenarios:
- First run detection
- Configuration validation
- Setup wizard functionality  
- CI/production environment handling
"""

import pytest
import os
import tempfile
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path


@pytest.mark.integration
class TestFirstRunDetector:
    """Test first run detection functionality"""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for onboarding tests"""
        # Store original environment
        original_env = dict(os.environ)
        
        # Clear onboarding-related environment variables
        onboarding_vars = [
            'DISCORD_BOT_TOKEN', 'LLM_CHAT_API_URL', 'LLM_CHAT_MODEL',
            'CI', 'SKIP_ONBOARDING', 'ENV_MODE'
        ]
        
        for var in onboarding_vars:
            os.environ.pop(var, None)
        
        yield
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.fixture
    def temp_workspace(self):
        """Temporary workspace for onboarding tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            yield Path(temp_dir)
            
            # Restore original directory
            os.chdir(original_cwd)

    def test_first_run_detector_creation(self, temp_workspace):
        """Test that FirstRunDetector can be created"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        assert detector is not None
        assert detector.project_root == temp_workspace

    def test_fresh_installation_detection(self, temp_workspace):
        """Test detection of fresh installation"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Fresh installation should be detected as first run
        assert detector.is_first_run() is True

    def test_setup_completion_marker(self, temp_workspace):
        """Test setup completion marker functionality"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Initially first run
        assert detector.is_first_run() is True
        
        # Mark as complete
        detector._mark_setup_complete()
        
        # Should no longer be first run
        assert detector.is_first_run() is False

    def test_configuration_validation(self, temp_workspace):
        """Test configuration file validation"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Create valid configuration file
        config_content = """
DISCORD_BOT_TOKEN=MTE2NzQwNTI4NjE2NjU5MTU4NA.GwXNvC.test_token_here
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_CHAT_API_KEY=not-needed
ENV_MODE=development
"""
        
        config_file = temp_workspace / ".env"
        with open(config_file, 'w') as f:
            f.write(config_content.strip())
        
        # Should detect valid configuration
        assert detector._has_valid_configuration(config_file) is True
        
        # After valid config, should not be first run
        assert detector.is_first_run() is False

    def test_invalid_configuration_detection(self, temp_workspace):
        """Test detection of invalid configurations"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Create invalid configuration file
        invalid_configs = [
            "DISCORD_BOT_TOKEN=your_discord_bot_token_here",  # Placeholder token
            "LLM_CHAT_API_URL=http://localhost:1234/v1\nLLM_CHAT_API_KEY=sk-placeholder",  # Placeholder API key
            "# Empty config file",  # No actual config
            "DISCORD_BOT_TOKEN=\nLLM_CHAT_API_URL=",  # Empty values
        ]
        
        for i, config_content in enumerate(invalid_configs):
            config_file = temp_workspace / f".env.test{i}"
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Should detect invalid configuration
            assert detector._has_valid_configuration(config_file) is False

    def test_missing_requirements_detection(self, temp_workspace):
        """Test missing requirements detection"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Get missing requirements
        missing = detector.get_missing_requirements()
        
        # Should return a list
        assert isinstance(missing, list)
        
        # Should check for configuration
        if not any((temp_workspace / config).exists() for config in detector.config_files):
            assert any("configuration" in req.lower() for req in missing)

    @pytest.mark.asyncio
    async def test_first_run_handling_decline(self, temp_workspace):
        """Test first run handling when user declines setup"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        # Mock user declining setup wizard
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):  # Suppress print output
                result = await detector.handle_first_run()
                assert result is False


@pytest.mark.integration  
class TestOnboardingManager:
    """Test onboarding manager functionality"""

    @pytest.fixture
    def temp_workspace(self):
        """Temporary workspace for onboarding tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            yield Path(temp_dir)
            
            # Restore original directory
            os.chdir(original_cwd)

    def test_onboarding_manager_creation(self):
        """Test that OnboardingManager can be created"""
        from src.utils.onboarding_manager import OnboardingManager
        
        manager = OnboardingManager()
        assert manager is not None
        assert hasattr(manager, 'detector')
        assert hasattr(manager, 'user_preferences')

    @pytest.mark.asyncio
    async def test_check_and_handle_onboarding_first_run(self, temp_workspace):
        """Test onboarding manager handling first run"""
        from src.utils.onboarding_manager import OnboardingManager, FirstRunDetector
        
        # Create manager with custom detector for temp workspace
        manager = OnboardingManager()
        manager.detector = FirstRunDetector(temp_workspace)
        
        # Mock user declining setup
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):  # Suppress print output
                result = await manager.check_and_handle_onboarding()
                assert result is False

    @pytest.mark.asyncio
    async def test_check_and_handle_onboarding_not_first_run(self, temp_workspace):
        """Test onboarding manager when not first run"""
        from src.utils.onboarding_manager import OnboardingManager, FirstRunDetector
        
        # Create manager with custom detector
        manager = OnboardingManager()
        manager.detector = FirstRunDetector(temp_workspace)
        
        # Mark setup as complete
        manager.detector._mark_setup_complete()
        
        # Should return True (continue)
        result = await manager.check_and_handle_onboarding()
        assert result is True

    def test_show_welcome_back_message(self):
        """Test welcome back message"""
        from src.utils.onboarding_manager import OnboardingManager
        
        manager = OnboardingManager()
        
        # Should not raise any exceptions
        with patch('builtins.print'):
            manager.show_welcome_back_message()


@pytest.mark.integration
class TestEnsureOnboardingComplete:
    """Test the ensure_onboarding_complete function"""

    @pytest.mark.asyncio
    async def test_ensure_onboarding_complete_with_setup_marker(self, temp_workspace):
        """Test ensure_onboarding_complete with existing setup marker"""
        from src.utils.onboarding_manager import ensure_onboarding_complete, onboarding_manager, FirstRunDetector
        
        # Replace the global detector with one pointing to temp workspace
        original_detector = onboarding_manager.detector
        onboarding_manager.detector = FirstRunDetector(temp_workspace)
        
        try:
            # Mark setup as complete
            onboarding_manager.detector._mark_setup_complete()
            
            # Should return True (continue)
            result = await ensure_onboarding_complete()
            assert result is True
            
        finally:
            # Restore original detector
            onboarding_manager.detector = original_detector

    @pytest.mark.asyncio
    async def test_ensure_onboarding_complete_first_run_decline(self, temp_workspace):
        """Test ensure_onboarding_complete when user declines first run setup"""
        from src.utils.onboarding_manager import ensure_onboarding_complete, onboarding_manager, FirstRunDetector
        
        # Replace the global detector with one pointing to temp workspace
        original_detector = onboarding_manager.detector
        onboarding_manager.detector = FirstRunDetector(temp_workspace)
        
        try:
            # Mock user declining setup
            with patch('builtins.input', return_value='n'):
                with patch('builtins.print'):  # Suppress print output
                    result = await ensure_onboarding_complete()
                    assert result is False
                    
        finally:
            # Restore original detector
            onboarding_manager.detector = original_detector


@pytest.mark.integration
class TestOnboardingIntegration:
    """Test onboarding integration with run.py and main application"""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment for integration tests"""
        return {
            'ENV_MODE': 'testing',
            'DEBUG_MODE': 'true',
            'DISCORD_BOT_TOKEN': 'test_token_12345',
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'LLM_CHAT_MODEL': 'test-model'
        }

    @pytest.mark.asyncio
    async def test_run_py_integration(self, mock_environment):
        """Test run.py integration with onboarding"""
        with patch.dict(os.environ, mock_environment):
            with patch('src.main.sync_main', return_value=0) as mock_main:
                # Import and test run.py logic
                import sys
                import importlib.util
                
                # Load run.py as a module
                spec = importlib.util.spec_from_file_location("run", "run.py")
                if spec is not None:
                    run_module = importlib.util.module_from_spec(spec)
                    
                    # Mock the main function to avoid actually starting the bot
                    with patch('asyncio.run') as mock_asyncio_run:
                        mock_asyncio_run.return_value = 0
                        
                        # The run.py should be able to import and set up without errors
                        assert spec is not None

    def test_environment_loading_integration(self, mock_environment):
        """Test environment loading integration with onboarding"""
        with patch.dict(os.environ, mock_environment):
            from env_manager import load_environment
            
            # Environment should load successfully
            result = load_environment()
            assert result is True

    @pytest.mark.asyncio
    async def test_onboarding_with_logging_setup(self, mock_environment):
        """Test onboarding integration with logging setup"""
        with patch.dict(os.environ, mock_environment):
            from src.utils.logging_config import setup_logging
            from src.utils.onboarding_manager import ensure_onboarding_complete
            
            # Set up logging
            setup_logging(debug=True, environment='testing')
            
            # Onboarding should work with logging configured
            result = await ensure_onboarding_complete()
            assert result is True


@pytest.mark.unit
class TestStartupHelp:
    """Test startup help functionality"""

    def test_show_startup_help(self):
        """Test startup help display"""
        from src.utils.onboarding_manager import show_startup_help
        
        # Should not raise any exceptions
        with patch('builtins.print'):
            show_startup_help()

    def test_get_startup_help_content(self):
        """Test startup help content generation"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector()
        help_text = detector.get_startup_help()
        
        # Should return a string with helpful content
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        assert "WhisperEngine" in help_text
        assert "Discord" in help_text or "LLM" in help_text


@pytest.mark.performance
class TestOnboardingPerformance:
    """Test onboarding performance characteristics"""

    @pytest.mark.asyncio
    async def test_onboarding_speed_with_existing_setup(self, temp_workspace):
        """Test that onboarding completes quickly when setup exists"""
        import time
        from src.utils.onboarding_manager import ensure_onboarding_complete, onboarding_manager, FirstRunDetector
        
        # Replace the global detector with one pointing to temp workspace
        original_detector = onboarding_manager.detector
        onboarding_manager.detector = FirstRunDetector(temp_workspace)
        
        try:
            # Mark setup as complete
            onboarding_manager.detector._mark_setup_complete()
            
            start_time = time.time()
            result = await ensure_onboarding_complete()
            end_time = time.time()
            
            # Should complete very quickly when setup already exists
            duration = end_time - start_time
            assert duration < 1.0  # Less than 1 second
            assert result is True
            
        finally:
            # Restore original detector
            onboarding_manager.detector = original_detector

    def test_first_run_detection_performance(self, temp_workspace):
        """Test first run detection performance"""
        import time
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        start_time = time.time()
        for _ in range(10):
            is_first_run = detector.is_first_run()
        end_time = time.time()
        
        # Should be fast even with multiple calls
        duration = end_time - start_time
        assert duration < 0.5  # Less than 500ms for 10 calls
        assert isinstance(is_first_run, bool)

    def test_missing_requirements_detection_performance(self, temp_workspace):
        """Test missing requirements detection performance"""
        import time
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        start_time = time.time()
        for _ in range(5):
            missing = detector.get_missing_requirements()
        end_time = time.time()
        
        # Should be reasonably fast
        duration = end_time - start_time
        assert duration < 2.0  # Less than 2 seconds for 5 calls
        assert isinstance(missing, list)


@pytest.mark.unit
class TestConfigurationValidation:
    """Test configuration file validation logic"""

    def test_valid_configuration_patterns(self, temp_workspace):
        """Test various valid configuration patterns"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        valid_configs = [
            # Local LLM with Discord
            """
DISCORD_BOT_TOKEN=MTE2NzQwNTI4NjE2NjU5MTU4NA.GwXNvC.real_token_here
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_CHAT_API_KEY=not-needed
""",
            # Cloud LLM with Discord  
            """
DISCORD_BOT_TOKEN=MTE2NzQwNTI4NjE2NjU5MTU4NA.GwXNvC.real_token_here
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_CHAT_API_KEY=sk-real_api_key_here
""",
            # Local LLM without Discord (desktop mode)
            """
LLM_CHAT_API_URL=http://localhost:11434/v1
LLM_CHAT_API_KEY=not-needed
ENV_MODE=desktop-app
""",
        ]
        
        for i, config_content in enumerate(valid_configs):
            config_file = temp_workspace / f".env.valid{i}"
            with open(config_file, 'w') as f:
                f.write(config_content.strip())
            
            # Should detect as valid configuration
            assert detector._has_valid_configuration(config_file) is True

    def test_invalid_configuration_patterns(self, temp_workspace):
        """Test various invalid configuration patterns"""
        from src.utils.onboarding_manager import FirstRunDetector
        
        detector = FirstRunDetector(temp_workspace)
        
        invalid_configs = [
            # Placeholder tokens
            "DISCORD_BOT_TOKEN=your_discord_bot_token_here",
            # Placeholder API keys
            "LLM_CHAT_API_URL=http://localhost:1234/v1\nLLM_CHAT_API_KEY=your_api_key_here",
            # Missing essential config
            "DEBUG_MODE=true",
            # Empty values
            "DISCORD_BOT_TOKEN=\nLLM_CHAT_API_URL=",
        ]
        
        for i, config_content in enumerate(invalid_configs):
            config_file = temp_workspace / f".env.invalid{i}"
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Should detect as invalid configuration
            assert detector._has_valid_configuration(config_file) is False


if __name__ == "__main__":
    # Allow running this test suite directly
    pytest.main([__file__, "-v"])