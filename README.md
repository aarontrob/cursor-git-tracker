# Cursor Git Change Tracker

A Python script that automatically tracks and commits changes made by Cursor AI in Git repositories. The script provides automatic commit creation, file filtering, and backup branch management to help maintain a clean development history.

## Features

- 🔄 Automatic change detection and commits
- 📁 Customizable file pattern filtering
- 🔖 Automatic backup branch creation
- 📝 Detailed logging of all changes
- ⏪ Easy rollback capabilities
- ⚙️ Configurable settings via JSON

## Prerequisites

- Python 3.6 or higher
- Git installed and configured
- Required Python packages:
  ```bash
  pip install gitpython watchdog
  ```

## Installation

1. Clone or download this repository
2. Make the script executable (Unix-based systems):
   ```bash
   chmod +x cursor_git_tracker.py
   ```

## Usage

1. Run the script by providing your repository path:

   ```bash
   python cursor_git_tracker.py /path/to/your/repository
   ```

2. The script will create a default `config.json` in your repository if one doesn't exist.

## Configuration

The script uses a `config.json` file with the following structure:

```json
{
  "file_patterns": [
    "**/*.py",
    "**/*.js",
    "**/*.jsx",
    "**/*.ts",
    "**/*.tsx",
    "**/*.html",
    "**/*.css",
    "**/*.json",
    "**/*.md",
    "**/*.config.*"
  ],
  "ignore_patterns": [
    "**/.git/**",
    "**/node_modules/**",
    "**/venv/**",
    "**/build/**",
    "**/dist/**"
  ],
  "backup_branch_prefix": "cursor-backup",
  "max_backup_branches": 5,
  "commit_cooldown": 5,
  "create_backup_branches": true
}
```

### Configuration Options

- `file_patterns`: List of file patterns to track
- `ignore_patterns`: List of patterns to ignore
- `backup_branch_prefix`: Prefix for backup branch names
- `max_backup_branches`: Maximum number of backup branches to keep
- `commit_cooldown`: Minimum time (in seconds) between commits
- `create_backup_branches`: Enable/disable automatic backup branches

## Working with Backup Branches

### List all backup branches

```bash
git branch | grep cursor-backup
```

### Switch to a backup branch

```bash
git checkout cursor-backup-20240311_143022
```

### Compare changes with a backup branch

```bash
git diff cursor-backup-20240311_143022
```

## Rolling Back Changes

### View commit history

```bash
git log
```

### Roll back to a specific commit

```bash
git checkout <commit-hash>
```

### Revert the last commit

```bash
git revert HEAD
```

## Logging

The script maintains a `cursor_changes.log` file in the directory where it's run, containing detailed information about:

- File changes detected
- Commits created
- Backup branches created/removed
- Any errors or issues encountered

## Troubleshooting

### Common Issues

1. **Git configuration not found**

   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Permission denied**

   - Ensure you have write permissions to the repository
   - Check that you're authenticated for Git operations

3. **Path not found**
   - Verify the repository path is correct
   - Ensure the repository is cloned locally

## Best Practices

1. Run the script from the parent directory of your repository
2. Regularly check the log file for any issues
3. Periodically clean up old backup branches if not needed
4. Test the configuration on a small scale before using it with large repositories

## Virtual Environment Setup

For a clean installation, use a virtual environment:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate     # Windows

# Install packages
pip install gitpython watchdog

# Run the script
python cursor_git_tracker.py /path/to/repository
```

## License

This script is provided under the MIT License. Feel free to modify and distribute it according to your needs.

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest improvements
- Submit pull requests

## Support

If you encounter any issues or need help:

1. Check the log file for error messages
2. Verify your Git configuration
3. Ensure all prerequisites are installed correctly
4. Check your repository permissions
