import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def load_lm_lexicon(filepath="Loughran-McDonald_MasterDictionary_1993-2025.csv"):
    """
    Loads the Loughran-McDonald financial sentiment lexicon
    and returns positive and negative word sets.
    """
    try:
        df = pd.read_csv(filepath, low_memory=False)

        # Column names vary by version — handle both
        word_col = "Word" if "Word" in df.columns else df.columns[0]
        pos_col = "Positive" if "Positive" in df.columns else None
        neg_col = "Negative" if "Negative" in df.columns else None

        # Find correct column names
        for col in df.columns:
            if col.lower() == "positive":
                pos_col = col
            if col.lower() == "negative":
                neg_col = col

        positive_words = set()
        negative_words = set()

        if pos_col:
            pos_mask = df[pos_col] != 0
            positive_words = set(df[pos_mask][word_col].str.lower().tolist())

        if neg_col:
            neg_mask = df[neg_col] != 0
            negative_words = set(df[neg_mask][word_col].str.lower().tolist())

        print(f"Loaded LM lexicon: {len(positive_words)} positive, {len(negative_words)} negative words")
        return positive_words, negative_words

    except Exception as e:
        print(f"Could not load LM lexicon: {e}")
        return set(), set()


def build_enhanced_analyzer():
    """
    Creates a VADER analyzer enhanced with Loughran-McDonald
    financial sentiment vocabulary.

    LM lexicon captures financial-specific sentiment that VADER misses:
    - "volatile" — neutral in general language, negative in finance
    - "headwinds" — negative in finance
    - "upside" — positive in finance
    - "writedown" — negative in finance
    - "restatement" — negative in finance
    """
    analyzer = SentimentIntensityAnalyzer()

    positive_words, negative_words = load_lm_lexicon()

    if not positive_words and not negative_words:
        print("Using standard VADER — LM lexicon not loaded")
        return analyzer

    # VADER's lexicon uses scores from -4 to +4
    # We add financial terms with moderate scores
    # so they influence but don't dominate

    lm_additions = {}

    for word in positive_words:
        if word not in analyzer.lexicon:
            lm_additions[word] = 2.0  # moderate positive

    for word in negative_words:
        if word not in analyzer.lexicon:
            lm_additions[word] = -2.0  # moderate negative

    # Special high-conviction financial terms
    high_conviction = {
        # Strongly negative in finance
        "writedown": -3.0,
        "writeoff": -3.0,
        "restatement": -3.0,
        "bankruptcy": -3.5,
        "insolvency": -3.5,
        "default": -2.5,
        "delisted": -3.0,
        "headwinds": -2.0,
        "deterioration": -2.5,
        "impairment": -2.5,
        "shortfall": -2.0,
        "downgrade": -2.5,
        "volatile": -1.5,
        "volatility": -1.5,
        "lawsuit": -2.0,
        "litigation": -2.0,
        "investigation": -2.0,
        "fraud": -3.5,
        "manipulation": -3.0,
        # Strongly positive in finance
        "outperform": 2.5,
        "upgrade": 2.5,
        "upside": 2.0,
        "tailwinds": 2.0,
        "beat": 2.0,
        "exceeded": 2.5,
        "record": 1.5,
        "profitability": 2.0,
        "breakout": 2.0,
        "momentum": 1.5,
        "accretive": 2.0,
        "synergies": 1.5,
    }

    lm_additions.update(high_conviction)
    analyzer.lexicon.update(lm_additions)

    print(f"Enhanced VADER with {len(lm_additions)} financial terms")
    return analyzer


# Create enhanced analyzer once at module level
enhanced_analyzer = build_enhanced_analyzer()


def score_financial_sentiment(text):
    """
    Score text using the enhanced financial VADER analyzer.
    Drop-in replacement for standard VADER.
    """
    return enhanced_analyzer.polarity_scores(text)


if __name__ == "__main__":
    # Test financial terms
    test_phrases = [
        "The company announced a writedown of $2 billion",
        "Strong earnings beat with significant upside potential",
        "Headwinds from rising rates and volatile markets",
        "Upgrade to outperform with bullish momentum",
        "SEC investigation into potential fraud and restatement",
        "Record revenue with strong tailwinds from AI demand",
        "NVDA is a strong buy with massive upside",
        "Bankruptcy risk is real given the debt load",
    ]

    standard = SentimentIntensityAnalyzer()

    print("STANDARD VADER vs ENHANCED FINANCIAL VADER\n")
    for phrase in test_phrases:
        std_score = standard.polarity_scores(phrase)["compound"]
        enh_score = score_financial_sentiment(phrase)["compound"]
        diff = round(enh_score - std_score, 3)
        print(f"Phrase: {phrase[:60]}")
        print(f"  Standard: {std_score} | Enhanced: {enh_score} | Diff: {diff}")
        print()