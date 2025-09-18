# WhisperEngine Utilities

This directory contains development utilities and tools that are not part of the main application flow.

## Directory Structure

### `/debug/`
Debug scripts and tools for troubleshooting specific components:

- `debug_attribute_error.py` - Debugging utility for attribute errors
- `debug_memory_manager.py` - Memory system debugging tool
- `debug_relationships.py` - Relationship debugging utility
- `comprehensive_test.py` - Comprehensive testing script
- `simple_log_test.py` - Logging system test utility
- `simple_memory_moments_test.py` - Memory moments testing
- `simple_test_server.py` - Server testing utility
- `demo_character_graph_memory.py` - Character memory system demonstration
- `demo_character_memory_integration.py` - Memory integration demo
- `multi_entity_relationship_demo.py` - Multi-entity relationship demo

### `/performance/`
Performance testing and benchmarking utilities:

- `test_batch_optimization.py` - Batch processing optimization tests
- `test_parallel_processing_performance.py` - Parallel processing benchmarks
- `test_redundancy_removal.py` - Redundancy removal testing
- `performance_comparison.py` - Performance comparison utility

## Usage

These utilities are intended for development and debugging purposes. They are not part of the main application startup or test suite, but can be run individually when needed for troubleshooting or performance analysis.

### Running Debug Scripts
```bash
cd utilities/debug
python debug_memory_manager.py
```

### Running Performance Tests
```bash
cd utilities/performance  
python performance_comparison.py
```

## Integration with Main Application

These utilities are **not** automatically integrated with the main WhisperEngine application. They are standalone tools that can be used independently for development and debugging purposes.

For production monitoring and health checks, use the integrated monitoring commands available through the Discord bot interface (see `src/handlers/monitoring_commands.py`).