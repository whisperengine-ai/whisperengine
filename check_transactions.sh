#!/bin/bash

# Quick script to check recent transactions in the database
echo "🔍 Checking recent role_transactions..."

docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
    transaction_id,
    user_id,
    bot_name,
    transaction_type,
    state,
    context,
    created_at
FROM role_transactions 
ORDER BY created_at DESC 
LIMIT 10;
"

echo ""
echo "📊 Transaction summary:"
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
    bot_name,
    transaction_type,
    state,
    COUNT(*) as count
FROM role_transactions 
GROUP BY bot_name, transaction_type, state
ORDER BY bot_name, transaction_type, state;
"