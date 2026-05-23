def get_subreddits(query):
    query_lower = query.lower()

    mappings = [

        # ── DEFENSE & MILITARY ──
        {
            "keywords": ["defense", "defence", "military", "aerospace",
                         "lockheed", "raytheon", "northrop", "bae systems",
                         "weapon", "nato", "arms", "fighter jet", "drone"],
            "subreddits": ["investing", "stocks", "wallstreetbets", "SecurityAnalysis", "geopolitics"]
        },

        # ── INDIA ──
        {
            "keywords": ["india", "indian", "sensex", "nifty", "bse", "nse",
                         "rupee", "rbi", "sebi", "modi", "mumbai", "delhi",
                         "import tax", "custom duty", "zerodha", "groww", "tcs",
                         "infosys", "wipro", "reliance", "hdfc bank", "icici bank",
                         "mutual fund india", "sip", "elss", "nfo"],
            "subreddits": ["IndiaInvestments", "IndianStockMarket", "IndianStreetBets",
                           "mutualfunds_india", "IndiaPersonalFinance", "india"]
        },

        # ── AUSTRALIA ──
        {
            "keywords": ["australia", "australian", "asx", "aud", "rba",
                         "sydney", "melbourne", "superannuation", "super fund",
                         "asx200", "commbank", "westpac", "anz", "macquarie"],
            "subreddits": ["AusFinance", "AusProperty", "ausstocks",
                           "AusEcon", "fiaustralia", "AusPropertyChat"]
        },

        # ── UK ──
        {
            "keywords": ["uk", "britain", "british", "ftse", "pound", "gbp",
                         "bank of england", "isa", "hmrc", "london stock",
                         "chancellor", "reeves", "sunak"],
            "subreddits": ["UKPersonalFinance", "unitedkingdom", "UKInvesting",
                           "FIREUK", "LegalAdviceUK"]
        },

        # ── CANADA ──
        {
            "keywords": ["canada", "canadian", "tsx", "cad", "bank of canada",
                         "toronto", "tsx composite", "tfsa", "rrsp"],
            "subreddits": ["PersonalFinanceCanada", "CanadianInvestor", "investing",
                           "canadafinance", "TorontoRealEstate"]
        },

        # ── EUROPE ──
        {
            "keywords": ["europe", "european", "euro", "ecb", "dax", "cac",
                         "ftse mib", "ibex", "germany", "france", "italy",
                         "spain", "netherlands", "switzerland"],
            "subreddits": ["eupersonalfinance", "investing", "stocks",
                           "europe", "EuropeFIRE"]
        },

        # ── CHINA ──
        {
            "keywords": ["china", "chinese", "ccp", "hang seng", "shanghai",
                         "shenzhen", "yuan", "renminbi", "alibaba", "tencent",
                         "baidu", "a shares", "h shares"],
            "subreddits": ["investing", "stocks", "economics",
                           "China", "Sino"]
        },

        # ── US MEGA CAP STOCKS ──
        {
            "keywords": ["nvda", "nvidia", "amd", "intel", "tsmc", "semiconductor", "chip", "gpu"],
            "subreddits": ["investing", "stocks", "wallstreetbets",
                           "SecurityAnalysis", "ValueInvesting"]
        },
        {
            "keywords": ["apple", "aapl", "google", "googl", "microsoft", "msft",
                         "amazon", "amzn", "meta", "tesla", "tsla", "netflix", "nflx",
                         "uber", "airbnb", "abnb", "spotify", "palantir", "pltr"],
            "subreddits": ["investing", "stocks", "wallstreetbets",
                           "SecurityAnalysis", "stockmarket"]
        },

        # ── US GENERAL STOCKS ──
        {
            "keywords": ["stock", "stocks", "equity", "shares", "sp500", "s&p",
                         "nasdaq", "dow", "nyse", "ipo", "earnings", "dividend"],
            "subreddits": ["investing", "stocks", "stockmarket",
                           "wallstreetbets", "SecurityAnalysis"]
        },

        # ── US MACRO & POLICY ──
        {
            "keywords": ["trump", "tariff", "tariffs", "trade war", "fed",
                         "federal reserve", "jerome powell", "inflation",
                         "recession", "gdp", "cpi", "interest rate", "fomc",
                         "treasury", "debt ceiling", "fiscal policy"],
            "subreddits": ["investing", "economics", "stocks",
                           "MacroEconomics", "econmonitor"]
        },

        # ── CRYPTO ──
        {
            "keywords": ["crypto", "bitcoin", "btc", "ethereum", "eth",
                         "coin", "defi", "web3", "altcoin", "binance",
                         "coinbase", "cryptocurrency", "blockchain", "nft",
                         "solana", "cardano", "dogecoin", "xrp", "ripple"],
            "subreddits": ["CryptoCurrency", "bitcoin", "CryptoMarkets",
                           "ethfinance", "CryptoInvesting"]
        },

        # ── GOLD & COMMODITIES ──
        {
            "keywords": ["gold", "silver", "oil", "crude", "copper",
                         "platinum", "commodity", "commodities", "precious metal",
                         "natural gas", "lng", "opec", "brent", "wti"],
            "subreddits": ["investing", "Gold", "stocks",
                           "Commodities", "silverbugs"]
        },

        # ── NUCLEAR & ENERGY ──
        {
            "keywords": ["nuclear", "uranium", "energy stocks", "clean energy",
                         "renewable", "solar", "wind power", "battery",
                         "ev", "electric vehicle", "lithium", "cobalt",
                         "cameco", "energy transition"],
            "subreddits": ["investing", "stocks", "RenewableEnergy",
                           "uranium", "EVs"]
        },

        # ── REAL ESTATE ──
        {
            "keywords": ["real estate", "property", "housing", "mortgage",
                         "reit", "rent", "landlord", "house price", "house",
                         "home", "buy a house", "buying a house", "first home",
                         "first time buyer", "stamp duty", "hdb", "condo"],
            "subreddits": ["realestate", "personalfinance", "FirstTimeHomeBuyer",
                           "REBubble", "RealEstateInvesting"]
        },

        # ── PERSONAL FINANCE & ETFs ──
        {
            "keywords": ["etf", "index fund", "vanguard", "fidelity", "voo",
                         "spy", "retirement", "401k", "ira", "pension",
                         "savings", "budget", "debt", "emergency fund",
                         "fire", "financial independence", "passive income"],
            "subreddits": ["personalfinance", "financialindependence", "investing",
                           "Bogleheads", "Fire"]
        },

        # ── BANKING & FINTECH ──
        {
            "keywords": ["bank", "banking", "jpmorgan", "goldman sachs",
                         "morgan stanley", "wells fargo", "bank of america",
                         "fintech", "payments", "visa", "mastercard",
                         "paypal", "square", "stripe", "interest rates"],
            "subreddits": ["investing", "stocks", "economics",
                           "fintech", "Banking"]
        },

        # ── HEALTHCARE & BIOTECH ──
        {
            "keywords": ["pharma", "biotech", "healthcare", "drug", "fda",
                         "clinical trial", "pfizer", "moderna", "johnson",
                         "abbott", "medtronic", "eli lilly", "novo nordisk",
                         "ozempic", "weight loss drug", "glp"],
            "subreddits": ["investing", "stocks", "Biotech",
                           "medicine", "pharmacy"]
        },

        # ── AI & TECH GENERAL ──
        {
            "keywords": ["artificial intelligence", "machine learning", "openai",
                         "chatgpt", "anthropic", "ai bubble", "ai stocks",
                         "data centre", "cloud computing", "saas", "software"],
            "subreddits": ["investing", "stocks", "artificial",
                           "MachineLearning", "singularity"]
        },

        # ── EMERGING MARKETS ──
        {
            "keywords": ["emerging market", "vietnam", "indonesia", "brazil",
                         "mexico", "south africa", "turkey", "argentina",
                         "southeast asia", "latam", "brics"],
            "subreddits": ["investing", "economics", "stocks",
                           "EmergingMarkets", "worldnews"]
        },
    ]
    for mapping in mappings:
        for keyword in mapping["keywords"]:
            if keyword in query_lower:
                return mapping["subreddits"]

    # Default
    return ["investing", "stocks", "personalfinance"]


if __name__ == "__main__":
    test_queries = [
        "should I invest in NVDA",
        "gold import tax increase in india",
        "should I invest in ASX200",
        "will Trump tariffs crash the market",
        "how is bitcoin doing",
        "should I buy a house in australia",
        "what is happening with sensex",
        "best ETF for retirement",
        "should I invest in defense stocks",
        "is nuclear energy a good investment",
        "what does Reddit think about Tesla",
        "should I invest in UK stocks",
        "is biotech a good sector right now",
        "what about ozempic stocks",
        "should I buy gold",
        "is the AI bubble about to burst"
    ]
    for query in test_queries:
        subreddits = get_subreddits(query)
        print(f"'{query}'")
        print(f"  → {subreddits}\n")