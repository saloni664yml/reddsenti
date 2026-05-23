import finnhub
import requests
from financial_lexicon import score_financial_sentiment
from datetime import datetime, timedelta
from config import FINNHUB_KEY, NEWSAPI_KEY, GUARDIAN_KEY
from reddit_fetch import TICKER_ALIASES
from relevance_scorer import filter_news_by_relevance

client = finnhub.Client(api_key=FINNHUB_KEY)

INDIA_KEYWORDS = ["india", "indian", "sensex", "nifty", "bse", "nse",
                  "rupee", "rbi", "sebi", "modi", "mumbai", "delhi",
                  "import tax", "custom duty", "zerodha", "groww"]

AUSTRALIA_KEYWORDS = ["australia", "australian", "asx", "aud", "rba",
                      "sydney", "melbourne", "superannuation", "asx200",
                      "commbank", "westpac", "anz", "macquarie"]

def is_relevant_headline(headline, search_term):
    headline_lower = headline.lower()
    keywords = [k for k in search_term.lower().split() if len(k) > 2]

    # Also check company name aliases
    alias_map = {
        "NVDA": ["nvidia", "nvda"],
        "TSLA": ["tesla", "tsla"],
        "AAPL": ["apple", "aapl"],
        "BTC": ["bitcoin", "btc"],
        "ETH": ["ethereum", "eth"]
    }

    extra_keywords = []
    for ticker, aliases in alias_map.items():
        if ticker in search_term.upper():
            extra_keywords.extend(aliases)

    all_keywords = keywords + extra_keywords
    return any(kw in headline_lower for kw in all_keywords)


def extract_keywords(query):
    stop_words = ["what", "do", "people", "think", "about", "how",
                  "is", "will", "the", "are", "does", "feel", "going",
                  "should", "i", "we", "they", "a", "an", "to", "and",
                  "or", "for", "of", "in", "on", "at", "with", "this",
                  "reddit", "community", "invest", "investing", "market",
                  "increase", "decrease", "crash", "happen", "happening"]

    finance_terms = ["tax", "tariff", "import", "export", "rate", "price",
                     "stock", "share", "fund", "gold", "oil", "crypto",
                     "inflation", "recession", "gdp", "trade", "economy"]

    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words]

    finance_first = [w for w in keywords if w in finance_terms]
    others = [w for w in keywords if w not in finance_terms]
    ordered = finance_first + others

    return ordered[:4]


def get_finnhub_news(ticker, month_ago, today):
    try:
        news = client.company_news(ticker, _from=month_ago, to=today)
        articles = []
        for article in news[:20]:  # fetch more, then filter
            headline = article.get("headline", "")
            url = article.get("url", "")

            if "finnhub.io/api/news" in url:
                url = ""

            # Only keep relevant headlines
            if headline and is_relevant_headline(headline, ticker):
                sentiment = score_financial_sentiment(headline)
                articles.append({
                    "headline": headline,
                    "sentiment": sentiment["compound"],
                    "source": article.get("source", ""),
                    "url": url,
                    "is_financial": True
                })

            if len(articles) >= 5:
                break

        return articles
    except Exception as e:
        print(f"Finnhub error: {e}")
        return []


def get_newsapi_news(query, month_ago, today):
    try:
        keywords = extract_keywords(query)
        search_term = " ".join(keywords[:4])
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={requests.utils.quote(search_term)}"
            f"&from={month_ago}"
            f"&to={today}"
            f"&sortBy=relevancy"
            f"&language=en"
            f"&pageSize=10"
            f"&apiKey={NEWSAPI_KEY}"
        )
        response = requests.get(url)
        data = response.json()
        articles = []
        if data.get("status") == "ok" and data.get("articles"):
            for article in data["articles"]:
                headline = article.get("title", "")
                if headline and headline != "[Removed]":
                    sentiment = score_financial_sentiment(headline)
                    articles.append({
                        "headline": headline,
                        "sentiment": sentiment["compound"],
                        "source": article.get("source", {}).get("name", ""),
                        "url": article.get("url", ""),
                        "is_financial": True
                    })
        return articles
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


def get_guardian_news(query, month_ago, today, section="business"):
    try:
        keywords = extract_keywords(query)
        search_term = " AND ".join(keywords[:3])
        url = (
            f"https://content.guardianapis.com/search"
            f"?q={requests.utils.quote(search_term)}"
            f"&from-date={month_ago}"
            f"&to-date={today}"
            f"&order-by=relevance"
            f"&section={section}"
            f"&show-fields=trailText"
            f"&page-size=10"
            f"&api-key={GUARDIAN_KEY}"
        )
        response = requests.get(url)
        data = response.json()
        articles = []
        if data["response"]["status"] == "ok" and data["response"]["total"] > 0:
            for result in data["response"]["results"]:
                headline = result.get("webTitle", "")
                if headline:
                    sentiment = score_financial_sentiment(headline)
                    articles.append({
                        "headline": headline,
                        "sentiment": sentiment["compound"],
                        "source": "The Guardian",
                        "url": result.get("webUrl", ""),
                        "is_financial": True
                    })
        return articles
    except Exception as e:
        print(f"Guardian error: {e}")
        return []

def get_political_context(query, month_ago, today):
    try:
        keywords = extract_keywords(query)
        search_term = " ".join(keywords[:3])
        url = (
            f"https://content.guardianapis.com/search"
            f"?q={requests.utils.quote(search_term)}"
            f"&from-date={month_ago}"
            f"&to-date={today}"
            f"&order-by=relevance"
            f"&show-fields=trailText"
            f"&page-size=5"
            f"&api-key={GUARDIAN_KEY}"
        )
        response = requests.get(url)
        data = response.json()
        articles = []
        if data["response"]["status"] == "ok" and data["response"]["total"] > 0:
            for result in data["response"]["results"]:
                headline = result.get("webTitle", "")
                if headline:
                    sentiment = score_financial_sentiment(headline)
                    articles.append({
                        "headline": headline,
                        "sentiment": sentiment["compound"],
                        "source": "The Guardian",
                        "url": result.get("webUrl", ""),
                        "is_financial": False
                    })
        return articles
    except Exception as e:
        print(f"Political context error: {e}")
        return []

def get_news_sentiment(query):
    today = datetime.today().strftime('%Y-%m-%d')
    month_ago = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')

    query_lower = query.lower()
    articles = []
    source_used = None
    is_political_fallback = False

    # Path 1 — match company name or ticker → Finnhub
    matched_ticker = None
    for ticker, aliases in TICKER_ALIASES.items():
        for alias in aliases:
            if alias in query_lower:
                matched_ticker = ticker
                break
        if matched_ticker:
            break

    INDIAN_TICKERS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO",
                      "TATAMOTORS", "ADANIENT", "BAJFINANCE"]

    if matched_ticker:
        if matched_ticker in INDIAN_TICKERS:
            articles = get_newsapi_news(query, month_ago, today)
            source_used = "NewsAPI"
        else:
            articles = get_finnhub_news(matched_ticker, month_ago, today)
            source_used = "Finnhub"

    # Path 2 — India query → NewsAPI
    elif any(kw in query_lower for kw in INDIA_KEYWORDS):
        articles = get_newsapi_news(query + " stock market economy finance", month_ago, today)
        source_used = "NewsAPI"

    # Path 3 — Australia query → NewsAPI
    elif any(kw in query_lower for kw in AUSTRALIA_KEYWORDS):
        articles = get_newsapi_news(query + " shares finance", month_ago, today)
        source_used = "NewsAPI"
        if not articles:
            articles = get_guardian_news("australia economy", month_ago, today, section="business")
            source_used = "Guardian"

    # Path 3b — Crypto query → NewsAPI
    elif any(kw in query_lower for kw in [
        "crypto", "bitcoin", "ethereum", "blockchain", "btc", "eth",
        "defi", "altcoin", "web3", "nft", "cryptocurrency"
    ]):
        articles = get_newsapi_news(query, month_ago, today)
        source_used = "NewsAPI"
        if not articles:
            articles = get_finnhub_news("BTC", month_ago, today)
            source_used = "Finnhub"

    # Path 3c — Personal finance query → NewsAPI
    elif any(kw in query_lower for kw in [
        "invest", "investing", "savings", "retirement", "etf",
        "index fund", "portfolio", "personal finance", "budget",
        "start investing", "beginner", "where to invest"
    ]):
        articles = get_newsapi_news(query + " investing personal finance", month_ago, today)
        source_used = "NewsAPI"

    # Path 3d — Commodity query → NewsAPI
    elif any(kw in query_lower for kw in [
        "gold", "silver", "oil", "copper", "platinum",
        "commodity", "commodities", "precious metal"
    ]):
        articles = get_newsapi_news(query + " investing price", month_ago, today)
        source_used = "NewsAPI"
        if not articles:
            articles = get_guardian_news(query, month_ago, today, section="business")
            source_used = "Guardian"

    # Path 3e — Defense/thematic stocks → NewsAPI
    elif any(kw in query_lower for kw in [
        "defense", "defence", "military", "aerospace", "nuclear",
        "uranium", "lockheed", "raytheon", "arms", "weapon"
    ]):
        articles = get_newsapi_news(query + " stocks investing", month_ago, today)
        source_used = "NewsAPI"

    # Path 3f — Emerging markets → NewsAPI
    elif any(kw in query_lower for kw in [
        "emerging market", "emerging markets", "vietnam", "indonesia",
        "brazil", "mexico", "brics", "frontier market"
    ]):
        articles = get_newsapi_news(query + " investing stocks", month_ago, today)
        source_used = "NewsAPI"

    # Path 3g — Interest rates & bonds → NewsAPI
    elif any(kw in query_lower for kw in [
        "interest rate", "rate cut", "rate hike", "bond", "treasury",
        "yield curve", "10 year", "fed rate", "monetary policy"
    ]):
        articles = get_newsapi_news(query + " federal reserve economy", month_ago, today)
        source_used = "NewsAPI"

    # Path 3h — Banking & financial sector → NewsAPI
    elif any(kw in query_lower for kw in [
        "bank", "banking", "jpmorgan", "goldman", "morgan stanley",
        "wells fargo", "financial sector", "fintech"
    ]):
        articles = get_newsapi_news(query + " stocks finance", month_ago, today)
        source_used = "NewsAPI"

    # Path 3i — Healthcare & biotech → NewsAPI
    elif any(kw in query_lower for kw in [
        "pharma", "biotech", "healthcare", "drug", "fda", "ozempic",
        "glp", "weight loss", "pfizer", "moderna", "eli lilly"
    ]):
        articles = get_newsapi_news(query + " stocks investing", month_ago, today)
        source_used = "NewsAPI"

    # Path 3j — Real estate → NewsAPI
    elif any(kw in query_lower for kw in [
        "real estate", "housing market", "house prices", "mortgage rate",
        "reit", "property market"
    ]):
        articles = get_newsapi_news(query + " market investing", month_ago, today)
        source_used = "NewsAPI"

     # Path 3k — Market crash/correction queries → NewsAPI
    elif any(kw in query_lower for kw in [
         "crash", "market crash", "stock market crash", "correction",
         "bear market", "recession", "bubble", "collapse",
         "market timing", "wait for dip", "buy the dip"
    ]):
        articles = get_newsapi_news(query + " stock market investing", month_ago, today)
        source_used = "NewsAPI"


    # Path 4 — General macro → Guardian business
    else:
        articles = get_guardian_news(query, month_ago, today, section="business")
        source_used = "Guardian"
        if not articles:
            articles = get_newsapi_news(query, month_ago, today)
            source_used = "NewsAPI"

    # Path 5 — Nothing found → political context fallback
    if not articles:
        articles = get_political_context(query, month_ago, today)
        source_used = "Guardian (political context)"
        is_political_fallback = True

    if not articles:
        return None

    # Filter articles by relevance to query BEFORE scoring
    if not is_political_fallback:
        articles = filter_news_by_relevance(articles, query)

    if not articles:
        return None

    avg_sentiment = sum(a["sentiment"] for a in articles) / len(articles)

    return {
        "articles": articles,
        "avg_sentiment": round(avg_sentiment, 3),
        "verdict": "Positive" if avg_sentiment > 0.05 else "Negative" if avg_sentiment < -0.05 else "Neutral",
        "source": source_used,
        "is_political_fallback": is_political_fallback
    }



if __name__ == "__main__":
    print("Testing NVDA:")
    result = get_news_sentiment("should I invest in nvidia stock")
    if result:
        print(f"Verdict: {result['verdict']} ({result['avg_sentiment']}) via {result['source']}")
        for a in result["articles"][:3]:
            print(f"  {a['sentiment']} | {a['headline'][:80]}")

    print("\nTesting gold import tax india:")
    result = get_news_sentiment("gold import tax increase in india")
    if result:
        print(f"Verdict: {result['verdict']} ({result['avg_sentiment']}) via {result['source']}")
        for a in result["articles"][:3]:
            print(f"  {a['sentiment']} | {a['headline'][:80]}")

    print("\nTesting ASX australia:")
    result = get_news_sentiment("should I invest in ASX200 australia")
    if result:
        print(f"Verdict: {result['verdict']} ({result['avg_sentiment']}) via {result['source']}")
        for a in result["articles"][:3]:
            print(f"  {a['sentiment']} | {a['headline'][:80]}")

    print("\nTesting Trump tariffs:")
    result = get_news_sentiment("will Trump tariffs crash the market")
    if result:
        print(f"Verdict: {result['verdict']} ({result['avg_sentiment']}) via {result['source']}")
        for a in result["articles"][:3]:
            print(f"  {a['sentiment']} | {a['headline'][:80]}")

    print("\nTesting Reliance:")
    result = get_news_sentiment("what do people think about Reliance Industries")
    if result:
        print(f"Verdict: {result['verdict']} ({result['avg_sentiment']}) via {result['source']}")
        for a in result["articles"][:3]:
            print(f"  {a['sentiment']} | {a['headline'][:80]}")