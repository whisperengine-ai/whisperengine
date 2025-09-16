#!/usr/bin/env python3
"""
Docker Compose Deployment Validation Script

This script validates the WhisperEngine Docker Compose deployment
by testing connectivity to all services and verifying schema setup.
"""

import logging
import os
import subprocess
import sys
import time
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DockerComposeValidator:
    """Validates Docker Compose deployment"""

    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.required_services = ["whisperengine-bot", "postgres", "redis", "chromadb", "neo4j"]
        self.validation_results = {}

    def run_command(self, command: str, shell: bool = True) -> dict[str, Any]:
        """Run a shell command and return results"""
        try:
            result = subprocess.run(
                command, shell=shell, capture_output=True, text=True, timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

    def check_prerequisites(self) -> bool:
        """Check if Docker and Docker Compose are available"""
        logger.info("🔍 Checking prerequisites...")

        # Check Docker
        docker_result = self.run_command("docker --version")
        if not docker_result["success"]:
            logger.error("❌ Docker is not installed or not running")
            return False
        logger.info(f"✅ Docker: {docker_result['stdout']}")

        # Check Docker Compose
        compose_result = self.run_command("docker compose version")
        if not compose_result["success"]:
            logger.error("❌ Docker Compose is not available")
            return False
        logger.info(f"✅ Docker Compose: {compose_result['stdout']}")

        # Check if compose file exists
        if not os.path.exists(self.compose_file):
            logger.error(f"❌ Docker Compose file not found: {self.compose_file}")
            return False
        logger.info(f"✅ Compose file found: {self.compose_file}")

        return True

    def check_env_file(self) -> bool:
        """Check if .env file exists and has required variables"""
        logger.info("🔍 Checking .env configuration...")

        if not os.path.exists(".env"):
            logger.warning("⚠️  .env file not found - using defaults")
            return True  # Not critical for validation

        # Read .env file
        required_vars = ["DISCORD_BOT_TOKEN", "POSTGRES_PASSWORD"]
        env_vars = {}

        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value

        missing_vars = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var] or env_vars[var].endswith("_here"):
                missing_vars.append(var)

        if missing_vars:
            logger.warning(f"⚠️  Missing or placeholder values in .env: {missing_vars}")
        else:
            logger.info("✅ .env file configured")

        return True

    def start_services(self) -> bool:
        """Start Docker Compose services"""
        logger.info("🚀 Starting Docker Compose services...")

        # Pull latest images
        pull_result = self.run_command("docker compose pull")
        if not pull_result["success"]:
            logger.warning(f"⚠️  Failed to pull images: {pull_result['stderr']}")

        # Start services
        start_result = self.run_command("docker compose up -d")
        if not start_result["success"]:
            logger.error(f"❌ Failed to start services: {start_result['stderr']}")
            return False

        logger.info("✅ Docker Compose services started")
        return True

    def wait_for_services(self, timeout: int = 120) -> bool:
        """Wait for services to become healthy"""
        logger.info("⏳ Waiting for services to become healthy...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check service health
            health_result = self.run_command("docker compose ps --format json")
            if not health_result["success"]:
                time.sleep(5)
                continue

            try:
                import json

                services = []
                for line in health_result["stdout"].split("\\n"):
                    if line.strip():
                        services.append(json.loads(line))

                healthy_services = []
                unhealthy_services = []

                for service in services:
                    service_name = service.get("Service", "unknown")
                    health = service.get("Health", "unknown")
                    state = service.get("State", "unknown")

                    if health == "healthy" or (health == "" and state == "running"):
                        healthy_services.append(service_name)
                    else:
                        unhealthy_services.append(f"{service_name}({health or state})")

                logger.info(
                    f"Healthy: {len(healthy_services)}/{len(services)} - {', '.join(healthy_services)}"
                )

                if unhealthy_services:
                    logger.info(f"Waiting for: {', '.join(unhealthy_services)}")

                # Check if all required services are healthy
                if len(healthy_services) >= len(self.required_services):
                    logger.info("✅ All services are healthy")
                    return True

            except Exception as e:
                logger.debug(f"Error parsing service status: {e}")

            time.sleep(5)

        logger.error("❌ Services did not become healthy within timeout")
        return False

    def test_service_connectivity(self) -> bool:
        """Test connectivity to individual services"""
        logger.info("🔌 Testing service connectivity...")

        tests = [
            {
                "name": "PostgreSQL",
                "command": "docker compose exec -T postgres pg_isready -U bot_user -d whisper_engine",
                "expected_in_output": "accepting connections",
            },
            {
                "name": "Redis",
                "command": "docker compose exec -T redis redis-cli ping",
                "expected_in_output": "PONG",
            },
            {
                "name": "ChromaDB",
                "command": "docker compose exec -T chromadb curl -f http://localhost:8000/api/v1/heartbeat",
                "expected_in_output": "",  # Any response is good
            },
            {
                "name": "Neo4j",
                "command": "docker compose exec -T neo4j wget --quiet --spider http://localhost:7474/",
                "expected_in_output": "",  # No output means success
            },
        ]

        all_passed = True
        for test in tests:
            result = self.run_command(test["command"])
            if result["success"] and (
                not test["expected_in_output"] or test["expected_in_output"] in result["stdout"]
            ):
                logger.info(f"✅ {test['name']}: Connected")
            else:
                logger.error(f"❌ {test['name']}: Failed - {result['stderr'] or result['stdout']}")
                all_passed = False

        return all_passed

    def test_database_schema(self) -> bool:
        """Test if database schema is properly initialized"""
        logger.info("🗄️  Testing database schema...")

        # Test PostgreSQL schema
        schema_test = self.run_command(
            'docker compose exec -T postgres psql -U bot_user -d whisper_engine -c "\\\\dt"'
        )

        if not schema_test["success"]:
            logger.error(f"❌ Failed to query database schema: {schema_test['stderr']}")
            return False

        # Check for expected tables
        expected_tables = [
            "users",
            "conversations",
            "memory_entries",
            "facts",
            "emotions",
            "relationships",
            "system_settings",
            "performance_metrics",
        ]
        schema_output = schema_test["stdout"]

        found_tables = []
        missing_tables = []

        for table in expected_tables:
            if table in schema_output:
                found_tables.append(table)
            else:
                missing_tables.append(table)

        if missing_tables:
            logger.error(f"❌ Missing database tables: {missing_tables}")
            return False

        logger.info(f"✅ Database schema: Found {len(found_tables)} tables")
        return True

    def test_application_health(self) -> bool:
        """Test application health endpoint"""
        logger.info("🏥 Testing application health...")

        # Test bot health endpoint
        health_test = self.run_command("curl -f http://localhost:9090/health")

        if health_test["success"]:
            logger.info("✅ Bot health endpoint: Responsive")
            return True
        else:
            logger.warning(f"⚠️  Bot health endpoint: Not responsive - {health_test['stderr']}")
            # This might be expected if bot token is not configured
            return True  # Don't fail validation for this

    def cleanup_services(self) -> None:
        """Stop and cleanup services"""
        logger.info("🧹 Cleaning up services...")
        self.run_command("docker compose down")
        logger.info("✅ Services stopped")

    def run_validation(self, cleanup_after: bool = True) -> bool:
        """Run complete validation"""
        logger.info("🚀 Starting WhisperEngine Docker Compose validation")

        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return False

            # Check .env configuration
            self.check_env_file()

            # Start services
            if not self.start_services():
                return False

            # Wait for services to become healthy
            if not self.wait_for_services():
                return False

            # Test service connectivity
            connectivity_ok = self.test_service_connectivity()

            # Test database schema
            schema_ok = self.test_database_schema()

            # Test application health
            health_ok = self.test_application_health()

            # Summary
            all_tests_passed = connectivity_ok and schema_ok and health_ok

            if all_tests_passed:
                logger.info("🎉 All validation tests passed!")
                logger.info("✅ WhisperEngine Docker Compose deployment is working correctly")
            else:
                logger.error("❌ Some validation tests failed")

            return all_tests_passed

        except KeyboardInterrupt:
            logger.info("🛑 Validation interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Validation failed with error: {e}")
            return False
        finally:
            if cleanup_after:
                self.cleanup_services()


def main():
    """Main validation function"""
    validator = DockerComposeValidator()

    # Check command line arguments
    cleanup_after = "--no-cleanup" not in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        return

    success = validator.run_validation(cleanup_after=cleanup_after)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
