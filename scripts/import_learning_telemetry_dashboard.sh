#!/bin/bash
# Import Learning System Telemetry Dashboard to Grafana

GRAFANA_URL="http://localhost:3002"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Read the dashboard JSON
DASHBOARD_JSON=$(cat grafana_dashboards/learning_system_telemetry.json)

# Create the API payload
API_PAYLOAD=$(cat <<EOF
{
  "dashboard": $(echo "$DASHBOARD_JSON" | jq '.dashboard'),
  "folderId": 0,
  "overwrite": true
}
EOF
)

echo "🚀 Importing Learning System Telemetry Dashboard to Grafana..."
echo "📍 Grafana URL: $GRAFANA_URL"
echo ""

# Import the dashboard
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "$GRAFANA_URL/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
  -d "$API_PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ Dashboard imported successfully!"
  echo ""
  DASHBOARD_UID=$(echo "$BODY" | jq -r '.uid')
  DASHBOARD_URL=$(echo "$BODY" | jq -r '.url')
  echo "📊 Dashboard UID: $DASHBOARD_UID"
  echo "🔗 Dashboard URL: $GRAFANA_URL$DASHBOARD_URL"
  echo ""
  echo "🎯 Open in browser: $GRAFANA_URL$DASHBOARD_URL"
elif [ "$HTTP_CODE" -eq 401 ]; then
  echo "❌ Authentication failed!"
  echo "   Default credentials: admin/admin"
  echo "   If you changed the password, update the script."
else
  echo "❌ Import failed with HTTP $HTTP_CODE"
  echo ""
  echo "Response:"
  echo "$BODY" | jq '.'
fi
