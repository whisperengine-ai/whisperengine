-- Roleplay Transaction State Table
-- For tracking stateful interactions like drink orders, purchases, quests, etc.

CREATE TABLE IF NOT EXISTS roleplay_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,  -- 'drink_order', 'quest', 'purchase', 'service', etc.
    state VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'awaiting_payment', 'completed', 'cancelled'
    context JSONB NOT NULL DEFAULT '{}',  -- Flexible transaction data
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Create indexes (removed overly restrictive unique constraint)
CREATE INDEX IF NOT EXISTS idx_roleplay_user_bot ON roleplay_transactions(user_id, bot_name);
CREATE INDEX IF NOT EXISTS idx_roleplay_state ON roleplay_transactions(state) WHERE completed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_roleplay_created ON roleplay_transactions(created_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_roleplay_transaction_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp on row updates
DROP TRIGGER IF EXISTS trigger_update_roleplay_transaction_timestamp ON roleplay_transactions;
CREATE TRIGGER trigger_update_roleplay_transaction_timestamp
    BEFORE UPDATE ON roleplay_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_roleplay_transaction_timestamp();

-- Example transaction data for Dotty the bartender:
-- {
--   "drink": "whiskey",
--   "price": 5,
--   "quantity": 1,
--   "special_requests": "on the rocks",
--   "order_message": "I'll have a whiskey on the rocks"
-- }

-- Example queries:
-- Check pending transactions for user: SELECT * FROM roleplay_transactions WHERE user_id = '123' AND bot_name = 'dotty' AND state = 'pending';
-- Complete transaction: UPDATE roleplay_transactions SET state = 'completed', completed_at = NOW() WHERE id = 1;
-- Get transaction history: SELECT * FROM roleplay_transactions WHERE user_id = '123' AND bot_name = 'dotty' ORDER BY created_at DESC LIMIT 10;
