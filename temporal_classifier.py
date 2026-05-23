import re
from collections import defaultdict


HISTORICAL_SIGNALS = [
    "was", "were", "had", "bought", "sold", "lost", "gained", "happened",
    "went", "fell", "rose", "crashed", "peaked", "did", "learned", "realized",
    "turned out", "ended up", "used to", "back then", "previously", "historically",
    "last year", "last month", "last week", "in 2020", "in 2021", "in 2022",
    "in 2023", "in 2024", "back in", "ago", "since then", "after the", "during the",
    "remember when", "back when", "at the time", "that time", "those days"
]

PRESENT_SIGNALS = [
    "is", "are", "currently", "right now", "today", "this week", "this month",
    "at the moment", "presently", "now", "still", "continues", "remains",
    "seeing", "showing", "trading", "sitting", "holding", "looks like",
    "seems", "appears", "think", "believe", "feel", "seems like"
]

FUTURE_SIGNALS = [
    "will", "going to", "expect", "predict", "forecast", "target", "could hit",
    "might reach", "should reach", "by end of", "next year", "next month",
    "next quarter", "in the future", "eventually", "long term", "potential",
    "upcoming", "soon", "anticipate", "project", "estimate", "outlook",
    "would", "if", "when it", "once it", "before it", "looking forward"
]


def classify_comment_time(comment_body):
    """
    Classifies a comment as historical, present or future oriented.
    Returns the dominant temporal orientation.
    """
    body_lower = comment_body.lower()

    historical_count = sum(1 for signal in HISTORICAL_SIGNALS if signal in body_lower)
    present_count = sum(1 for signal in PRESENT_SIGNALS if signal in body_lower)
    future_count = sum(1 for signal in FUTURE_SIGNALS if signal in body_lower)

    total = historical_count + present_count + future_count
    if total == 0:
        return "present"  # default

    # Determine dominant orientation
    if future_count > historical_count and future_count > present_count:
        return "future"
    elif historical_count > present_count and historical_count > future_count:
        return "historical"
    else:
        return "present"

def classify_comments_by_time(comments, search_term=""):
    """
    Splits comments into historical, present and future buckets.
    Filters for relevance to search term before bucketing.
    """
    buckets = defaultdict(list)

    search_keywords = [k for k in search_term.lower().split() if len(k) > 2]

    for c in comments:
        body = c["body"]

        # Skip URLs and very short comments
        if "https://" in body[:100] or "http://" in body[:100]:
            continue
        if len(body.split()) < 8:
            continue

        # Only include comments that mention search term
        # OR have high relevance score if available
        body_lower = body.lower()
        if search_keywords:
            mentions_topic = any(kw in body_lower for kw in search_keywords)
            has_relevance_score = "relevance_score" in c
            relevance_ok = (
                mentions_topic or
                (has_relevance_score and c["relevance_score"] > 0.05)
            )
            if not relevance_ok:
                continue

        orientation = classify_comment_time(body)
        buckets[orientation].append(c)

    # Sort each bucket by score
    for key in buckets:
        buckets[key].sort(key=lambda x: x["score"], reverse=True)

    historical = buckets.get("historical", [])
    present = buckets.get("present", [])
    future = buckets.get("future", [])

    return {
        "historical": {
            "comments": historical[:2],
            "count": len(historical),
            "label": "📜 Historical — what happened before",
            "description": "Past performance, lessons learned, what already occurred"
        },
        "present": {
            "comments": present[:2],
            "count": len(present),
            "label": "📍 Present — what's happening now",
            "description": "Current sentiment, right now positioning, today's view"
        },
        "future": {
            "comments": future[:2],
            "count": len(future),
            "label": "🔮 Future — what people expect",
            "description": "Predictions, forecasts, expectations, price targets"
        }
    }

if __name__ == "__main__":
    test_comments = [
        {"body": "I bought NVDA back in 2020 and it was the best decision I ever made", "score": 500},
        {"body": "NVDA is currently trading at all time highs and looks strong right now", "score": 300},
        {"body": "I think NVDA will hit $200 by end of next year with AI demand accelerating", "score": 400},
        {"body": "Last year when DeepSeek came out the stock crashed hard but recovered", "score": 200},
        {"body": "The upcoming earnings next week will determine if this rally continues", "score": 350},
        {"body": "China export restrictions are a real concern for long term holders", "score": 250},
    ]

    result = classify_comments_by_time(test_comments)

    for bucket, data in result.items():
        print(f"\n{data['label']} ({data['count']} comments)")
        for c in data["comments"]:
            print(f"  ↑{c['score']} | {c['body'][:80]}")