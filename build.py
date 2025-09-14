#!/usr/bin/env python3
"""
WhisperEngine Universal Build Script
Builds WhisperEngine for multiple deployment targets with smart configuration.
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.packaging.unified_builder import (
    UnifiedPackagingSystem, BuildConfig, DeploymentTarget, Platform
)
from src.config.adaptive_config import AdaptiveConfigManager


def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if debug
               else '%(levelname)s: %(message)s'
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


def get_recommended_config() -> Dict[str, Any]:
    """Get recommended configuration based on environment"""
    # Try to detect environment info, fallback to defaults
    try:
        config_manager = AdaptiveConfigManager()
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
        "debug_mode": False
    }
    
    # Adjust based on detected scale tier
    scale_tier = env_info.get("scale_tier", "tier_1")
    
    if scale_tier == "tier_1":  # Low resource
        recommendations.update({
            "database_type": "sqlite",
            "optimize_size": True,
            "bundle_dependencies": True
        })
    elif scale_tier in ["tier_2", "tier_3"]:  # Medium/High resource
        recommendations.update({
            "database_type": "postgresql",
            "optimize_size": False,
            "bundle_dependencies": True
        })
    else:  # Enterprise
        recommendations.update({
            "database_type": "postgresql", 
            "optimize_size": False,
            "bundle_dependencies": False
        })
    
    return recommendations


def print_build_matrix():
    """Print available build targets and platforms"""
    print("🏗️  WhisperEngine Build Matrix")
    print("="*50)
    
    print("\n📱 Deployment Targets:")
    targets = [
        ("native_desktop", "Native desktop app with embedded SQLite"),
        ("docker_single", "Single Docker container (all-in-one)"),
        ("docker_compose", "Multi-container Docker setup with databases"),
        ("kubernetes", "Kubernetes deployment manifests"),
        ("web_only", "Web-only deployment (no Discord)")
    ]
    
    for target, description in targets:
        print(f"  • {target:<16} - {description}")
    
    print("\n💻 Platforms:")
    platforms = [
        ("windows", "Windows 10/11 (x64)"),
        ("macos", "macOS 10.15+ (Intel/Apple Silicon)"),
        ("linux", "Linux distributions (x64)"),
        ("universal", "Cross-platform compatible")
    ]
    
    for platform, description in platforms:
        print(f"  • {platform:<12} - {description}")
    
    print("\n🎯 Recommended Combinations:")
    print("  • Desktop Users:    native_desktop + your_platform")
    print("  • Developers:       docker_single + universal") 
    print("  • Self-Hosting:     docker_compose + linux")
    print("  • Enterprise:       kubernetes + universal")
    print("  • Web-Only Demo:    web_only + universal")


async def interactive_build():
    """Interactive build configuration"""
    print("🤖 WhisperEngine Interactive Build Setup")
    print("="*45)
    
    # Get recommendations
    recommendations = get_recommended_config()
    
    print(f"\n🔍 Detected Environment:")
    print(f"  Platform: {recommendations['platform'].value}")
    print(f"  Discord Token: {'✅ Found' if recommendations['include_discord'] else '❌ Not found'}")
    
    # Ask for build target
    print(f"\n🎯 Select Deployment Target:")
    targets = list(DeploymentTarget)
    for i, target in enumerate(targets, 1):
        print(f"  {i}. {target.value}")
    
    while True:
        try:
            choice = int(input(f"\nEnter choice (1-{len(targets)}): ")) - 1
            if 0 <= choice < len(targets):
                selected_target = targets[choice]
                break
            else:
                print("Invalid choice, please try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Configure based on target
    if selected_target == DeploymentTarget.NATIVE_DESKTOP:
        database_type = "sqlite"
        include_discord = recommendations['include_discord']
    elif selected_target in [DeploymentTarget.DOCKER_COMPOSE, DeploymentTarget.KUBERNETES]:
        database_type = "postgresql"
        include_discord = True  # Assume production deployment wants Discord
    else:
        database_type = recommendations.get('database_type', 'sqlite')
        include_discord = recommendations['include_discord']
    
    # Ask about Discord integration if not auto-detected
    if not os.environ.get("DISCORD_BOT_TOKEN"):
        discord_choice = input(f"\n🤖 Include Discord integration? (y/N): ").lower()
        include_discord = discord_choice in ['y', 'yes']
    
    # Ask about optimization
    optimize_choice = input(f"\n🗜️  Optimize for smaller size? (Y/n): ").lower()
    optimize = optimize_choice not in ['n', 'no']
    
    # Ask for custom name
    app_name = input(f"\n📛 Application name (WhisperEngine): ").strip()
    if not app_name:
        app_name = "WhisperEngine"
    
    # Ask for output directory
    output_dir = input(f"\n📁 Output directory (./dist): ").strip()
    if not output_dir:
        output_dir = "./dist"
    
    # Create build config
    config = BuildConfig(
        target=selected_target,
        platform=recommendations['platform'],
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
        debug_mode=False
    )
    
    # Show summary
    print(f"\n📋 Build Configuration:")
    print(f"  Target:       {config.target.value}")
    print(f"  Platform:     {config.platform.value}")
    print(f"  App Name:     {config.app_name}")
    print(f"  Output:       {config.output_dir}")
    print(f"  Database:     {config.database_type}")
    print(f"  Discord:      {'✅ Enabled' if config.include_discord else '❌ Disabled'}")
    print(f"  Web UI:       {'✅ Enabled' if config.include_web_ui else '❌ Disabled'}")
    print(f"  Optimized:    {'✅ Yes' if config.optimize_size else '❌ No'}")
    
    # Confirm and build
    confirm = input(f"\n🚀 Proceed with build? (Y/n): ").lower()
    if confirm in ['n', 'no']:
        print("Build cancelled.")
        return 1
    
    return await execute_build(config)


async def execute_build(config: BuildConfig) -> int:
    """Execute build with given configuration"""
    print(f"\n🏗️  Starting build for {config.target.value}...")
    
    try:
        # Create packaging system
        packaging_system = UnifiedPackagingSystem()
        
        # Execute build
        result = await packaging_system.build(config)
        
        if result.success:
            print(f"\n✅ Build completed successfully!")
            print(f"📁 Output:     {result.output_path}")
            print(f"📦 Size:       {result.size_mb}MB")
            print(f"⏱️  Time:       {result.build_time_seconds}s")
            print(f"📄 Artifacts:  {', '.join(result.artifacts)}")
            
            # Show next steps based on target
            await show_next_steps(config, result)
            
            return 0
        else:
            print(f"\n❌ Build failed!")
            if result.errors:
                for error in result.errors:
                    print(f"   • {error}")
            return 1
    
    except Exception as e:
        logging.error(f"Build failed with exception: {e}")
        return 1


async def show_next_steps(config: BuildConfig, result):
    """Show next steps after successful build"""
    print(f"\n🎯 Next Steps:")
    
    if config.target == DeploymentTarget.NATIVE_DESKTOP:
        if config.platform == Platform.MACOS:
            print(f"  1. Double-click {config.app_name}.app to launch")
        else:
            exe_suffix = ".exe" if config.platform == Platform.WINDOWS else ""
            print(f"  1. Run ./{config.app_name}{exe_suffix} to launch")
        print(f"  2. Open http://localhost:8080 in your browser")
        print(f"  3. Start chatting with your AI assistant!")
        
        if config.include_discord and not os.environ.get("DISCORD_BOT_TOKEN"):
            print(f"\n⚠️  Discord Integration:")
            print(f"  • Set DISCORD_BOT_TOKEN environment variable")
            print(f"  • Or configure in the web UI settings")
    
    elif config.target == DeploymentTarget.DOCKER_SINGLE:
        print(f"  1. Load Docker image: docker load < {result.artifacts[0]}")
        print(f"  2. Run container: ./run.sh")
        print(f"  3. Open http://localhost:8080 in your browser")
        
        if not os.environ.get("OPENROUTER_API_KEY"):
            print(f"\n⚠️  API Configuration:")
            print(f"  • Set OPENROUTER_API_KEY environment variable")
            print(f"  • Update run.sh script with your API key")
    
    elif config.target == DeploymentTarget.DOCKER_COMPOSE:
        print(f"  1. Copy .env.template to .env")
        print(f"  2. Edit .env with your API keys and passwords")
        print(f"  3. Run: ./setup.sh")
        print(f"  4. Open http://localhost:8080 in your browser")
    
    elif config.target == DeploymentTarget.KUBERNETES:
        print(f"  1. Configure kubectl for your cluster")
        print(f"  2. Update ConfigMaps with your API keys")
        print(f"  3. Apply manifests: kubectl apply -f ./")
        print(f"  4. Access via ingress or port-forward")
    
    print(f"\n📚 Documentation: Check the generated README files for details")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WhisperEngine Universal Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                           # Interactive mode
  python build.py native_desktop             # Build native app for current platform
  python build.py docker_single --optimize  # Build optimized Docker container
  python build.py --matrix                  # Show all available options
  python build.py --all                     # Build all targets
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "target", 
        nargs="?",
        choices=[t.value for t in DeploymentTarget],
        help="Deployment target (interactive mode if not specified)"
    )
    
    # Optional arguments
    parser.add_argument("--platform", choices=[p.value for p in Platform],
                       help="Target platform (auto-detected if not specified)")
    parser.add_argument("--output", "-o", default="./dist", 
                       help="Output directory (default: ./dist)")
    parser.add_argument("--name", default="WhisperEngine", 
                       help="Application name (default: WhisperEngine)")
    parser.add_argument("--version", "-v", default="1.0.0", 
                       help="Version (default: 1.0.0)")
    
    # Feature flags
    parser.add_argument("--no-discord", action="store_true", 
                       help="Disable Discord integration")
    parser.add_argument("--no-web", action="store_true", 
                       help="Disable web UI")
    parser.add_argument("--no-api", action="store_true", 
                       help="Disable REST API")
    parser.add_argument("--sqlite", action="store_true", 
                       help="Use SQLite instead of PostgreSQL")
    parser.add_argument("--voice", action="store_true", 
                       help="Enable voice features")
    parser.add_argument("--optimize", action="store_true", 
                       help="Optimize for smaller size")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug mode")
    
    # Special modes
    parser.add_argument("--all", action="store_true", 
                       help="Build all supported targets")
    parser.add_argument("--matrix", action="store_true", 
                       help="Show build matrix and exit")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Force interactive mode")
    
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
        include_discord=not args.no_discord and recommendations.get('include_discord', True),
        include_web_ui=not args.no_web,
        include_api=not args.no_api,
        database_type="sqlite" if args.sqlite else recommendations.get('database_type', 'postgresql'),
        enable_voice=args.voice,
        bundle_dependencies=True,
        optimize_size=args.optimize or recommendations.get('optimize_size', False),
        debug_mode=args.debug
    )
    
    if args.all:
        # Build all targets
        print("🏗️  Building all targets...")
        packaging_system = UnifiedPackagingSystem()
        results = await packaging_system.build_all_targets(config)
        
        print("\n📊 Build Summary:")
        success_count = 0
        for target, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"  {status} {target.value:<20} {result.size_mb:>6.1f}MB  {result.build_time_seconds:>5.1f}s")
            if result.success:
                success_count += 1
        
        print(f"\n🎯 {success_count}/{len(results)} builds successful")
        return 0 if success_count == len(results) else 1
    
    else:
        # Build single target
        return await execute_build(config)


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n👋 Build cancelled by user")
        sys.exit(1)