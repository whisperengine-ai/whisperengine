"""
Integration module for Adaptive Configuration System
Connects the adaptive configuration to existing WhisperEngine architecture.
"""

import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_manager import load_environment
from src.config.adaptive_config import AdaptiveConfigManager


class WhisperEngineConfigIntegrator:
    """Integrates adaptive configuration with existing WhisperEngine systems"""

    def __init__(self, config_override: dict[str, Any] | None = None):
        self.config_manager = AdaptiveConfigManager(config_override)
        self.deployment_info = self.config_manager.get_deployment_info()
        self.env_vars = self.config_manager.get_env_vars()

    def setup_environment(self) -> bool:
        """Setup environment with adaptive configuration"""
        try:
            # First load existing environment
            if not load_environment():
                pass

            # Apply adaptive configuration environment variables
            for key, value in self.env_vars.items():
                os.environ[key] = value

            # Set deployment-specific variables
            os.environ["WHISPERENGINE_DEPLOYMENT_MODE"] = self.deployment_info["deployment_mode"]
            os.environ["WHISPERENGINE_SCALE_TIER"] = str(self.deployment_info["scale_tier"])
            os.environ["WHISPERENGINE_PLATFORM"] = self.deployment_info["platform"]
            os.environ["WHISPERENGINE_CPU_CORES"] = str(self.deployment_info["cpu_cores"])
            os.environ["WHISPERENGINE_MEMORY_GB"] = str(round(self.deployment_info["memory_gb"], 1))

            return True
        except Exception:
            return False

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration for current environment"""
        db_config = self.config_manager.config.database

        # Map adaptive database config to WhisperEngine database settings
        config = {
            "use_postgresql": db_config.primary_type != "sqlite",
            "use_redis_cache": db_config.cache_type != "memory",
            "connection_pool_size": db_config.connection_pool_size,
            "backup_enabled": db_config.backup_enabled,
            "vector_database_mode": db_config.vector_type,
        }

        # Desktop-specific SQLite configuration
        if db_config.primary_type == "sqlite":
            config.update(
                {
                    "sqlite_path": os.path.expanduser("~/.whisperengine/database.db"),
                    "sqlite_backup_path": os.path.expanduser("~/.whisperengine/backups/"),
                    "sqlite_wal_mode": True,  # Better performance for desktop apps
                }
            )

        return config

    def get_ai_config(self) -> dict[str, Any]:
        """Get AI/ML configuration for current environment"""
        perf_config = self.config_manager.config.performance
        features = self.config_manager.config.features

        return {
            # Historical: use_external_embeddings was deprecated in September 2025. Local embedding is always used.
            "enable_semantic_clustering": perf_config.enable_semantic_clustering,
            "cpu_threads": perf_config.cpu_threads,
            "memory_limit_gb": perf_config.memory_limit_gb,
            "batch_size": perf_config.batch_size,
            "timeout_seconds": perf_config.timeout_seconds,
            "cache_size_mb": perf_config.cache_size_mb,
            "enable_phase3_memory": features.get("enable_phase3_memory", True),
            "enable_phase4_human_like": features.get("enable_phase4_human_like", True),
            "enable_emotions": features.get("enable_emotions", True),
            "enable_auto_facts": features.get("enable_auto_facts", True),
            "enable_global_facts": features.get("enable_global_facts", False),
        }

    def get_performance_recommendations(self) -> dict[str, Any]:
        """Get performance recommendations for current configuration"""
        scale_tier = self.deployment_info["scale_tier"]
        deployment_mode = self.deployment_info["deployment_mode"]

        recommendations = {
            "scale_tier": scale_tier,
            "deployment_mode": deployment_mode,
            "recommendations": [],
        }

        # Scale tier specific recommendations
        if scale_tier == 1:
            recommendations["recommendations"].extend(
                [
                    "Consider upgrading to 32GB+ RAM for better performance",
                    "External API embeddings recommended over local models",
                    "SQLite database is optimal for desktop usage",
                    "Disable semantic clustering if experiencing slowdowns",
                ]
            )
        elif scale_tier == 2:
            recommendations["recommendations"].extend(
                [
                    "Your system is well-balanced for single-bot usage",
                    "Consider local AI models if privacy is important",
                    "PostgreSQL recommended for multi-user scenarios",
                    "Redis caching will improve response times",
                ]
            )
        elif scale_tier == 3:
            recommendations["recommendations"].extend(
                [
                    "Excellent configuration for high-performance usage",
                    "Local AI models fully supported",
                    "Consider running multiple bot instances",
                    "All advanced features can be enabled",
                ]
            )
        else:  # Scale tier 4
            recommendations["recommendations"].extend(
                [
                    "Enterprise/cloud configuration detected",
                    "Horizontal scaling patterns recommended",
                    "Use distributed databases and caching",
                    "API-based AI services for predictable scaling",
                ]
            )

        # Platform-specific recommendations
        if self.deployment_info["platform"] == "Darwin":  # macOS
            recommendations["recommendations"].extend(
                [
                    "Apple Silicon GPU acceleration available",
                    "Unified memory architecture provides excellent performance",
                    "Native app packaging recommended over Docker",
                ]
            )
        elif self.deployment_info["platform"] == "Linux":
            if deployment_mode == "container":
                recommendations["recommendations"].append(
                    "Container deployment detected - ensure sufficient resource limits"
                )
            else:
                recommendations["recommendations"].append(
                    "Native Linux deployment - optimal for server usage"
                )

        return recommendations

    def create_desktop_app_config(self) -> dict[str, Any]:
        """Create configuration optimized for desktop application"""
        return {
            "app_mode": "desktop",
            "data_directory": os.path.expanduser("~/.whisperengine/"),
            "logs_directory": os.path.expanduser("~/.whisperengine/logs/"),
            "backups_directory": os.path.expanduser("~/.whisperengine/backups/"),
            "cache_directory": os.path.expanduser("~/.whisperengine/cache/"),
            "auto_start": True,
            "system_tray": True,
            "auto_update": True,
            "local_server_port": 8080,
            "enable_gui": True,
            "minimize_to_tray": True,
            "database": self.get_database_config(),
            "ai": self.get_ai_config(),
            "deployment_info": self.deployment_info,
        }

    def generate_env_file(self, output_path: str | None = None) -> str:
        """Generate .env file with adaptive configuration"""
        if output_path is None:
            output_path = os.path.join(os.getcwd(), ".env.adaptive")

        env_content = [
            "# WhisperEngine Adaptive Configuration",
            f"# Generated for {self.deployment_info['deployment_mode']} deployment",
            f"# Scale Tier: {self.deployment_info['scale_tier']}",
            f"# Platform: {self.deployment_info['platform']} ({self.deployment_info['cpu_cores']} cores, {self.deployment_info['memory_gb']:.1f}GB RAM)",
            "",
            "# === Adaptive Environment Variables ===",
        ]

        for key, value in sorted(self.env_vars.items()):
            env_content.append(f"{key}={value}")

        env_content.extend(
            [
                "",
                "# === Deployment Information ===",
                f"WHISPERENGINE_DEPLOYMENT_MODE={self.deployment_info['deployment_mode']}",
                f"WHISPERENGINE_SCALE_TIER={self.deployment_info['scale_tier']}",
                f"WHISPERENGINE_PLATFORM={self.deployment_info['platform']}",
                f"WHISPERENGINE_CPU_CORES={self.deployment_info['cpu_cores']}",
                f"WHISPERENGINE_MEMORY_GB={self.deployment_info['memory_gb']:.1f}",
                f"WHISPERENGINE_GPU_AVAILABLE={self.deployment_info['gpu_available']}",
                "",
                "# === Required Settings (Add your values) ===",
                "DISCORD_BOT_TOKEN=your_token_here",
                "LLM_CHAT_API_URL=http://localhost:1234/v1",
                "LLM_MODEL_NAME=your_model_name",
            ]
        )

        # Add optional API settings based on configuration
        if not self.config_manager.config.performance.enable_local_ai:
            env_content.extend(
                [
                    "",
                    "# === External API Configuration ===",
                    "OPENROUTER_API_KEY=your_openrouter_key_here",
                    "OPENROUTER_EMBEDDING_MODEL=text-embedding-3-small",
                ]
            )

        env_file_content = "\n".join(env_content)

        with open(output_path, "w") as f:
            f.write(env_file_content)

        return output_path

    def print_deployment_summary(self):
        """Print a summary of the current deployment configuration"""

        # Deployment information

        # System resources

        # Configuration summary
        self.get_ai_config()
        self.get_database_config()

        # Performance recommendations
        recommendations = self.get_performance_recommendations()
        for _rec in recommendations["recommendations"][:3]:  # Show top 3
            pass

        if len(recommendations["recommendations"]) > 3:
            pass


# CLI interface for testing and configuration generation
def main():
    """CLI interface for adaptive configuration"""
    import argparse

    parser = argparse.ArgumentParser(description="WhisperEngine Adaptive Configuration")
    parser.add_argument(
        "--generate-env", action="store_true", help="Generate .env file with adaptive configuration"
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".env.adaptive",
        help="Output file for generated .env (default: .env.adaptive)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print deployment configuration summary"
    )
    parser.add_argument(
        "--desktop-config", action="store_true", help="Generate desktop application configuration"
    )

    args = parser.parse_args()

    # Create integrator
    integrator = WhisperEngineConfigIntegrator()

    if args.summary:
        integrator.print_deployment_summary()

    if args.generate_env:
        integrator.generate_env_file(args.output)

    if args.desktop_config:
        desktop_config = integrator.create_desktop_app_config()
        import json

        config_file = "desktop_app_config.json"
        with open(config_file, "w") as f:
            json.dump(desktop_config, f, indent=2)

    if not any([args.summary, args.generate_env, args.desktop_config]):
        integrator.print_deployment_summary()


if __name__ == "__main__":
    main()
