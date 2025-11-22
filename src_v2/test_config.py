import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from src_v2.config.settings import settings

def test_config():
    print("--- Configuration Test ---")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"LLM Model: {settings.LLM_MODEL_NAME}")
    
    # Secrets should be masked
    print(f"Discord Token: {settings.DISCORD_TOKEN.get_secret_value()[:5]}..." if settings.DISCORD_TOKEN else "None")
    print(f"Postgres URL: {settings.POSTGRES_URL}")
    print(f"Neo4j Password: {settings.NEO4J_PASSWORD.get_secret_value()[:3]}..." if settings.NEO4J_PASSWORD else "None")
    
    print("\nConfiguration loaded successfully!")

if __name__ == "__main__":
    try:
        test_config()
    except Exception as e:
        print(f"Configuration failed: {e}")
