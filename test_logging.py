#!/usr/bin/env python3

import unittest
import os
import logging
import tempfile
from reporewrite import LoggingModule

class TestLoggingModule(unittest.TestCase):
    def setUp(self):
        # Create a temporary log file
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_log.log")
        self.logging_module = LoggingModule(log_to_file=True, log_file=self.log_file)
    
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_log_event(self):
        """Test that log events are properly recorded."""
        self.logging_module.log_event("TEST", "This is a test message")
        self.logging_module.log_event("ERROR", "This is an error message", level=logging.ERROR)
        
        logs = self.logging_module.retrieve_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn("TEST", logs[0])
        self.assertIn("ERROR", logs[1])
        
        # Check that log file was created
        self.assertTrue(os.path.exists(self.log_file))
        
        # Check log file contents
        with open(self.log_file, 'r') as f:
            content = f.read()
            self.assertIn("This is a test message", content)
            self.assertIn("This is an error message", content)
    
    def test_clear_logs(self):
        """Test that logs can be cleared."""
        self.logging_module.log_event("TEST", "Message before clearing")
        self.logging_module.clear_logs()
        logs = self.logging_module.retrieve_logs()
        self.assertEqual(len(logs), 0)

if __name__ == "__main__":
    unittest.main()