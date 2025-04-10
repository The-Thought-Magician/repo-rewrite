#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
from git import Repo
from reporewrite import LoggingModule, RepositoryHandler

class TestRepositoryHandler(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.logging_module = LoggingModule(log_to_file=False)
        self.repo_handler = RepositoryHandler(self.logging_module)
        
        # Create a test repository URL
        self.test_repo_url = "https://github.com/The-Thought-Magician/TEST.git"
    
    def tearDown(self):
        # Clean up temporary directory
        self.repo_handler.cleanup()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_clone_repo(self):
        """Test repository cloning functionality."""
        try:
            # Clone the repository
            repo_path = self.repo_handler.clone_repo(self.test_repo_url, self.temp_dir)
            
            # Check that the repository was cloned successfully
            self.assertTrue(os.path.exists(os.path.join(repo_path, ".git")))
            self.assertIsNotNone(self.repo_handler.repo)
        except Exception as e:
            self.fail(f"Repository cloning failed with error: {str(e)}")
    
    def test_fetch_repo_info(self):
        """Test fetching repository information."""
        # Clone the repository first
        self.repo_handler.clone_repo(self.test_repo_url, self.temp_dir)
        
        # Fetch repository info
        repo_info = self.repo_handler.fetch_repo_info()
        
        # Check that repo_info contains the expected keys
        self.assertIn('branches', repo_info)
        self.assertIn('commits', repo_info)
        self.assertIn('remotes', repo_info)
        
        # Check that there's at least one branch
        self.assertGreater(len(repo_info['branches']), 0)
        
        # Check that there's at least one commit
        self.assertGreater(len(repo_info['commits']), 0)
        
        # Check that there's at least one remote
        self.assertGreater(len(repo_info['remotes']), 0)

if __name__ == "__main__":
    unittest.main()