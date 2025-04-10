# Git Repository History Manipulator & Rewriter

A powerful Python-based tool for modifying Git repository history and metadata. This application allows you to rewrite commit history, modify authors, randomize commit dates, rename branches, and clean sensitive information from repositories, all through an intuitive GUI interface.

![Git Repository History Manipulator & Rewriter](https://via.placeholder.com/800x450.png?text=Git+Repository+History+Manipulator+%26+Rewriter)

## Features

- Modify commit authors and emails across the entire repository history
- Randomize commit dates while maintaining chronological order
- Rename branches
- Clean sensitive information from repositories (e.g., author names, license, copyright)
- Configure new remote repositories via GitHub API and push changes
- Process multiple repositories in batch mode
- Detailed logging and preview functionality

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Git installed and configured
- GitHub account (optional, for creating new repositories)

### Dependencies

- GitPython
- Tkinter (usually comes with Python installations)
- Requests

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/reporewrite.git
cd reporewrite
```

2. Create a virtual environment:
```bash
# Using venv (recommended)
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, create it with the following content:
```
gitpython>=3.1.0
requests>=2.25.0
```

## Running the Application

After activating your virtual environment, run the application with:

```bash
python reporewrite.py
```

This will launch the graphical user interface where you can:

1. Enter a repository URL
2. Configure history rewriting options
3. Set up remote repository details
4. Preview and execute the changes

## Testing

The project includes a comprehensive test suite to verify functionality. To run all tests:

```bash
# Run all tests
python -m unittest discover

# Or run specific test modules
python -m unittest test_logging
python -m unittest test_repository
python -m unittest test_commit_modifier
python -m unittest test_file_processor
```

### Test Components

- `test_logging.py`: Tests for the logging module
- `test_repository.py`: Tests for repository handling operations
- `test_commit_modifier.py`: Tests for modifying commit metadata
- `test_file_processor.py`: Tests for finding and removing sensitive data

## SSH Key Setup for GitHub API

To use GitHub API functionality for creating new repositories:

1. Generate an SSH key if you don't already have one:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. Add the SSH key to your GitHub account:
   - Copy your public key content (usually in `~/.ssh/id_ed25519.pub`)
   - Go to GitHub Settings → SSH and GPG keys → New SSH key
   - Paste your key and save

3. Generate a personal access token:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Generate new token
   - Select the `repo` scope
   - Copy the generated token
   - Use this token in the application when prompted

## Usage Examples

### Single Repository Mode

1. Enter the repository URL
2. Configure author name and email
3. Select options like randomizing commit dates or removing sensitive data
4. Preview the changes
5. Click "Execute" to apply changes

### Batch Mode

1. Enter multiple repository URLs (one per line)
2. Set common settings for all repositories
3. Configure a template for new repository names
4. Preview the changes
5. Execute batch processing

## Troubleshooting

**Error during cloning**: Ensure the repository URL is correct and accessible.

**Authentication issues**: Check your SSH key configuration and GitHub API token.

**Git history rewriting fails**: Some repositories may have protection mechanisms that prevent history rewriting. Ensure you have proper permissions.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.