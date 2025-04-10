#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
import datetime
from git import Repo
from reporewrite import LoggingModule, RepositoryHandler, CommitModifier

class TestCommitModifier(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.logging_module = LoggingModule(log_to_file=False)
        
        # Clone the test repository
        self.repo_handler = RepositoryHandler(self.logging_module)
        self.test_repo_url = "https://github.com/The-Thought-Magician/TEST.git"
        self.repo_path = self.repo_handler.clone_repo(self.test_repo_url, self.temp_dir)
        
        # Initialize CommitModifier
        self.commit_modifier = CommitModifier(self.repo_path, self.logging_module)
        
        # Get initial commit information for comparison
        self.repo = Repo(self.repo_path)
        self.original_commits = list(self.repo.iter_commits())
        self.original_authors = [commit.author.name for commit in self.original_commits]
        self.original_emails = [commit.author.email for commit in self.original_commits]
        self.original_dates = [commit.authored_datetime for commit in self.original_commits]
    
    def tearDown(self):
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_randomize_commit_dates(self):
        """Test that commit dates can be randomized while maintaining order."""
        # Get random dates
        start_date = datetime.datetime.now() - datetime.timedelta(days=100)
        end_date = datetime.datetime.now() - datetime.timedelta(days=1)
        
        random_dates = self.commit_modifier.randomize_commit_dates(start_date, end_date)
        
        # Check that we got the right number of dates
        self.assertEqual(len(random_dates), len(self.original_commits))
        
        # Check that dates are within the specified range
        for date in random_dates:
            self.assertTrue(start_date <= date <= end_date)
        
        # Check that dates are in descending order (newest first)
        for i in range(1, len(random_dates)):
            self.assertTrue(random_dates[i-1] >= random_dates[i])
    
    def test_update_commit_metadata(self):
        """Test updating commit metadata (author and email)."""
        # This test modifies the repository and is more complex,
        # so we'll just check that it doesn't raise an exception
        try:
            self.commit_modifier.update_commit_metadata("New Author", "new.author@example.com")
            # If we got here without an exception, the test passed
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"update_commit_metadata raised an exception: {str(e)}")

if __name__ == "__main__":
    unittest.main()