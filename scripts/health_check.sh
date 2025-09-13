#!/bin/bash

# WhisperEngine Infrastructure Health Check
# Validates all 4 required datastores are accessible

echo "🔍 WhisperEngine Infrastructure Health Check"
echo "============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
tests_passed=0
tests_total=0

# Test function
test_service() {
    local service_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    ((tests_total++))
    echo -n "Testing $service_name... "
    
    if eval "$test_command" 2>/dev/null | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((tests_passed++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo
echo "🔄 Testing Datastore Connectivity:"

# PostgreSQL
test_service "PostgreSQL" "PGPASSWORD=bot_password_change_me psql -h localhost -p 5432 -U bot_user -d whisper_engine -c 'SELECT 1'" "1"

# Redis
test_service "Redis" "redis-cli -h localhost -p 6379 ping" "PONG"

# ChromaDB
test_service "ChromaDB" "curl -s http://localhost:8000/api/v2/version" "1.0.0"

# Neo4j
test_service "Neo4j Web" "curl -s http://localhost:7474" "neo4j_version"

echo
echo "📊 Test Results: $tests_passed/$tests_total tests passed"

if [[ $tests_passed -eq $tests_total ]]; then
    echo -e "${GREEN}🎉 All datastores are healthy and accessible!${NC}"
    echo
    echo "📋 Service Endpoints:"
    echo "   PostgreSQL: localhost:5432 (user: bot_user, db: whisper_engine)"
    echo "   Redis:      localhost:6379"
    echo "   ChromaDB:   localhost:8000"
    echo "   Neo4j:      localhost:7474 (web) / localhost:7687 (bolt)"
    echo
    echo "💾 Persistent Data Volumes:"
    echo "   PostgreSQL: discord-bot-postgres"
    echo "   Redis:      discord-bot-redis" 
    echo "   ChromaDB:   discord-bot-chromadb"
    echo "   Neo4j:      discord-bot-neo4j-data, discord-bot-neo4j-logs"
    exit 0
else
    echo -e "${RED}❌ Some services are not accessible${NC}"
    echo -e "${YELLOW}💡 Try: ./bot.sh status${NC}"
    exit 1
fi