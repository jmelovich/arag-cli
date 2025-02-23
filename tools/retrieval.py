import apsw
import os
import json
import numpy as np
from .index import generateEmbedding
from .helpers import get_file_from_arag, is_packaged
from .vfs import zip_vfs  # Import the registered ZipVFS instance

def query(arag_path, query_string, topk=1, api_key=None, get_file=False):
    """
    Query the corpus database with a string, returning the top-k results.
    Accesses corpus.db directly from the archive if packaged.
    """
    # Load metadata
    metadata_str = get_file_from_arag(arag_path, 'index.json')
    if metadata_str is None:
        print(f"Index file index.json not found in arag {arag_path}")
        return
    metadata = json.loads(metadata_str)
    method = metadata['method']
    model = metadata['model']
    options = {'method': method, 'model': model}
    if method == 'openai':
        effective_api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not effective_api_key:
            print("OpenAI API key is required for 'openai' method. Provide --api-key or set OPENAI_API_KEY environment variable.")
            return
        options['api_key'] = effective_api_key

    # Generate query embedding
    try:
        query_embedding = generateEmbedding(query_string, options)
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return

    # Determine the connection URI
    arag_path_abs = os.path.abspath(arag_path)
    if is_packaged(arag_path_abs):
        # URI for packaged .arag, accessing corpus.db inside the archive
        uri = f"file:corpus.db?archive={arag_path_abs}&vfs=zipvfs"
    else:
        # URI for directory .arag, accessing corpus.db as a regular file
        db_path = os.path.join(arag_path_abs, 'corpus.db')
        uri = f"file:{db_path}?vfs=zipvfs"

    # Connect to the database and query
    try:
        conn = apsw.Connection(
            uri,
            flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, embedding FROM chunks WHERE embedding IS NOT NULL AND embedding != ''")
        rows = cursor.fetchall()
        if not rows:
            print("No embeddings found in the corpus.")
            conn.close()
            return

        # Process embeddings and compute similarities
        ids = []
        embeddings = []
        for row in rows:
            ids.append(row[0])
            embedding = json.loads(row[1])
            embeddings.append(embedding)
        embeddings = np.array(embeddings)
        query_embedding = np.array(query_embedding)
        similarities = np.dot(embeddings, query_embedding)
        topk_indices = np.argsort(similarities)[-topk:][::-1]
        topk_ids = [ids[i] for i in topk_indices]

        # Fetch top-k results
        placeholders = ','.join('?' * len(topk_ids))
        cursor.execute(f"SELECT id, file_path, content FROM chunks WHERE id IN ({placeholders})", topk_ids)
        results = cursor.fetchall()
        results_dict = {row[0]: (row[1], row[2]) for row in results}

        # Display results
        if get_file:
            for id in topk_ids:
                file_path, _ = results_dict[id]
                print(file_path)
        else:
            for id in topk_ids:
                file_path, content = results_dict[id]
                print(f"File: {file_path}")
                print(f"Content: {content}")
                print("---")

        conn.close()
    except Exception as e:
        print(f"Error querying the corpus: {e}")