import os
import shutil
import sqlite3

from .arag_ops import updateContentList
from .helpers import processFileToText

def find_split(s, max_bytes):
    """
    Find the largest prefix of string s whose UTF-8 encoded length is <= max_bytes.
    Uses binary search for efficiency.
    """
    low = 0
    high = len(s)
    while low < high:
        mid = (low + high + 1) // 2
        if len(s[:mid].encode('utf-8')) <= max_bytes:
            low = mid
        else:
            high = mid - 1
    return low

def isCorpified(arag_path):
    """
    Checks if the given .arag directory is corpified by checking for corpus.db.

    Args:
        arag_path (str): Path to the .arag directory.
    
    Returns:
        bool: True if corpus.db exists, False otherwise.
    """
    corpus_db_path = os.path.join(arag_path, 'corpus.db')
    return os.path.exists(corpus_db_path)

def corpify(arag_path, options=None):
    """
    Process text files in .arag/content/ and store chunked content in a SQLite database at .arag/corpus.db.

    Args:
        arag_path (str): Path to the .arag directory.
        options (dict, optional): Configuration options. Supports:
            - 'chunk_size' (int): Max size in bytes for each chunk (default: 1MB).
            - 'force' (bool): If True, overwrite existing corpus.db (default: False).
    """
    if options is None:
            options = {}

    corpus_db_path = os.path.join(arag_path, 'corpus.db')

    if os.path.exists(corpus_db_path):
        if not options.get('force', False):
            print("Cannot corpify as existing corpus.db exists, run --force to remove it")
            return
        else:
            # Check if 'embedding' column exists
            conn = sqlite3.connect(corpus_db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(chunks)")
            columns = [col[1] for col in cursor.fetchall()]
            conn.close()
            if 'embedding' in columns:
                if not options.get('yes', False):
                    response = input("The existing corpus has embeddings stored, recorpifying will remove these. Are you sure you want to continue? (y/n): ")
                    if response.lower() != 'y':
                        print("Aborted")
                        return
            os.remove(corpus_db_path)

    # Connect to SQLite database (creates the file if it doesn’t exist)
    conn = sqlite3.connect(corpus_db_path)
    cursor = conn.cursor()

    # Create the chunks table
    cursor.execute('''CREATE TABLE chunks
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       file_path TEXT,
                       chunk_order INTEGER,
                       content TEXT)''')

    # Define content directory and chunk size
    content_path = os.path.join(arag_path, 'content')
    chunk_size = options.get('chunk_size', 8192)  # Default in bytes, overridden by argparse if specified

    # Process each file recursively
    for root, _, files in os.walk(content_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
            except UnicodeDecodeError:
                content = processFileToText(file_path)
                if content is None:
                    print(f"Skipping non-UTF-8 or non-convertable file: {file_path}")
                    continue

            # Compute relative path
            rel_path = os.path.relpath(file_path, content_path)
            chunk_order = 0

            # Split content into chunks and insert into database
            while content:
                k = find_split(content, chunk_size)
                if k == 0:
                    # Handle edge case where a character exceeds chunk_size
                    break
                chunk = content[:k]
                cursor.execute('INSERT INTO chunks (file_path, chunk_order, content) VALUES (?, ?, ?)',
                               (rel_path, chunk_order, chunk))
                chunk_order += 1
                content = content[k:]

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print(f"Corpified arag {arag_path}")


def clean(arag_path):
    corpus_db_path = os.path.join(arag_path, 'corpus.db')
    if not os.path.exists(corpus_db_path):
        print("Corpus database does not exist. Nothing to clean.")
        return

    content_path = os.path.join(arag_path, 'content')

    # Get unique file_paths from database
    conn = sqlite3.connect(corpus_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT file_path FROM chunks")
    db_file_paths = set(row[0] for row in cursor.fetchall())
    conn.close()

    # Get all files in content_path recursively
    all_files = []
    for root, _, files in os.walk(content_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, content_path)
            all_files.append(rel_path)

    # Find files to remove
    files_to_remove = [f for f in all_files if f not in db_file_paths]

    # Remove them
    for rel_path in files_to_remove:
        abs_path = os.path.join(content_path, rel_path)
        os.remove(abs_path)

    updateContentList(arag_path)

    print(f"Removed {len(files_to_remove)} files from content folder")


def isCorpusUpdated(arag_path):
    """
    Check if the content folder has changed since the last corpification.

    Args:
        arag_path (str): Path to the .arag directory.

    Returns:
        bool: False if the content folder has changed, True otherwise.
    """
    corpus_db_path = os.path.join(arag_path, 'corpus.db')
    if not os.path.exists(corpus_db_path):
        return False

    content_path = os.path.join(arag_path, 'content')
    corpus_mtime = os.path.getmtime(corpus_db_path)

    # Get all files in content_path recursively
    all_files = []
    for root, _, files in os.walk(content_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, content_path)
            all_files.append(rel_path)

    # Get unique file_paths from database
    conn = sqlite3.connect(corpus_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT file_path FROM chunks")
    db_file_paths = set(row[0] for row in cursor.fetchall())
    conn.close()

    # Check if sets match
    if set(all_files) != db_file_paths:
        return False

    # Check modification times
    for rel_path in all_files:
        abs_path = os.path.join(content_path, rel_path)
        file_mtime = os.path.getmtime(abs_path)
        if file_mtime > corpus_mtime:
            return False

    return True