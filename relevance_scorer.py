from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def score_comment_relevance(comments, query, threshold=0.05):
    """
    Scores each comment by how relevant it is to the query using TF-IDF.
    Returns comments above the relevance threshold, sorted by relevance score.

    This replaces keyword matching with proper statistical relevance scoring.
    A comment about "AI data centres" will score near zero for a gold query.
    A comment about "import duty on gold" will score high.
    """
    if not comments:
        return []

    # Extract comment bodies
    bodies = [c["body"] for c in comments]

    # Add query as first document so TF-IDF learns query vocabulary
    all_docs = [query] + bodies

    try:
        # Build TF-IDF matrix
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2)  # unigrams and bigrams
        )
        tfidf_matrix = vectorizer.fit_transform(all_docs)

        # Query vector is first row
        query_vector = tfidf_matrix[0]

        # Comment vectors are remaining rows
        comment_vectors = tfidf_matrix[1:]

        # Compute cosine similarity between query and each comment
        similarities = cosine_similarity(query_vector, comment_vectors)[0]

        # Attach scores to comments
        scored = []
        for i, comment in enumerate(comments):
            scored.append({
                **comment,
                "relevance_score": float(similarities[i])
            })

        # Filter by threshold — keep only relevant comments
        relevant = [c for c in scored if c["relevance_score"] >= threshold]

        # Sort by combined score — relevance * log(upvotes)
        # This balances topic relevance with community endorsement
        import math
        for c in relevant:
            weight = math.log(max(c["score"], 1) + 1)
            c["combined_score"] = c["relevance_score"] * weight

        relevant.sort(key=lambda x: x["combined_score"], reverse=True)

        return relevant

    except Exception as e:
        print(f"TF-IDF scoring error: {e}")
        return comments  # fallback to original if error


def filter_news_by_relevance(articles, query, threshold=0.08):
    """
    Filters news articles by relevance to the query using TF-IDF.
    Removes articles that are only loosely related.
    """
    if not articles:
        return []

    headlines = [a["headline"] for a in articles]
    all_docs = [query] + headlines

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=1000,
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        query_vector = tfidf_matrix[0]
        headline_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(query_vector, headline_vectors)[0]

        relevant_articles = []
        for i, article in enumerate(articles):
            if similarities[i] >= threshold:
                relevant_articles.append({
                    **article,
                    "relevance_score": float(similarities[i])
                })

        # Sort by relevance
        relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)

        # If nothing passes threshold return top 3 by score anyway
        if not relevant_articles:
            scored = [{**a, "relevance_score": float(similarities[i])}
                      for i, a in enumerate(articles)]
            scored.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored[:3]

        return relevant_articles

    except Exception as e:
        print(f"News TF-IDF error: {e}")
        return articles


if __name__ == "__main__":
    # Test with mock data
    test_comments = [
        {"body": "Gold import duty increase will hurt jewellery stocks in India", "score": 500},
        {"body": "NVDA AI data centre demand is accelerating fast", "score": 400},
        {"body": "The government never thinks about the middle class tax burden", "score": 300},
        {"body": "Gold ETFs are a good way to invest given the import duty hike", "score": 200},
        {"body": "I bought some tech stocks today", "score": 100},
        {"body": "India gold import duty will impact domestic gold prices significantly", "score": 800},
    ]

    query = "gold import tax increase india investment"
    results = score_comment_relevance(test_comments, query)

    print("RANKED BY RELEVANCE:")
    for c in results:
        print(f"  Score: {c['relevance_score']:.3f} | {c['body'][:80]}")

    print("\nNEWS FILTER TEST:")
    test_articles = [
        {"headline": "India doubles gold import duty to 15 percent", "sentiment": 0.0},
        {"headline": "AI data centre demand accelerating says Nvidia", "sentiment": 0.5},
        {"headline": "Gold ETFs rally after India raises import tax", "sentiment": 0.3},
        {"headline": "Economic management war discussion", "sentiment": -0.2},
    ]

    filtered = filter_news_by_relevance(test_articles, query)
    print("RELEVANT NEWS:")
    for a in filtered:
        print(f"  Score: {a['relevance_score']:.3f} | {a['headline']}")