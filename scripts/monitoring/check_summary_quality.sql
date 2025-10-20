-- Conversation Summary Quality Monitoring Queries
-- Run these queries to track enrichment worker summary quality over time

-- Query 1: Overall Quality Metrics (Last 100 Summaries)
SELECT 
    COUNT(*) as total_summaries,
    COUNT(*) FILTER (WHERE 'general conversation' = ANY(key_topics)) as fallback_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE 'general conversation' = ANY(key_topics)) / COUNT(*), 2) as fallback_percentage,
    ROUND(AVG(compression_ratio)::numeric, 3) as avg_compression,
    ROUND(AVG(confidence_score)::numeric, 3) as avg_confidence,
    ROUND(AVG(message_count)::numeric, 1) as avg_messages,
    ROUND(AVG(LENGTH(summary_text))::numeric, 0) as avg_summary_length
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Query 2: Quality Issues by Bot (Last 7 Days)
SELECT 
    bot_name,
    COUNT(*) as total_summaries,
    COUNT(*) FILTER (WHERE LENGTH(summary_text) < 100) as too_short_count,
    COUNT(*) FILTER (WHERE compression_ratio < 0.05) as over_compressed_count,
    COUNT(*) FILTER (WHERE 'general conversation' = ANY(key_topics)) as fallback_count,
    ROUND(AVG(compression_ratio)::numeric, 3) as avg_compression,
    ROUND(AVG(LENGTH(summary_text))::numeric, 0) as avg_length
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY bot_name
ORDER BY total_summaries DESC;

-- Query 3: Recent Fallback Summaries (Need Investigation)
SELECT 
    bot_name,
    user_id,
    message_count,
    LENGTH(summary_text) as summary_length,
    compression_ratio,
    confidence_score,
    created_at
FROM conversation_summaries
WHERE 'general conversation' = ANY(key_topics)
    AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 10;

-- Query 4: Quality Trend Over Time (Daily Aggregates)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as summaries_generated,
    COUNT(*) FILTER (WHERE 'general conversation' = ANY(key_topics)) as fallback_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE 'general conversation' = ANY(key_topics)) / COUNT(*), 2) as fallback_pct,
    ROUND(AVG(compression_ratio)::numeric, 3) as avg_compression,
    ROUND(AVG(confidence_score)::numeric, 3) as avg_confidence
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Query 5: Summary Length Distribution
SELECT 
    CASE 
        WHEN LENGTH(summary_text) < 100 THEN 'Very Short (<100)'
        WHEN LENGTH(summary_text) < 300 THEN 'Short (100-300)'
        WHEN LENGTH(summary_text) < 600 THEN 'Medium (300-600)'
        WHEN LENGTH(summary_text) < 1000 THEN 'Long (600-1000)'
        ELSE 'Very Long (1000+)'
    END as length_category,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY length_category
ORDER BY MIN(LENGTH(summary_text));

-- Query 6: Compression Ratio Distribution
SELECT 
    CASE 
        WHEN compression_ratio < 0.1 THEN 'Very High (<10%)'
        WHEN compression_ratio < 0.3 THEN 'High (10-30%)'
        WHEN compression_ratio < 0.5 THEN 'Medium (30-50%)'
        WHEN compression_ratio < 0.7 THEN 'Low (50-70%)'
        ELSE 'Very Low (70%+)'
    END as compression_category,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY compression_category
ORDER BY MIN(compression_ratio);
