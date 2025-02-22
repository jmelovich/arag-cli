import sqlite3
import json
import os
import numpy as np
from .index import generateEmbedding

def query(arag_path, query_string, topk=1):
    index_json_path = os.path.join(arag_path, 'index.json')
    if not os.path.exists(index_json_path):
        print("Index not found. Run 'arag index' first.")
        return
    with open(index_json_path, 'r') as f:
        metadata = json.load(f)
    method = metadata['method']
    model = metadata['model']
    options = {'method': method, 'model': model}
    if method == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
            return
        options['api_key'] = api_key
    try:
        query_embedding = generateEmbedding(query_string, options)
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return
    corpus_db_path = os.path.join(arag_path, 'corpus.db')
    if not os.path.exists(corpus_db_path):
        print("Corpus database not found. Run 'arag corpify' first.")
        return
    conn = sqlite3.connect(corpus_db_path)
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