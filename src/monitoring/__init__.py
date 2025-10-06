"""
Monitoring Integration

Minimal monitoring - Docker healthchecks handle container orchestration.
Performance metrics handled by InfluxDB via fidelity_metrics_collector.py.
"""

import logging

logger = logging.getLogger(__name__)

# Export public API (minimal - most monitoring is via Docker healthchecks)
__all__ = []

logger.info("Monitoring module loaded - using Docker healthchecks for container orchestration")
