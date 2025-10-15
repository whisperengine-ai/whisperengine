#!/usr/bin/env python3
"""
WhisperEngine Bot Orchestrator

Dynamically manages character bot deployment based on database configurations.
Reads character configs from PostgreSQL and creates/destroys Docker containers as needed.

Features:
- Database-driven deployment (no .env files needed)
- Automatic port assignment
- Health monitoring
- Rolling updates
- Container lifecycle management
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import docker
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Add the src directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.database.cdl_database_adapter import CDLDatabaseAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BotDeployment:
    """Represents a deployed character bot"""
    character_id: int
    character_name: str
    container_name: str
    container_id: str
    port: int
    status: str
    created_at: datetime
    health_check_url: str

class BotOrchestrator:
    """Manages dynamic deployment of character bots"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.db_adapter = CDLDatabaseAdapter()
        self.deployed_bots: Dict[int, BotDeployment] = {}
        self.port_start = int(os.getenv("BOT_PORT_START", "9090"))
        self.image_name = f"whisperengine-bot:{os.getenv('VERSION', 'latest')}"
        self.network_name = os.getenv("NETWORK_NAME", "whisperengine-platform")
        self.running = True
        
        # Database connection details
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "whisperengine"),
            "password": os.getenv("POSTGRES_PASSWORD", "whisperengine_password"),
            "database": os.getenv("POSTGRES_DB", "whisperengine")
        }
    
    async def get_database_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        return await asyncpg.connect(**self.db_config)
    
    async def get_characters_with_deployment_config(self) -> List[Dict]:
        """Get all characters that should be deployed"""
        conn = await self.get_database_connection()
        try:
            query = """
            SELECT 
                c.id,
                c.name,
                c.display_name,
                dc.enabled,
                dc.auto_start,
                dc.port,
                dc.resource_limits,
                llm.provider as llm_provider,
                llm.api_key as llm_api_key,
                disc.bot_token as discord_token
            FROM characters c
            LEFT JOIN character_deployment_config dc ON c.id = dc.character_id
            LEFT JOIN character_llm_config llm ON c.id = llm.character_id  
            LEFT JOIN character_discord_config disc ON c.id = disc.character_id
            WHERE dc.enabled = true AND dc.auto_start = true
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
    
    def get_next_available_port(self) -> int:
        """Find next available port starting from port_start"""
        used_ports = {bot.port for bot in self.deployed_bots.values()}
        port = self.port_start
        while port in used_ports:
            port += 1
        return port
    
    async def deploy_character_bot(self, character_config: Dict) -> BotDeployment:
        """Deploy a single character bot container"""
        character_id = character_config["id"]
        character_name = character_config["name"]
        
        # Check if already deployed
        if character_id in self.deployed_bots:
            logger.info(f"Character {character_name} already deployed")
            return self.deployed_bots[character_id]
        
        # Assign port
        port = character_config.get("port") or self.get_next_available_port()
        
        # Container configuration
        container_name = f"whisperengine-{character_name.lower()}-bot"
        
        # Environment variables for the bot
        environment = {
            "DISCORD_BOT_NAME": character_name,
            "POSTGRES_HOST": "postgres",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": self.db_config["user"],
            "POSTGRES_PASSWORD": self.db_config["password"],
            "POSTGRES_DB": self.db_config["database"],
            "QDRANT_HOST": "qdrant",
            "QDRANT_PORT": "6333",
            "HEALTH_CHECK_PORT": str(port),
            "HEALTH_CHECK_HOST": "0.0.0.0",
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "PYTHONUNBUFFERED": "1",
            "MODEL_CACHE_DIR": "/app/models",
            "HF_HOME": "/app/cache/huggingface",
            "FASTEMBED_CACHE_PATH": "/app/cache/fastembed"
        }
        
        # Add LLM config if available
        if character_config.get("llm_provider"):
            environment["LLM_PROVIDER"] = character_config["llm_provider"]
        if character_config.get("llm_api_key"):
            environment["LLM_API_KEY"] = character_config["llm_api_key"]
            
        # Add Discord token if available
        if character_config.get("discord_token"):
            environment["DISCORD_BOT_TOKEN"] = character_config["discord_token"]
        
        # Resource limits
        resource_limits = character_config.get("resource_limits", {})
        if isinstance(resource_limits, str):
            resource_limits = json.loads(resource_limits)
        
        mem_limit = resource_limits.get("memory", "2G")
        cpu_limit = resource_limits.get("cpu", "2.0")
        
        try:
            # Create and start container
            container = self.docker_client.containers.run(
                image=self.image_name,
                name=container_name,
                environment=environment,
                ports={f"{port}/tcp": port},
                network=self.network_name,
                mem_limit=mem_limit,
                cpu_count=float(cpu_limit),
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                healthcheck={
                    "test": f"curl -f http://localhost:{port}/health || exit 1",
                    "interval": 30000000000,  # 30s in nanoseconds
                    "timeout": 10000000000,   # 10s in nanoseconds
                    "retries": 3,
                    "start_period": 40000000000  # 40s in nanoseconds
                }
            )
            
            deployment = BotDeployment(
                character_id=character_id,
                character_name=character_name,
                container_name=container_name,
                container_id=container.id,
                port=port,
                status="starting",
                created_at=datetime.now(),
                health_check_url=f"http://localhost:{port}/health"
            )
            
            self.deployed_bots[character_id] = deployment
            logger.info(f"Deployed character bot: {character_name} on port {port}")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy character {character_name}: {e}")
            raise
    
    async def remove_character_bot(self, character_id: int) -> bool:
        """Remove a deployed character bot"""
        if character_id not in self.deployed_bots:
            return False
        
        deployment = self.deployed_bots[character_id]
        
        try:
            container = self.docker_client.containers.get(deployment.container_id)
            container.stop(timeout=30)
            container.remove()
            
            del self.deployed_bots[character_id]
            logger.info(f"Removed character bot: {deployment.character_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove character {deployment.character_name}: {e}")
            return False
    
    async def sync_deployments(self):
        """Sync deployed bots with database configuration"""
        try:
            # Get desired state from database
            desired_characters = await self.get_characters_with_deployment_config()
            desired_ids = {char["id"] for char in desired_characters}
            current_ids = set(self.deployed_bots.keys())
            
            # Deploy new characters
            to_deploy = desired_ids - current_ids
            for character_config in desired_characters:
                if character_config["id"] in to_deploy:
                    await self.deploy_character_bot(character_config)
            
            # Remove characters no longer needed
            to_remove = current_ids - desired_ids
            for character_id in to_remove:
                await self.remove_character_bot(character_id)
                
            # Update deployment status
            await self.update_deployment_status()
            
        except Exception as e:
            logger.error(f"Error syncing deployments: {e}")
    
    async def update_deployment_status(self):
        """Update the status of deployed bots"""
        for deployment in self.deployed_bots.values():
            try:
                container = self.docker_client.containers.get(deployment.container_id)
                deployment.status = container.status
            except Exception as e:
                logger.error(f"Failed to get status for {deployment.character_name}: {e}")
                deployment.status = "unknown"
    
    async def run_orchestrator(self):
        """Main orchestrator loop"""
        logger.info("Starting Bot Orchestrator...")
        
        while self.running:
            try:
                await self.sync_deployments()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Orchestrator stopping...")

# FastAPI app for orchestrator management
app = FastAPI(title="WhisperEngine Bot Orchestrator", version="1.0.0")
orchestrator = BotOrchestrator()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/deployments")
async def get_deployments():
    """Get current bot deployments"""
    await orchestrator.update_deployment_status()
    return {
        "deployments": [
            {
                "character_id": dep.character_id,
                "character_name": dep.character_name,
                "container_name": dep.container_name,
                "port": dep.port,
                "status": dep.status,
                "health_check_url": dep.health_check_url,
                "created_at": dep.created_at.isoformat()
            }
            for dep in orchestrator.deployed_bots.values()
        ]
    }

@app.post("/deployments/{character_id}/restart")
async def restart_deployment(character_id: int):
    """Restart a specific character bot"""
    if character_id not in orchestrator.deployed_bots:
        raise HTTPException(status_code=404, detail="Character bot not found")
    
    deployment = orchestrator.deployed_bots[character_id]
    try:
        container = orchestrator.docker_client.containers.get(deployment.container_id)
        container.restart(timeout=30)
        return {"message": f"Restarted {deployment.character_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart: {e}")

@app.post("/sync")
async def force_sync():
    """Force sync with database"""
    await orchestrator.sync_deployments()
    return {"message": "Sync completed"}

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    orchestrator.stop()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run orchestrator and API server
    async def main():
        # Start orchestrator in background
        orchestrator_task = asyncio.create_task(orchestrator.run_orchestrator())
        
        # Start API server
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            await server.serve()
        finally:
            orchestrator.stop()
            await orchestrator_task
    
    asyncio.run(main())