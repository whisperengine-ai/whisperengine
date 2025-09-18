#!/usr/bin/env python3
"""
WhisperEngine Universal Build Script
Builds WhisperEngine for multiple deployment targets with smart configuration.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.adaptive_config import AdaptiveConfigManager
from src.packaging.unified_builder import (
    BuildConfig,
    DeploymentTarget,
    Platform,
    UnifiedPackagingSystem,
)


def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if debug
            else "%(levelname)s: %(message)s"
        ),
    )


def detect_platform() -> Platform:
    """Auto-detect current platform"""
    import platform as plt

    system = plt.system().lower()
    if system == "darwin":
        return Platform.MACOS
    elif system == "windows":
        return Platform.WINDOWS
    elif system == "linux":
        return Platform.LINUX
    else:
        return Platform.UNIVERSAL


def get_recommended_config() -> dict[str, Any]:
    """Get recommended configuration based on environment"""
    # Try to detect environment info, fallback to defaults
    try:
        AdaptiveConfigManager()
        env_info = {"scale_tier": "tier_1"}  # Default fallback
    except:
        env_info = {"scale_tier": "tier_1"}

    recommendations = {
        "platform": detect_platform(),
        "include_discord": bool(os.environ.get("DISCORD_BOT_TOKEN")),
        "include_web_ui": True,
        "include_api": True,
        "enable_voice": False,  # Disabled by default for compatibility
        "optimize_size": True,
        "debug_mode": False,
    }

    # Adjust based on detected scale tier
    scale_tier = env_info.get("scale_tier", "tier_1")

    if scale_tier == "tier_1":  # Low resource
        recommendations.update(
            {"database_type": "sqlite", "optimize_size": True, "bundle_dependencies": True}
        )
    elif scale_tier in ["tier_2", "tier_3"]:  # Medium/High resource
        recommendations.update(
            {"database_type": "postgresql", "optimize_size": False, "bundle_dependencies": True}
        )
    else:  # Enterprise
        recommendations.update(
            {"database_type": "postgresql", "optimize_size": False, "bundle_dependencies": False}
        )

    return recommendations


def print_build_matrix():
    """Print available build targets and platforms"""

    targets = [
        ("docker_single", "Single Docker container (all-in-one)"),
        ("docker_compose", "Multi-container Docker setup with databases"),
        ("kubernetes", "Kubernetes deployment manifests"),
        ("web_only", "Web-only deployment (no Discord)"),
    ]

    for _target, _description in targets:
        pass

    platforms = [
        ("windows", "Windows 10/11 (x64)"),
        ("macos", "macOS 10.15+ (Intel/Apple Silicon)"),
        ("linux", "Linux distributions (x64)"),
        ("universal", "Cross-platform compatible"),
    ]

    for _platform, _description in platforms:
        pass


async def interactive_build():
    """Interactive build configuration"""

    # Get recommendations
    recommendations = get_recommended_config()

    # Ask for build target
    targets = list(DeploymentTarget)
    for _i, _target in enumerate(targets, 1):
        pass

    while True:
        try:
            choice = int(input(f"\nEnter choice (1-{len(targets)}): ")) - 1
            if 0 <= choice < len(targets):
                selected_target = targets[choice]
                break
            else:
                pass
        except ValueError:
            pass

    # Configure based on target
    if selected_target in [DeploymentTarget.DOCKER_COMPOSE, DeploymentTarget.KUBERNETES]:
        database_type = "postgresql"
        include_discord = True  # Assume production deployment wants Discord
    else:
        database_type = recommendations.get("database_type", "postgresql")
        include_discord = recommendations["include_discord"]

    # Ask about Discord integration if not auto-detected
    if not os.environ.get("DISCORD_BOT_TOKEN"):
        discord_choice = input("\n🤖 Include Discord integration? (y/N): ").lower()
        include_discord = discord_choice in ["y", "yes"]

    # Ask about optimization
    optimize_choice = input("\n🗜️  Optimize for smaller size? (Y/n): ").lower()
    optimize = optimize_choice not in ["n", "no"]

    # Ask for custom name
    app_name = input("\n📛 Application name (WhisperEngine): ").strip()
    if not app_name:
        app_name = "WhisperEngine"

    # Ask for output directory
    output_dir = input("\n📁 Output directory (./dist): ").strip()
    if not output_dir:
        output_dir = "./dist"

    # Create build config
    config = BuildConfig(
        target=selected_target,
        platform=recommendations["platform"],
        output_dir=output_dir,
        app_name=app_name,
        version="1.0.0",
        include_discord=include_discord,
        include_web_ui=True,
        include_api=True,
        database_type=database_type,
        enable_voice=False,
        bundle_dependencies=True,
        optimize_size=optimize,
        debug_mode=False,
    )

    # Show summary

    # Confirm and build
    confirm = input("\n🚀 Proceed with build? (Y/n): ").lower()
    if confirm in ["n", "no"]:
        return 1

    return await execute_build(config)


async def execute_build(config: BuildConfig) -> int:
    """Execute build with given configuration"""

    try:
        # Create packaging system
        packaging_system = UnifiedPackagingSystem()

        # Execute build
        result = await packaging_system.build(config)

        if result.success:

            # Show next steps based on target
            await show_next_steps(config, result)

            return 0
        else:
            if result.errors:
                for _error in result.errors:
                    pass
            return 1

    except Exception as e:
        logging.error(f"Build failed with exception: {e}")
        return 1


async def show_next_steps(config: BuildConfig, result):
    """Show next steps after successful build"""

    if config.target == DeploymentTarget.DOCKER_SINGLE:

        if not os.environ.get("OPENROUTER_API_KEY"):
            pass

    elif config.target == DeploymentTarget.DOCKER_COMPOSE:
        pass

    elif config.target == DeploymentTarget.KUBERNETES:
        pass


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WhisperEngine Universal Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                           # Interactive mode
  python build.py docker_single --optimize  # Build optimized Docker container
  python build.py --matrix                  # Show all available options
  python build.py --all                     # Build all targets
        """,
    )

    # Positional arguments
    parser.add_argument(
        "target",
        nargs="?",
        choices=[t.value for t in DeploymentTarget],
        help="Deployment target (interactive mode if not specified)",
    )

    # Optional arguments
    parser.add_argument(
        "--platform",
        choices=[p.value for p in Platform],
        help="Target platform (auto-detected if not specified)",
    )
    parser.add_argument(
        "--output", "-o", default="./dist", help="Output directory (default: ./dist)"
    )
    parser.add_argument(
        "--name", default="WhisperEngine", help="Application name (default: WhisperEngine)"
    )
    parser.add_argument("--version", "-v", default="1.0.0", help="Version (default: 1.0.0)")

    # Feature flags
    parser.add_argument("--no-discord", action="store_true", help="Disable Discord integration")
    parser.add_argument("--no-web", action="store_true", help="Disable web UI")
    parser.add_argument("--no-api", action="store_true", help="Disable REST API")
    parser.add_argument("--sqlite", action="store_true", help="Use SQLite instead of PostgreSQL")
    parser.add_argument("--voice", action="store_true", help="Enable voice features")
    parser.add_argument("--optimize", action="store_true", help="Optimize for smaller size")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Special modes
    parser.add_argument("--all", action="store_true", help="Build all supported targets")
    parser.add_argument("--matrix", action="store_true", help="Show build matrix and exit")
    parser.add_argument("--interactive", "-i", action="store_true", help="Force interactive mode")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Show build matrix if requested
    if args.matrix:
        print_build_matrix()
        return 0

    # Interactive mode
    if not args.target or args.interactive:
        return await interactive_build()

    # Get platform
    platform = Platform(args.platform) if args.platform else detect_platform()

    # Get recommendations for smart defaults
    recommendations = get_recommended_config()

    # Create build configuration
    config = BuildConfig(
        target=DeploymentTarget(args.target),
        platform=platform,
        output_dir=args.output,
        app_name=args.name,
        version=args.version,
        include_discord=not args.no_discord and recommendations.get("include_discord", True),
        include_web_ui=not args.no_web,
        include_api=not args.no_api,
        database_type=(
            "sqlite" if args.sqlite else recommendations.get("database_type", "postgresql")
        ),
        enable_voice=args.voice,
        bundle_dependencies=True,
        optimize_size=args.optimize or recommendations.get("optimize_size", False),
        debug_mode=args.debug,
    )

    if args.all:
        # Build all targets
        packaging_system = UnifiedPackagingSystem()
        results = await packaging_system.build_all_targets(config)

        success_count = 0
        for _target, result in results.items():
            if result.success:
                success_count += 1

        return 0 if success_count == len(results) else 1

    else:
        # Build single target
        return await execute_build(config)


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(1)
