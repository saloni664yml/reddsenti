from collections import Counter
import math
import re
STOP_WORDS = set([
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "this", "that", "these",
    "those", "i", "you", "he", "she", "we", "they", "it", "my",
    "your", "his", "her", "our", "its", "just", "also", "not",
    "like", "more", "very", "so", "if", "as", "by", "from", "get",
    "got", "going", "think", "know", "want", "need", "really", "even",
    "what", "who", "when", "where", "how", "why", "which", "there",
    "their", "they", "them", "than", "then", "now", "here", "about",
    "some", "any", "all", "each", "both", "few", "most", "other",
    "into", "through", "during", "before", "after", "above", "up",
    "down", "out", "off", "over", "under", "again", "once", "same",
    "can", "make", "made", "take", "taken", "come", "came", "said",
    "good", "well", "back", "still", "too", "much", "only", "own",
    "new", "first", "last", "right", "big", "high", "low", "next",
    "old", "large", "great", "things", "thing", "something", "anything",
    "everything", "nothing", "people", "way", "time", "year", "money",
    "closed", "cannot", "unless", "without", "because", "although", "however",
    "therefore", "whereas", "whether", "neither", "either", "perhaps",
    "maybe", "actually", "basically", "literally", "simply", "just"
])

def get_theme_context(comments, theme_keywords, search_term, max_words=4):
    stop_words = STOP_WORDS
    search_words = set(search_term.lower().split())
    relevant_words = Counter()
    for c in comments:
        body_lower = c["body"].lower()
        if any(kw in body_lower for kw in theme_keywords):
            words = body_lower.split()
            for word in words:
                word = word.strip(".,!?;:\"'()")
                if (len(word) > 3 and
                    word not in stop_words and
                    word not in search_words and
                    word not in theme_keywords and
                    word.isalpha()):
                    relevant_words[word] += 1
    if not relevant_words:
        return "mentioned in community discussions"
    top_words = [w for w, _ in relevant_words.most_common(max_words)]
    return f"discussed alongside: {', '.join(top_words)}"

def has_investment_thesis(text):
    """
    Returns True if comment contains an actual investment argument.
    Filters out memes, politics, generic reactions.
    """
    text_lower = text.lower()

    # Must have minimum length
    if len(text.split()) < 12:
        return False

    # Must contain at least one investment signal
    investment_signals = [
        "buy", "sell", "hold", "invest", "bullish", "bearish",
        "price", "valuation", "earnings", "revenue", "growth",
        "demand", "supply", "rate", "inflation", "market cap",
        "pe ratio", "dividend", "yield", "return", "profit",
        "loss", "risk", "opportunity", "upside", "downside",
        "support", "resistance", "target", "forecast", "outlook",
        "long", "short", "position", "portfolio", "allocation",
        "diversify", "hedge", "exposure", "sector", "trend",
        "momentum", "fundamental", "technical", "analysis",
        "gold", "silver", "bitcoin", "crypto", "stock", "bond",
        "etf", "fund", "index", "commodity", "currency"
    ]

    has_signal = any(signal in text_lower for signal in investment_signals)
    if not has_signal:
        return False

    # Reject if dominated by politics/drama with no finance
    noise_signals = [
        "trump rape", "elon ketamine", "wtf is", "lol",
        "this is fine", "clown", "circus", "rant"
    ]

    is_noise = any(noise in text_lower for noise in noise_signals)
    if is_noise:
        return False

    return True

def extract_dynamic_thesis(comments, direction="bull"):
    """
    Uses Phi-3 to extract clean investment thesis points from comments.
    Much better than bigram extraction — actually understands the argument.
    """
    import ollama
    from financial_lexicon import score_financial_sentiment

    loss_signals = [
        "lost", "down to", "dropped to", "tanked", "wiped out",
        "margin call", "lost my", "down big", "lost all", "blew up", "rekt"
    ]

    gain_signals = [
        "profit", "gain", "bullish", "strong", "growth",
        "demand", "buy", "invest", "hold", "long term"
    ]

    # Filter to relevant sentiment direction
    relevant_comments = []
    for c in comments:
        sentiment = score_financial_sentiment(c["body"])
        compound = sentiment["compound"]
        if direction == "bull" and compound <= 0.05:
            continue
        if direction == "bear" and compound >= -0.05:
            continue
        if direction == "bull":
            body_lower = c["body"].lower()
            if any(signal in body_lower for signal in loss_signals):
                continue
        relevant_comments.append({
            "body": c["body"],
            "score": c["score"],
            "sentiment": compound
        })

    if not relevant_comments:
        return ["positive community sentiment" if direction == "bull" else "general market caution"]

    # Sort by score and take top 3
    top_comments = sorted(relevant_comments, key=lambda x: x["score"], reverse=True)[:3]

    # Format comments for Phi-3
    comments_text = "\n\n".join([
        f"Comment {i + 1} ({c['score']} upvotes): {c['body'][:300]}"
        for i, c in enumerate(top_comments)
    ])

    direction_word = "bullish/positive" if direction == "bull" else "bearish/negative"

    prompt = f"""You are a financial analyst. Extract the main investment arguments from these Reddit comments.

These are {direction_word} comments about a financial asset.

{comments_text}

List the 2-3 main investment arguments being made. Be specific and concise.
Respond ONLY with a JSON array of strings, no other text:
["argument 1", "argument 2", "argument 3"]

Each argument should be 5-10 words, specific to what was actually said."""

    try:
        print(f"Calling Phi-3 for {direction} thesis with {len(top_comments)} comments...")
        response = ollama.chat(
            model="phi3",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        content = response["message"]["content"].strip()
        print(f"Phi-3 {direction} thesis response: {content[:200]}")

        # Clean markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        import json
        thesis_points = json.loads(content)

        # Ensure it's a list of strings
        if isinstance(thesis_points, list):
            return [str(p) for p in thesis_points[:3]]
        else:
            raise ValueError("Not a list")

    except Exception as e:
        print(f"Phi-3 thesis error: {e}")
        # Fallback to simple extraction
        if relevant_comments:
            top = sorted(relevant_comments, key=lambda x: x["score"], reverse=True)[0]
            snippet = top["body"][:100].strip()
            return [snippet]
        return ["positive community sentiment" if direction == "bull" else "general market caution"]

def extract_thesis(comments, search_term, direction="bull"):
    """
    Wrapper that uses dynamic extraction.
    Kept for backwards compatibility with app.py imports.
    """
    return extract_dynamic_thesis(comments, direction)

def extract_themes(comments, search_term):
    from financial_lexicon import score_financial_sentiment

    theme_groups = {
        "AI & Technology": ["ai", "artificial intelligence", "machine learning",
                            "gpu", "chip", "data center", "cloud", "compute", "tech"],
        "Earnings & Revenue": ["earnings", "revenue", "profit", "eps", "guidance",
                               "beat", "miss", "quarter", "results", "sales"],
        "Valuation": ["overvalued", "undervalued", "valuation", "pe ratio",
                      "expensive", "cheap", "fair value", "bubble", "price target"],
        "Competition": ["amd", "intel", "competition", "competitor", "market share",
                        "rival", "versus", "alternative"],
        "China & Geopolitics": ["china", "export", "ban", "restriction", "geopolit",
                                "taiwan", "trade war", "tariff", "sanction", "rare earth"],
        "Growth": ["growth", "expand", "demand", "future", "potential",
                   "opportunity", "upside", "long term", "secular"],
        "Risk": ["risk", "concern", "worry", "danger", "volatile",
                 "uncertainty", "caution", "careful", "hedge"],
        "Market Sentiment": ["bullish", "bearish", "buy", "sell", "hold",
                             "dip", "rally", "moon", "crash", "momentum"],
        "Gold & Commodities": ["gold", "silver", "commodity", "import duty",
                               "jewellery", "bullion", "sgb", "mcx", "precious"],
        "India Policy": ["rbi", "sebi", "budget", "import duty", "customs",
                         "government", "modi", "rupee", "policy", "regulation"],
        "Crypto & Digital Assets": ["bitcoin", "crypto", "ethereum", "blockchain",
                                    "defi", "web3", "altcoin", "token"],
        "Real Estate": ["real estate", "property", "housing", "mortgage",
                        "reit", "rent", "landlord", "realty"],
        "Interest Rates & Macro": ["rate", "inflation", "fed", "rbi", "central bank",
                                   "gdp", "recession", "macro", "monetary", "fiscal"]
    }

    search_keywords = [k for k in search_term.lower().split() if len(k) > 2]

    loss_signals = [
        "lost", "down to", "dropped to", "tanked", "lost almost",
        "wiped out", "margin call", "lost my", "down big",
        "lost all", "blew up", "rekt"
    ]

    gain_signals = [
        "profit", "gain", "bullish", "strong", "growth",
        "demand", "buy", "invest", "hold", "long term"
    ]

    scored_comments = []
    for c in comments:
        body_lower = c["body"].lower()
        sentiment = score_financial_sentiment(c["body"])
        directly_mentions = any(kw in body_lower for kw in search_keywords)
        relevance_multiplier = 3 if directly_mentions else 1
        # Square root weighting — reduces viral comment dominance
        effective_score = math.sqrt(max(c["score"], 1)) * relevance_multiplier
        scored_comments.append({
            "body": c["body"],
            "score": c["score"],
            "effective_score": effective_score,
            "sentiment": sentiment["compound"],
            "directly_mentions": directly_mentions
        })

    def is_genuine_bull(comment):
        body = comment["body"].lower()
        if any(signal in body for signal in loss_signals):
            return False
        return True

    def is_genuine_bear(comment):
        body = comment["body"].lower()
        positive_count = sum(1 for s in gain_signals if s in body)
        loss_count = sum(1 for s in loss_signals if s in body)
        return loss_count >= positive_count

    bull_comments = sorted(
        [c for c in scored_comments if c["sentiment"] > 0.05 and is_genuine_bull(c)],
        key=lambda x: (x["directly_mentions"], x["score"]),
        reverse=True
    )
    bear_comments = sorted(
        [c for c in scored_comments if c["sentiment"] < -0.05 and is_genuine_bear(c)],
        key=lambda x: (x["directly_mentions"], x["score"]),
        reverse=True
    )

    # Score themes by weighted comment relevance
    theme_counts = {}
    for theme, keywords in theme_groups.items():
        count = 0
        for c in scored_comments:
            body_lower = c["body"].lower()
            if any(kw in body_lower for kw in keywords):
                count += c["effective_score"] + 1
        if count > 0:
            theme_counts[theme] = count

        # Only include themes with meaningful presence
        # Prevents weak themes from surfacing (e.g. "Real Estate" from 2 stray comments)
        min_theme_score = max(theme_counts.values()) * 0.15 if theme_counts else 0

        filtered_themes = {
            theme: score for theme, score in theme_counts.items()
            if score >= min_theme_score
        }

        sorted_themes = sorted(filtered_themes.items(), key=lambda x: x[1], reverse=True)
        top_themes = [t[0] for t in sorted_themes[:3]]
    # Generate dynamic context for each theme
    theme_context = {}
    for theme in top_themes:
        keywords = theme_groups[theme]
        theme_context[theme] = get_theme_context(comments, keywords, search_term)

    return {
        "top_themes": top_themes,
        "theme_context": theme_context,
        "bull_comments": bull_comments[:2],
        "bear_comments": bear_comments[:2],
        "bull_count": len(bull_comments),
        "bear_count": len(bear_comments),
        "neutral_count": len(scored_comments) - len(bull_comments) - len(bear_comments)
    }

def extract_recommendations(comments, search_term):
    from collections import Counter
    from financial_lexicon import score_financial_sentiment

    known_entities = {
        "voo": "VOO (Vanguard S&P 500 ETF)",
        "vti": "VTI (Vanguard Total Market ETF)",
        "spy": "SPY (S&P 500 ETF)",
        "qqq": "QQQ (Nasdaq 100 ETF)",
        "schb": "SCHB (Schwab Total Market ETF)",
        "vxus": "VXUS (Vanguard International ETF)",
        "bnd": "BND (Vanguard Bond ETF)",
        "vanguard": "Vanguard",
        "fidelity": "Fidelity",
        "fudelity": "Fidelity",
        "schwab": "Charles Schwab",
        "bogleheads": "Bogleheads approach",
        "bogle": "Bogleheads approach",
        "index fund": "Index funds",
        "target date": "Target date funds",
        "roth ira": "Roth IRA",
        "roth": "Roth IRA",
        "401k": "401k",
        "etf": "ETFs generally",
        "zerodha": "Zerodha",
        "groww": "Groww",
        "hdfc": "HDFC Bank",
        "sbi": "SBI",
        "icici": "ICICI Bank",
        "bitcoin": "Bitcoin (BTC)",
        "ethereum": "Ethereum (ETH)",
        "nvidia": "NVIDIA (NVDA)",
        "apple": "Apple (AAPL)",
        "interactive brokers": "Interactive Brokers",
        "commsec": "CommSec",
        "selfwealth": "SelfWealth",
        "stake": "Stake",
        "pearler": "Pearler",
        "asx": "ASX-listed ETFs",
        "betashares": "BetaShares",
        "cmc": "CMC Markets",
        "cmc markets": "CMC Markets",
        "superhero": "Superhero",
        "nabtrade": "nabtrade",
        "moomoo": "moomoo",
        "robinhood": "Robinhood",
        "webull": "Webull",
        "thinkorswim": "thinkorswim",
    }

    recommendation_scores = Counter()
    recommendation_context = {}

    for c in comments:
        sentiment = score_financial_sentiment(c["body"])
        if sentiment["compound"] < -0.2:
            continue

        weight = max(c["score"], 1)
        body_lower = c["body"].lower()

        for key, display_name in known_entities.items():
            if key in body_lower:
                recommendation_scores[display_name] += weight
                if display_name not in recommendation_context:
                    idx = body_lower.find(key)
                    start = max(0, idx - 30)
                    end = min(len(c["body"]), idx + 80)
                    recommendation_context[display_name] = c["body"][start:end].strip()

    if not recommendation_scores:
        return []

    min_threshold = 10
    filtered = {k: v for k, v in recommendation_scores.items() if v >= min_threshold}

    if not filtered:
        return []

    top = Counter(filtered).most_common(5)
    return [{"name": name, "mentions": score, "context": recommendation_context.get(name, "")}
            for name, score in top]

def generate_analysis(query, reddit_results, news_result):

    avg_reddit = sum(
        d["weighted_sentiment"] for d in reddit_results.values()
    ) / len(reddit_results)

    bullish_subs = [s for s, d in reddit_results.items() if "Bullish" in d["verdict"]]
    bearish_subs = [s for s, d in reddit_results.items() if "Bearish" in d["verdict"]]

    total_comments = sum(d["total_comments"] for d in reddit_results.values())
    total_subs = len(reddit_results)
    search_term = list(reddit_results.values())[0]["search_term"]

    all_comments = []
    for d in reddit_results.values():
        all_comments.extend(d["all_comments"])

    has_news = news_result is not None
    is_political = news_result.get("is_political_fallback", False) if has_news else False
    news_score = news_result["avg_sentiment"] if has_news else None
    divergence = round(abs(avg_reddit - news_score), 3) if has_news and not is_political else None

    query_lower = query.lower()
    query_intent = list(reddit_results.values())[0].get("query_intent", "sentiment_check")

    is_recommendation_query = (
        query_intent == "recommendation_request" or
        any(w in query_lower for w in [
            "which", "best", "recommend", "suggest", "top",
            "what mutual fund", "what etf", "what stock",
            "what crypto", "what index fund", "how to invest",
            "how do i start", "how to start", "without a middleman",
            "without middleman", "self directed"
        ])
    )
    # Use Phi-3 extracted entity for display if available
    phi3_entity = list(reddit_results.values())[0].get("phi3_entity", "")
    if phi3_entity and len(phi3_entity) > 2:
        display_topic = phi3_entity
    else:
        display_topic = query.rstrip("?!.,").strip()
        for frame in ["is now a good time to buy", "should i buy", "should i invest in",
                      "what does reddit think about", "is it a good time to buy",
                      "should i invest in", "should i"]:
            if display_topic.lower().startswith(frame):
                display_topic = display_topic[len(frame):].strip()
                break
        for suffix in [" right now", " now", " today", " currently"]:
            if display_topic.lower().endswith(suffix):
                display_topic = display_topic[:-len(suffix)].strip()
                break

    overall_direction = (
        "strongly bullish" if avg_reddit > 0.35 else
        "bullish" if avg_reddit > 0.15 else
        "slightly bullish" if avg_reddit > 0.05 else
        "strongly bearish" if avg_reddit < -0.35 else
        "bearish" if avg_reddit < -0.15 else
        "slightly bearish" if avg_reddit < -0.05 else
        "neutral"
    )

    bullish_count = len(bullish_subs)
    bearish_count = len(bearish_subs)
    query_lower_check = query.lower()

    wants_to_sell = any(w in query_lower_check for w in [
        "sell", "exit", "cash out", "take profit", "get out"
    ])
    wants_to_buy = any(w in query_lower_check for w in [
        "good time to buy", "time to buy", "should i buy",
        "worth buying", "buy now", "invest now", "should i invest"
    ])
    is_comparison = query_intent == "comparison"

    # ── SENTENCE 1 — Direct answer ──
    if wants_to_sell:
        if avg_reddit < -0.05:
            s1 = f"Reddit leans **yes, sell** — sentiment on {display_topic} is {overall_direction} ({bullish_count} of {total_subs} communities bearish across {total_comments} comments)."
        else:
            s1 = f"Reddit leans **hold, don't sell** — sentiment on {display_topic} remains {overall_direction} ({bullish_count} of {total_subs} communities still bullish across {total_comments} comments)."

    elif wants_to_buy:
        if avg_reddit > 0.05:
            s1 = f"Reddit leans **yes** on {display_topic} — {bullish_count} of {total_subs} communities are {overall_direction} across {total_comments} comments."
        elif avg_reddit < -0.05:
            s1 = f"Reddit leans **wait** on {display_topic} — sentiment is {overall_direction} across {total_comments} comments, with {bearish_count} of {total_subs} communities cautious."
        else:
            s1 = f"Reddit is **divided** on {display_topic} — no clear signal across {total_comments} comments from {total_subs} communities."

    elif is_comparison:
        if avg_reddit > 0.05:
            s1 = f"Reddit leans towards **buying** — sentiment on {display_topic} is {overall_direction} ({bullish_count} of {total_subs} communities positive across {total_comments} comments)."
        elif avg_reddit < -0.05:
            s1 = f"Reddit leans towards **renting/waiting** — sentiment on {display_topic} is {overall_direction} ({bearish_count} of {total_subs} communities cautious across {total_comments} comments)."
        else:
            s1 = f"Reddit is **divided** on {display_topic} — no clear consensus across {total_comments} comments from {total_subs} communities."

    else:
        if bullish_count == total_subs:
            s1 = f"Reddit is **{overall_direction}** on {display_topic} — all {total_subs} communities align across {total_comments} comments."
        elif bearish_count == total_subs:
            s1 = f"Reddit is **{overall_direction}** on {display_topic} — all {total_subs} communities are cautious across {total_comments} comments."
        elif bullish_count > bearish_count:
            s1 = f"Reddit leans **{overall_direction}** on {display_topic} — {bullish_count} of {total_subs} communities are positive across {total_comments} comments."
        elif bearish_count > bullish_count:
            s1 = f"Reddit leans **{overall_direction}** on {display_topic} — {bearish_count} of {total_subs} communities are cautious across {total_comments} comments."
        else:
            s1 = f"Reddit is **divided** on {display_topic} — no clear consensus across {total_comments} comments from {total_subs} communities."

    # ── SENTENCE 2 — News comparison ──
    if has_news and not is_political and news_score is not None:
        if divergence is not None and divergence > 0.2:
            if avg_reddit > news_score:
                s2 = f"Financial media is more cautious — news at {round(abs(news_score) * 100)}% vs Reddit's {round(abs(avg_reddit) * 100)}%, a gap worth watching."
            else:
                s2 = f"Financial media is more optimistic than Reddit — news at {round(abs(news_score) * 100)}% vs Reddit's {round(abs(avg_reddit) * 100)}%."
        elif divergence is not None:
            s2 = f"Financial media broadly agrees — news ({round(abs(news_score) * 100)}%) is close to Reddit's ({round(abs(avg_reddit) * 100)}%)."
        else:
            s2 = ""
    else:
        s2 = ""

    # ── SENTENCE 3 — Recommendations if applicable ──
    s3 = ""
    if is_recommendation_query:
        recommendations = extract_recommendations(all_comments, search_term)
        if recommendations:
            rec_names = ", ".join(f"**{r['name']}**" for r in recommendations[:4])
            s3 = f"Most mentioned by Reddit: {rec_names}."

    # ── DISCLAIMER ──
    disclaimer = "*Sentiment analysis based on Reddit communities. Not financial advice.*"
    disclaimer = "*Sentiment analysis based on Reddit communities. Not financial advice.*"

    sentences = [s for s in [s1, s2, s3] if s]
    verdict = " ".join(sentences)

    return verdict + "\n\n" + disclaimer

if __name__ == "__main__":
    mock_reddit = {
        "investing": {
            "weighted_sentiment": 0.359,
            "verdict": "Strongly Bullish",
            "total_comments": 25,
            "top_comments": [{"body": "NVDA is a strong hold long term", "score": 500}],
            "all_comments": [
                {"body": "NVDA AI demand is accelerating fast", "score": 400},
                {"body": "I sold my NVDA position too expensive now", "score": 200}
            ],
            "search_term": "NVDA"
        },
        "wallstreetbets": {
            "weighted_sentiment": -0.07,
            "verdict": "Slightly Bearish",
            "total_comments": 8,
            "top_comments": [{"body": "NVDA tanked during liberation day", "score": 820}],
            "all_comments": [
                {"body": "Lost everything on NVDA options", "score": 100},
                {"body": "NVDA to the moon still", "score": 50}
            ],
            "search_term": "NVDA"
        }
    }

    mock_news = {
        "avg_sentiment": 0.12,
        "verdict": "Positive",
        "source": "Finnhub",
        "is_political_fallback": False,
        "articles": [
            {"headline": "Nvidia Earnings on May 20 What History Tells Us", "sentiment": 0.0},
            {"headline": "Chinese Blockade Risks Put TSMC Central Chip Role Under Scrutiny",
             "sentiment": -0.3},
        ]
    }

    result = generate_analysis("should I invest in nvidia stock", mock_reddit, mock_news)
    print(result)

