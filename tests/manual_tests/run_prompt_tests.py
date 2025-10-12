#!/usr/bin/env python
"""Simple test runner for prompt assembly tests (bypasses pytest config issues)."""
import sys
import unittest

# Import all test classes
from tests.unit.test_prompt_assembler import (
    TestPromptComponent,
    TestPromptAssembler,
    TestComponentFactories,
    TestIntegrationScenarios
)

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPromptComponent))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptAssembler))
    suite.addTests(loader.loadTestsFromTestCase(TestComponentFactories))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
