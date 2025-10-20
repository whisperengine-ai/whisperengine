#!/bin/bash
#
# Check Conversation Summary Quality Metrics
# Usage: ./check_summary_quality.sh [query_number]
#
# If no query number provided, runs Query 1 (overall metrics)

QUERY=${1:-1}

case $QUERY in
  1)
    echo "📊 QUERY 1: Overall Quality Metrics (Last 7 Days)"
    ;;
  2)
    echo "📊 QUERY 2: Quality Issues by Bot (Last 7 Days)"
    ;;
  3)
    echo "📊 QUERY 3: Recent Fallback Summaries (Need Investigation)"
    ;;
  4)
    echo "📊 QUERY 4: Quality Trend Over Time (Daily Aggregates)"
    ;;
  5)
    echo "📊 QUERY 5: Summary Length Distribution"
    ;;
  6)
    echo "📊 QUERY 6: Compression Ratio Distribution"
    ;;
  all)
    echo "📊 RUNNING ALL QUALITY QUERIES"
    ;;
  *)
    echo "❌ Invalid query number. Use 1-6 or 'all'"
    exit 1
    ;;
esac

echo ""

if [ "$QUERY" = "all" ]; then
  # Run all queries
  docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres \
    psql -U whisperengine -d whisperengine -f /scripts/monitoring/check_summary_quality.sql
else
  # Run specific query by extracting it from the SQL file
  docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres \
    psql -U whisperengine -d whisperengine -c "$(sed -n "/-- Query ${QUERY}:/,/^$/p" scripts/monitoring/check_summary_quality.sql | grep -v '^--')"
fi
