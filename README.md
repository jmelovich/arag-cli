# aRAG CLI Tool

aRAG, or `arag`, is a command-line interface (CLI) tool for creating, managing, and querying a custom file type called `.arag`. This tool enables users to package content into a structured format, process it into a searchable corpus, generate embeddings for vector-based querying, and retrieve information efficiently. It currently supports both local and OpenAI-based embedding methods and includes features for content management, packaging, and interactive usage.

The goal of the `arag` file type is to create a simple, self-contained method for creating localized vector databases that can be easily implemented for use with RAG and LLMs. Imagine, for example, if you could download the entire documentation for some coding language or package, generate an `arag` with a couple clicks, and then drag and drop this file into your AI chats, giving it the information effectively without compromising your context window. The current plan is that support for `arag` files will be added to popular LLM chats (like chatgpt.com) via a browser extension to further increase their usefulness.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Commands](#commands)
  - [Interactive Mode](#interactive-mode)
  - [Spec File Creation](#spec-file-creation)
  - [Examples](#examples)
- [File Structure](#file-structure)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Create `.arag` Files**: Generate `.arag` directories or packaged archives with a custom structure.
- **Content Management**: Add, delete, list, and clean content within `.arag` files.
- **Corpus Processing**: Convert content into a SQLite-based searchable corpus with chunking support.
- **Embedding Generation**: Index content using OpenAI or local SentenceTransformer models for vector search.
- **Vector Querying**: Perform similarity searches on indexed content using a query string.
- **Packaging**: Compress `.arag` directories into `.arag` archives and unpackage them as needed.
- **Interactive Mode**: Open an `.arag` file and manage it interactively.
- **Custom VFS**: Query packaged `.arag` files directly using a SQLite Virtual File System (VFS).

## Installation

### Prerequisites

- Python (3.11 was used for development)
- `pip` package manager

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/jmelovich/arag-cli.git
   cd arag
   ```

2. **Install the Package**:
   ```bash
   pip install .
   ```

   To include optional support for local embeddings (SentenceTransformer), use:
   ```bash
   pip install ".[local_embeddings]"
   ```

3. **Verify Installation**:
   ```bash
   arag --help
   ```

   This should display the CLI help message with available commands.

## Usage

The `arag` CLI provides a variety of subcommands to manage `arag` files. Below is an overview of the commands and their usage.

### Commands

#### `create`
Create a new `arag` directory, spec file, or packaged `.arag` from a spec.

- **Create a Directory**:
  ```bash
  arag create dir myarag /path/to/directory
  ```
  Creates `myarag-arag` directory at the specified path. An `arag` directory works the same as an `.arag` file, but is not read only (until packaged into a file). This is the principle way to create an `arag`.

- **Create a Spec File**:
  ```bash
  arag create spec /path/to/example.arag-json
  ```
  Generates a template `.arag-json` file. You can modify this template to set all the settings needed to create a `.arag` file.

- **Create from Spec**:
  ```bash
  arag create from-spec /path/to/spec.arag-json
  ```
  Builds a packaged `.arag` file based on the spec file. This is the easiest way to create an `arag` file.

#### `content`
Manage content within an `.arag` directory (not supported for packaged files). Content is whatever you want to be indexed, so (for now) any sort of text information, pdfs, or docx files.

- **Add Content**:
  ```bash
  arag content add myfile.txt --arag /path/to/myarag-arag
  ```
  Adds `myfile.txt` to the `content` folder. This also supports directories, and will add all files in a pointed directory recursively.

- **Delete Content**:
  ```bash
  arag content del myfile.txt --arag /path/to/myarag-arag
  ```
  Removes `myfile.txt` from the `content` folder. Also works with directories.

- **List Contents**:
  ```bash
  arag content ls --arag /path/to/myarag-arag
  ```
  Lists all files in the `content` folder.

- **Corpify Content**:
  ```bash
  arag content corpify --arag /path/to/myarag-arag --chunk-size 8192 --force
  ```
  Processes content into `corpus.db` with specified chunk size. The `--force` flag overwrites any existing corpus. The `--chunk-size` argument determines how often each entry (file) being added to the corpus should be split into its own row, in bytes (the default is typically fine).

- **Clean Content**:
  ```bash
  arag content clean --arag /path/to/myarag-arag
  ```
  Removes files from `content` not present in `corpus.db`. This is always recommended as to not waste space.

#### `index`
Generate embeddings for the corpus.

- **Index with OpenAI**:
  ```bash
  arag index --arag /path/to/myarag-arag --method openai --api-key YOUR_API_KEY
  ```
  Indexes using OpenAI embeddings. The `--api-key` flag is optional if you have an api key set as an evironmental variable called `OPENAI_API_KEY`.

- **Index Locally**:
  ```bash
  arag index --arag /path/to/myarag-arag --method local
  ```
  Uses the default SentenceTransformer model. Pass the `--model` argument to determine the model to use, given as a huggingface name such as `sentence-transformers/all-MiniLM-L6-v2`.

#### `query`
Search the corpus with a query string.

- **Query with Results**:
  ```bash
  arag query "search term" --arag /path/to/myarag.arag --topk 3
  ```
  Returns top 3 matching chunks with content. `--topk` defaults to 1.

- **Query with File Paths**:
  ```bash
  arag query "search term" --arag /path/to/myarag.arag --get-file
  ```
  Returns just file paths instead of content.

#### `package`
Package an `.arag` directory into a `.arag` file.

- **Package Directory**:
  ```bash
  arag package /path/to/myarag-arag --remove-original
  ```
  Creates `myarag.arag` and removes the original directory.

#### `unpackage`
Unpackage a `.arag` file into a directory.

- **Unpackage File**:
  ```bash
  arag unpackage /path/to/myarag.arag --remove-original
  ```
  Extracts to `myarag-arag` and removes the original file.

#### `open`
Enter interactive mode with an `.arag` file or directory.

- **Open a File**:
  ```bash
  arag open /path/to/myarag.arag
  ```
  Starts an interactive shell for managing the `.arag`.

### Interactive Mode

Run `arag open <path>` to interact with an `.arag` file or directory. Commands can be entered without the `arag` prefix, or an `--arag` argument:

```bash
> content ls
> content add myfile.txt
> query "find this" --topk 2
> close
```

Type `quit` or `close` to exit.

### Spec File Creation

Use `arag create spec <destination>` to generate a template `.arag-json` file at the destination, then modify it:

```json
{
    "arag_name": "myarag",
    "arag_dest": "./myarag.arag",
    "content_include": ["file1.txt", "dir/docs"],
    "clean_content": true,
    "chunk_size": 8192,
    "index_method": "openai",
    "index_model": "text-embedding-3-small",
    "api_key": "YOUR_API_KEY",
    "openai_endpoint": "https://api.openai.com/v1",
    "arag_version": "0.1.0",
    "should_package": true,
    "remove_arag_dir": true
}
```

Run `arag create from-spec <.arag-json-path>` to build the `.arag` file.

### Examples

1. **Full Workflow**:
   ```bash
   # Create an arag directory
   arag create dir myarag ./data
   # Open the arag directory in interactive mode
   arag open ./data/myarag-arag
   # Add content
   content add document.pdf
   # Corpify
   content corpify --clean
   # Index locally
   index --method local
   # Package the file and remove this directoru
   package --remove-original
   # Open the .arag file
   arag open ./data/myarag.arag
   # Query
   query "important info"
   ```

2. **Using a Spec File**:
   ```bash
   arag create spec myarag.arag-json

   # Edit myarag.arag-json as needed
   nano myarag.arag-json

   arag create from-spec myarag.arag-json
   ```

## File Structure

An `arag` directory/file has the following structure:

- `content/`: Stores raw files and directories.
- `content_list.txt`: Lists all files in `content/`.
- `corpus.db`: SQLite database with chunked content & vector embeddings.
- `index.json`: Metadata about embeddings (method, model, etc.).

A packaged `.arag` file is a special ZIP archive containing these components. (In a `.arag` file, only the content folder is compressed. The rest is stored directly for direct access.)

## Dependencies

- **Required**:
  - `apsw`: SQLite with custom VFS support.
  - `numpy`: For vector operations.
  - `openai`: For OpenAI embeddings.
  - `pypdf`: For PDF processing.
  - `spire.doc`: For DOCX processing.

- **Optional**:
  - `sentence-transformers`: For local embeddings (`pip install ".[local_embeddings]"`).

Install additional dependencies as needed for specific file types.

## Configuration

- **OpenAI API Key**: Set via `--api-key` or the `OPENAI_API_KEY` environment variable.
- **Embedding Models**: Default models are `sentence-transformers/all-MiniLM-L6-v2` (local) and `text-embedding-3-small` (OpenAI). Override with `--model`.
- **Chunk Size**: Default is 8192 bytes; adjust with `--chunk-size`.

## Contributing

Contributions are welcome! Please:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/yourfeature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/yourfeature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
