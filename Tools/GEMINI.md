# Gemini Project Analysis: Spinneret

## Project Overview

This directory contains `spinneret.sh`, an interactive Bash script that functions as a project manager for a creative writing workflow. The script leverages the Gemini CLI (`gemini`) to automate the process of turning a story outline into a full first draft.

The system is designed to be state-aware and resilient. Running the script presents a dashboard of all writing projects in the directory, allowing the user to manage multiple stories and pick up where they left off in the workflow. State is managed via a non-destructive, folder-based approval system. Each generation step (synopses, drafts) has a `drafts` and an `approved` subdirectory. The script determines project status by comparing the files in these two directories.

### Core Workflow

1.  **Project Creation:** The user selects a new outline file (`.txt` or `.md`). The script creates a self-contained project directory with a `synopses/drafts`, `synopses/approved`, `drafts/scenes/drafts`, and `drafts/scenes/approved` structure.
2.  **Synopsis Generation:** The script calls the Gemini CLI, and the initial AI-generated synopses are saved into the `synopses/drafts` directory.
3.  **Synopsis Approval:** The script pauses, waiting for user approval. To approve a scene, the user edits the file from the `synopses/drafts` folder and saves the final version into the `synopses/approved` folder. This preserves the original AI output. The script's approval gate prevents proceeding until all drafts have a corresponding file in the `approved` folder.
4.  **Draft Generation:** Once all synopses are approved, the script loops through each file in `synopses/approved`, calls the Gemini CLI to expand it into a full scene, and saves the output into the `drafts/scenes/drafts` directory.
5.  **Draft Approval:** The process pauses again for the user to approve the generated scene drafts by editing them and saving them into the `drafts/scenes/approved` directory.
6.  **Compilation:** After all drafts are approved, the script concatenates the files from `drafts/scenes/approved` in the correct order into a single Markdown manuscript file.

## Running the Script

There is no build process. The script is run directly from the terminal.

*   **To launch the project manager:**
    ```bash
    ./spinneret.sh
    ```

## Development Conventions

*   **Language:** The script is written entirely in Bash.
*   **Dependencies:** It relies on standard Unix utilities (`find`, `mkdir`, `mv`, `cat`, `awk`, `sed`) and a single external command-line tool, assumed to be `gemini`.
*   **User Interface:** The UI is built with interactive shell menus (`read`, `case`).
*   **State Management:** Project state is determined by analyzing the file system at runtime. The presence, absence, and naming of files and directories dictate the options available to the user.
