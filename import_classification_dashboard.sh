#!/bin/bash

# Import Vector Classification Intelligence Dashboard to Grafana
# This script imports the dashboard JSON file via Grafana API

set -e

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="whisperengine_grafana"
DASHBOARD_FILE="grafana_dashboards/vector_classification_intelligence.json"

echo "🎯 Importing Vector Classification Intelligence Dashboard"
echo "=========================================================="
echo ""
echo "Grafana URL: $GRAFANA_URL"
echo "Dashboard File: $DASHBOARD_FILE"
echo ""

# Check if dashboard file exists
if [ ! -f "$DASHBOARD_FILE" ]; then
    echo "❌ Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

# Check if Grafana is accessible
echo "🔍 Checking Grafana connectivity..."
if ! curl -s "$GRAFANA_URL/api/health" > /dev/null; then
    echo "❌ Cannot connect to Grafana at $GRAFANA_URL"
    echo "   Make sure Grafana is running: docker ps | grep grafana"
    exit 1
fi

echo "✅ Grafana is accessible"
echo ""

# Get InfluxDB data source UID
echo "🔍 Finding InfluxDB data source..."
DATASOURCE_RESPONSE=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" \
    "$GRAFANA_URL/api/datasources/name/InfluxDB")

if echo "$DATASOURCE_RESPONSE" | grep -q "uid"; then
    DATASOURCE_UID=$(echo "$DATASOURCE_RESPONSE" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Found InfluxDB data source: $DATASOURCE_UID"
else
    echo "⚠️  InfluxDB data source not found, using default 'influxdb'"
    DATASOURCE_UID="influxdb"
fi
echo ""

# Prepare dashboard JSON with correct data source UID
echo "📝 Preparing dashboard configuration..."
DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")

# Replace datasource UID placeholders with actual UID
DASHBOARD_JSON=$(echo "$DASHBOARD_JSON" | sed "s/\"uid\": \"influxdb\"/\"uid\": \"$DATASOURCE_UID\"/g")

# Wrap dashboard in API format
API_PAYLOAD=$(cat <<EOF
{
  "dashboard": $(echo "$DASHBOARD_JSON" | jq '.dashboard'),
  "overwrite": true,
  "message": "Imported Vector Classification Intelligence Dashboard"
}
EOF
)

echo "✅ Dashboard prepared"
echo ""

# Import dashboard
echo "📤 Importing dashboard to Grafana..."
IMPORT_RESPONSE=$(curl -s -X POST \
    -u "$GRAFANA_USER:$GRAFANA_PASS" \
    -H "Content-Type: application/json" \
    -d "$API_PAYLOAD" \
    "$GRAFANA_URL/api/dashboards/db")

# Check if import was successful
if echo "$IMPORT_RESPONSE" | grep -q '"status":"success"'; then
    DASHBOARD_URL=$(echo "$IMPORT_RESPONSE" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
    DASHBOARD_ID=$(echo "$IMPORT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    
    echo "✅ Dashboard imported successfully!"
    echo ""
    echo "📊 Dashboard Details:"
    echo "   - ID: $DASHBOARD_ID"
    echo "   - URL: $GRAFANA_URL$DASHBOARD_URL"
    echo ""
    echo "🌐 Open dashboard:"
    echo "   $GRAFANA_URL$DASHBOARD_URL"
    echo ""
    echo "📝 Login credentials:"
    echo "   Username: $GRAFANA_USER"
    echo "   Password: $GRAFANA_PASS"
    
elif echo "$IMPORT_RESPONSE" | grep -q '"message"'; then
    ERROR_MSG=$(echo "$IMPORT_RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
    echo "❌ Import failed: $ERROR_MSG"
    echo ""
    echo "Full response:"
    echo "$IMPORT_RESPONSE" | jq '.'
    exit 1
else
    echo "❌ Import failed with unknown error"
    echo ""
    echo "Full response:"
    echo "$IMPORT_RESPONSE"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Open the dashboard URL above"
echo "2. Wait 1-2 minutes for data to populate (or refresh with test queries)"
echo "3. Set up alerts if needed (see NEXT_STEPS_CLASSIFICATION_GRAFANA.md)"
echo ""
