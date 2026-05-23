import re


def clean_comment(text):
    """
    Cleans Reddit comment text for sentiment analysis.

    Preserves:
    - Capitalisation (VADER uses it for emphasis scoring)
    - Punctuation like ! and ? (VADER uses for intensity)
    - Emojis (sentiment signals)
    - Sentence structure

    Removes:
    - URLs
    - HTML tags and entities
    - Reddit markdown formatting
    - Deleted/removed placeholders
    - Excessive repeated characters (sooooo → soo)
    - Excessive whitespace
    """

    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove HTML entities
    text = text.replace('&gt;', '')
    text = text.replace('&lt;', '')
    text = text.replace('&amp;', '&')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#x200B;', '')
    text = text.replace('&quot;', '"')

    # Remove Reddit markdown
    text = re.sub(r'\*\*|\*|~~|`', '', text)
    text = re.sub(r'#{1,6}\s', '', text)

    # Remove deleted/removed placeholders
    text = re.sub(r'\[deleted\]|\[removed\]', '', text)

    # Normalise repeated characters — sooooooo → sooo (max 3)
    text = re.sub(r'(.)\1{3,}', r'\1\1\1', text)

    # Normalise excessive punctuation — !!!!! → !!! (max 3)
    text = re.sub(r'([!?.]){3,}', r'\1\1\1', text)

    # Normalise whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def clean_comments(comments):
    """
    Applies clean_comment to a list of comment dicts.
    Returns cleaned list.
    """
    cleaned = []
    for c in comments:
        body = clean_comment(c.get("body", ""))
        if body and len(body.split()) > 3:
            c["body"] = body
            cleaned.append(c)
    return cleaned


if __name__ == "__main__":
    test_comments = [
        "NVDA is sooooooooo bullish right nowwwww!!!!!! 🚀🚀🚀",
        "Check this out: https://reddit.com/r/investing/post123 really interesting",
        "**Bold text** and *italic* with ~~strikethrough~~ formatting",
        "[deleted]",
        "I bought NVDA at $400 and it&#x27;s up 200%!!! LETS GOOOOO",
        "&gt; quoted text here that should be removed",
        "This    has     lots     of     spaces",
    ]

    print("PREPROCESSOR TEST\n")
    for c in test_comments:
        cleaned = clean_comment(c)
        print(f"Before: {c}")
        print(f"After:  {cleaned}")
        print()
