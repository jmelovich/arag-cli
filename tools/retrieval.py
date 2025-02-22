import sqlite3
import json
import os
import numpy as np
from .index import generateEmbedding
from .helpers import get_file_from_arag, get_corpus_db_temp, is_packaged

def query(arag_path, query_string, topk=1, api_key=None):
    metadata_str = get_file_from_arag(arag_path, 'index.json')
    if metadata_str is None:
        print(f"Index file index.json not found in arag {arag_path}")
        return
    metadata = json.loads(metadata_str)
    method = metadata['method']
    model = metadata['model']
    options = {'method': method, 'model': model}
    if method == 'openai':
        # Use provided api_key if available, otherwise fall back to environment variable
        effective_api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not effective_api_key:
            print("OpenAI API key is required for 'openai' method. Provide --api-key or set OPENAI_API_KEY environment variable.")
            return
        options['api_key'] = effective_api_key
    try:
        query_embedding = generateEmbedding(query_string, options)
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return
    try:
        corpus_db_temp = get_corpus_db_temp(arag_path)
        conn = sqlite3.connect(corpus_db_temp)
        cursor = conn.cursor()
        cursor.execute("SELECT id, embedding FROM chunks WHERE embedding IS NOT NULL AND embedding != ''")
        rows = cursor.fetchall()
        if not rows:
            print("No embeddings found in the corpus.")
            conn.close()
            return
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
        placeholders = ','.join('?' * len(topk_ids))
        cursor.execute(f"SELECT id, file_path, content FROM chunks WHERE id IN ({placeholders})", topk_ids)
        results = cursor.fetchall()
        results_dict = {row[0]: (row[1], row[2]) for row in results}
        for id in topk_ids:
            file_path, content = results_dict[id]
            print(f"File: {file_path}")
            print(f"Content: {content}")
            print("---")
        conn.close()
    except KeyError:
        print(f"Corpus database corpus.db not found in arag {arag_path}")
        return
    finally:
        if is_packaged(arag_path) and 'corpus_db_temp' in locals():
            os.remove(corpus_db_temp)