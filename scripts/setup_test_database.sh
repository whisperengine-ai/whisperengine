#!/bin/bash
"""
Create Test Database for CDL Import Testing

Creates a separate test database so we can safely test imports
without risking production character data.

Usage:
    ./scripts/setup_test_database.sh
"""

set -e  # Exit on error

echo "🧪 Setting up test database for CDL import testing"
echo "=================================================="
echo ""

# Database configuration
TEST_DB="whisperengine_test"
PROD_DB="whisperengine"
DB_USER="whisperengine"
DB_PASSWORD="whisperengine_password"
DB_HOST="localhost"
DB_PORT="5433"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "📋 Configuration:"
echo "  Production DB: $PROD_DB"
echo "  Test DB: $TEST_DB"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  User: $DB_USER"
echo ""

# Check if PostgreSQL is running
if ! docker ps | grep -q postgres; then
    echo -e "${RED}❌ PostgreSQL container not running${NC}"
    echo "Start it with: docker-compose up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Check if test database already exists
if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $TEST_DB; then
    echo -e "${YELLOW}⚠️  Test database already exists${NC}"
    read -p "Do you want to DROP and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Dropping existing test database..."
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"
    else
        echo "Keeping existing test database"
        exit 0
    fi
fi

# Create test database
echo "🏗️  Creating test database..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $TEST_DB;"

echo "✅ Test database created"
echo ""

# Copy schema from production database
echo "📋 Copying schema from production database..."
echo "  (This may take a minute...)"

# Export schema only (no data)
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER --schema-only $PROD_DB > /tmp/whisperengine_schema.sql

# Import schema to test database
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB < /tmp/whisperengine_schema.sql > /dev/null 2>&1

# Clean up
rm /tmp/whisperengine_schema.sql

echo "✅ Schema copied"
echo ""

# Verify tables were created
TABLE_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo "📊 Test database statistics:"
echo "  Tables created: $TABLE_COUNT"
echo ""

# Create .env.test file for testing
ENV_TEST_FILE=".env.test"

echo "📝 Creating $ENV_TEST_FILE for test environment..."

cat > $ENV_TEST_FILE << EOF
# Test Database Configuration
# DO NOT USE IN PRODUCTION!

POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=whisperengine_test
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=whisperengine_password

# Note: This points to the TEST database
# Production database: whisperengine
# Test database: whisperengine_test
EOF

echo "✅ Created $ENV_TEST_FILE"
echo ""

echo "=================================================="
echo "✅ Test database setup complete!"
echo "=================================================="
echo ""
echo "📋 How to use:"
echo ""
echo "1. For testing imports, use:"
echo "   export POSTGRES_DB=whisperengine_test"
echo "   python scripts/import_character_from_yaml.py test_character.yaml"
echo ""
echo "2. Or use the test env file:"
echo "   source <(grep -v '^#' .env.test | xargs -I {} echo export {})"
echo "   python scripts/import_character_from_yaml.py test_character.yaml"
echo ""
echo "3. To verify test data:"
echo "   psql -h localhost -p 5433 -U whisperengine -d whisperengine_test"
echo ""
echo "4. To drop test database when done:"
echo "   psql -h localhost -p 5433 -U whisperengine -d postgres -c 'DROP DATABASE whisperengine_test;'"
echo ""
echo "⚠️  IMPORTANT: Test database is empty - import test characters to verify!"
