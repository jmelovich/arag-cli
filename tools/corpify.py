import os
import shutil

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
    Checks if the given .arag directory is corpified.
    
    Args:
        arag_path (str): Path to the .arag directory.
    """

    
    # Define paths
    corpus_path = os.path.join(arag_path, 'corpus')
    
    # Check for existing corpus folder
    return os.path.exists(corpus_path)

def corpify(arag_path, options=None):
    """
    Process text files in .arag/content/ and create chunked text files in .arag/corpus/.
    
    Args:
        arag_path (str): Path to the .arag directory.
        options (dict, optional): Configuration options. Supports:
            - 'chunk_size' (int): Max size in bytes for each corpus file (default: 1MB).
            - 'force' (bool): If True, overwrite existing corpus folder (default: False).
    """
    if options is None:
        options = {}
    
    # Define paths
    corpus_path = os.path.join(arag_path, 'corpus')
    content_path = os.path.join(arag_path, 'content')
    
    # Check for existing corpus folder
    if os.path.exists(corpus_path):
        if not options.get('force', False):
            print("Cannot corpify as existing corpus exists, run --force to remove it")
            return
        shutil.rmtree(corpus_path)
    
    # Create the corpus directory
    os.makedirs(corpus_path)
    
    # Get chunk size from options, default to 1MB (1024*1024 bytes)
    chunk_size = options.get('chunk_size', 1024 * 1024)
    
    # Initialize variables for corpus file creation
    file_counter = 1
    current_file = os.path.join(corpus_path, f"{file_counter}.txt")
    current_size = 0
    
    # Open the first corpus file
    with open(current_file, 'w', encoding='utf-8') as f:
        # Recursively traverse the content directory
        for root, _, files in os.walk(content_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Attempt to read the file as UTF-8 text
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                except UnicodeDecodeError:
                    # Skip non-text or non-UTF-8 files
                    print(f"Skipping non-UTF-8 file: {file_path}")
                    continue

                # Process the content string
                while content:
                    if current_size >= chunk_size:
                        # Current file is full; close it and start a new one
                        f.close()
                        file_counter += 1
                        current_file = os.path.join(corpus_path, f"{file_counter}.txt")
                        f = open(current_file, 'w', encoding='utf-8')
                        current_size = 0
                    
                    # Calculate remaining bytes in the current chunk
                    remaining = chunk_size - current_size
                    # Find how much content can be written without exceeding chunk_size
                    k = find_split(content, remaining)
                    
                    if k == 0:
                        if current_size == 0:
                            # Rare case: a single character exceeds chunk_size
                            print(f"Warning: file {file_path} has a character larger than chunk size")
                            break
                        continue  # Move to next iteration to start a new file
                    
                    # Write the chunk and update state
                    to_write = content[:k]
                    f.write(to_write)
                    current_size += len(to_write.encode('utf-8'))
                    content = content[k:]

    print(f"Corpified arag {arag_path}")