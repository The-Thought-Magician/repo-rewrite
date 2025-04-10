#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
from git import Repo
from reporewrite import LoggingModule, RepositoryHandler, FileProcessor

class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.logging_module = LoggingModule(log_to_file=False)
        
        # Clone the test repository
        self.repo_handler = RepositoryHandler(self.logging_module)
        self.test_repo_url = "https://github.com/The-Thought-Magician/TEST.git"
        self.repo_path = self.repo_handler.clone_repo(self.test_repo_url, self.temp_dir)
        
        # Initialize FileProcessor
        self.file_processor = FileProcessor(self.repo_path, self.logging_module)
        
        # Create some test files with sensitive information
        self.test_file1 = os.path.join(self.repo_path, "test_file1.txt")
        with open(self.test_file1, "w") as f:
            f.write("This file contains copyright information and the author's name.")
        
        self.test_file2 = os.path.join(self.repo_path, "test_file2.txt")
        with open(self.test_file2, "w") as f:
            f.write("This file contains license information.")
    
    def tearDown(self):
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_scan_and_replace(self):
        """Test scanning and replacing patterns in a file."""
        patterns = ["copyright", "author"]
        replacement = "[REDACTED]"
        
        # Replace patterns in the first test file
        result = self.file_processor.scan_and_replace(self.test_file1, patterns, replacement)
        
        # Check that the replacement was successful
        self.assertTrue(result)
        
        # Read the file content and check that patterns were replaced
        with open(self.test_file1, "r") as f:
            content = f.read()
            self.assertIn("[REDACTED]", content)
            self.assertNotIn("copyright", content.lower())
            self.assertNotIn("author", content.lower())
    
    def test_update_all_files(self):
        """Test updating all files in the repository."""
        patterns = ["copyright", "license", "author"]
        replacement = "[REDACTED]"
        
        # Update all files
        count = self.file_processor.update_all_files(patterns, replacement)
        
        # Check that at least one file was updated
        self.assertGreaterEqual(count, 1)
        
        # Read the test files and check for replacements
        with open(self.test_file1, "r") as f:
            content1 = f.read()
            self.assertIn("[REDACTED]", content1)
        
        with open(self.test_file2, "r") as f:
            content2 = f.read()
            self.assertIn("[REDACTED]", content2)
    
    def test_find_sensitive_files(self):
        """Test finding files with sensitive information."""
        # Create a file that would be identified as sensitive
        license_file = os.path.join(self.repo_path, "LICENSE")
        with open(license_file, "w") as f:
            f.write("This is a license file.")
        
        # Find sensitive files
        sensitive_files = self.file_processor.find_sensitive_files()
        
        # Check that the LICENSE file is in the list
        license_path = os.path.join(self.repo_path, "LICENSE")
        self.assertIn(license_path, sensitive_files)

if __name__ == "__main__":
    unittest.main()