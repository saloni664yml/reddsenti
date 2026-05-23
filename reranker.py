from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

# Load models once at module level so they're not reloaded on every query
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

print("Loading reranker model...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

print("Models loaded.")


def rerank_comments(query, comments, top_n=35):
    """
    Takes a pool of candidate comments and reranks them by
    how relevant they are to the user's actual question.

    Uses a cross-encoder which scores each (query, comment) pair directly.
    Much more accurate than TF-IDF keyword matching.

    Returns top_n most relevant comments.
    """
    if not comments:
        return []

    if len(comments) <= top_n:
        return comments

    # Prepare (query, comment) pairs for cross-encoder
    pairs = [(query, c["body"][:512]) for c in comments]

    # Score each pair — higher = more relevant
    scores = reranker.predict(pairs)

    # Attach scores to comments
    for i, c in enumerate(comments):
        c["rerank_score"] = float(scores[i])

    # Sort by rerank score descending
    ranked = sorted(comments, key=lambda x: x["rerank_score"], reverse=True)

    return ranked[:top_n]


def embed_query(query):
    """
    Converts a query string into a semantic embedding vector.
    Used for similarity-based retrieval if needed.
    """
    return embedding_model.encode(query, convert_to_numpy=True)


def semantic_similarity(query, text):
    """
    Returns cosine similarity between query and text embeddings.
    Score between 0 and 1 — higher means more semantically similar.
    """
    query_emb = embedding_model.encode(query, convert_to_numpy=True)
    text_emb = embedding_model.encode(text, convert_to_numpy=True)

    # Cosine similarity
    similarity = np.dot(query_emb, text_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(text_emb)
    )
    return float(similarity)


if __name__ == "__main__":
    test_query = "should I invest in NVDA stock"

    test_comments = [
        {"body": "NVDA is a strong buy right now, AI demand is accelerating and data centre spending is not slowing",
         "score": 500},
        {"body": "I bought NVDA back in 2020 and held through all the dips, best decision I made", "score": 400},
        {"body": "Congrats on closing your trade, the hardest part is knowing when to take profits", "score": 2400},
        {"body": "Lol google bought 15 percent of anthropic for 3 billion, now worth 150 billion", "score": 1600},
        {"body": "NVDA tanked during liberation day and I was down to basically nothing on my options", "score": 800},
        {"body": "The nvidia 10-1 stock split in June 2024 changed the accessibility of the stock dramatically",
         "score": 300},
        {"body": "China export restrictions are a real long term risk for NVDA revenue growth", "score": 250},
        {"body": "Amazon is a hyperscaler with a relatively small retail business on the side", "score": 1800},
    ]

    print(f"Query: '{test_query}'")
    print(f"Input: {len(test_comments)} comments")
    print()

    ranked = rerank_comments(test_query, test_comments, top_n=5)

    print("TOP 5 MOST RELEVANT:")
    for i, c in enumerate(ranked):
        print(f"  {i + 1}. Score: {c['rerank_score']:.3f} | {c['body'][:80]}")