# File Integrity Checker — Cybersecurity Project

**Author: Muskan Sain**

A beginner-friendly Python tool that uses **SHA-256** to create a baseline of files and later detect files that were modified, added, or deleted.

## Features
- Calculates SHA-256 hashes using Python's `hashlib`.
- Saves file hashes and sizes in a JSON baseline.
- Verifies current files against the saved baseline.
- Reports unchanged, modified, added, and missing files.
- Reads files in chunks, so large files do not need to be loaded fully into memory.
- Skips symbolic links and excludes the baseline file itself.
- Uses only the Python standard library.

## Requirements
- Python 3.9 or newer.
- No third-party packages are required. `requirements.txt` is included for standard project setup.

Check Python:
```bash
python --version
```
On some Windows installations, use `py --version`.

## Project structure
```text
File_Integrity_Checker_Muskan_Sain/
├── file_integrity_checker.py
├── File_Integrity_Checker.ipynb
├── requirements.txt
├── README.md
├── PROJECT_REPORT.docx
└── tests/
    └── test_file_integrity_checker.py
```

## Run from terminal
Open a terminal in the project folder.

### 1. Create a test folder
```bash
mkdir sample_files
echo Original content > sample_files/notes.txt
```
On Windows Command Prompt, if `echo` redirection behaves differently, create `notes.txt` manually and type `Original content`.

### 2. Create the baseline
```bash
python file_integrity_checker.py baseline sample_files
```
This creates `sample_files/.file_integrity_baseline.json`. The baseline stores hashes, not copies of the original file contents.

### 3. Verify without changing anything
```bash
python file_integrity_checker.py verify sample_files
```
Expected result: `PASS — no changes detected.`

### 4. Test modification detection
Edit `sample_files/notes.txt` and change its content, save it, then run:
```bash
python file_integrity_checker.py verify sample_files
```
Expected result: `Modified: 1` and `WARNING`.

### 5. Test added-file detection
Create `sample_files/new.txt`, then verify again. Expected result includes `Added: new.txt`.

### 6. Test deleted-file detection
Delete `sample_files/notes.txt`, then verify again. Expected result includes `Missing: notes.txt`.

### 7. Reset the baseline
If the current files are now trusted, create a fresh baseline:
```bash
python file_integrity_checker.py baseline sample_files
```
This replaces the old baseline. Only do this after confirming the current files are safe and expected.

## Optional: choose another baseline path
```bash
python file_integrity_checker.py baseline sample_files --baseline trusted_baseline.json
python file_integrity_checker.py verify sample_files --baseline trusted_baseline.json
```

## Automated tests
Run:
```bash
python -m unittest discover -s tests -v
```
The tests create temporary files and check clean verification, modification, addition, deletion, and invalid baseline handling.

## Jupyter Notebook
Open `File_Integrity_Checker.ipynb` in Jupyter Notebook, JupyterLab, or Google Colab. Run the cells from top to bottom. The notebook demonstrates hashing, baseline creation, clean verification, and tamper detection using a temporary sample directory.

## Important security notes
- SHA-256 is a cryptographic hash function used to detect content changes. It does not encrypt files.
- Keep the baseline in a trusted location. If an attacker can change both the files and the baseline, the checker may not detect the tampering.
- A baseline records what was present at the time it was created; it does not prove that those files were safe.
- The tool skips symbolic links. Review any skipped links separately if they matter to your environment.
- The project is an educational integrity-monitoring demonstration, not a complete endpoint security product.

## Author
**Muskan Sain**
