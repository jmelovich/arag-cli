import os
import shutil
import sqlite3

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

    # Define the database path
    corpus_db_path = os.path.join(arag_path, 'corpus.db')

    # Handle existing corpus.db
    if os.path.exists(corpus_db_path):
        if not options.get('force', False):
            print("Cannot corpify as existing corpus.db exists, run --force to remove it")
            return
        else:
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
    chunk_size = options.get('chunk_size', 1024 * 128)  # Default in bytes, overridden by argparse if specified

    # Process each file recursively
    for root, _, files in os.walk(content_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
            except UnicodeDecodeError:
                print(f"Skipping non-UTF-8 file: {file_path}")
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