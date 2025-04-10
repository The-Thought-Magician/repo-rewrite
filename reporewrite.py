#!/usr/bin/env python3

import os
import re
import git
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import datetime
import random
import requests
import json
import tempfile
import shutil
import subprocess
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import time
import sys
import watchdog.observers
import watchdog.events


class LoggingModule:
    """Module responsible for logging all operations and changes."""
    
    def __init__(self, log_to_file=True, log_file="reporewrite.log"):
        self.logs = []
        self.log_to_file = log_to_file
        self.log_file = log_file
        
        # Configure logger
        self.logger = logging.getLogger("RepoRewrite")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.log_to_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_event(self, event_type: str, message: str, level=logging.INFO):
        """Log an event with timestamp."""
        log_entry = f"{datetime.datetime.now().isoformat()} - {event_type} - {message}"
        self.logs.append(log_entry)
        
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)
    
    def retrieve_logs(self) -> List[str]:
        """Retrieve all logs."""
        return self.logs
    
    def clear_logs(self):
        """Clear current logs."""
        self.logs = []


class RepositoryHandler:
    """Module for handling repository operations like cloning and fetching info."""
    
    def __init__(self, logging_module: LoggingModule):
        self.logger = logging_module
        self.repo = None
        self.temp_dir = None
    
    def clone_repo(self, url: str, target_dir: str = None) -> str:
        """Clone the repository from the given URL to the target directory."""
        try:
            # If target_dir is not provided, create a temporary directory
            if target_dir is None:
                self.temp_dir = tempfile.mkdtemp()
                target_dir = self.temp_dir
            
            self.logger.log_event("CLONE", f"Cloning repository from {url} to {target_dir}")
            self.repo = git.Repo.clone_from(url, target_dir)
            self.logger.log_event("CLONE", f"Repository cloned successfully")
            return target_dir
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to clone repository: {str(e)}", level=logging.ERROR)
            raise
    
    def fetch_repo_info(self) -> Dict:
        """Fetch information about the repository."""
        if not self.repo:
            self.logger.log_event("ERROR", "No repository available", level=logging.ERROR)
            raise ValueError("No repository available")
        
        try:
            # Get branches
            branches = []
            for branch in self.repo.branches:
                branches.append(branch.name)
            
            # Get commits
            commits = []
            for commit in self.repo.iter_commits():
                commits.append({
                    'hexsha': commit.hexsha,
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'date': commit.authored_datetime,
                    'message': commit.message
                })
            
            # Get remotes
            remotes = []
            for remote in self.repo.remotes:
                remotes.append({
                    'name': remote.name,
                    'url': remote.url
                })
            
            repo_info = {
                'branches': branches,
                'commits': commits,
                'remotes': remotes
            }
            
            self.logger.log_event("INFO", "Repository information fetched successfully")
            return repo_info
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to fetch repository info: {str(e)}", level=logging.ERROR)
            raise
    
    def cleanup(self):
        """Clean up temporary directories if needed."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.logger.log_event("CLEANUP", f"Removed temporary directory: {self.temp_dir}")


class CommitModifier:
    """Module for modifying commit history."""
    
    def __init__(self, repo_path: str, logging_module: LoggingModule):
        self.repo_path = repo_path
        self.logger = logging_module
    
    def randomize_commit_dates(self, start_date=None, end_date=None) -> List[datetime.datetime]:
        """Generate random commit dates while maintaining chronological order."""
        try:
            repo = git.Repo(self.repo_path)
            
            if start_date is None:
                start_date = datetime.datetime.now() - datetime.timedelta(days=365)
            if end_date is None:
                end_date = datetime.datetime.now()
                
            # Get list of commits
            commits = list(repo.iter_commits())
            num_commits = len(commits)
            
            # Calculate time range
            time_range = (end_date - start_date).total_seconds()
            
            # Create sorted random dates
            random_seconds = [random.random() * time_range for _ in range(num_commits)]
            random_seconds.sort(reverse=True)  # Newest commits first
            
            random_dates = [start_date + datetime.timedelta(seconds=sec) for sec in random_seconds]
            
            self.logger.log_event("INFO", f"Generated {num_commits} random commit dates between {start_date} and {end_date}")
            
            return random_dates
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to randomize commit dates: {str(e)}", level=logging.ERROR)
            raise
    
    def update_commit_metadata(self, new_author: str, new_email: str, new_dates: List[datetime.datetime] = None):
        """Update commit metadata including author and dates."""
        try:
            # Create an environment dictionary for the filter-branch command
            env = os.environ.copy()
            
            # Prepare the filter-branch command based on what needs to be changed
            filter_cmd = []
            
            # Author and email filter
            if new_author and new_email:
                author_filter = f"""
                    if [ "$GIT_AUTHOR_NAME" != "{new_author}" ] || [ "$GIT_AUTHOR_EMAIL" != "{new_email}" ]; then
                        export GIT_AUTHOR_NAME="{new_author}"
                        export GIT_AUTHOR_EMAIL="{new_email}"
                        export GIT_COMMITTER_NAME="{new_author}"
                        export GIT_COMMITTER_EMAIL="{new_email}"
                    fi
                """
                filter_cmd.append(f'--env-filter \'{author_filter}\'')
            
            # Execute the filter-branch command
            if filter_cmd:
                cmd = f"cd {self.repo_path} && git filter-branch -f " + " ".join(filter_cmd) + " -- --all"
                self.logger.log_event("INFO", f"Running command: {cmd}")
                
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    self.logger.log_event("ERROR", f"Error updating commit metadata: {stderr.decode()}", level=logging.ERROR)
                    raise RuntimeError(f"Error updating commit metadata: {stderr.decode()}")
                
                self.logger.log_event("INFO", "Commit metadata updated successfully")
            
            # If dates need to be updated, we need to use a different approach
            if new_dates:
                self._update_commit_dates(new_dates)
                
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to update commit metadata: {str(e)}", level=logging.ERROR)
            raise
    
    def _update_commit_dates(self, new_dates: List[datetime.datetime]):
        """Update commit dates using git filter-branch."""
        try:
            repo = git.Repo(self.repo_path)
            commits = list(repo.iter_commits())
            
            if len(commits) != len(new_dates):
                error_msg = f"Number of commits ({len(commits)}) doesn't match number of dates ({len(new_dates)})"
                self.logger.log_event("ERROR", error_msg, level=logging.ERROR)
                raise ValueError(error_msg)
            
            # Create a map of commit SHA to new date
            date_map = {}
            for commit, new_date in zip(commits, new_dates):
                date_map[commit.hexsha[:7]] = new_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Write the date map to a file
            date_map_file = os.path.join(self.repo_path, '.git', 'date_map.txt')
            with open(date_map_file, 'w') as f:
                for sha, date_str in date_map.items():
                    f.write(f"{sha} {date_str}\n")
            
            # Create the filter script
            filter_script = os.path.join(self.repo_path, '.git', 'change_dates.sh')
            with open(filter_script, 'w') as f:
                f.write("""#!/bin/bash
                while read line; do
                    SHA=$(echo $line | cut -d' ' -f1)
                    DATE=$(echo $line | cut -d' ' -f2-)
                    if [[ "$GIT_COMMIT" == "$SHA"* ]]; then
                        export GIT_AUTHOR_DATE="$DATE"
                        export GIT_COMMITTER_DATE="$DATE"
                        break
                    fi
                done < .git/date_map.txt
                """)
            
            # Make the script executable
            os.chmod(filter_script, 0o755)
            
            # Run filter-branch
            cmd = f"cd {self.repo_path} && git filter-branch -f --env-filter '.git/change_dates.sh' -- --all"
            self.logger.log_event("INFO", f"Running command: {cmd}")
            
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.log_event("ERROR", f"Error updating commit dates: {stderr.decode()}", level=logging.ERROR)
                raise RuntimeError(f"Error updating commit dates: {stderr.decode()}")
            
            # Clean up temporary files
            os.remove(date_map_file)
            os.remove(filter_script)
            
            self.logger.log_event("INFO", "Commit dates updated successfully")
            
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to update commit dates: {str(e)}", level=logging.ERROR)
            raise


class BranchRemoteManager:
    """Module for managing branches and remotes."""
    
    def __init__(self, repo_path: str, logging_module: LoggingModule):
        self.repo_path = repo_path
        self.logger = logging_module
        try:
            self.repo = git.Repo(repo_path)
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to open repository: {str(e)}", level=logging.ERROR)
            raise
    
    def rename_branch(self, old_name: str, new_name: str) -> bool:
        """Rename a branch in the repository."""
        try:
            # Check if branch exists
            if old_name not in [branch.name for branch in self.repo.branches]:
                self.logger.log_event("ERROR", f"Branch {old_name} does not exist", level=logging.ERROR)
                return False
            
            # Check if target branch name already exists
            if new_name in [branch.name for branch in self.repo.branches]:
                self.logger.log_event("ERROR", f"Branch {new_name} already exists", level=logging.ERROR)
                return False
            
            # Rename the branch
            self.repo.git.branch("-m", old_name, new_name)
            self.logger.log_event("INFO", f"Renamed branch from {old_name} to {new_name}")
            
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to rename branch: {str(e)}", level=logging.ERROR)
            raise
    
    def set_remote_url(self, remote_name: str, new_url: str) -> bool:
        """Update the URL of a remote."""
        try:
            # Check if remote exists
            remotes = {remote.name: remote for remote in self.repo.remotes}
            if remote_name not in remotes:
                self.logger.log_event("ERROR", f"Remote {remote_name} does not exist", level=logging.ERROR)
                return False
            
            # Set the new URL
            remotes[remote_name].set_url(new_url)
            self.logger.log_event("INFO", f"Updated URL for remote {remote_name} to {new_url}")
            
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to set remote URL: {str(e)}", level=logging.ERROR)
            raise
    
    def add_remote(self, remote_name: str, remote_url: str) -> bool:
        """Add a new remote to the repository."""
        try:
            # Check if remote already exists
            remotes = {remote.name: remote for remote in self.repo.remotes}
            if remote_name in remotes:
                self.logger.log_event("WARNING", f"Remote {remote_name} already exists", level=logging.WARNING)
                return self.set_remote_url(remote_name, remote_url)
            
            # Add the new remote
            self.repo.create_remote(remote_name, remote_url)
            self.logger.log_event("INFO", f"Added remote {remote_name} with URL {remote_url}")
            
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to add remote: {str(e)}", level=logging.ERROR)
            raise


class FileProcessor:
    """Module for processing files in the repository."""
    
    def __init__(self, repo_path: str, logging_module: LoggingModule):
        self.repo_path = repo_path
        self.logger = logging_module
    
    def scan_and_replace(self, file_path: str, patterns: List[str], replacement: str) -> bool:
        """Scan a file and replace patterns with replacement."""
        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                self.logger.log_event("WARNING", f"File {file_path} does not exist", level=logging.WARNING)
                return False
            
            # Check if file is binary
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                self.logger.log_event("INFO", f"Skipping binary file {file_path}")
                return False
            
            # Check for patterns and replace
            modifications_made = False
            for pattern in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modifications_made = True
            
            if modifications_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.log_event("INFO", f"Modified file {file_path}")
            
            return modifications_made
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to scan and replace in file {file_path}: {str(e)}", level=logging.ERROR)
            raise
    
    def update_all_files(self, patterns: List[str], replacement: str) -> int:
        """Update all text files in the repository by replacing patterns with replacement."""
        try:
            count = 0
            # Walk through all files in the repository
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.scan_and_replace(file_path, patterns, replacement):
                        count += 1
            
            self.logger.log_event("INFO", f"Updated {count} files in the repository")
            return count
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to update all files: {str(e)}", level=logging.ERROR)
            raise
    
    def find_sensitive_files(self) -> List[str]:
        """Find files that might contain sensitive information (e.g., license, author info)."""
        sensitive_files = []
        patterns = [
            r'license', r'copyright', r'author', r'contributor',
            r'readme', r'changelog', r'authors', r'contributors',
            r'maintainers', r'codeowners', r'code of conduct', r'governance'
        ]
        
        try:
            # Walk through all files in the repository
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_lower = file.lower()
                    for pattern in patterns:
                        if re.search(pattern, file_lower):
                            sensitive_files.append(os.path.join(root, file))
                            break
            
            self.logger.log_event("INFO", f"Found {len(sensitive_files)} potentially sensitive files")
            return sensitive_files
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to find sensitive files: {str(e)}", level=logging.ERROR)
            raise


class RemoteRepositoryManager:
    """Module for managing remote repositories."""
    
    def __init__(self, logging_module: LoggingModule):
        self.logger = logging_module
    
    def create_remote_repo(self, repo_name: str, token: str, is_private: bool = True, use_ssh: bool = False) -> str:
        """Create a new remote repository using GitHub API."""
        try:
            # Setup API endpoint and headers
            url = "https://api.github.com/user/repos"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Setup repository data
            data = {
                "name": repo_name,
                "private": is_private,
                "auto_init": False
            }
            
            # Make API request
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            # Check response
            if response.status_code == 201:
                repo_data = response.json()
                # Choose between SSH and HTTPS URLs based on preference
                repo_url = repo_data["ssh_url"] if use_ssh else repo_data["clone_url"]
                self.logger.log_event("INFO", f"Created new repository: {repo_url}")
                return repo_url
            else:
                error = response.json()
                error_message = error.get('message', 'Unknown error')
                if error_message == "Bad credentials":
                    error_message += ": Please check your GitHub token is valid and has proper permissions (repo scope)"
                self.logger.log_event("ERROR", f"Failed to create repository: {error_message}", level=logging.ERROR)
                raise Exception(f"Failed to create repository: {error_message}")
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to create remote repository: {str(e)}", level=logging.ERROR)
            raise
    
    def configure_ssh_key(self, ssh_key_path: str, ssh_key_content: str = None) -> bool:
        """Configure SSH key for Git operations."""
        try:
            # If SSH key content is provided, write it to the file
            if ssh_key_content:
                os.makedirs(os.path.dirname(ssh_key_path), exist_ok=True)
                with open(ssh_key_path, 'w') as f:
                    f.write(ssh_key_content)
                # Set proper permissions (read/write for the owner only)
                os.chmod(ssh_key_path, 0o600)
                self.logger.log_event("INFO", f"SSH key written to {ssh_key_path}")
            
            # Configure SSH to use the key
            ssh_dir = os.path.expanduser("~/.ssh")
            os.makedirs(ssh_dir, exist_ok=True)
            
            # Create/update SSH config
            ssh_config_path = os.path.join(ssh_dir, "config")
            with open(ssh_config_path, 'a+') as f:
                f.seek(0)
                content = f.read()
                if "github.com" not in content:
                    f.write(f"\nHost github.com\n  IdentityFile {ssh_key_path}\n  User git\n")
            
            self.logger.log_event("INFO", "SSH key configured successfully")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to configure SSH key: {str(e)}", level=logging.ERROR)
            raise
    
    def test_ssh_connection(self) -> bool:
        """Test SSH connection to GitHub."""
        try:
            cmd = "ssh -T git@github.com -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # GitHub returns exit code 1 even on successful authentication with message:
            # "Hi username! You've successfully authenticated, but GitHub does not provide shell access."
            stderr_str = stderr.decode()
            if "successfully authenticated" in stderr_str:
                self.logger.log_event("INFO", "SSH connection to GitHub is working")
                return True
            else:
                self.logger.log_event("ERROR", f"SSH connection failed: {stderr_str}", level=logging.ERROR)
                return False
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to test SSH connection: {str(e)}", level=logging.ERROR)
            return False
    
    def configure_remote(self, repo_path: str, remote_url: str, remote_name: str = "origin") -> bool:
        """Configure the remote for a local repository."""
        try:
            branch_manager = BranchRemoteManager(repo_path, self.logger)
            
            # Set/add remote URL
            success = branch_manager.add_remote(remote_name, remote_url)
            
            if success:
                self.logger.log_event("INFO", f"Remote {remote_name} configured with URL {remote_url}")
                return True
            else:
                self.logger.log_event("ERROR", "Failed to configure remote", level=logging.ERROR)
                return False
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to configure remote: {str(e)}", level=logging.ERROR)
            raise
    
    def push_changes(self, repo_path: str, remote_name: str = "origin", force: bool = True) -> bool:
        """Push changes to the remote repository."""
        try:
            repo = git.Repo(repo_path)
            
            # Get the current branch
            branch = repo.active_branch.name
            
            # Try to push changes
            try:
                push_info_list = repo.remotes[remote_name].push(f"{branch}:{branch}", force=force)
                
                # Check if push was successful
                for push_info in push_info_list:
                    if push_info.flags & push_info.ERROR:
                        self.logger.log_event("ERROR", f"Failed to push changes: {push_info.summary}", level=logging.ERROR)
                        return False
                
                self.logger.log_event("INFO", f"Successfully pushed changes to {remote_name}/{branch}")
                return True
            except git.exc.GitCommandError as git_err:
                error_msg = str(git_err)
                if "Could not read from remote repository" in error_msg:
                    suggestions = [
                        "1. Ensure your SSH key is correctly configured and added to your GitHub account",
                        "2. Try using HTTPS URL instead of SSH if SSH key setup is problematic",
                        "3. Check if you have proper network connectivity to GitHub"
                    ]
                    self.logger.log_event("ERROR", f"GitHub Connection Error: {error_msg}\nTroubleshooting suggestions:\n" + 
                                         "\n".join(suggestions), level=logging.ERROR)
                else:
                    self.logger.log_event("ERROR", f"Failed to push changes: {error_msg}", level=logging.ERROR)
                return False
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to push changes: {str(e)}", level=logging.ERROR)
            raise


class BackendController:
    """Central controller that orchestrates operations between modules."""
    
    def __init__(self, logging_module: LoggingModule):
        self.logger = logging_module
        self.repo_handler = None
        self.commit_modifier = None
        self.branch_manager = None
        self.file_processor = None
        self.remote_manager = None
        self.repo_path = None
        self.repo_info = None
        self.batch_mode = False
        self.batch_results = []
    
    def initialize(self, repo_url: str, target_dir: str = None) -> bool:
        """Initialize the controller with a repository."""
        try:
            # Create repository handler
            self.repo_handler = RepositoryHandler(self.logger)
            
            # Clone repository
            self.repo_path = self.repo_handler.clone_repo(repo_url, target_dir)
            
            # Fetch repository info
            self.repo_info = self.repo_handler.fetch_repo_info()
            
            # Initialize other modules
            self.commit_modifier = CommitModifier(self.repo_path, self.logger)
            self.branch_manager = BranchRemoteManager(self.repo_path, self.logger)
            self.file_processor = FileProcessor(self.repo_path, self.logger)
            self.remote_manager = RemoteRepositoryManager(self.logger)
            
            self.logger.log_event("INFO", f"Backend controller initialized with repository at {self.repo_path}")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to initialize controller: {str(e)}", level=logging.ERROR)
            raise
    
    def process_batch(self, repo_urls: List[str], operations: Dict) -> List[Dict]:
        """
        Process multiple repositories in batch mode.
        
        Args:
            repo_urls: List of repository URLs to process
            operations: Dictionary containing operations to perform on each repository
                {
                    'new_author': str,
                    'new_email': str,
                    'randomize_dates': bool,
                    'start_date': datetime.datetime,
                    'end_date': datetime.datetime,
                    'branch_mapping': Dict[str, str],
                    'patterns': List[str],
                    'replacement': str,
                    'remote_url': str,
                    'token': str,
                    'repo_name_template': str,
                }
        
        Returns:
            List of results for each repository processing
        """
        self.batch_mode = True
        self.batch_results = []
        
        for i, repo_url in enumerate(repo_urls):
            result = {
                'repo_url': repo_url,
                'success': False,
                'error': None,
                'operations_completed': []
            }
            
            try:
                # Initialize with the repository
                self.logger.log_event("BATCH", f"Processing repository {i+1}/{len(repo_urls)}: {repo_url}")
                self.initialize(repo_url)
                
                # Extract repository name from URL for templating
                repo_name = repo_url.split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                
                # Rewrite history if needed
                if operations.get('new_author') and operations.get('new_email'):
                    self.rewrite_history(
                        operations['new_author'],
                        operations['new_email'],
                        operations.get('randomize_dates', False),
                        operations.get('start_date'),
                        operations.get('end_date')
                    )
                    result['operations_completed'].append('rewrite_history')
                
                # Rename branches if needed
                if operations.get('branch_mapping'):
                    self.rename_branches(operations['branch_mapping'])
                    result['operations_completed'].append('rename_branches')
                
                # Clean sensitive data if needed
                if operations.get('patterns') and operations.get('replacement'):
                    self.clean_sensitive_data(operations['patterns'], operations['replacement'])
                    result['operations_completed'].append('clean_sensitive_data')
                
                # Setup remote and push if needed
                remote_url = operations.get('remote_url')
                token = operations.get('token')
                
                # If repo_name_template is provided, use it to generate a repo name
                repo_name_for_remote = None
                if operations.get('repo_name_template'):
                    # Replace {repo_name} with the actual repo name
                    repo_name_for_remote = operations['repo_name_template'].format(
                        repo_name=repo_name,
                        index=i+1
                    )
                
                if remote_url or (token and repo_name_for_remote):
                    self.setup_remote_and_push(remote_url, token, repo_name_for_remote)
                    result['operations_completed'].append('setup_remote_and_push')
                
                result['success'] = True
                self.logger.log_event("BATCH", f"Successfully processed repository: {repo_url}")
                
            except Exception as e:
                result['error'] = str(e)
                self.logger.log_event("ERROR", f"Failed to process repository {repo_url}: {str(e)}", level=logging.ERROR)
            finally:
                # Clean up resources
                self.cleanup()
                self.batch_results.append(result)
                
        return self.batch_results
    
    def rewrite_history(self, new_author: str, new_email: str, randomize_dates: bool = False,
                      start_date: datetime.datetime = None, end_date: datetime.datetime = None) -> bool:
        """Rewrite repository history with new author and dates."""
        try:
            # Get dates for commits if randomization is requested
            new_dates = None
            if randomize_dates:
                new_dates = self.commit_modifier.randomize_commit_dates(start_date, end_date)
            
            # Update commit metadata
            self.commit_modifier.update_commit_metadata(new_author, new_email, new_dates)
            
            self.logger.log_event("INFO", "Repository history rewritten successfully")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to rewrite history: {str(e)}", level=logging.ERROR)
            raise
    
    def rename_branches(self, branch_mapping: Dict[str, str]) -> bool:
        """Rename branches according to the provided mapping."""
        try:
            for old_name, new_name in branch_mapping.items():
                if old_name != new_name:
                    self.branch_manager.rename_branch(old_name, new_name)
            
            self.logger.log_event("INFO", "Branches renamed successfully")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to rename branches: {str(e)}", level=logging.ERROR)
            raise
    
    def clean_sensitive_data(self, patterns: List[str], replacement: str) -> bool:
        """Clean sensitive data from repository files."""
        try:
            # Process all files
            files_modified = self.file_processor.update_all_files(patterns, replacement)
            
            # Only commit if files were actually modified
            if files_modified > 0:
                repo = git.Repo(self.repo_path)
                repo.git.add(".")
                repo.git.commit("-m", "Clean sensitive data")
                self.logger.log_event("INFO", f"Committed changes to {files_modified} files with sensitive data removed")
            else:
                self.logger.log_event("INFO", "No files needed sensitive data cleaning")
            
            self.logger.log_event("INFO", "Sensitive data cleaning process completed successfully")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to clean sensitive data: {str(e)}", level=logging.ERROR)
            raise
    
    def setup_remote_and_push(self, remote_url: str = None, token: str = None, 
                            repo_name: str = None, force_push: bool = True) -> bool:
        """Setup remote repository and push changes."""
        try:
            # Create new remote repository if token and repo_name are provided
            if token and repo_name and not remote_url:
                remote_url = self.remote_manager.create_remote_repo(repo_name, token)
            
            if not remote_url:
                self.logger.log_event("ERROR", "No remote URL provided", level=logging.ERROR)
                return False
            
            # Configure remote
            self.remote_manager.configure_remote(self.repo_path, remote_url)
            
            # Push changes
            self.remote_manager.push_changes(self.repo_path, force=force_push)
            
            self.logger.log_event("INFO", "Repository changes pushed successfully")
            return True
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to setup remote and push: {str(e)}", level=logging.ERROR)
            raise
    
    def cleanup(self):
        """Clean up resources used by the controller."""
        try:
            if self.repo_handler:
                self.repo_handler.cleanup()
            
            self.logger.log_event("INFO", "Resources cleaned up successfully")
        except Exception as e:
            self.logger.log_event("ERROR", f"Failed to clean up resources: {str(e)}", level=logging.ERROR)


class RepoRewriteGUI:
    """GUI for the Git Repository History Manipulator & Rewriter."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Git Repository History Manipulator & Rewriter")
        self.root.geometry("900x700")
        
        # Initialize logging module
        self.logging_module = LoggingModule()
        
        # Initialize backend controller
        self.controller = BackendController(self.logging_module)
        
        # Create GUI components
        self._create_widgets()
        
        # Configure root window behavior
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """Create and arrange GUI widgets."""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        single_repo_tab = ttk.Frame(self.notebook)
        batch_repo_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(single_repo_tab, text="Single Repository")
        self.notebook.add(batch_repo_tab, text="Batch Processing")
        
        # Create single repository tab content
        self._create_single_repo_tab(single_repo_tab)
        
        # Create batch processing tab content
        self._create_batch_repo_tab(batch_repo_tab)
        
        # Create log frame (common to both tabs)
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Configure button frame columns to expand properly
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)
        
        # Add buttons
        ttk.Button(button_frame, text="Preview Changes", command=self._preview_changes).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(button_frame, text="Execute", command=self._execute_changes).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(button_frame, text="Exit", command=self._on_close).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Initialize log text with welcome message
        self._update_log("Welcome to Git Repository History Manipulator & Rewriter!")
    
    def _create_single_repo_tab(self, parent):
        """Create widgets for the single repository tab."""
        # Create top frame for input fields
        input_frame = ttk.LabelFrame(parent, text="Repository Information")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Repository URL
        ttk.Label(input_frame, text="Repository URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.repo_url_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.repo_url_var, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Target Directory (optional)
        ttk.Label(input_frame, text="Target Directory (optional):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_dir_var = tk.StringVar()
        target_dir_entry = ttk.Entry(input_frame, textvariable=self.target_dir_var, width=50)
        target_dir_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self._browse_directory).grid(row=1, column=2, padx=5, pady=5)
        
        # Create frame for commit modification options
        commit_frame = ttk.LabelFrame(parent, text="Commit Modification Options")
        commit_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # New Author Name
        ttk.Label(commit_frame, text="New Author Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.author_name_var = tk.StringVar()
        ttk.Entry(commit_frame, textvariable=self.author_name_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # New Author Email
        ttk.Label(commit_frame, text="New Author Email:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.author_email_var = tk.StringVar()
        ttk.Entry(commit_frame, textvariable=self.author_email_var, width=30).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Randomize Commit Dates
        self.randomize_dates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(commit_frame, text="Randomize Commit Dates", variable=self.randomize_dates_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Date Range (only enabled if randomize_dates is selected)
        date_frame = ttk.Frame(commit_frame)
        date_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.end_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=15).grid(row=0, column=3, padx=5, pady=5)
        
        # Create frame for branch and remote options
        branch_remote_frame = ttk.LabelFrame(parent, text="Branch and Remote Options")
        branch_remote_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Branch Renaming
        ttk.Label(branch_remote_frame, text="Branch Renaming (old:new, comma-separated):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.branch_rename_var = tk.StringVar()
        ttk.Entry(branch_remote_frame, textvariable=self.branch_rename_var, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Remote Repository Options
        ttk.Label(branch_remote_frame, text="New Remote URL (optional):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.remote_url_var = tk.StringVar()
        ttk.Entry(branch_remote_frame, textvariable=self.remote_url_var, width=50).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # GitHub API token for creating new repositories
        ttk.Label(branch_remote_frame, text="GitHub API Token (for new repos):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.github_token_var = tk.StringVar()
        ttk.Entry(branch_remote_frame, textvariable=self.github_token_var, width=50, show="*").grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # New Repository Name
        ttk.Label(branch_remote_frame, text="New Repository Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.repo_name_var = tk.StringVar()
        ttk.Entry(branch_remote_frame, textvariable=self.repo_name_var, width=30).grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Create frame for sensitive data options
        sensitive_data_frame = ttk.LabelFrame(parent, text="Sensitive Data Removal")
        sensitive_data_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Enable Sensitive Data Removal
        self.remove_sensitive_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sensitive_data_frame, text="Remove Sensitive Data", variable=self.remove_sensitive_data_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Patterns to search for (comma-separated)
        ttk.Label(sensitive_data_frame, text="Patterns to Replace (regex, comma-separated):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.patterns_var = tk.StringVar(value="copyright,license,author")
        ttk.Entry(sensitive_data_frame, textvariable=self.patterns_var, width=50).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Replacement text
        ttk.Label(sensitive_data_frame, text="Replacement Text:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.replacement_var = tk.StringVar(value="[REDACTED]")
        ttk.Entry(sensitive_data_frame, textvariable=self.replacement_var, width=30).grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        commit_frame.columnconfigure(1, weight=1)
        branch_remote_frame.columnconfigure(1, weight=1)
        sensitive_data_frame.columnconfigure(1, weight=1)
    
    def _create_batch_repo_tab(self, parent):
        """Create widgets for the batch processing tab."""
        # Create top frame for input fields
        input_frame = ttk.LabelFrame(parent, text="Repository Information")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Repository URLs (one per line)
        ttk.Label(input_frame, text="Repository URLs (one per line):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_repo_urls_text = scrolledtext.ScrolledText(input_frame, height=5, width=50)
        self.batch_repo_urls_text.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Batch operation options frame
        options_frame = ttk.LabelFrame(parent, text="Batch Operation Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # New Author Name
        ttk.Label(options_frame, text="New Author Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_author_name_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.batch_author_name_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # New Author Email
        ttk.Label(options_frame, text="New Author Email:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_author_email_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.batch_author_email_var, width=30).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Randomize Commit Dates
        self.batch_randomize_dates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Randomize Commit Dates", variable=self.batch_randomize_dates_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Remove Sensitive Data
        self.batch_remove_sensitive_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Remove Sensitive Data", variable=self.batch_remove_sensitive_data_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Patterns to search for (comma-separated)
        ttk.Label(options_frame, text="Patterns to Replace:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_patterns_var = tk.StringVar(value="copyright,license,author")
        ttk.Entry(options_frame, textvariable=self.batch_patterns_var, width=30).grid(row=4, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Replacement text
        ttk.Label(options_frame, text="Replacement Text:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_replacement_var = tk.StringVar(value="[REDACTED]")
        ttk.Entry(options_frame, textvariable=self.batch_replacement_var, width=30).grid(row=5, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Remote repository creation options
        remote_frame = ttk.LabelFrame(parent, text="Remote Repository Creation")
        remote_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # GitHub API Token
        ttk.Label(remote_frame, text="GitHub API Token:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_github_token_var = tk.StringVar()
        ttk.Entry(remote_frame, textvariable=self.batch_github_token_var, width=50, show="*").grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Repository Name Template
        ttk.Label(remote_frame, text="Repository Name Template:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_repo_name_template_var = tk.StringVar(value="{repo_name}-rewritten")
        ttk.Entry(remote_frame, textvariable=self.batch_repo_name_template_var, width=30).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Help text for template
        help_label = ttk.Label(remote_frame, text="Use {repo_name} for original repo name and {index} for index number")
        help_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(1, weight=1)
        remote_frame.columnconfigure(1, weight=1)
    
    def _browse_directory(self):
        """Open a directory selection dialog."""
        directory = filedialog.askdirectory(title="Select Target Directory")
        if directory:
            self.target_dir_var.set(directory)
    
    def _update_log(self, message: str):
        """Update the log text area with new message."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _clear_log(self):
        """Clear the log text area."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _parse_branch_rename_mapping(self) -> Dict[str, str]:
        """Parse branch rename mapping from the input field."""
        mapping = {}
        if self.branch_rename_var.get():
            for pair in self.branch_rename_var.get().split(","):
                if ":" in pair:
                    old_name, new_name = pair.strip().split(":", 1)
                    mapping[old_name.strip()] = new_name.strip()
        return mapping
    
    def _parse_patterns(self, batch_mode=False) -> List[str]:
        """Parse patterns from the input field."""
        patterns_var = self.batch_patterns_var if batch_mode else self.patterns_var
        if patterns_var.get():
            return [pattern.strip() for pattern in patterns_var.get().split(",")]
        return []
    
    def _parse_date(self, date_str: str) -> datetime.datetime:
        """Parse date string to datetime object."""
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self._update_log(f"Invalid date format: {date_str}. Using current date instead.")
            return datetime.datetime.now()
    
    def _parse_batch_repo_urls(self) -> List[str]:
        """Parse repository URLs from batch processing text area."""
        urls_text = self.batch_repo_urls_text.get(1.0, tk.END).strip()
        if urls_text:
            return [url.strip() for url in urls_text.split('\n') if url.strip()]
        return []
    
    def _preview_changes(self):
        """Generate a preview of the changes that will be made."""
        try:
            # Clear the log
            self._clear_log()
            
            # Check which tab is active
            current_tab = self.notebook.index(self.notebook.select())
            
            if current_tab == 0:  # Single Repository tab
                self._preview_single_repo()
            else:  # Batch Processing tab
                self._preview_batch_repos()
            
        except Exception as e:
            self._update_log(f"Error generating preview: {str(e)}")
            messagebox.showerror("Error", f"Error generating preview: {str(e)}")
    
    def _preview_single_repo(self):
        """Preview changes for a single repository."""
        # Get input values
        repo_url = self.repo_url_var.get()
        if not repo_url:
            messagebox.showerror("Error", "Please enter a repository URL")
            return
        
        self._update_log(f"Preview for repository: {repo_url}")
        
        # Author changes
        author_name = self.author_name_var.get()
        author_email = self.author_email_var.get()
        if author_name and author_email:
            self._update_log(f"Author will be changed to: {author_name} <{author_email}>")
        
        # Date randomization
        if self.randomize_dates_var.get():
            start_date = self._parse_date(self.start_date_var.get())
            end_date = self._parse_date(self.end_date_var.get())
            self._update_log(f"Commit dates will be randomized between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")
        
        # Branch renaming
        branch_mapping = self._parse_branch_rename_mapping()
        if branch_mapping:
            self._update_log("Branches will be renamed:")
            for old_name, new_name in branch_mapping.items():
                self._update_log(f"  {old_name} -> {new_name}")
        
        # Remote repository
        remote_url = self.remote_url_var.get()
        github_token = self.github_token_var.get()
        repo_name = self.repo_name_var.get()
        
        if remote_url:
            self._update_log(f"Repository will be pushed to: {remote_url}")
        elif github_token and repo_name:
            self._update_log(f"A new repository named '{repo_name}' will be created and used as remote")
        
        # Sensitive data removal
        if self.remove_sensitive_data_var.get():
            patterns = self._parse_patterns()
            replacement = self.replacement_var.get()
            self._update_log(f"Sensitive data will be removed using patterns: {', '.join(patterns)}")
            self._update_log(f"Replacement text: '{replacement}'")
        
        self._update_log("Preview generation complete. Click 'Execute' to apply these changes.")
    
    def _preview_batch_repos(self):
        """Preview changes for batch repository processing."""
        # Get repository URLs
        repo_urls = self._parse_batch_repo_urls()
        if not repo_urls:
            messagebox.showerror("Error", "Please enter at least one repository URL")
            return
        
        self._update_log(f"Preview for batch processing {len(repo_urls)} repositories")
        
        # Author changes
        author_name = self.batch_author_name_var.get()
        author_email = self.batch_author_email_var.get()
        if author_name and author_email:
            self._update_log(f"Author will be changed to: {author_name} <{author_email}>")
        
        # Date randomization
        if self.batch_randomize_dates_var.get():
            self._update_log("Commit dates will be randomized for each repository")
        
        # Sensitive data removal
        if self.batch_remove_sensitive_data_var.get():
            patterns = self._parse_patterns(batch_mode=True)
            replacement = self.batch_replacement_var.get()
            self._update_log(f"Sensitive data will be removed using patterns: {', '.join(patterns)}")
            self._update_log(f"Replacement text: '{replacement}'")
        
        # Remote repository creation
        token = self.batch_github_token_var.get()
        repo_name_template = self.batch_repo_name_template_var.get()
        
        if token and repo_name_template:
            self._update_log(f"New repositories will be created using template: '{repo_name_template}'")
            self._update_log("Example repository names:")
            for i, url in enumerate(repo_urls[:3]):  # Show first 3 examples
                repo_name = url.split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                new_repo_name = repo_name_template.format(repo_name=repo_name, index=i+1)
                self._update_log(f"  {url} -> {new_repo_name}")
            
            if len(repo_urls) > 3:
                self._update_log(f"  ... and {len(repo_urls) - 3} more")
        
        self._update_log("Preview generation complete. Click 'Execute' to apply these changes.")
    
    def _execute_changes(self):
        """Execute the repository rewriting process."""
        # Disable all buttons during execution
        self._disable_buttons()
        
        # Check which tab is active
        current_tab = self.notebook.index(self.notebook.select())
        
        # Start the process in a separate thread
        if current_tab == 0:  # Single Repository tab
            threading.Thread(target=self._execute_single_repo_thread, daemon=True).start()
        else:  # Batch Processing tab
            threading.Thread(target=self._execute_batch_repos_thread, daemon=True).start()
    
    def _execute_single_repo_thread(self):
        """Thread function for executing changes on a single repository."""
        try:
            # Clear the log
            self.root.after(0, self._clear_log)
            
            # Get input values
            repo_url = self.repo_url_var.get()
            if not repo_url:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please enter a repository URL"))
                return
            
            target_dir = self.target_dir_var.get() if self.target_dir_var.get() else None
            
            # Initialize the controller
            self.root.after(0, lambda: self._update_log(f"Cloning repository: {repo_url}"))
            self.controller.initialize(repo_url, target_dir)
            self.root.after(0, lambda: self._update_log(f"Repository cloned successfully"))
            
            # Rewrite history
            author_name = self.author_name_var.get()
            author_email = self.author_email_var.get()
            randomize_dates = self.randomize_dates_var.get()
            
            if author_name and author_email:
                start_date = self._parse_date(self.start_date_var.get()) if randomize_dates else None
                end_date = self._parse_date(self.end_date_var.get()) if randomize_dates else None
                
                self.root.after(0, lambda: self._update_log(f"Rewriting commit history..."))
                self.controller.rewrite_history(author_name, author_email, randomize_dates, start_date, end_date)
                self.root.after(0, lambda: self._update_log(f"Commit history rewritten successfully"))
            
            # Rename branches
            branch_mapping = self._parse_branch_rename_mapping()
            if branch_mapping:
                self.root.after(0, lambda: self._update_log(f"Renaming branches..."))
                self.controller.rename_branches(branch_mapping)
                self.root.after(0, lambda: self._update_log(f"Branches renamed successfully"))
            
            # Remove sensitive data
            if self.remove_sensitive_data_var.get():
                patterns = self._parse_patterns()
                replacement = self.replacement_var.get()
                
                self.root.after(0, lambda: self._update_log(f"Removing sensitive data..."))
                self.controller.clean_sensitive_data(patterns, replacement)
                self.root.after(0, lambda: self._update_log(f"Sensitive data removed successfully"))
            
            # Setup remote and push
            remote_url = self.remote_url_var.get()
            github_token = self.github_token_var.get()
            repo_name = self.repo_name_var.get()
            
            if remote_url or (github_token and repo_name):
                self.root.after(0, lambda: self._update_log(f"Setting up remote repository..."))
                self.controller.setup_remote_and_push(remote_url, github_token, repo_name)
                self.root.after(0, lambda: self._update_log(f"Changes pushed to remote repository successfully"))
            
            # Cleanup
            self.controller.cleanup()
            
            self.root.after(0, lambda: self._update_log(f"Process completed successfully!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Repository rewriting completed successfully!"))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda error=error_msg: self._update_log(f"Error during execution: {error}"))
            self.root.after(0, lambda error=error_msg: messagebox.showerror("Error", f"Error during execution: {error}"))
        finally:
            # Re-enable buttons
            self.root.after(0, self._enable_buttons)
    
    def _execute_batch_repos_thread(self):
        """Thread function for executing batch repository processing."""
        try:
            # Clear the log
            self.root.after(0, self._clear_log)
            
            # Get repository URLs
            repo_urls = self._parse_batch_repo_urls()
            if not repo_urls:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please enter at least one repository URL"))
                return
            
            # Prepare operations dictionary
            operations = {}
            
            # Author changes
            author_name = self.batch_author_name_var.get()
            author_email = self.batch_author_email_var.get()
            if author_name and author_email:
                operations['new_author'] = author_name
                operations['new_email'] = author_email
            
            # Date randomization
            if self.batch_randomize_dates_var.get():
                operations['randomize_dates'] = True
                operations['start_date'] = datetime.datetime.now() - datetime.timedelta(days=365)
                operations['end_date'] = datetime.datetime.now()
            
            # Sensitive data removal
            if self.batch_remove_sensitive_data_var.get():
                operations['patterns'] = self._parse_patterns(batch_mode=True)
                operations['replacement'] = self.batch_replacement_var.get()
            
            # Remote repository creation
            token = self.batch_github_token_var.get()
            repo_name_template = self.batch_repo_name_template_var.get()
            
            if token and repo_name_template:
                operations['token'] = token
                operations['repo_name_template'] = repo_name_template
            
            # Execute batch processing
            self.root.after(0, lambda: self._update_log(f"Starting batch processing of {len(repo_urls)} repositories..."))
            
            # Process repositories
            batch_results = self.controller.process_batch(repo_urls, operations)
            
            # Show results
            success_count = sum(1 for result in batch_results if result['success'])
            self.root.after(0, lambda: self._update_log(f"Batch processing complete: {success_count}/{len(repo_urls)} repositories processed successfully"))
            
            # Log details for each repository
            for result in batch_results:
                if result['success']:
                    self.root.after(0, lambda result=result: self._update_log(f"Success: {result['repo_url']} - Operations: {', '.join(result['operations_completed'])}"))
                else:
                    self.root.after(0, lambda result=result: self._update_log(f"Failed: {result['repo_url']} - Error: {result['error']}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Batch Processing Complete", f"{success_count}/{len(repo_urls)} repositories processed successfully"))
            
        except Exception as e:
            self.root.after(0, lambda: self._update_log(f"Error during batch execution: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error during batch execution: {str(e)}"))
        finally:
            # Re-enable buttons
            self.root.after(0, self._enable_buttons)
    
    def _disable_buttons(self):
        """Disable all buttons during processing."""
        for widget in self.root.winfo_children():
            self._disable_widgets_recursive(widget)
    
    def _enable_buttons(self):
        """Enable all buttons after processing."""
        for widget in self.root.winfo_children():
            self._enable_widgets_recursive(widget)
    
    def _disable_widgets_recursive(self, widget):
        """Recursively disable all button widgets."""
        if isinstance(widget, ttk.Button):
            widget.state(['disabled'])
        
        for child in widget.winfo_children():
            self._disable_widgets_recursive(child)
    
    def _enable_widgets_recursive(self, widget):
        """Recursively enable all button widgets."""
        if isinstance(widget, ttk.Button):
            widget.state(['!disabled'])
        
        for child in widget.winfo_children():
            self._enable_widgets_recursive(child)
    
    def _on_close(self):
        """Clean up resources and close the application."""
        try:
            if self.controller:
                self.controller.cleanup()
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            self.root.destroy()


class FileChangeHandler(watchdog.events.FileSystemEventHandler):
    """File system event handler for code auto-update."""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = time.time()
        
    def on_modified(self, event):
        # Ignore events for non-Python files and directory modifications
        if not event.is_directory and event.src_path.endswith('.py'):
            # Debounce to avoid multiple reloads for the same change
            current_time = time.time()
            if current_time - self.last_modified > 1:  # 1 second debounce
                self.last_modified = current_time
                self.callback(event.src_path)
                
    def on_created(self, event):
        # Only watch for new Python files
        if not event.is_directory and event.src_path.endswith('.py'):
            current_time = time.time()
            if current_time - self.last_modified > 1:  # 1 second debounce
                self.last_modified = current_time
                self.callback(event.src_path)


class FileWatcher:
    """Watches for file changes and restarts the application."""
    
    def __init__(self, watch_dir: str, logger=None):
        self.watch_dir = watch_dir
        self.logger = logger
        self.observer = None
        
    def start(self):
        """Start watching for file changes."""
        if self.observer is None:
            self.observer = watchdog.observers.Observer()
            handler = FileChangeHandler(self.on_file_changed)
            self.observer.schedule(handler, self.watch_dir, recursive=True)
            self.observer.start()
            if self.logger:
                self.logger.log_event("INFO", f"File watcher started for {self.watch_dir}")
            else:
                print(f"File watcher started for {self.watch_dir}")
    
    def stop(self):
        """Stop watching for file changes."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            if self.logger:
                self.logger.log_event("INFO", "File watcher stopped")
            else:
                print("File watcher stopped")
    
    def on_file_changed(self, file_path: str):
        """Callback for when a file is changed."""
        if self.logger:
            self.logger.log_event("INFO", f"Detected change in {file_path}, restarting application...")
        else:
            print(f"Detected change in {file_path}, restarting application...")
            
        # Restart the application
        python = sys.executable
        os.execl(python, python, *sys.argv)


def main():
    """Main entry point for the application."""
    # Setup basic logging
    print("Starting Git Repository History Manipulator & Rewriter...")
    
    # Fix the logging module's format
    file_handler = None
    for handler in logging.getLogger("RepoRewrite").handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            file_handler = handler
            
    # Create and start the Tkinter application
    root = tk.Tk()
    app = RepoRewriteGUI(root)
    
    # Start file watcher for auto-updating when code changes
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_watcher = FileWatcher(script_dir, app.logging_module)
    file_watcher.start()
    
    # Print startup message
    print(f"File watcher started for {script_dir}")
    print("Application will automatically restart if code files are modified")
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"Error in main loop: {str(e)}")
    finally:
        # Ensure watcher is stopped when application exits
        file_watcher.stop()
        print("Application shutdown complete")


if __name__ == "__main__":
    main()
