import ollama
import json
import re


def parse_query(query):
    prompt = f"""You are a financial query parser. Extract structured information from this investment query.

Query: "{query}"

Respond ONLY with a JSON object, no other text:
{{
    "entity": "the main financial asset, topic or event",
    "intent": "one of: buy_decision, sell_decision, sentiment_check, recommendation_request, macro_analysis, price_prediction, comparison",
    "search_term": "2-4 word clean search term for Reddit, removing question words",
    "context": "any important context like recent events, time frame, or conditions"
}}

Examples:
- "should I invest in NVDA?" → {{"entity": "NVDA", "intent": "buy_decision", "search_term": "NVDA stock invest", "context": ""}}
- "how can I start investing without a middleman?" → {{"entity": "self-directed investing", "intent": "recommendation_request", "search_term": "self directed brokerage investing", "context": "no financial advisor"}}
- "what does Reddit think about gold given inflation?" → {{"entity": "gold", "intent": "sentiment_check", "search_term": "gold inflation hedge", "context": "inflation concern"}}
- "should I sell my Apple shares?" → {{"entity": "AAPL", "intent": "sell_decision", "search_term": "AAPL sell hold", "context": ""}}
- "is the US heading into recession?" → {{"entity": "US economy", "intent": "macro_analysis", "search_term": "US recession economy", "context": ""}}
- "should I wait for a stock market crash before investing?" → {{"entity": "stock market", "intent": "macro_analysis", "search_term": "stock market crash timing", "context": "waiting for crash"}}
- "is it better to buy or rent?" → {{"entity": "real estate", "intent": "comparison", "search_term": "buy vs rent real estate", "context": "buy or rent decision"}}
- "stocks vs crypto which is better?" → {{"entity": "stocks vs crypto", "intent": "comparison", "search_term": "stocks crypto comparison", "context": "asset comparison"}}"""

    try:
        response = ollama.chat(
            model="phi3",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        content = response["message"]["content"].strip()

        # Try to extract JSON object from response
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        elif "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        return parsed

    except Exception as e:
        print(f"Query parser error: {e}")
        cleaned = query.lower()
        for word in ["should i", "is it", "will", "can i", "how do i", "what is",
                     "wait for", "before investing", "good time to", "worth"]:
            cleaned = cleaned.replace(word, "")
        words = [w for w in cleaned.split() if len(w) > 2]
        fallback_term = " ".join(words[:4]).strip()
        return {
            "entity": query,
            "intent": "sentiment_check",
            "search_term": fallback_term if fallback_term else query,
            "context": ""
        }

def get_search_term(query):
    result = parse_query(query)
    return result.get("search_term", query)


def get_intent(query):
    result = parse_query(query)
    return result.get("intent", "sentiment_check")


if __name__ == "__main__":
    test_queries = [
        "should I invest in NVDA stock",
        "how can I start a portfolio without a middleman",
        "what does Reddit think about gold given inflation",
        "should I sell my Apple shares",
        "is the US economy heading into a recession",
        "what mutual funds should I invest in",
        "will Bitcoin hit 100k this year",
        "how is Reddit reacting to Trump tariffs",
        "should I wait for a stock market crash before investing",
    ]

    print("QUERY PARSER TEST\n")
    for q in test_queries:
        result = parse_query(q)
        print(f"Query: {q}")
        print(f"  Entity: {result['entity']}")
        print(f"  Intent: {result['intent']}")
        print(f"  Search term: {result['search_term']}")
        print(f"  Context: {result['context']}")
        print()