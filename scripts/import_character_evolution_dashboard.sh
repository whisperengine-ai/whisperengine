#!/bin/bash

# Character Emotional Evolution Dashboard Import Script
# Imports the dashboard into Grafana via API

set -e

GRAFANA_URL="http://localhost:3002"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"
DASHBOARD_FILE="grafana_dashboards/character_emotional_evolution.json"

echo "🚀 Importing Character Emotional Evolution Dashboard to Grafana..."
echo ""

# Check if dashboard file exists
if [ ! -f "$DASHBOARD_FILE" ]; then
    echo "❌ Error: Dashboard file not found: $DASHBOARD_FILE"
    exit 1
fi

# Check if Grafana is running
if ! curl -s "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Grafana at $GRAFANA_URL"
    echo "   Make sure Grafana is running: docker ps | grep grafana"
    exit 1
fi

echo "✅ Grafana is running at $GRAFANA_URL"
echo ""

# Read dashboard JSON
DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")

# Wrap in import structure
IMPORT_PAYLOAD=$(jq -n \
    --argjson dashboard "$DASHBOARD_JSON" \
    '{
        "dashboard": $dashboard,
        "overwrite": true,
        "inputs": [],
        "folderUid": ""
    }')

# Import dashboard
echo "📤 Importing dashboard..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d "$IMPORT_PAYLOAD" \
    "$GRAFANA_URL/api/dashboards/import")

# Check response
if echo "$RESPONSE" | jq -e '.uid' > /dev/null 2>&1; then
    DASHBOARD_UID=$(echo "$RESPONSE" | jq -r '.uid')
    DASHBOARD_URL="$GRAFANA_URL/d/$DASHBOARD_UID/character-emotional-evolution"
    
    echo ""
    echo "✅ Dashboard imported successfully!"
    echo ""
    echo "📊 Dashboard URL: $DASHBOARD_URL"
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Open: $DASHBOARD_URL"
    echo "   2. Select bot character from dropdown (default: elena)"
    echo "   3. Adjust time range (default: Last 7 days)"
    echo "   4. Set refresh rate (default: 30 seconds)"
    echo ""
    echo "💡 Tip: Send a message to Elena to generate new data points!"
    echo ""
else
    echo ""
    echo "❌ Dashboard import failed!"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.'
    echo ""
    echo "Possible issues:"
    echo "   - Grafana credentials incorrect (default: admin/admin)"
    echo "   - InfluxDB datasource not configured"
    echo "   - Dashboard JSON invalid"
    echo ""
    echo "Try manual import:"
    echo "   1. Open Grafana: $GRAFANA_URL"
    echo "   2. Navigate to Dashboards → Import"
    echo "   3. Upload: $DASHBOARD_FILE"
    echo ""
    exit 1
fi
