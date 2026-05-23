import warnings
warnings.filterwarnings("ignore")
import streamlit as st
from sentiment_engine import analyze_query
from news_fetch import get_news_sentiment
from analysis_engine import generate_analysis, extract_themes, extract_thesis
from temporal_classifier import classify_comments_by_time
from analysis_engine import generate_analysis, extract_themes, extract_thesis, extract_recommendations


from functools import lru_cache
st.set_page_config(page_title="ReddSenti", page_icon="📊", layout="wide")


st.markdown("""
<style>
/* ── GLOBAL ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0f0f0f;
    color: #e0e0e0;
}

/* ── HIDE STREAMLIT BRANDING ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── MAIN CONTAINER ── */
.main .block-container {
    padding: 2rem 3rem;
    max-width: 1200px;
}

/* ── TITLE ── */
h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: #FF4500 !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem !important;
}

h2 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 400 !important;
    color: #888 !important;
    margin-bottom: 2rem !important;
}

/* ── HEADERS ── */
h3 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #e0e0e0 !important;
    text-transform: none !important;
    letter-spacing: 0em !important;
    margin-top: 0.5rem !important;
    margin-bottom: 0.3rem !important;
    border-bottom: 1px solid #2a2a2a !important;
    padding-bottom: 0.3rem !important;
}

/* ── INPUT ── */
.stTextInput input {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 4px !important;
    color: #e0e0e0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput input:focus {
    border-color: #FF4500 !important;
    box-shadow: 0 0 0 1px #FF4500 !important;
}

/* ── BUTTON ── */
.stButton button {
    background-color: #FF4500 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 2rem !important;
    transition: opacity 0.2s !important;
}

.stButton button:hover {
    opacity: 0.85 !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    padding: 1rem !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #666 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    color: #e0e0e0 !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ── ALERT BOXES — softer ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border-left-width: 3px !important;
    background-color: #1a1a1a !important;
}

/* Success — muted green */
[data-testid="stAlert"][kind="success"] {
    border-left-color: #2d6a4f !important;
    background-color: #0d1f17 !important;
    color: #95d5b2 !important;
}

/* Warning — muted amber */
[data-testid="stAlert"][kind="warning"] {
    border-left-color: #b5830a !important;
    background-color: #1f1700 !important;
    color: #ffd166 !important;
}

/* Error — muted red */
[data-testid="stAlert"][kind="error"] {
    border-left-color: #8b2020 !important;
    background-color: #1f0d0d !important;
    color: #e07070 !important;
}

/* Info — muted blue */
[data-testid="stAlert"][kind="info"] {
    border-left-color: #1a4a6b !important;
    background-color: #0d1520 !important;
    color: #7eb8d4 !important;
}

/* ── SELECTBOX ── */
.stSelectbox select,
[data-testid="stSelectbox"] {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #e0e0e0 !important;
    border-radius: 4px !important;
}

/* ── SLIDER ── */
.stSlider [data-testid="stThumbValue"] {
    background-color: #FF4500 !important;
    color: white !important;
}

.stSlider [data-baseweb="slider"] div[role="slider"] {
    background-color: #FF4500 !important;
}

/* ── DIVIDER ── */
hr {
    border-color: #2a2a2a !important;
    margin: 1.5rem 0 !important;
}

/* ── CAPTIONS ── */
.stCaptionContainer, [data-testid="stCaptionContainer"] {
    color: #666 !important;
    font-size: 0.78rem !important;
}

/* ── MARKDOWN TEXT ── */
.stMarkdown p {
    color: #c0c0c0 !important;
    line-height: 1.7 !important;
    font-size: 0.92rem !important;
}

/* ── SPINNER ── */
.stSpinner {
    color: #FF4500 !important;
}

/* ── TABLE ── */
table {
    background-color: #1a1a1a !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}

th {
    background-color: #222 !important;
    color: #888 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1rem !important;
}

td {
    color: #c0c0c0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
    border-color: #2a2a2a !important;
}

/* ── SIDEBAR (if used) ── */
[data-testid="stSidebar"] {
    background-color: #111 !important;
    border-right: 1px solid #2a2a2a !important;
}

/* ── INFO BOXES ── */
.stInfo {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# ReddSenti")
st.markdown("""
<p style="color: #aaa; font-size: 0.95rem; line-height: 1.7; max-width: 750px; margin-bottom: 1.5rem;">
ReddSenti is a retail narrative intelligence platform that analyses Reddit discussions across investing communities — r/investing, r/wallstreetbets, r/CryptoCurrency, r/Gold, r/AusFinance, r/IndiaInvestments and more — then compares retail sentiment against financial media coverage to surface where they diverge. Ask about US, Indian, or Australian stocks, crypto assets, ETFs, macro events, or investment decisions. Works best for specific assets and market questions — not general financial advice.
</p>
""", unsafe_allow_html=True)

query = st.text_input(
    "What do you want to know about?",
    placeholder="e.g. Should I buy NVDA stock? · Is Bitcoin a good investment? · How is Reddit reacting to Trump tariffs? · Should I sell my Apple shares? · What mutual funds should I invest in?"
)
col_sort, col_time, col_posts = st.columns(3)

with col_sort:
    sort_by = st.selectbox(
        "Sort posts by",
        options=["top", "new", "hot"],
        index=0,
        help="Top: most upvoted. New: most recent. Hot: trending right now."
    )

with col_time:
    time_filter = st.selectbox(
        "Time period",
        options=["week", "month", "year", "all"],
        index=2,
        help="How far back to look for posts."
    )

with col_posts:
    num_posts = st.slider(
        "Number of posts",
        min_value=3,
        max_value=15,
        value=10,
        help="More posts = stronger signal but slower."
    )

if st.button("Analyse", type="primary"):
    if not query:
        st.warning("Please enter a question first.")
    else:
        @st.cache_data(ttl=1800, show_spinner=False)
        def cached_analyze(query, num_posts, sort_by, time_filter):
            return analyze_query(query, num_posts=num_posts, sort_by=sort_by, time_filter=time_filter)


        @st.cache_data(ttl=1800, show_spinner=False)
        def cached_news(query):
            return get_news_sentiment(query)


        with st.spinner("Fetching Reddit sentiment..."):
            reddit_results = cached_analyze(query, num_posts, sort_by, time_filter)

        with st.spinner("Fetching news..."):
            # Use Phi-3 extracted search term for better news matching
            news_query = list(reddit_results.values())[0]["search_term"] if reddit_results else query
            news_result = cached_news(news_query)
        if not reddit_results:
            st.error("No Reddit data found. Try a different query.")
            st.stop()

        search_term = list(reddit_results.values())[0]["search_term"] if reddit_results else query

        avg_reddit = sum(
            d["weighted_sentiment"] for d in reddit_results.values()
        ) / len(reddit_results)

        all_comments_combined = []
        for data in reddit_results.values():
            all_comments_combined.extend(data["all_comments"])

        themes = extract_themes(all_comments_combined, search_term)

        # Compute bull/bear thesis in parallel before rendering UI
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=2) as executor:
            bull_future = executor.submit(extract_thesis, all_comments_combined, search_term, "bull")
            bear_future = executor.submit(extract_thesis, all_comments_combined, search_term, "bear")
            bull_thesis = bull_future.result()
            bear_thesis = bear_future.result()

        print(f"News result: {news_result}")
        st.divider()

        # ── DIVERGENCE HERO BANNER ──
        if news_result and not news_result.get("is_political_fallback"):
            news_score_hero = news_result["avg_sentiment"]
            divergence_hero = round(abs(avg_reddit - news_score_hero), 3)

            if avg_reddit > 0.35:
                reddit_direction = "Strongly Bullish "
            elif avg_reddit > 0.15:
                reddit_direction = "Bullish "
            elif avg_reddit > 0.05:
                reddit_direction = "Slightly Bullish "
            elif avg_reddit < -0.35:
                reddit_direction = "Strongly Bearish "
            elif avg_reddit < -0.15:
                reddit_direction = "Bearish "
            elif avg_reddit < -0.05:
                reddit_direction = "Slightly Bearish "
            else:
                reddit_direction = "Neutral "

            news_direction = (
                "Positive " if news_result["verdict"] == "Positive"
                else "Negative " if news_result["verdict"] == "Negative"
                else "Neutral "
            )

            gap_direction = "Reddit more bullish than news" if avg_reddit > news_score_hero else "News more bullish than Reddit"

            if divergence_hero > 0.2:
                border_color = "#8b2020"
                label_color = "#e07070"
                label = "HIGH DIVERGENCE DETECTED"
                description = "Reddit retail investors and financial media are seeing this very differently right now. Historically, large divergences have preceded elevated volatility."
            elif divergence_hero > 0.1:
                border_color = "#b5830a"
                label_color = "#ffd166"
                label = "MODERATE DIVERGENCE"
                description = "Some disagreement between retail investors and establishment coverage. Worth monitoring."
            else:
                border_color = "#2d6a4f"
                label_color = "#95d5b2"
                label = "CONSENSUS SIGNAL"
                description = "Reddit retail investors and financial media are broadly aligned. When retail and media agree closely, the signal tends to be more reliable."

            st.markdown(f"""
                    <div style="
                        background-color: #1a1a1a;
                        border-left: 3px solid {border_color};
                        border-radius: 6px;
                        padding: 1.2rem 1.5rem;
                        margin-bottom: 1rem;
                    ">
                        <div style="color: {label_color}; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; margin-bottom: 0.6rem;">
                             {label}
                        </div>
                        <div style="color: #888; font-size: 0.85rem; margin-bottom: 1rem; line-height: 1.5;">
                            {description}
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #2a2a2a;">
                                <th style="text-align: left; padding: 0.4rem 0.8rem; color: #555; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; background: transparent;"></th>
                                <th style="text-align: left; padding: 0.4rem 0.8rem; color: #555; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; background: transparent;">Signal</th>
                                <th style="text-align: left; padding: 0.4rem 0.8rem; color: #555; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; background: transparent;">Direction</th>
                            </tr>
                            <tr style="border-bottom: 1px solid #222;">
                                <td style="padding: 0.5rem 0.8rem; color: #FF4500; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;"> Reddit</td>
                                <td style="padding: 0.5rem 0.8rem; color: #e0e0e0; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;">{"(" + str(round(abs(avg_reddit) * 100)) + "%)" if avg_reddit < 0 else str(round(abs(avg_reddit) * 100)) + "%"}</td>                                <td style="padding: 0.5rem 0.8rem; color: #e0e0e0; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;">{reddit_direction}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #222;">
                                <td style="padding: 0.5rem 0.8rem; color: #888; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;"> News</td>
                                <td style="padding: 0.5rem 0.8rem; color: #e0e0e0; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;">{"(" + str(round(abs(news_score_hero) * 100)) + "%)" if news_score_hero < 0 else str(round(abs(news_score_hero) * 100)) + "%"}</td>
                                <td style="padding: 0.5rem 0.8rem; color: #e0e0e0; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;">{news_direction}</td>
                            </tr>
                            <tr>
                                <td style="padding: 0.5rem 0.8rem; color: #888; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;"> Gap</td>
                                <td style="padding: 0.5rem 0.8rem; color: {label_color}; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; font-weight: 600; background: transparent;">{round(divergence_hero * 100)}%</td>
                                <td style="padding: 0.5rem 0.8rem; color: #888; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; background: transparent;">{gap_direction}</td>
                            </tr>
                        </table>
                        <div style="color: #555; font-size: 0.75rem; margin-top: 0.6rem; font-style: italic;">
                            Signal ranges from 0% (neutral) to 100% (maximum conviction). Gap above 20 points indicates meaningful divergence.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        # ── SECTION 1 — THE VERDICT ──
        st.markdown("### The Verdict")
        analysis = generate_analysis(query, reddit_results, news_result)
        paragraphs = analysis.split("\n\n")
        for i, para in enumerate(paragraphs):
            if i == len(paragraphs) - 1:
                st.caption(para)
            else:
                st.markdown(para)


        # ── BULL VS BEAR ──
        bull_col, bear_col = st.columns(2)

        with bull_col:
            st.markdown(f"**{themes['bull_count']} Redditors are bullish**")
            if bull_thesis:
                for point in bull_thesis:
                    st.markdown(
                        f"""<div style="border-left: 2px solid #2d6a4f; padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; background: #0d1f17; border-radius: 4px; color: #95d5b2; font-size: 0.88rem;">✓ {point}</div>""",
                        unsafe_allow_html=True)
            if themes["bull_comments"]:
                for c in themes["bull_comments"][:2]:
                    st.markdown(
                        f"""<div style="border: 1px solid #2a2a2a; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; background: #1a1a1a; border-radius: 4px; color: #888; font-size: 0.82rem;">↑ {c['score']} upvotes — {c['body'][:150]}</div>""",
                        unsafe_allow_html=True)

        with bear_col:
            st.markdown(f"**{themes['bear_count']} Redditors are bearish**")
            if bear_thesis:
                for point in bear_thesis:
                    st.markdown(
                        f"""<div style="border-left: 2px solid #8b2020; padding: 0.5rem 0.8rem; margin-bottom: 0.5rem; background: #1f0d0d; border-radius: 4px; color: #e07070; font-size: 0.88rem;">✗ {point}</div>""",
                        unsafe_allow_html=True)
            if themes["bear_comments"]:
                for c in themes["bear_comments"][:2]:
                    st.markdown(
                        f"""<div style="border: 1px solid #2a2a2a; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; background: #1a1a1a; border-radius: 4px; color: #888; font-size: 0.82rem;">↑ {c['score']} upvotes — {c['body'][:150]}</div>""",
                        unsafe_allow_html=True)

        # ── SECTION 2 — WHAT REDDIT THINKS ──
        st.markdown("### Community Sentiment")
        cols = st.columns(len(reddit_results))
        for i, (subreddit, data) in enumerate(reddit_results.items()):
            with cols[i]:
                verdict = data["verdict"]
                score = data["weighted_sentiment"]
                st.metric(
                    label=f"r/{subreddit}",
                    value=verdict,
                    delta=f"{round(abs(score) * 100)}% signal"
                )
                st.caption(f"Based on {data['total_comments']} comments")

        total_comments_count = sum(d["total_comments"] for d in reddit_results.values())

        if total_comments_count >= 100:
            signal_strength = " Strong "
            signal_caption = f"{total_comments_count} comments — high confidence"
        elif total_comments_count >= 30:
            signal_strength = " Moderate "
            signal_caption = f"{total_comments_count} comments — moderate confidence"
        else:
            signal_strength = "⚠ Low "
            signal_caption = f"Only {total_comments_count} comments — treat with caution"
        stat1, stat2, stat3, stat4, stat5 = st.columns(5)
        with stat1:
            st.metric("Signal strength", signal_strength)
            st.caption(signal_caption)
        with stat2:
            st.metric("Total comments", total_comments_count)
        with stat3:
            st.metric(" Bullish", themes["bull_count"])
        with stat4:
            st.metric(" Bearish", themes["bear_count"])
        with stat5:
            st.metric(" Neutral", themes["neutral_count"])

        # ── TEMPORAL SECTION ──
        st.markdown("### Narrative Over Time")
        temporal = classify_comments_by_time(all_comments_combined, search_term)
        hist_col, pres_col, fut_col = st.columns(3)

        with hist_col:
            data = temporal["historical"]
            st.markdown(
                f"<span style='color: #6b7280; font-weight: 600;'>{data['label']}</span> — {data['description']}",
                unsafe_allow_html=True)
            st.caption(f"{data['count']} comments")
            if data["comments"]:
                for c in data["comments"]:
                    st.markdown(
                        f"""<div style="border: 1px solid #2a2a2a; border-left: 2px solid #6b7280; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; background: #1a1a1a; border-radius: 4px; color: #888; font-size: 0.82rem;">↑ {c['score']} — {c['body'][:150]}</div>""",
                        unsafe_allow_html=True)
            else:
                st.caption("No historical comments found.")

        with pres_col:
            data = temporal["present"]
            st.markdown(
                f"<span style='color: #10b981; font-weight: 600;'>{data['label']}</span> — {data['description']}",
                unsafe_allow_html=True)
            st.caption(f"{data['count']} comments")
            if data["comments"]:
                for c in data["comments"]:
                    st.markdown(
                        f"""<div style="border: 1px solid #2a2a2a; border-left: 2px solid #10b981; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; background: #1a1a1a; border-radius: 4px; color: #888; font-size: 0.82rem;">↑ {c['score']} — {c['body'][:150]}</div>""",
                        unsafe_allow_html=True)
            else:
                st.caption("No present comments found.")

        with fut_col:
            data = temporal["future"]
            st.markdown(
                f"<span style='color: #6366f1; font-weight: 600;'>{data['label']}</span> — {data['description']}",
                unsafe_allow_html=True)
            st.caption(f"{data['count']} comments")
            if data["comments"]:
                for c in data["comments"]:
                    st.markdown(
                        f"""<div style="border: 1px solid #2a2a2a; border-left: 2px solid #6366f1; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; background: #1a1a1a; border-radius: 4px; color: #888; font-size: 0.82rem;">↑ {c['score']} — {c['body'][:150]}</div>""",
                        unsafe_allow_html=True)
            else:
                st.caption("No forward-looking comments found.")

        # ── SECTION 3 — WHAT THE NEWS SAYS ──
        if news_result:
            is_political = news_result.get("is_political_fallback", False)

            if is_political:
                st.markdown("### Political & Macro Context")
                st.caption(
                    "No direct financial news found for this topic. "
                    "The articles below provide broader context that may help explain "
                    "what is driving sentiment."
                )
            else:
                st.markdown("### Media Coverage")
                st.caption(f"Source: {news_result['source']}")

            st.markdown("**Recent headlines:**")
            for article in news_result["articles"][:5]:
                sentiment_emoji = "🟢" if article["sentiment"] > 0.05 else "🔴" if article["sentiment"] < -0.05 else "⚪"
                url = article.get("url", "")
                source = news_result.get("source", "")

                if (url and
                    "finnhub" not in source.lower() and
                    not url.startswith("http://localhost") and
                    "finnhub.io" not in url):
                    st.markdown(f"{sentiment_emoji} [{article['headline']}]({url})")
                else:
                    st.markdown(f"{sentiment_emoji} {article['headline']}")

        else:
            st.header(" What the news says")
            st.info("No news found for this topic. Try a more specific query.")


