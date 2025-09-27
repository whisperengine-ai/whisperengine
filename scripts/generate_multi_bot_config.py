#!/usr/bin/env python3
"""
Template-Based Multi-Bot Configuration Generator

This script auto-discovers bot configurations from .env.* files and character JSON files,
then fills in a Docker Compose template with the discovered configurations.

Usage:
    python scripts/generate_multi_bot_config.py

Requirements:
    - .env.{bot_name} files for bot-specific configuration
    - characters/examples/{character_name}.json files for CDL character definitions
    - docker-compose.multi-bot.template.yml template file
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Optional
import argparse

class BotConfigDiscovery:
    """Discovers and manages bot configurations dynamically."""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.env_pattern = re.compile(r"^\.env\.(.+)$")
        self.character_pattern = re.compile(r"^(.+)\.json$")
        self.template_file = self.workspace_root / "docker-compose.multi-bot.template.yml"
        self.output_file = self.workspace_root / "docker-compose.multi-bot.yml"
        
    def discover_bot_configs(self) -> Dict[str, Dict]:
        """
        Discover all bot configurations by scanning for .env.* files.
        Returns mapping of bot_name -> config_info
        """
        bot_configs = {}
        
        # Scan for .env.* files (excluding .example, .template, and .local files)
        for env_file in self.workspace_root.glob(".env.*"):
            if env_file.name.endswith(".example") or env_file.name.endswith(".template") or env_file.name.endswith(".local"):
                continue
                
            match = self.env_pattern.match(env_file.name)
            if match:
                bot_name = match.group(1)
                
                # Read health check port from env file
                health_port = self._extract_health_port(env_file)
                
                # Auto-discover character file
                character_file = self._find_character_file(bot_name)
                
                bot_configs[bot_name] = {
                    "env_file": str(env_file),
                    "character_file": character_file,
                    "health_port": health_port,
                    "service_name": f"{bot_name}-bot",
                    "container_name": f"whisperengine-{bot_name}-bot",
                    "display_name": self._get_display_name(bot_name)
                }
                
        return bot_configs
    
    def _extract_health_port(self, env_file: Path) -> int:
        """Extract HEALTH_CHECK_PORT from environment file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('HEALTH_CHECK_PORT='):
                        return int(line.split('=')[1].strip())
        except (IOError, ValueError, IndexError):
            pass
        
        # Default port based on bot name hash for consistency
        return 9000 + abs(hash(env_file.stem)) % 1000
    
    def _find_character_file(self, bot_name: str) -> Optional[str]:
        """
        Auto-discover character JSON file for a bot.
        Tries multiple naming patterns:
        1. Direct match: {bot_name}.json
        2. Underscore variant: {bot_name.replace('-', '_')}.json
        3. Dash variant: {bot_name.replace('_', '-')}.json
        """
        character_dir = self.workspace_root / "characters" / "examples"
        
        if not character_dir.exists():
            return None
            
        # Try different naming patterns
        patterns = [
            bot_name,
            bot_name.replace('-', '_'),
            bot_name.replace('_', '-'),
            bot_name.replace('-', '_').replace('_', '-'),  # normalize
            # Specific mappings
            f"{bot_name}-rodriguez" if bot_name == "elena" else None,
            f"{bot_name}-thompson" if bot_name == "marcus" else None,
            f"{bot_name}-tether" if bot_name == "gabriel" else None,
            f"{bot_name}_of_the_endless" if bot_name == "dream" else None,
            f"{bot_name}-blake" if bot_name == "sophia" else None,
            f"{bot_name}-sterling" if bot_name == "jake" else None,
            # Special case for ryan -> ryan-chen character file migration
            "ryan-chen" if bot_name == "ryan" else None,
            # Special case for aethys -> aethys-omnipotent-entity character file
            f"{bot_name}-omnipotent-entity" if bot_name == "aethys" else None,
        ]
        
        # Filter out None values
        patterns = [p for p in patterns if p is not None]
        
        for pattern in patterns:
            character_file = character_dir / f"{pattern}.json"
            if character_file.exists():
                return str(character_file)
                
        return None
    
    def _get_display_name(self, bot_name: str) -> str:
        """
        Get the display name for a bot, handling special cases.
        Special mapping for ryan-chen -> ryan migration.
        """
        # Special case for ryan-chen -> ryan migration
        if bot_name == "ryan-chen":
            return "ryan"
        
        # Default: convert dashes to spaces and title case
        return bot_name.replace("-", " ").title()

    def generate_bot_service_yaml(self, bot_name: str, config: Dict) -> str:
        """Generate YAML for a single bot service."""
        
        environment_vars = [
            f"DISCORD_BOT_NAME={config['display_name']}",
            "POSTGRES_HOST=postgres",
            "REDIS_HOST=redis", 
            "QDRANT_HOST=qdrant",
            "MODEL_CACHE_DIR=/app/models",
            "DISABLE_MODEL_DOWNLOAD=true",
            "HF_HUB_OFFLINE=false",
            "TRANSFORMERS_OFFLINE=0",
            "LOG_LEVEL=${LOG_LEVEL:-INFO}",
            "DEBUG_MODE=false",
            "PYTHONUNBUFFERED=1",
            f"HEALTH_CHECK_PORT={config['health_port']}",
            "HEALTH_CHECK_HOST=0.0.0.0"
        ]
        
        # Add character file if available
        if config['character_file']:
            environment_vars.append(f"CDL_DEFAULT_CHARACTER={config['character_file']}")
        
        service_yaml = f"""  {config['service_name']}:
    image: whisperengine-bot:${{VERSION:-latest}}
    container_name: {config['container_name']}
    restart: unless-stopped
    env_file:
      - {config['env_file']}
    environment:"""
        
        for env_var in environment_vars:
            service_yaml += f"\n      - {env_var}"
            
        service_yaml += f"""
    ports:
      - "{config['health_port']}:{config['health_port']}"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{bot_name}-{{.ImageName}}-{{.Name}}-{{.ID}}"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "4.0"
        reservations:
          memory: 2G
          cpus: "2.0"
    healthcheck:
      test:
        - CMD-SHELL
        - curl -f http://localhost:{config['health_port']}/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - {bot_name}_backups:/app/backups
      - {bot_name}_privacy:/app/privacy
      - {bot_name}_temp:/app/temp
      - ./sql:/app/sql:ro
      # Live code mounting for development (no rebuild needed)
      - ./src:/app/src
      - ./scripts:/app/scripts
      - ./characters:/app/characters
      - ./config:/app/config
      - ./validate_config.py:/app/validate_config.py
      - ./run.py:/app/run.py
      - ./env_manager.py:/app/env_manager.py
      # Note: Using Docker logging instead of mounted log volumes
    networks:
      - bot_network
    depends_on:
      - postgres
      - redis
      - qdrant"""
        
        return service_yaml

    def generate_bot_volumes_yaml(self, bot_configs: Dict[str, Dict]) -> str:
        """Generate YAML for bot-specific volumes."""
        volumes_yaml = ""
        
        for bot_name, config in bot_configs.items():
            volumes_yaml += f"""  {bot_name}_backups:
    name: whisperengine-multi_{bot_name}_backups
  {bot_name}_privacy:
    name: whisperengine-multi_{bot_name}_privacy
  {bot_name}_temp:
    name: whisperengine-multi_{bot_name}_temp
  {bot_name}_logs:
    name: whisperengine-multi_{bot_name}_logs
"""
        
        return volumes_yaml.rstrip()

    def generate_docker_compose_from_template(self, bot_configs: Dict[str, Dict]) -> str:
        """Generate Docker Compose by filling template with discovered bot configurations."""
        
        if not self.template_file.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_file}")
        
        # Read template
        with open(self.template_file, 'r') as f:
            template_content = f.read()
        
        # Generate bot services YAML
        bot_services_yaml = ""
        for bot_name, config in bot_configs.items():
            bot_services_yaml += self.generate_bot_service_yaml(bot_name, config) + "\n\n"
        
        # Generate bot volumes YAML
        bot_volumes_yaml = self.generate_bot_volumes_yaml(bot_configs)
        
        # Replace placeholders in template
        filled_content = template_content.replace(
            "  # BOT_SERVICES_PLACEHOLDER", 
            bot_services_yaml.rstrip()
        ).replace(
            "  # BOT_VOLUMES_PLACEHOLDER", 
            bot_volumes_yaml
        )
        
        return filled_content

    def generate_management_script(self, bot_configs: Dict[str, Dict]) -> str:
        """Generate the multi-bot management script."""
        
        bot_names = list(bot_configs.keys())
        bot_names_str = " ".join(bot_names)
        bot_array_str = "(" + " ".join(f'"{name}"' for name in bot_names) + ")"
        
        script_content = f'''#!/bin/bash
# Auto-generated Multi-Bot Management Script
# DO NOT EDIT: This file is generated by scripts/generate_multi_bot_config.py

set -e

# Discovered bot configurations
AVAILABLE_BOTS={bot_array_str}
PROJECT_NAME="whisperengine-multi"
COMPOSE_FILE="docker-compose.multi-bot.yml"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

show_usage() {{
    echo "Multi-Bot Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [BOT_NAME]"
    echo ""
    echo "Commands:"
    echo "  list                    List all available bots"
    echo "  start [bot_name|all]    Start specific bot or all bots"
    echo "  stop [bot_name|all]     Stop specific bot or all bots"
    echo "  restart [bot_name|all]  Restart specific bot or all bots"
    echo "  logs [bot_name]         Show logs for specific bot"
    echo "  status                  Show status of all containers"
    echo "  health                  Check health of all services"
    echo ""
    echo "Available bots: {bot_names_str}"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 start elena"
    echo "  $0 start all"
    echo "  $0 logs marcus"
    echo "  $0 stop"
}}

validate_bot_name() {{
    local bot_name="$1"
    if [[ "$bot_name" == "all" ]]; then
        return 0
    fi
    
    for valid_bot in "${{AVAILABLE_BOTS[@]}}"; do
        if [[ "$valid_bot" == "$bot_name" ]]; then
            return 0
        fi
    done
    
    echo -e "${{RED}}Error: Invalid bot name '$bot_name'${{NC}}"
    echo -e "Available bots: {bot_names_str}"
    return 1
}}

list_bots() {{
    echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Available bot configurations:"
    for bot in "${{AVAILABLE_BOTS[@]}}"; do
        echo "  ✓ $bot"
    done
}}

start_bot() {{
    local bot_name="$1"
    
    if [[ "$bot_name" == "all" ]]; then
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Starting all bots..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    else
        validate_bot_name "$bot_name" || return 1
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Starting $bot_name bot..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d "${{bot_name}}-bot"
    fi
}}

stop_bot() {{
    local bot_name="$1"
    
    if [[ "$bot_name" == "all" || -z "$bot_name" ]]; then
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Stopping all services..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    else
        validate_bot_name "$bot_name" || return 1
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Stopping $bot_name bot..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" stop "${{bot_name}}-bot"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" rm -f "${{bot_name}}-bot"
    fi
}}

restart_bot() {{
    local bot_name="$1"
    
    if [[ "$bot_name" == "all" ]]; then
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Restarting all services..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart
    else
        validate_bot_name "$bot_name" || return 1
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Restarting $bot_name bot..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart "${{bot_name}}-bot"
    fi
}}

show_logs() {{
    local bot_name="$1"
    
    if [[ -z "$bot_name" ]]; then
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Showing logs for all services..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
    else
        validate_bot_name "$bot_name" || return 1
        echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Showing logs for $bot_name bot..."
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "${{bot_name}}-bot"
    fi
}}

show_status() {{
    echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Container status:"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
}}

check_health() {{
    echo -e "${{BLUE}}[MULTI-BOT]${{NC}} Health check results:"
    for bot in "${{AVAILABLE_BOTS[@]}}"; do
        container_name="whisperengine-${{bot}}-bot"
        if docker ps --format "table {{{{.Names}}}}" | grep -q "$container_name"; then
            health=$(docker inspect --format='{{{{.State.Health.Status}}}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
            if [[ "$health" == "healthy" ]]; then
                echo -e "  ✅ $bot: ${{GREEN}}$health${{NC}}"
            elif [[ "$health" == "no-healthcheck" ]]; then
                echo -e "  ⚠️  $bot: ${{YELLOW}}running (no healthcheck)${{NC}}"
            else
                echo -e "  ❌ $bot: ${{RED}}$health${{NC}}"
            fi
        else
            echo -e "  💤 $bot: ${{YELLOW}}not running${{NC}}"
        fi
    done
}}

# Main command processing
case "$1" in
    list)
        list_bots
        ;;
    start)
        start_bot "$2"
        ;;
    stop)
        stop_bot "$2"
        ;;
    restart)
        restart_bot "$2"
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
'''
        return script_content

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate dynamic multi-bot configuration from discovered .env files"
    )
    parser.add_argument(
        "--workspace", 
        default=".", 
        help="Workspace root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Initialize discovery
    discovery = BotConfigDiscovery(args.workspace)
    
    # Discover configurations
    print("🔍 Discovering bot configurations...")
    bot_configs = discovery.discover_bot_configs()
    
    if not bot_configs:
        print("❌ No bot configurations found!")
        print("   Create .env.{bot_name} files to get started")
        return 1
    
    # Display discovered configurations
    print(f"✅ Found {len(bot_configs)} bot configurations:")
    for bot_name, config in bot_configs.items():
        character_status = f"character={config['character_file']}" if config['character_file'] else "no character file"
        print(f"  ✓ {bot_name}: env={config['env_file']}, {character_status}, port={config['health_port']}")
    
    try:
        # Generate Docker Compose from template
        print("\\n🐳 Generating Docker Compose configuration from template...")
        compose_content = discovery.generate_docker_compose_from_template(bot_configs)
        
        # Write Docker Compose file
        with open(discovery.output_file, 'w') as f:
            f.write(compose_content)
        print(f"✅ Generated: {discovery.output_file}")
        
        # Generate management script
        print("🛠 Generating management script...")
        script_content = discovery.generate_management_script(bot_configs)
        script_file = discovery.workspace_root / "multi-bot.sh"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_file, 0o755)
        print(f"✅ Generated: {script_file}")
        
        print("\\n🎉 Template-based multi-bot configuration complete!")
        print("\\nNext steps:")
        print("1. To add a new bot, copy .env.template to .env.{bot_name}")
        print("2. Customize the template with bot-specific values")
        print("3. Ensure corresponding character JSON exists in characters/examples/")
        print("4. Regenerate config: source .venv/bin/activate && python scripts/generate_multi_bot_config.py")
        print("5. Test with: ./multi-bot.sh list")
        print("6. Start bots: ./multi-bot.sh start [bot_name]")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating configuration: {e}")
        return 1

if __name__ == "__main__":
    exit(main())