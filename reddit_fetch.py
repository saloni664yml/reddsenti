import requests
import re
from preprocessor import clean_comment

TICKER_ALIASES = {
    # US stocks
    "NVDA": ["nvda", "nvidia"],
    "TSLA": ["tsla", "tesla"],
    "AAPL": ["aapl", "apple"],
    "GOOGL": ["googl", "google", "alphabet"],
    "MSFT": ["msft", "microsoft"],
    "AMZN": ["amzn", "amazon"],
    "META": ["meta", "facebook"],
    "BTC": ["btc", "bitcoin"],
    "ETH": ["eth", "ethereum"],
    "AMD": ["amd"],
    "INTC": ["intc", "intel"],
    "TSMC": ["tsmc"],
    "GME": ["gme", "gamestop"],
    "NFLX": ["nflx", "netflix"],
    "COIN": ["coin", "coinbase"],
    "PLTR": ["pltr", "palantir"],
    "UBER": ["uber"],
    "ABNB": ["abnb", "airbnb"],
    # Indian stocks
    "RELIANCE": ["reliance", "reliance industries"],
    "TCS": ["tcs", "tata consultancy"],
    "INFY": ["infy", "infosys"],
    "HDFCBANK": ["hdfc bank", "hdfc"],
    "WIPRO": ["wipro"],
    "TATAMOTORS": ["tata motors", "tata cars"],
    "ADANIENT": ["adani", "adani enterprises"],
    "BAJFINANCE": ["bajaj finance"],
    # Australian stocks
    "CBA": ["cba", "commonwealth bank"],
    "BHP": ["bhp", "bhp group"],
    "CSL": ["csl limited"],
    "ANZ": ["anz bank"],
    "WBC": ["westpac"],
    "NAB": ["nab", "national australia bank"],
    "WES": ["wesfarmers"],
    "WOW": ["woolworths"]
}


def clean_comment_text(text):
    text = text.replace("&gt;", "")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("`", "")
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_reddit_posts(subreddit, query, limit=25, sort_by="top", time_filter="year"):
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    headers = {"User-Agent": "ReddSenti/1.0"}
    params = {
        "q": query,
        "sort": sort_by,
        "limit": limit,
        "restrict_sr": True,
        "t": time_filter
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Skipping r/{subreddit} — status {response.status_code}")
            return []
        data = response.json()
        posts = []
        for post in data["data"]["children"]:
            p = post["data"]
            posts.append({
                "title": p["title"],
                "score": p["score"],
                "upvote_ratio": p["upvote_ratio"],
                "num_comments": p["num_comments"],
                "url": p["url"]
            })
        return posts
    except Exception as e:
        print(f"Error fetching posts from r/{subreddit}: {e}")
        return []


def get_post_comments(post_url, limit=50):
    try:
        json_url = post_url + ".json"
        headers = {"User-Agent": "ReddSenti/1.0"}
        params = {"limit": limit, "sort": "top"}
        response = requests.get(json_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Skipping post — status {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list) or len(data) < 2:
            print("Skipping post — unexpected response format")
            return []

        comments = []
        for comment in data[1]["data"]["children"]:
            c = comment["data"]
            body = c.get("body", "")
            if (body and
                body != "[deleted]" and
                body != "[removed]" and
                not body.startswith("http") and
                not body.startswith("![]") and
                not body.startswith("https") and
                len(body.split()) > 5):
                comments.append({
                    "body": clean_comment(body),
                    "score": c["score"]
                })
        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


if __name__ == "__main__":
    posts = get_reddit_posts("investing", "NVDA", limit=5)
    print("POSTS:")
    for p in posts:
        print(p["title"], "| score:", p["score"])