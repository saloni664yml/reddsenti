import math
from financial_lexicon import score_financial_sentiment
from reddit_fetch import get_reddit_posts, get_post_comments, TICKER_ALIASES
from subreddit_mapper import get_subreddits
from relevance_scorer import score_comment_relevance
from concurrent.futures import ThreadPoolExecutor, as_completed
from reranker import rerank_comments
from query_parser import parse_query

def canonicalise_query(query):
    """
    Cleans and normalises a natural language query into a proper financial topic.
    Removes question framing, filler phrases and extracts the core financial subject.
    """
    query_lower = query.lower().strip()

    # Fix common misspellings first
    corrections = {
        "nvdia": "nvidia", "nividia": "nvidia", "nvida": "nvidia",
        "tesala": "tesla", "appl": "apple", "gooogle": "google",
        "amazn": "amazon", "bitconi": "bitcoin"
    }
    for wrong, right in corrections.items():
        query_lower = query_lower.replace(wrong, right)

    # Disambiguate common financial terms
    financial_context_fixes = {
        "portfolio without middleman": "self directed investing brokerage",
        "without a middleman": "self directed investing brokerage",
        "without middleman": "self directed investing brokerage",
        "without a broker": "self directed investing brokerage",
        "without financial advisor": "self directed investing",
        "by myself": "self directed investing",
        "on my own": "self directed investing",
    }

    for phrase, replacement in financial_context_fixes.items():
        if phrase in query_lower:
            query_lower = query_lower.replace(phrase, replacement)
            break

    # Remove question framing phrases
    question_frames = [
        "what do people think about", "what does reddit think about",
        "how is reddit reacting to", "how are people feeling about",
        "what do investors think about", "what is the sentiment on",
        "how do people feel about", "what does the community think about",
        "should i invest in", "should i buy", "is it worth buying",
        "is it a good time to buy", "what do people say about",
        "how is the market reacting to", "what is happening with",
        "tell me about", "what about", "how about",
        "what are people saying about", "what is reddit saying about",
        "is the us economy", "is the economy", "is there a",
        "is there going to be", "will there be a",
        "are we heading into", "is us heading into",
        "which stock should i invest in", "what stock should i invest in",
        "should i be worried about", "what do you think about",
        "how does reddit feel about", "what is going on with",
        "is it safe to invest in", "is now a good time to buy",
        "is it a good time to get into",
        "is it a good time to",
        "is now a good time to",
        "is this a good time to",
    ]
    for frame in question_frames:
        if query_lower.startswith(frame):
            query_lower = query_lower[len(frame):].strip()
            break

    # Extract topic after causal connectors
    for connector in ["because of", "because", "due to", "given that",
                      "as a result of", "since", "after", "following"]:
        if connector in query_lower:
            parts = query_lower.split(connector)
            if len(parts) > 1 and len(parts[1].strip()) > 5:
                query_lower = parts[1].strip()
            break

    # Remove trailing question marks and punctuation
    query_lower = query_lower.rstrip("?!.,")

    # Remove leading filler words
    filler_starts = ["the ", "a ", "an ", "this ", "these ", "those "]
    for filler in filler_starts:
        if query_lower.startswith(filler):
            query_lower = query_lower[len(filler):]
            break

    return query_lower.strip()


def extract_search_term(query):
    # First canonicalise the query
    query_lower = canonicalise_query(query)

    # Check ticker aliases on canonicalised query
    for ticker, aliases in TICKER_ALIASES.items():
        for alias in aliases:
            if alias in query_lower:
                return ticker

    # Strip remaining stop words
    stop_words = [
        "what", "do", "people", "think", "about", "how", "is", "will",
        "the", "are", "does", "feel", "regarding", "on", "a", "an",
        "in", "of", "to", "and", "or", "going", "should",
        "i", "reddit", "community", "everyone", "anybody",
        "which", "where", "when", "reacting", "feeling", "saying",
        "heading", "into", "onto", "towards", "toward", "get",
        "start", "starting", "begin", "beginning", "now", "currently",
        "time", "good", "right", "best", "today"
    ]
    words = query_lower.split()
    keywords = [w for w in words if w not in stop_words]
    return " ".join(keywords[:5])

def is_relevant_comment(body, search_term, post_title):
    body_lower = body.lower()
    post_lower = post_title.lower()
    search_lower = search_term.lower()

    keywords = [k for k in search_lower.split() if len(k) > 2]

    comment_mentions = any(kw in body_lower for kw in keywords)
    if comment_mentions:
        return True

    title_mentions = sum(1 for kw in keywords if kw in post_lower)
    title_is_relevant = title_mentions >= max(1, len(keywords) // 2)

    investing_signals = [
        "buy", "sell", "hold", "price", "market", "stock", "share",
        "invest", "profit", "loss", "gain", "risk", "bullish", "bearish",
        "valuation", "earnings", "revenue", "growth", "short", "long",
        "position", "portfolio", "trade", "rally", "dip", "crash",
        "support", "resistance", "target", "analyst", "forecast"
    ]

    has_investing_context = any(signal in body_lower for signal in investing_signals)
    is_substantive = len(body.split()) > 20

    if title_is_relevant and has_investing_context and is_substantive:
        return True

    return False

def analyze_query(query, num_posts=15, sort_by="top", time_filter="year"):
    # Use Phi-3 to extract structured intent from query
    print(f"Parsing query with Phi-3...")
    parsed = parse_query(query)
    print(f"Parsed: {parsed}")

    # Use AI-extracted search term if available, fallback to rule-based
    ai_search_term = parsed.get("search_term", "")
    canonical_query = canonicalise_query(query)

    # AI search term takes priority over rule-based
    if ai_search_term and len(ai_search_term) > 3:
        search_term = ai_search_term
        print(f"Using AI search term: '{search_term}'")
    else:
        search_term = extract_search_term(query)
        print(f"Using rule-based search term: '{search_term}'")

    all_subreddits = get_subreddits(canonical_query)
    # Try up to 5 subreddits, keep top 3 by results
    subreddits = all_subreddits[:5]
    print(f"Search term: '{search_term}'")
    print(f"Searching subreddits: {subreddits}")
    print(f"Sort: {sort_by} | Time: {time_filter} | Posts: {num_posts}")

    results = {}

    def fetch_subreddit(subreddit):
        print(f"Fetching r/{subreddit}...")
        posts = get_reddit_posts(subreddit, search_term, limit=num_posts, sort_by=sort_by, time_filter=time_filter)
        if not posts:
            return subreddit, None

        raw_comments = []
        for post in posts:
            comments = get_post_comments(post["url"])
            for c in comments:
                c["post_title"] = post["title"]
                c["post_score"] = post["score"]
                raw_comments.append(c)

        if not raw_comments:
            return subreddit, None

        # Semantic reranking — finds comments that actually answer the query
        print(f"  Reranking {len(raw_comments)} comments for r/{subreddit}...")
        all_comments = rerank_comments(query, raw_comments, top_n=35)

        # Fallback if reranker returns too few
        if len(all_comments) < 10:
            print(f"Reranker returned too few — falling back to TF-IDF for '{search_term}'")
            all_comments = score_comment_relevance(raw_comments, search_term, threshold=0.03)

        # Final fallback — investing context filter
        if len(all_comments) < 10:
            print(f"TF-IDF too strict — using investing context filter")
            all_comments = []
            for c in raw_comments:
                body_lower = c["body"].lower()
                investing_signals = [
                    "buy", "sell", "hold", "price", "market", "stock",
                    "invest", "profit", "loss", "gain", "risk", "trade"
                ]
                has_context = any(s in body_lower for s in investing_signals)
                is_substantive = len(c["body"].split()) > 15
                if has_context and is_substantive:
                    all_comments.append(c)

        if not all_comments:
            return subreddit, None

        weighted_scores = []
        total_weight = 0
        for c in all_comments:
            sentiment = score_financial_sentiment(c["body"])
            # Reduced upvote influence — square root instead of log
            # This means a comment with 10000 upvotes is only 10x more weighted
            # than one with 100 upvotes, not 100x
            # Prevents viral meme comments dominating analytical ones
            weight = math.sqrt(max(c["score"], 1))
            weighted_scores.append(sentiment["compound"] * weight)
            total_weight += weight

        weighted_avg = sum(weighted_scores) / total_weight if total_weight > 0 else 0
        seen_posts = {}
        for c in sorted(all_comments, key=lambda x: x["score"], reverse=True):
            post_title = c.get("post_title", "unknown")
            if post_title not in seen_posts:
                seen_posts[post_title] = c
            if len(seen_posts) >= 3:
                break

        top_comments = list(seen_posts.values())

        return subreddit, {
            "weighted_sentiment": round(weighted_avg, 3),
            "verdict": (
                "Strongly Bullish" if weighted_avg > 0.35 else
                "Bullish" if weighted_avg > 0.15 else
                "Slightly Bullish" if weighted_avg > 0.05 else
                "Strongly Bearish" if weighted_avg < -0.35 else
                "Bearish" if weighted_avg < -0.15 else
                "Slightly Bearish" if weighted_avg < -0.05 else
                "Neutral"
            ),
            "total_comments": len(all_comments),
            "top_comments": top_comments,
            "all_comments": all_comments,
            "search_term": search_term,
            "query_intent": parsed.get("intent", "sentiment_check"),
            "phi3_entity": parsed.get("entity", "")
        }

# Fetch all subreddits in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_subreddit, sub): sub for sub in subreddits}
        for future in as_completed(futures):
            subreddit, data = future.result()
            if data is not None:
                results[subreddit] = data

    # Keep only top 3 subreddits by comment count
    if len(results) > 3:
        results = dict(sorted(
            results.items(),
            key=lambda x: x[1]["total_comments"],
            reverse=True
        )[:3])

    return results


if __name__ == "__main__":
    query = "should I invest in nvidia stock"
    print(f"Analysing: '{query}'\n")
    results = analyze_query(query)

    for subreddit, data in results.items():
        print(f"r/{subreddit}:")
        print(f"  Verdict: {data['verdict']} ({data['weighted_sentiment']})")
        print(f"  Based on {data['total_comments']} comments")
        print(f"  Top comment: {data['top_comments'][0]['body'][:100]}")
        print()