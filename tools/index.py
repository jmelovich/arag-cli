import sqlite3
import json
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

import globals

def generateEmbedding(content, options):
    """
    Generate an embedding for the given content based on the specified method in options.

    Args:
        content (str): The text content to embed.
        options (dict): Configuration options including:
            - 'method' (str): 'openai' for OpenAI API or 'local' for local model (default: 'local').
            - 'model' (str): Model name (default: 'all-MiniLM-L6-v2' for local, 'text-embedding-ada-002' for OpenAI).
            - 'api_key' (str, optional): OpenAI API key if using 'openai' method.

    Returns:
        list: The embedding vector as a list of floats.

    Raises:
        ImportError: If required libraries are not installed.
        ValueError: If method is unsupported or API key is missing for OpenAI.
    """
    method = options.get('method', 'local')
    model_name = options.get('model')
    if not model_name:
        model_name = globals.DEFAULT_LOCAL_EMBEDDING_MODEL if method == 'local' else globals.DEFAULT_OPENAI_EMBEDDING_MODEL

    if method == 'openai':
        if OpenAI is None:
            raise ImportError("openai library is not installed. Install it with 'pip install openai'")
        api_key = options.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Provide it in options['api_key'] or set OPENAI_API_KEY environment variable.")
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=content, model=model_name)
        embedding = response.data[0].embedding
    elif method == 'local':
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers library is not installed. Install it with 'pip install sentence-transformers'")
        model = SentenceTransformer(model_name)
        embedding = model.encode(content).tolist()
    else:
        raise ValueError(f"Unsupported method: {method}. Use 'openai' or 'local'.")

    return embedding

def index(arag_path, options):
    """
    Index the corpus by generating embeddings for each row in corpus.db and save metadata.

    Args:
        arag_path (str): Path to the .arag directory.
        options (dict): Configuration options for embedding generation (passed to generateEmbedding).

    Notes:
        - Adds an 'embedding' column to the 'chunks' table if it doesn't exist.
        - Processes only rows where 'embedding' is NULL or empty.
        - Saves metadata to 'index.json' in the .arag directory.
    """
    corpus_db_path = os.path.join(arag_path, 'corpus.db')
    if not os.path.exists(corpus_db_path):
        print("Corpus database does not exist. Run 'arag corpify' first.")
        return

    # Connect to the SQLite database
    conn = sqlite3.connect(corpus_db_path)
    cursor = conn.cursor()

    # Check if 'embedding' column exists; add it if not
    cursor.execute("PRAGMA table_info(chunks)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'embedding' not in columns:
        cursor.execute("ALTER TABLE chunks ADD COLUMN embedding TEXT")

    # Retrieve rows needing embeddings
    cursor.execute("SELECT id, content FROM chunks WHERE embedding IS NULL OR embedding = ''")
    rows = cursor.fetchall()

    # Process each row
    for row in rows:
        id, content = row
        try:
            embedding = generateEmbedding(content, options)
            embedding_json = json.dumps(embedding)
            cursor.execute("UPDATE chunks SET embedding = ? WHERE id = ?", (embedding_json, id))
        except Exception as e:
            print(f"Error generating embedding for id {id}: {e}")

    conn.commit()

    # Collect metadata
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL AND embedding != ''")
    total_embeddings = cursor.fetchone()[0]

    # Get vector size from a sample embedding (assuming all embeddings have the same size)
    cursor.execute("SELECT embedding FROM chunks WHERE embedding IS NOT NULL AND embedding != '' LIMIT 1")
    sample_embedding = cursor.fetchone()
    vector_size = len(json.loads(sample_embedding[0])) if sample_embedding else 0

    method = options.get('method', 'local')

    model_name = options.get('model')
    if not model_name:
        model_name = globals.DEFAULT_LOCAL_EMBEDDING_MODEL if method == 'local' else globals.DEFAULT_OPENAI_EMBEDDING_MODEL

    metadata = {
        'method': method,
        'model': model_name,
        'vector_size': vector_size,
        'total_embeddings': total_embeddings
    }

    # Save metadata to index.json
    index_json_path = os.path.join(arag_path, globals.INDEX_JSON)
    with open(index_json_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    conn.close()
    print(f"Indexed {total_embeddings} embeddings in arag {arag_path}")