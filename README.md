# librolibero

A command-line importer that tracks a folder of PDFs and EPUBs, extracts ISBNs, searches for bibliographic metadata from online services, and creates *book* items in Zotero with linked file attachments, compatible with the ZotMoov plugin.

## Description

`librolibero` automates the process of importing a collection of books into Zotero. It:

1. **Scans** a folder for PDFs and EPUBs
2. **Extracts ISBNs** from file names or document content
3. **Resolves metadata** bibliographically via cascading APIs (isbnlib, Open Library, Google Books)
4. **Detects duplicates** in Zotero and offers interactive handling options
5. **Creates items** in Zotero with linked file attachments
6. **Optionally moves** files to trash after successful import

### Use case

Import collections of books whose file names follow a structured pattern:
```
Title -- Author -- Year -- Publisher -- isbn13 XXXXXXXXXXXXX -- hash -- suffix.pdf
```

## Requirements

- Python 3.8+
- Zotero API credentials (ID and access key)

## Installation

### Via pip

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

### Dependencies

- **pyzotero** — Zotero API access
- **isbnlib** — ISBN metadata resolution
- **pymupdf** (fitz) — ISBN extraction from PDFs
- **ebooklib** — EPUB metadata extraction
- **requests** — HTTP requests
- **tomli** — TOML file parsing
- **python-dotenv** — environment variable loading
- **send2trash** — safe file deletion to trash

## Configuration

### Environment Variables

Create a `.nosync/.env` file in the project root with your Zotero credentials:

```env
ZOTERO_ID=your_user_id_here
zoteroKEY=your_api_key_here
```

**Getting credentials:**
1. Visit [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
2. Create a new access key with write permissions
3. Your User ID is available at [zotero.org/settings/profile](https://www.zotero.org/settings/profile)

### Configuration File

Optionally, create a `config.toml` file in the project root to customize behavior:

```toml
[config]
directory = "books/"
extensions = [".pdf", ".epub"]
zotmoov_mode = false
```

**Parameters:**

- **directory** — path to folder containing books (default: `books/`)
- **extensions** — file extensions to process (default: `[".pdf", ".epub"]`)
- **zotmoov_mode** — when `true`, suppresses trash behavior of `--trash-after-import` since ZotMoov plugin moves files automatically (default: `false`)

## Usage

### Basic Command

```bash
python -m librolibero
```

Processes all files in the default folder (`books/`) and imports them into Zotero.

### Command-Line Options

```bash
python -m librolibero --help
```

**Available options:**

- `--dir DIR` — source folder containing books (overrides `config.toml`)
- `--dry-run` — executes without sending POST requests to Zotero; only shows what would be done
- `--trash-after-import` — moves files to trash after successful import (ignored if `zotmoov_mode=true`)

### Examples

**Test without changing anything:**
```bash
python -m librolibero --dry-run
```

**Import from a specific folder:**
```bash
python -m librolibero --dir /path/to/my_books
```

**Import and move files to trash:**
```bash
python -m librolibero --trash-after-import
```

## Execution Pipeline

The processing flow follows this diagram:

```
scan_and_extract()
    ↓
    extract_isbn_from_filename()
         └→ extract_isbn_from_content() [fallback]
    ↓
resolve_metadata(isbn)
    ├→ isbnlib merge
    ├→ isbnlib openl [fallback]
    ├→ Open Library REST [fallback]
    ├→ Google Books REST [fallback]
    └→ resolve_metadata_from_filename() [fallback final]
    ↓
import_file()
    ├→ find_existing_by_isbn() [detects duplicates]
    ├→ create_item() [creates new item in Zotero]
    └→ attach_linked_file() [attaches linked file]
    ↓
send2trash() [optional, if --trash-after-import]
```

### Detailed Steps

#### 1. Scan Files
Tracks the folder and lists all files with configured extensions (`.pdf`, `.epub`).

#### 2. Extract ISBN
Attempts to extract ISBN in priority order:
1. Explicit pattern `isbn13 XXXXXXXXXXXXX` (structured names with highlighted ISBN)
2. Generic ISBN-13 (13 consecutive digits)
3. Generic ISBN-10 (9 digits + check digit)
4. **Fallback:** reads file content (first 5 pages of PDF or EPUB metadata)

#### 3. Resolve Metadata
Searches for bibliographic information via cascading APIs:
- isbnlib (merge)
- isbnlib (openl)
- Open Library REST
- Google Books REST
- Fallback: extracts title and year from file name

#### 4. Import to Zotero
Before creating, checks if an item with the same ISBN already exists:
- **Duplicate found:**
  - Asks user (or uses global strategy)
  - Options: ignore, create new item, or attach to existing
- **No duplicate:**
  - Creates new item in Zotero
  - Attaches file as linked file

#### 5. Optional Cleanup
If `--trash-after-import` is used (and not in `zotmoov_mode`), moves the file to trash.

## Project Structure

```
librolibero/
├── __init__.py           # Package version
├── __main__.py           # Entry point (python -m librolibero)
├── cli.py                # Command-line interface (argparse)
├── config.py             # .env and config.toml loading
├── scanner.py            # File tracking and ISBN extraction
├── metadata.py           # Metadata lookup via APIs
├── zotero_client.py      # Zotero API integration
└── report.py             # Logging and final summary
```

## Logs

Import logs are saved in `logs/import_YYYY-MM-DD.log` with detailed information about each processed file, successes, failures, and warnings.

## Duplicate Handling

When the same ISBN already exists in Zotero, the program offers interactive options:

```
1) Ignore this file
2) Create new item anyway
3) Attach to existing item (most recent)
4) Ignore ALL next duplicates
5) Create new items for ALL next duplicates
6) Attach ALL next duplicates to existing item
```

Choosing option 4, 5, or 6 applies the strategy to all subsequent files, avoiding repeated prompts.

## Troubleshooting

### "ZOTERO_ID or zoteroKEY not found"
Make sure the `.nosync/.env` file exists and contains the correct credentials.

### "Metadata not found"
If the ISBN is not extracted correctly, the program attempts to extract metadata from the file name. Check if the name format is close to the expected one (title, author, year).

### ZotMoov Mode
If using the ZotMoov plugin, configure `zotmoov_mode = true` in `config.toml` to avoid conflicts with automatic file management.

## License

Personal project. Feel free to use and modify as needed.
