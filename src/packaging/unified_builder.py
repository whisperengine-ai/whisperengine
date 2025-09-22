"""
WhisperEngine Unified Packaging System
Builds Discord bot containers and cloud deployments.

Deployment Targets:
- DOCKER_SINGLE: Single Docker container for Discord bot
- DOCKER_COMPOSE: Multi-container Docker setup for Discord bot
- WEB_DEPLOYMENT: Web-based deployment
- CLOUD_DEPLOYMENT: Cloud platform deployment
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class DeploymentTarget(Enum):
    """Supported deployment targets"""

    DOCKER_SINGLE = "docker_single"  # Single Docker container
    DOCKER_COMPOSE = "docker_compose"  # Multi-container Docker setup
    KUBERNETES = "kubernetes"  # Kubernetes deployment
    CLOUD_LAMBDA = "cloud_lambda"  # Serverless functions
    CLOUD_VM = "cloud_vm"  # Cloud VM deployment
    WEB_ONLY = "web_only"  # Web-only deployment (no Discord)


class Platform(Enum):
    """Supported platforms"""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNIVERSAL = "universal"


@dataclass
class BuildConfig:
    """Configuration for build process"""

    target: DeploymentTarget
    platform: Platform
    output_dir: str
    app_name: str = "WhisperEngine"
    version: str = "1.0.0"
    include_discord: bool = True
    include_web_ui: bool = True
    include_api: bool = True
    database_type: str = "sqlite"  # sqlite, postgresql
    enable_voice: bool = False
    bundle_dependencies: bool = True
    optimize_size: bool = True
    debug_mode: bool = False
    custom_config: dict[str, Any] | None = None


@dataclass
class BuildResult:
    """Result of build process"""

    success: bool
    target: DeploymentTarget
    platform: Platform
    output_path: str
    size_mb: float
    build_time_seconds: float
    artifacts: list[str]
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class BaseBuildStrategy:
    """Base class for build strategies"""

    def __init__(self, config: BuildConfig, project_root: Path):
        self.config = config
        self.project_root = project_root
        self.output_path = Path(config.output_dir)
        self.temp_dir: Path | None = None

    async def build(self) -> BuildResult:
        """Execute the build process"""
        import time

        start_time = time.time()

        try:
            # Create output directory
            self.output_path.mkdir(parents=True, exist_ok=True)

            # Create temporary build directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix="whisperengine_build_"))

            # Execute build steps
            artifacts = await self._execute_build()

            # Calculate build metrics
            build_time = time.time() - start_time
            total_size = sum(
                os.path.getsize(os.path.join(root, file))
                for root, _, files in os.walk(self.output_path)
                for file in files
            ) / (
                1024 * 1024
            )  # MB

            return BuildResult(
                success=True,
                target=self.config.target,
                platform=self.config.platform,
                output_path=str(self.output_path),
                size_mb=round(total_size, 2),
                build_time_seconds=round(build_time, 2),
                artifacts=artifacts,
            )

        except Exception as e:
            logging.error(f"Build failed: {e}")
            return BuildResult(
                success=False,
                target=self.config.target,
                platform=self.config.platform,
                output_path=str(self.output_path),
                size_mb=0,
                build_time_seconds=time.time() - start_time,
                artifacts=[],
                errors=[str(e)],
            )

        finally:
            # Cleanup temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

    async def _execute_build(self) -> list[str]:
        """Override in subclasses"""
        raise NotImplementedError

    def _copy_source_files(self, exclude_patterns: list[str] | None = None) -> Path:
        """Copy source files to temp directory"""
        if self.temp_dir is None:
            raise RuntimeError("temp_dir not initialized")

        if exclude_patterns is None:
            exclude_patterns = [
                "__pycache__",
                "*.pyc",
                ".git",
                ".pytest_cache",
                "node_modules",
                "logs",
                "temp_images",
                "data/neo4j_backups",
                "backups",
            ]

        source_dir = self.temp_dir / "src"

        # Copy entire project
        shutil.copytree(
            self.project_root, source_dir, ignore=shutil.ignore_patterns(*exclude_patterns)
        )

        return source_dir

    def _generate_environment_config(self, target_config: dict[str, Any]) -> str:
        """Generate environment configuration for target"""
        env_config = {
            # Base configuration
            "WHISPERENGINE_MODE": self.config.target.value,
            "WHISPERENGINE_VERSION": self.config.version,
            "WHISPERENGINE_DATABASE_TYPE": self.config.database_type,
            "ENABLE_WEB_UI": str(self.config.include_web_ui).lower(),
            "ENABLE_API": str(self.config.include_api).lower(),
            "ENABLE_VOICE": str(self.config.enable_voice).lower(),
            "DEBUG_MODE": str(self.config.debug_mode).lower(),
        }

        # Add Discord config if enabled
        if self.config.include_discord:
            env_config["ENABLE_DISCORD"] = "true"
            env_config["DISCORD_BOT_TOKEN"] = "${DISCORD_BOT_TOKEN}"
        else:
            env_config["ENABLE_DISCORD"] = "false"

        # Add target-specific config
        env_config.update(target_config)

        # Add custom config
        if self.config.custom_config:
            env_config.update(self.config.custom_config)

        # Generate .env file content
        env_content = "\n".join([f"{k}={v}" for k, v in env_config.items()])
        return env_content

    def _run_command(self, command: list[str], cwd: Path | None = None) -> str:
        """Run shell command and return output"""
        try:
            result = subprocess.run(
                command, cwd=cwd or self.temp_dir, capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {' '.join(command)}")
            logging.error(f"Error: {e.stderr}")
            raise



class DockerBuilder(BaseBuildStrategy):
    """Build Docker containers"""

    async def _create_entry_script(self, source_dir: Path) -> Path:
        """Create entry point script for native app"""
        entry_content = '''#!/usr/bin/env python3
"""
WhisperEngine Native Desktop Application
Entry point for standalone desktop usage with web UI.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point for native desktop app"""
    try:
        # Import after path setup
        from src.platforms.universal_chat import UniversalChatOrchestrator
        from src.database.database_integration import DatabaseIntegrationManager

        print("🤖 Starting WhisperEngine Desktop...")

        # Simplified environment detection
        print("🔍 Environment: Docker container mode")

        # Initialize database with simplified configuration
        db_manager = DatabaseIntegrationManager()
        await db_manager.initialize()

        # Create universal chat platform
        chat_platform = create_universal_chat_platform(db_manager)

        # Initialize chat platforms (Web UI + any configured platforms)
        if await chat_platform.initialize():
            print("✅ Chat platforms initialized")
        else:
            print("❌ Failed to initialize chat platforms")
            return 1

        # Start web UI
        web_ui = WhisperEngineWebUI(db_manager)

        print("🌐 Starting web interface at http://localhost:8080")
        print("📱 Check your system tray for WhisperEngine icon")
        print("💬 Open your browser to start chatting!")

        # Run web UI (this will block)
        await web_ui.start()

    except KeyboardInterrupt:
        print("\\n👋 Shutting down WhisperEngine...")
    except Exception as e:
        logging.error(f"Error running WhisperEngine: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
'''

        entry_script = source_dir / "main_desktop.py"
        entry_script.write_text(entry_content)
        return entry_script

    async def _create_pyinstaller_spec(self, source_dir: Path, entry_script: Path) -> Path:
        """Create PyInstaller spec file"""
        app_name = self.config.app_name

        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Define paths
src_path = Path(SPECPATH) / "src"
static_path = src_path / "ui" / "static"
templates_path = src_path / "ui" / "templates"

a = Analysis(
    ['{entry_script.name}'],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        (str(static_path), 'src/ui/static'),
        (str(templates_path), 'src/ui/templates'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'src.platforms.universal_chat',
        'src.ui.web_ui',
        'src.config.adaptive_config',
        'src.database.database_integration',
        'src.optimization.cost_optimizer',
        'uvicorn',
        'fastapi',
        'jinja2',
        'aiosqlite',
        'pystray',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'discord.py',
        'neo4j',
        'psycopg2',
    ] if not {self.config.include_discord} else [],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

"""

        if self.config.optimize_size:
            # Single file executable
            spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug={self.config.debug_mode},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={self.config.debug_mode},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
        else:
            # Directory with dependencies
            spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{app_name}',
    debug={self.config.debug_mode},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={self.config.debug_mode},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)
"""

        # Add macOS app bundle
        if self.config.platform == Platform.MACOS:
            if self.config.optimize_size:
                # Single file - use exe directly
                spec_content += f"""
app = BUNDLE(
    exe,
    name='{app_name}.app',
    icon=None,
    bundle_identifier='ai.whisperengine.app',
    version='{self.config.version}',
)
"""
            else:
                # Directory - use coll
                spec_content += f"""
app = BUNDLE(
    coll,
    name='{app_name}.app',
    icon=None,
    bundle_identifier='ai.whisperengine.app',
    version='{self.config.version}',
)
"""

        spec_file = source_dir / f"{app_name}.spec"
        spec_file.write_text(spec_content)
        return spec_file

class DockerBuilder(BaseBuildStrategy):
    """Build Docker containers"""

    async def _execute_build(self) -> list[str]:
        """Build Docker containers"""
        # Copy source files
        source_dir = self._copy_source_files()

        if self.config.target == DeploymentTarget.DOCKER_SINGLE:
            return await self._build_single_container(source_dir)
        else:
            return await self._build_compose_setup(source_dir)

    async def _build_single_container(self, source_dir: Path) -> list[str]:
        """Build single Docker container"""
        # Create Dockerfile
        dockerfile = await self._create_dockerfile(source_dir)

        # Generate environment config
        env_config = self._generate_environment_config(
            {
                "WHISPERENGINE_DEPLOYMENT": "docker_single",
                "WEB_UI_HOST": "0.0.0.0",
                "WEB_UI_PORT": "8080",
            }
        )

        # Write environment config
        env_file = source_dir / ".env"
        env_file.write_text(env_config)

        # Build Docker image
        image_tag = f"{self.config.app_name.lower()}:{self.config.version}"

        self._run_command(
            ["docker", "build", "-t", image_tag, "-f", str(dockerfile), "."], cwd=source_dir
        )

        # Save Docker image to output
        image_file = self.output_path / f"{self.config.app_name.lower()}-{self.config.version}.tar"

        self._run_command(["docker", "save", "-o", str(image_file), image_tag])

        # Create run script
        run_script = await self._create_docker_run_script(image_tag)

        return [image_file.name, run_script.name]

    async def _create_dockerfile(self, source_dir: Path) -> Path:
        """Create optimized Dockerfile"""
        dockerfile_content = f"""# Multi-stage build for WhisperEngine
FROM python:3.13-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libsqlite3-0 \\
    {"libpq-dev" if self.config.database_type == "postgresql" else ""} \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy application code
COPY --chown=app:app . .

# Create data directory
RUN mkdir -p ~/.whisperengine/data

# Expose ports
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "src/main.py"]
"""

        dockerfile = source_dir / "Dockerfile"
        dockerfile.write_text(dockerfile_content)
        return dockerfile

    async def _create_docker_run_script(self, image_tag: str) -> Path:
        """Create Docker run script"""
        script_content = f"""#!/bin/bash
# WhisperEngine Docker Run Script

echo "🤖 Starting WhisperEngine Docker Container..."

# Create data volume if it doesn't exist
docker volume create whisperengine-data

# Run container
docker run -d \\
    --name whisperengine \\
    --restart unless-stopped \\
    -p 8080:8080 \\
    -v whisperengine-data:/home/app/.whisperengine \\
    -e DISCORD_BOT_TOKEN="${{DISCORD_BOT_TOKEN:-}}" \\
    -e OPENROUTER_API_KEY="${{OPENROUTER_API_KEY:-}}" \\
    {image_tag}

echo "✅ WhisperEngine started!"
echo "🌐 Web UI: http://localhost:8080"
echo "📋 Logs: docker logs -f whisperengine"
echo "🛑 Stop: docker stop whisperengine"
"""

        run_script = self.output_path / "run.sh"
        run_script.write_text(script_content)
        run_script.chmod(0o755)
        return run_script

    async def _build_compose_setup(self, source_dir: Path) -> list[str]:
        """Build Docker Compose setup"""
        # Create docker-compose.yml
        compose_file = await self._create_compose_file(source_dir)

        # Create Dockerfile
        await self._create_dockerfile(source_dir)

        # Copy compose file to output
        shutil.copy2(compose_file, self.output_path / "docker-compose.yml")

        # Create environment template
        await self._create_env_template()

        # Create setup script
        await self._create_compose_setup_script()

        return ["docker-compose.yml", ".env.template", "setup.sh"]

    async def _create_compose_file(self, source_dir: Path) -> Path:
        """Create Docker Compose configuration"""
        compose_config = {
            "version": "3.8",
            "services": {
                "whisperengine": {
                    "build": ".",
                    "ports": ["8080:8080"],
                    "environment": [
                        "WHISPERENGINE_DATABASE_TYPE=${WHISPERENGINE_DATABASE_TYPE:-postgresql}",
                        "POSTGRES_HOST=postgres",
                        "POSTGRES_PORT=5432",
                        "POSTGRES_DB=${POSTGRES_DB:-whisperengine}",
                        "POSTGRES_USER=${POSTGRES_USER:-whisperengine}",
                        "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}",
                        "DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-}",
                        "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
                        "REDIS_URL=redis://redis:6379/0",
                    ],
                    "volumes": ["whisperengine-data:/home/app/.whisperengine"],
                    "depends_on": ["postgres", "redis"],
                    "restart": "unless-stopped",
                },
                "postgres": {
                    "image": "postgres:15-alpine",
                    "environment": [
                        "POSTGRES_DB=${POSTGRES_DB:-whisperengine}",
                        "POSTGRES_USER=${POSTGRES_USER:-whisperengine}",
                        "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}",
                    ],
                    "volumes": ["postgres-data:/var/lib/postgresql/data"],
                    "restart": "unless-stopped",
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "volumes": ["redis-data:/data"],
                    "restart": "unless-stopped",
                },
            },
            "volumes": {"whisperengine-data": {}, "postgres-data": {}, "redis-data": {}},
        }

        compose_file = source_dir / "docker-compose.yml"
        with open(compose_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

        return compose_file

    async def _create_env_template(self) -> Path:
        """Create environment template"""
        env_template = """# WhisperEngine Configuration
# Copy this file to .env and fill in your values

# Required: OpenRouter API key for AI responses
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Discord bot token (leave empty to disable Discord)
DISCORD_BOT_TOKEN=

# Database configuration
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=your_secure_password_here

# Application settings
WHISPERENGINE_DATABASE_TYPE=postgresql
DEBUG_MODE=false
"""

        env_file = self.output_path / ".env.template"
        env_file.write_text(env_template)
        return env_file

    async def _create_compose_setup_script(self) -> Path:
        """Create setup script for Docker Compose"""
        script_content = """#!/bin/bash
# WhisperEngine Docker Compose Setup

set -e

echo "🤖 Setting up WhisperEngine with Docker Compose..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your configuration before continuing!"
    echo "📖 Required: OPENROUTER_API_KEY"
    echo "📖 Optional: DISCORD_BOT_TOKEN (for Discord integration)"
    exit 1
fi

# Check required environment variables
source .env

if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your_openrouter_api_key_here" ]; then
    echo "❌ OPENROUTER_API_KEY is required in .env file"
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
    echo "❌ POSTGRES_PASSWORD must be set in .env file"
    exit 1
fi

echo "🏗️  Building and starting WhisperEngine..."

# Start services
docker-compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 10

# Check health
if docker-compose ps | grep -q "Up"; then
    echo "✅ WhisperEngine is running!"
    echo "🌐 Web UI: http://localhost:8080"
    echo "📋 Logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose down"
else
    echo "❌ Some services failed to start"
    echo "📋 Check logs: docker-compose logs"
    exit 1
fi
"""

        setup_script = self.output_path / "setup.sh"
        setup_script.write_text(script_content)
        setup_script.chmod(0o755)
        return setup_script


class KubernetesBuilder(BaseBuildStrategy):
    """Build Kubernetes deployments"""

    async def _execute_build(self) -> list[str]:
        """Build Kubernetes manifests"""
        # Create Kubernetes manifests
        manifests = await self._create_k8s_manifests()

        # Create Helm chart (optional)
        helm_chart = await self._create_helm_chart()

        return manifests + helm_chart

    async def _create_k8s_manifests(self) -> list[str]:
        """Create Kubernetes YAML manifests"""
        # Implementation for K8s manifests
        # This would create deployments, services, configmaps, etc.
        return ["deployment.yml", "service.yml", "configmap.yml"]

    async def _create_helm_chart(self) -> list[str]:
        """Create Helm chart for easy deployment"""
        # Implementation for Helm chart
        return ["helm-chart.tgz"]


class UnifiedPackagingSystem:
    """Main packaging system that coordinates all build strategies"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.builders = {
            DeploymentTarget.DOCKER_SINGLE: DockerBuilder,
            DeploymentTarget.DOCKER_COMPOSE: DockerBuilder,
            DeploymentTarget.KUBERNETES: KubernetesBuilder,
        }

    async def build(self, config: BuildConfig) -> BuildResult:
        """Build for specified target"""
        if config.target not in self.builders:
            raise ValueError(f"Unsupported deployment target: {config.target}")

        builder_class = self.builders[config.target]
        builder = builder_class(config, self.project_root)

        logging.info(f"Starting build for {config.target.value} on {config.platform.value}")
        result = await builder.build()

        if result.success:
            logging.info(
                f"✅ Build successful: {result.output_path} ({result.size_mb}MB in {result.build_time_seconds}s)"
            )
        else:
            logging.error(f"❌ Build failed: {result.errors}")

        return result

    async def build_all_targets(
        self, base_config: BuildConfig
    ) -> dict[DeploymentTarget, BuildResult]:
        """Build for all supported targets"""
        results = {}

        for target in DeploymentTarget:
            if target in self.builders:
                config = BuildConfig(
                    target=target,
                    platform=base_config.platform,
                    output_dir=str(Path(base_config.output_dir) / target.value),
                    app_name=base_config.app_name,
                    version=base_config.version,
                    include_discord=base_config.include_discord,
                    include_web_ui=base_config.include_web_ui,
                    include_api=base_config.include_api,
                    database_type="postgresql",  # All remaining targets use PostgreSQL
                    enable_voice=base_config.enable_voice,
                    bundle_dependencies=base_config.bundle_dependencies,
                    optimize_size=base_config.optimize_size,
                    debug_mode=base_config.debug_mode,
                    custom_config=base_config.custom_config,
                )

                results[target] = await self.build(config)

        return results

    def get_supported_targets(self) -> list[DeploymentTarget]:
        """Get list of supported deployment targets"""
        return list(self.builders.keys())


# CLI interface
async def main():
    """Command-line interface for unified packaging"""
    import argparse

    parser = argparse.ArgumentParser(description="WhisperEngine Unified Packaging System")
    parser.add_argument(
        "target", choices=[t.value for t in DeploymentTarget], help="Deployment target"
    )
    parser.add_argument(
        "--platform",
        choices=[p.value for p in Platform],
        default=Platform.UNIVERSAL.value,
        help="Target platform",
    )
    parser.add_argument("--output", "-o", default="./dist", help="Output directory")
    parser.add_argument("--name", default="WhisperEngine", help="Application name")
    parser.add_argument("--version", "-v", default="1.0.0", help="Version")
    parser.add_argument("--no-discord", action="store_true", help="Disable Discord integration")
    parser.add_argument("--no-web", action="store_true", help="Disable web UI")
    parser.add_argument("--sqlite", action="store_true", help="Use SQLite instead of PostgreSQL")
    parser.add_argument("--optimize", action="store_true", help="Optimize for size")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--all", action="store_true", help="Build all targets")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Create build config
    config = BuildConfig(
        target=DeploymentTarget(args.target),
        platform=Platform(args.platform),
        output_dir=args.output,
        app_name=args.name,
        version=args.version,
        include_discord=not args.no_discord,
        include_web_ui=not args.no_web,
        include_api=True,
        database_type="sqlite" if args.sqlite else "postgresql",
        enable_voice=False,
        bundle_dependencies=True,
        optimize_size=args.optimize,
        debug_mode=args.debug,
    )

    # Create packaging system
    packaging_system = UnifiedPackagingSystem()

    try:
        if args.all:
            # Build all targets
            results = await packaging_system.build_all_targets(config)

            for _target, result in results.items():
                pass
        else:
            # Build single target
            result = await packaging_system.build(config)

            if result.success:
                pass
            else:
                if result.errors:
                    for _error in result.errors:
                        pass
                return 1

    except Exception as e:
        logging.error(f"Packaging failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
