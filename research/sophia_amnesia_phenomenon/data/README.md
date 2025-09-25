# Sophia Research Data Directory

## Data Collection Areas

### Conversation Logs
- Original Sophia-MarkAnthony angry conversation logs
- Multi-user interruption conversation logs  
- Post-amnesia conversation logs
- Control group conversations (normal behavior)

### Memory System State Dumps
- Vector memory contents before/after amnesia
- Emotional metadata in memory entries
- Memory retrieval query results
- Conversation history cache states

### Emotional Analysis Data
- Real-time emotion detection results
- Emotional intensity measurements over time
- Emotional context persistence patterns
- Cross-session emotional state tracking

### System Performance Metrics
- Memory cleanup execution logs
- User switching trigger events
- Safety intervention activations  
- Character personality consistency measurements

## Data Collection Commands

### Export Conversation Logs
```bash
# Export Discord conversation logs (requires Discord API)
# python export_discord_logs.py --user-id [USER] --bot-name sophia --date-range [RANGE]
```

### Memory System State Dump
```bash
# Export current memory state for analysis
# python dump_memory_state.py --user-id [USER] --output data/memory_dump_$(date +%Y%m%d).json
```

### Emotional Analysis Export
```bash
# Export emotional metadata from vector memory
# python export_emotional_data.py --user-id [USER] --output data/emotional_analysis_$(date +%Y%m%d).json
```

## Data Privacy & Ethics

### Anonymization Required
- Remove all personal identifying information
- Replace Discord user IDs with research identifiers  
- Anonymize any personal details shared in conversations
- Obtain explicit consent for research use

### Data Retention Policy
- Raw conversation logs: 90 days maximum
- Anonymized research data: Until research completion
- Published data: Permanent retention with full anonymization
- Safety incident logs: 1 year for regulatory compliance

---

*Place all collected data files in appropriate subdirectories with clear naming conventions and timestamp information.*