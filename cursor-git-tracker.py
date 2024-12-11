#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import git
import logging
import fnmatch
import json
from typing import Set, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_changes.log'),
        logging.StreamHandler()
    ]
)

class Config:
    DEFAULT_CONFIG = {
        "file_patterns": [
            # Source files - common programming languages
            "**/*.py",
            "**/*.js",
            "**/*.jsx",
            "**/*.ts",
            "**/*.tsx",
            "**/*.java",
            "**/*.cpp",
            "**/*.c",
            "**/*.h",
            "**/*.cs",
            "**/*.go",
            "**/*.rb",
            "**/*.php",
            "**/*.swift",
            "**/*.kt",
            # Web development files
            "**/*.html",
            "**/*.css",
            "**/*.scss",
            "**/*.sass",
            "**/*.less",
            "**/*.vue",
            "**/*.svelte",
            # Config and documentation files
            "**/*.json",
            "**/*.yml",
            "**/*.yaml",
            "**/*.xml",
            "**/*.md",
            "**/*.markdown",
            "**/README*",
            "**/LICENSE*",
            "**/*.config.*"
        ],
        "ignore_patterns": [
            # Version control
            "**/.git/**",
            "**/.svn/**",
            "**/.hg/**",
            # Dependencies and package managers
            "**/node_modules/**",
            "**/venv/**",
            "**/.virtualenv/**",
            "**/vendor/**",
            "**/.bundle/**",
            # Build and output directories
            "**/build/**",
            "**/dist/**",
            "**/out/**",
            "**/target/**",
            "**/bin/**",
            "**/obj/**",
            # Cache and temporary files
            "**/__pycache__/**",
            "**/.cache/**",
            "**/.temp/**",
            "**/.tmp/**",
            # IDE and editor files
            "**/.idea/**",
            "**/.vscode/**",
            "**/.vs/**",
            # Logs and debug files
            "**/logs/**",
            "**/*.log",
            "**/debug/**",
            # Other common ignore patterns
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.swp",
            "**/*.swo"
        ],
        "backup_branch_prefix": "cursor-backup",
        "max_backup_branches": 5,
        "commit_cooldown": 5,  # seconds
        "create_backup_branches": True
    }

    @staticmethod
    def load_config(repo_path: str) -> dict:
        config_path = os.path.join(repo_path, 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    return {**Config.DEFAULT_CONFIG, **user_config}
            except json.JSONDecodeError:
                logging.warning("Invalid config file. Using default configuration.")
        return Config.DEFAULT_CONFIG

class CursorChangeHandler(FileSystemEventHandler):
    def __init__(self, repo_path: str, config: dict):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        self.last_commit_time = time.time()
        self.pending_changes: Set[str] = set()
        self.config = config
        self.last_backup_time = time.time()

    def should_track_file(self, file_path: str) -> bool:
        relative_path = os.path.relpath(file_path, self.repo_path)

        # Check ignore patterns first
        for pattern in self.config["ignore_patterns"]:
            if fnmatch.fnmatch(relative_path, pattern):
                return False

        # Then check if file matches tracked patterns
        for pattern in self.config["file_patterns"]:
            if fnmatch.fnmatch(relative_path, pattern):
                return True

        return False

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        if not self.should_track_file(file_path):
            return

        relative_path = os.path.relpath(file_path, self.repo_path)
        self.pending_changes.add(relative_path)
        self._try_commit()

    def _try_commit(self):
        current_time = time.time()
        if current_time - self.last_commit_time >= self.config["commit_cooldown"] and self.pending_changes:
            self._create_commit()
            self.last_commit_time = current_time

            # Create backup branch if enabled and enough time has passed (every hour)
            if self.config["create_backup_branches"] and \
               current_time - self.last_backup_time >= 3600:  # 1 hour
                self._create_backup_branch()
                self.last_backup_time = current_time

    def _create_backup_branch(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"{self.config['backup_branch_prefix']}-{timestamp}"

            # Create new branch from current state
            current = self.repo.active_branch
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()

            # Switch back to original branch
            current.checkout()

            # Remove old backup branches if we exceed the maximum
            self._cleanup_backup_branches()

            logging.info(f"Created backup branch: {branch_name}")

        except Exception as e:
            logging.error(f"Error creating backup branch: {str(e)}")

    def _cleanup_backup_branches(self):
        backup_branches = sorted([
            branch for branch in self.repo.heads
            if branch.name.startswith(self.config['backup_branch_prefix'])
        ], key=lambda x: x.commit.committed_datetime)

        # Remove oldest branches if we exceed the maximum
        while len(backup_branches) > self.config["max_backup_branches"]:
            oldest_branch = backup_branches.pop(0)
            self.repo.delete_head(oldest_branch, force=True)
            logging.info(f"Removed old backup branch: {oldest_branch.name}")

    def _create_commit(self):
        try:
            # Stage all pending changes
            for file_path in self.pending_changes:
                self.repo.index.add([file_path])

            # Create commit with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Cursor changes at {timestamp}\n\nFiles changed:\n"
            commit_message += "\n".join(self.pending_changes)

            self.repo.index.commit(commit_message)
            logging.info(f"Created commit for changes in: {', '.join(self.pending_changes)}")

            # Clear pending changes
            self.pending_changes.clear()

        except Exception as e:
            logging.error(f"Error creating commit: {str(e)}")

def setup_git_config():
    """Ensure git configuration is set up"""
    try:
        subprocess.run(["git", "config", "--get", "user.name"], check=True)
        subprocess.run(["git", "config", "--get", "user.email"], check=True)
    except subprocess.CalledProcessError:
        print("Git user configuration not found. Please set up git config first:")
        print("git config --global user.name \"Your Name\"")
        print("git config --global user.email \"your.email@example.com\"")
        sys.exit(1)

def create_default_config(repo_path: str):
    """Create a default configuration file if it doesn't exist"""
    config_path = os.path.join(repo_path, '.cursor-tracker-config.json')
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(Config.DEFAULT_CONFIG, f, indent=2)
        print(f"Created default configuration file at {config_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python cursor_git_tracker.py <repository_path>")
        sys.exit(1)

    repo_path = os.path.abspath(sys.argv[1])

    if not os.path.exists(repo_path):
        print(f"Repository path does not exist: {repo_path}")
        sys.exit(1)

    try:
        git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        print(f"Not a valid git repository: {repo_path}")
        sys.exit(1)

    setup_git_config()
    create_default_config(repo_path)
    config = Config.load_config(repo_path)

    event_handler = CursorChangeHandler(repo_path, config)
    observer = Observer()
    observer.schedule(event_handler, repo_path, recursive=True)
    observer.start()

    logging.info(f"Started watching repository: {repo_path}")
    print(f"Watching for changes in {repo_path}")
    print("Current configuration:")
    print(json.dumps(config, indent=2))
    print("\nPress Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopped watching repository")

    observer.join()

if __name__ == "__main__":
    main()