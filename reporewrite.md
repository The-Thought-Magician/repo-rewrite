# Technical Specification: Git Repository History Manipulator & Rewriter

## 1. Overview

This project is a script-based tool designed to modify the history and metadata of a public GitHub repository. Given an input GitHub repository URL, the tool will provide a GUI that allows users to update various repository properties including commit dates, authors, branch names, and remote origin URLs. It will also offer options to randomize commit dates (while maintaining proper order) and automatically remove references to the original author name, license, and other identifying details from both the code and documentation files. Once changes have been confirmed, the tool will force-push the rewritten repository to a new (or user-supplied) remote repository.

The application will also support batch operations for multiple repositories and maintain robust logging of all actions and modifications.

## 2. Purpose and Scope

### 2.1 Purpose

- ✅ Provide a user-friendly tool to modify Git history and project metadata.
- ✅ Enable the anonymization and customization of repository details.
- ✅ Assist in the creation of clean, controlled repositories from existing public projects.

### 2.2 Scope

- ✅ Clone a public GitHub repository given its URL.
- ✅ GUI-based editing of:
  - ✅ Commit dates (with optional randomization in sequence),
  - ✅ Commit author names,
  - ✅ Branch names,
  - ✅ Remote URLs.
- ✅ Automated removal of sensitive references (such as original author names and license mentions) from source code and documentation.
- ✅ Option to create new remote repositories via the GitHub API (using SSH token authentication) or accept a manually provided repository URL.
- ✅ Batch processing for handling multiple repositories.
- ✅ Detailed logging and preview features to track and verify changes before execution.
- ✅ Force-pushing the modified repository to a designated remote repository.

## 3. Functional Requirements

### 3.1 Input and Initialization

- ✅ **Repository URL Input:** Accept a GitHub repository URL (or a list for batch processing).
- ✅ **Authentication:** Optionally authenticate using an SSH token for creating new remote repositories via the GitHub API.

### 3.2 Repository Operations

- ✅ **Cloning:** Clone the provided repository using Git.
- ✅ **History Rewriting:** Utilize Git history rewrite techniques (e.g., `git filter-branch`, `git rebase -i`, or libraries like GitPython) to:
  - ✅ Change commit dates,
  - ✅ Modify commit authors,
  - ✅ Rename branches,
  - ✅ Update remote origin URLs.
- ✅ **Random Commit Date Generator:** Option to auto-generate randomized commit dates ensuring chronological integrity.
- ✅ **Content Scrubbing:** Search through all text files (e.g., source code, README, license files) to:
  - ✅ Identify and remove original author names,
  - ✅ Remove explicit licensing information,
  - ✅ Optionally replace with user-defined placeholders.
- ✅ **Remote Repository Setup:**
  - ✅ Create a new repository via the GitHub API (if SSH token provided) or accept a user-defined remote URL.
  - ✅ Configure the new remote and force-push the modified history.

### 3.3 GUI Features

- ✅ **Dashboard:**
  - ✅ Input field(s) for repository URL(s).
  - ✅ Form elements for editing commit details and repository metadata.
  - ✅ Options for auto-randomizing commit dates.
  - ✅ Toggle for batch processing multiple repositories.
- ✅ **Preview Pane:**
  - ✅ Display planned changes (before execution).
  - ✅ Log changes with details on what modifications will be applied.
- ✅ **Action Buttons:**
  - ✅ Save/Execute: Runs the process and applies the changes.
  - ✅ Cancel/Reset: Revert any selections or modifications in the session.

### 3.4 Logging and Audit

- ✅ **Execution Logs:** Record each step of the process (e.g., cloning, editing commits, creating remote, pushing changes).
- ✅ **Change Preview Log:** Enable the user to review all pending modifications.
- ✅ **Error Handling:** Record errors and warnings with detailed messages in the logs, accessible via the GUI.

## 4. Non-Functional Requirements

- ✅ **Performance:** Efficient cloning and processing, even for repositories with a large commit history.
- ✅ **Reliability:** Ensure atomic operations where possible; guarantee that the repository's integrity is maintained (e.g., if rewriting fails, no partial changes are pushed).
- ✅ **Usability:** The GUI should be intuitive and provide clear instructions and real-time feedback.
- ✅ **Security:** Secure storage and usage of authentication tokens; ensure that sensitive data (like original repository details) is handled appropriately.
- ✅ **Portability:** The tool should work on major OS platforms (Windows, macOS, and Linux).
- ✅ **Extensibility:** Modular design to allow further feature enhancements like additional metadata edits or different hosting providers.

## 5. System Architecture

### 5.1 High-Level Architecture Diagram

```plaintext
+-------------------------------------------------------+
|                       GUI Layer                       |
|  - Input Forms (Repo URL, auth token, options)        |
|  - Preview & Logging Panels                           |
|                                                       |
+--------------------↓----------------------------------+
                     Backend Controller
                         (Orchestrator)
+-------------------------------------------------------+
|                   Core Modules                        |
| 1. Repository Handler Module                          |
|    - Cloning using Git commands                       |
|    - Managing local repo state                        |
|                                                       |
| 2. Commit Modifier Module                             |
|    - Parsing commit history                           |
|    - Rewriting commit details (dates, authors)        |
|    - Random commit date generator                     |
|                                                       |
| 3. Branch & Remote Manager Module                     |
|    - Renaming branches                                |
|    - Configuring/Updating remote URL                  |
|                                                       |
| 4. File Processor Module                              |
|    - Scanning codebase and docs for sensitive details  |
|    - Removing or replacing sensitive information      |
|                                                       |
| 5. Remote Repository Manager Module                   |
|    - Interfacing with GitHub API (if applicable)        |
|    - Creating new remote repo using provided credentials|
|                                                       |
| 6. Logging Module                                     |
|    - Detailed recording of actions and events         |
|                                                       |
+--------------------↓----------------------------------+
                     Execution Engine
                         (Script Runner)
+-------------------------------------------------------+
|                 Git CLI/Library Interface             |
|   - Execution of git commands (clone, filter-branch,   |
|     push --force, etc.)                                |
+-------------------------------------------------------+
```

### 5.2 Module Interactions

- ✅ **GUI ↔ Backend Controller:** The GUI collects user inputs and sends them to the controller, which then coordinates the operations with the core modules.
- ✅ **Repository Handler ↔ Commit Modifier:** After cloning, the commit modifier reads commit history and applies modifications as specified.
- ✅ **File Processor ↔ Repository Files:** Scans all textual files and applies cleansing operations.
- ✅ **Remote Repository Manager:** If a new remote repo is to be created, it interacts with the GitHub API; otherwise, it updates the remote configuration on the repository.
- ✅ **Logging Module:** Integrated into every module to capture detailed logs for each process step, displaying them in the GUI and optionally saving to file.

## 6. Detailed Component Description

### 6.1 Repository Handler Module

- ✅ **Responsibilities:**
  - ✅ Clone the repository using the provided URL.
  - ✅ Maintain local repository state.
  - ✅ Handle cleanup if the process is aborted.
- ✅ **Key Functions:**
  - ✅ `clone_repo(url: str, target_dir: str)`: Clones the repo.
  - ✅ `fetch_repo_info()`: Retrieves information about commits, branches, etc.

### 6.2 Commit Modifier Module

- ✅ **Responsibilities:**
  - ✅ Traverse commit history.
  - ✅ Modify commit metadata (dates, authors).
  - ✅ Implement commit date randomization:
    - ✅ Generate a random sequence of dates ensuring they remain in chronological order.
- ✅ **Key Functions:**
  - ✅ `update_commit_metadata(commit_list: List[Commit], new_author: str, new_dates: List[datetime])`
  - ✅ `randomize_commit_dates(commit_list: List[Commit])`

### 6.3 Branch & Remote Manager Module

- ✅ **Responsibilities:**
  - ✅ Rename branches and update branch references.
  - ✅ Update the remote origin URL.
- ✅ **Key Functions:**
  - ✅ `rename_branch(old_name: str, new_name: str)`
  - ✅ `set_remote_url(new_url: str)`
  
### 6.4 File Processor Module

- ✅ **Responsibilities:**
  - ✅ Recursively search through all repository files.
  - ✅ Identify files with sensitive metadata (author names, license text, etc.).
  - ✅ Remove or replace the data.
- ✅ **Key Functions:**
  - ✅ `scan_and_replace(file_path: str, patterns: List[str], replacement: str)`
  - ✅ `update_all_files(repo_dir: str, patterns: List[str], replacement: str)`

### 6.5 Remote Repository Manager Module

- ✅ **Responsibilities:**
  - ✅ Create a new remote repository via GitHub API when SSH token is provided.
  - ✅ Configure the new repository remote, or accept a manually provided URL.
- ✅ **Key Functions:**
  - ✅ `create_remote_repo(repo_name: str, token: str) -> str`
  - ✅ `configure_remote(repo_path: str, remote_url: str)`

### 6.6 Logging Module

- ✅ **Responsibilities:**
  - ✅ Record every modification and action.
  - ✅ Provide a preview of changes before executing push operations.
- ✅ **Key Functions:**
  - ✅ `log_event(event_type: str, message: str)`
  - ✅ `retrieve_logs() -> List[str]`

### 6.7 GUI Layer

- ✅ **Responsibilities:**
  - ✅ Present a clear and interactive dashboard for user inputs.
  - ✅ Allow previewing changes and viewing logs.
  - ✅ Provide feedback during long-running operations.
- ✅ **Technology Options:**
  - ✅ Use a Python-based toolkit such as **Tkinter** or **PyQt5/PySide2**.
- ✅ **Key Interface Elements:**
  - ✅ **Input Form:** Fields for repository URL(s), new commit metadata, remote repo details.
  - ✅ **Options Panel:** Options for random commit dates, batch processing toggles, sensitive data removal toggles.
  - ✅ **Log/Preview Panel:** Real-time listing of planned actions and changes.
  - ✅ **Action Buttons:** "Save/Execute", "Cancel", and "View Log".

## 7. Process Flow

1. ✅ **User Input & Initialization:**
   - ✅ User enters one or multiple repository URLs and provides required metadata (new commit authors, branch names, remote URL or credentials for new repo creation).
   - ✅ User selects options (e.g., auto-randomize commit dates, sensitive data removal).

2. ✅ **Cloning and Preprocessing:**
   - ✅ The Repository Handler clones the repository locally.
   - ✅ The Commit Modifier and File Processor modules scan the repository and build a preview list of changes.
   - ✅ The GUI displays the preview and logs.

3. ✅ **User Confirmation:**
   - ✅ The user reviews the preview. Adjustments can be made.
   - ✅ Once confirmed, the user clicks "Save/Execute".

4. ✅ **Modification Execution:**
   - ✅ The Commit Modifier rewrites the commit history with new dates and authors.
   - ✅ The Branch & Remote Manager updates branch names and remote URL.
   - ✅ The File Processor cleans up the repository contents to remove sensitive details.
   - ✅ The Remote Repository Manager either creates a new repository (if configured) or reconfigures the remote URL.

5. ✅ **Finalization:**
   - ✅ The script force-pushes the altered repository to the designated remote.
   - ✅ A final log is saved and displayed in the GUI.
   - ✅ In case of errors, detailed rollback or error handling procedures log the failure details.

## 8. Error Handling and Rollback

- ✅ **Transactional Operations:** Where feasible, ensure changes (especially in Git history rewriting) are rolled back if an error occurs.
- ✅ **Logging Errors:** Detailed logging including error codes, timestamps, and affected modules.
- ✅ **User Notification:** The GUI will provide clear messages if an error occurs, with potential steps for recovery.

## 9. Testing Strategy

- ✅ **Unit Testing:** Each module (Repository Handler, Commit Modifier, etc.) should have dedicated unit tests.
- ✅ **Integration Testing:** Validate interaction between modules such as commit rewriting and file scanning.
- ✅ **User Acceptance Testing (UAT):** Test the complete workflow with sample repositories to verify that all intended modifications are correctly applied.
- ✅ **Regression Testing:** Ensure that each new change does not negatively impact existing functionality.

## 10. Future Enhancements

- **Additional SCM Support:** Extend the tool to support other version control systems.
- **Enhanced Filtering:** More robust pattern matching and templating for sensitive data removal.
- **Undo Feature:** Option to roll back changes post-execution with backup branches.
- **Improved Analytics:** Graphical charts within the GUI showing commit history modifications and statistics.

## 11. Tooling and Libraries

- ✅ **Programming Language:** Python 3.x
- ✅ **Git Operations:** Utilize `GitPython` library or direct Git CLI commands.
- ✅ **GUI Framework:** Tkinter (for simplicity) or PyQt5/PySide2 (for advanced features).
- ✅ **HTTP Requests:** Use `requests` library for interacting with the GitHub API.
- ✅ **Logging:** Python's built-in `logging` module.
- ✅ **Regular Expressions:** Python's `re` module for pattern matching in file processing.

## 12. Deployment and Execution

- **Executable Packaging:** Consider packaging as a standalone executable using PyInstaller for easier distribution.
- ✅ **Configuration Files:** Allow settings to be loaded via YAML or JSON for environment-specific configurations.
- ✅ **Documentation:** Provide clear usage instructions and inline help in the GUI.

---

✅ This implementation now completes the technical specification for the Git Repository History Manipulator & Rewriter tool. All core features have been implemented and tested.
