import streamlit as st
import pandas as pd
import yfinance as yf
import os

from groq import Groq
from streamlit_autorefresh import st_autorefresh


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Stock Analysis AI Agent",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Elevating the Stock Analysis Agent")

st.markdown("""
Global stock search, live price tracking, company fundamentals,
historical charts, multi-currency conversion and AI-powered analysis.
""")

st.write("---")


# ==========================================================
# 2. GROQ API CONFIGURATION
# ==========================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# ==========================================================
# 3. AUTOMATIC REFRESH
# ==========================================================

st_autorefresh(
    interval=10000,
    key="stock_data_refresh"
)


# ==========================================================
# 4. INITIAL VARIABLES
# ==========================================================

ticker_input = None
current_price = 0.0
base_currency = "USD"
long_name = "No company selected"

stock_data = None
info = {}

exchange_rate = 1.0
target_currency = "Original Market Currency"


# ==========================================================
# 5. FINANCIAL WORKSPACE
# ==========================================================

col1, col2 = st.columns(2)


# ==========================================================
# LEFT COLUMN - STOCK SEARCH
# ==========================================================

with col1:

    st.subheader("🔍 Global Stock Search")

    user_query = st.text_input(
        "Search Company Name or Ticker",
        value="Krafton",
        placeholder="Example: Apple, Tesla, Tata, Krafton"
    )

    timeframe_map = {

        "1 day": "1d",
        "1 week": "5d",
        "1 month": "1mo",
        "2 months": "3mo",
        "6 months": "6mo",
        "1 year": "1y",
        "2 years": "2y",
        "5 years": "5y",
        "All time": "max"

    }

    timeframe_selection = st.selectbox(
        "Select Historical Timeframe",
        options=list(timeframe_map.keys()),
        index=2
    )

    timeframe = timeframe_map[timeframe_selection]


    # ------------------------------------------------------
    # STOCK SEARCH ENGINE
    # ------------------------------------------------------

    if user_query.strip():

        try:

            search_results = yf.Search(
                user_query,
                max_results=8
            ).quotes

            if search_results:

                options_list = []
                results_map = {}

                for match in search_results:

                    sym = match.get("symbol", "")

                    name = match.get(
                        "longname",
                        match.get("shortname", "Unknown Company")
                    )

                    exch = match.get(
                        "exchDisp",
                        "Global Exchange"
                    )

                    if sym:

                        display_label = (
                            f"{name} [{sym}] — {exch}"
                        )

                        options_list.append(display_label)

                        results_map[display_label] = sym


                if options_list:

                    st.success(
                        f"Found {len(options_list)} matching assets."
                    )

                    selected_label = st.selectbox(
                        "Select Company",
                        options=options_list
                    )

                    ticker_input = results_map[selected_label]


                    # --------------------------------------------------
                    # FETCH COMPANY INFORMATION
                    # --------------------------------------------------

                    stock_data = yf.Ticker(ticker_input)

                    info = stock_data.info

                    current_price = info.get(
                        "currentPrice",
                        info.get(
                            "regularMarketPrice",
                            info.get("previousClose", 0.0)
                        )
                    ) or 0.0

                    base_currency = info.get(
                        "currency",
                        "USD"
                    )

                    long_name = info.get(
                        "longName",
                        ticker_input
                    )

                    st.success(
                        f"🎯 Tracking: {long_name} ({ticker_input})"
                    )


                    # ==================================================
                    # 6. CURRENCY CONVERTER
                    # ==================================================

                    st.markdown(
                        "### 💱 Global Currency Converter"
                    )

                    currency_options = [
                        "Original Market Currency",
                        "USD",
                        "INR",
                        "EUR",
                        "GBP",
                        "KRW"
                    ]

                    target_currency = st.selectbox(
                        "Convert Stock Price To",
                        currency_options
                    )

                    converted_price = current_price

                    final_currency_label = base_currency

                    exchange_rate = 1.0


                    if (
                        target_currency != "Original Market Currency"
                        and target_currency != base_currency
                    ):

                        try:

                            forex_ticker = (
                                f"{base_currency}{target_currency}=X"
                            )

                            forex_data = yf.Ticker(forex_ticker)

                            forex_history = forex_data.history(
                                period="5d"
                            )

                            if not forex_history.empty:

                                exchange_rate = float(
                                    forex_history["Close"].dropna().iloc[-1]
                                )

                            else:

                                # Try inverse currency pair

                                inverse_ticker = (
                                    f"{target_currency}{base_currency}=X"
                                )

                                inverse_data = yf.Ticker(
                                    inverse_ticker
                                )

                                inverse_history = inverse_data.history(
                                    period="5d"
                                )

                                if not inverse_history.empty:

                                    inverse_rate = float(
                                        inverse_history["Close"].dropna().iloc[-1]
                                    )

                                    exchange_rate = 1 / inverse_rate

                                else:

                                    raise ValueError(
                                        "Exchange rate unavailable"
                                    )


                            converted_price = (
                                current_price * exchange_rate
                            )

                            final_currency_label = target_currency

                        except Exception:

                            st.warning(
                                "Currency conversion unavailable. "
                                "Showing original market currency."
                            )

                            converted_price = current_price

                            final_currency_label = base_currency


                    st.metric(
                        label="💰 Current Stock Price",
                        value=(
                            f"{converted_price:,.2f} "
                            f"{final_currency_label}"
                        )
                    )


                    # ==================================================
                    # 7. COMPANY FUNDAMENTAL OVERVIEW
                    # ==================================================

                    st.markdown(
                        "### 📊 Company Fundamental Overview"
                    )

                    market_cap = info.get("marketCap")

                    details_df = pd.DataFrame({

                        "Financial Metric": [

                            "Company Name",
                            "Market Capitalization",
                            "P/E Ratio",
                            "52-Week High",
                            "52-Week Low",
                            "Volume Traded",
                            "Dividend Yield",
                            "Sector",
                            "Industry"

                        ],

                        "Value": [

                            long_name,

                            f"{market_cap:,}" if market_cap else "N/A",

                            info.get("trailingPE", "N/A"),

                            f"{info.get('fiftyTwoWeekHigh', 'N/A')} {base_currency}",

                            f"{info.get('fiftyTwoWeekLow', 'N/A')} {base_currency}",

                            f"{info.get('volume', 0):,}",

                            info.get("dividendYield", "N/A"),

                            info.get("sector", "N/A"),

                            info.get("industry", "N/A")

                        ]

                    })

                    st.dataframe(
                        details_df,
                        use_container_width=True,
                        hide_index=True
                    )


                else:

                    st.error(
                        "No matching companies found."
                    )

            else:

                st.error(
                    "No global companies matched your search."
                )


        except Exception as e:

            st.error(
                f"Stock search error: {str(e)}"
            )


# ==========================================================
# RIGHT COLUMN - STOCK CHART
# ==========================================================

with col2:

    st.subheader("📈 Historical Stock Price Chart")

    if ticker_input and stock_data:

        try:

            historical_df = stock_data.history(
                period=timeframe
            )

            if not historical_df.empty:

                chart_df = historical_df[["Close"]].copy()

                # Convert chart prices into selected currency

                if (
                    target_currency != "Original Market Currency"
                    and target_currency != base_currency
                ):

                    chart_df["Close"] = (
                        chart_df["Close"] * exchange_rate
                    )

                st.line_chart(
                    chart_df,
                    use_container_width=True
                )

                st.caption(
                    f"Historical closing prices in "
                    f"{final_currency_label if 'final_currency_label' in locals() else base_currency}"
                )

            else:

                st.warning(
                    "No historical chart data available."
                )


        except Exception as e:

            st.error(
                f"Chart error: {str(e)}"
            )

    else:

        st.info(
            "Search and select a company to display its stock chart."
        )


st.write("---")


# ==========================================================
# 8. GROQ AI STOCK ASSISTANT
# ==========================================================

st.subheader("🤖 Groq AI Stock Assistant")

st.markdown(
    "Ask questions about company performance, "
    "financial metrics, market trends and stock analysis."
)


# ----------------------------------------------------------
# INITIALIZE CHAT HISTORY
# ----------------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [

        {
            "role": "assistant",

            "content": (
                "Hello! 👋 I am your AI Stock Analysis Assistant. "
                "Search for a company and ask me anything "
                "about its financial performance!"
            )
        }

    ]


# ----------------------------------------------------------
# DISPLAY PREVIOUS MESSAGES
# ----------------------------------------------------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.write(msg["content"])


# ----------------------------------------------------------
# CHAT INPUT
# ----------------------------------------------------------

user_input = st.chat_input(
    "Ask about financials, company performance or stock metrics..."
)


if user_input:

    # Display user message

    st.session_state.messages.append({

        "role": "user",

        "content": user_input

    })

    with st.chat_message("user"):

        st.write(user_input)


    # ------------------------------------------------------
    # CHECK API KEY
    # ------------------------------------------------------

    if not GROQ_API_KEY:

        st.error(
            "Groq API key not found. "
            "Add GROQ_API_KEY to .streamlit/secrets.toml."
        )


    else:

        try:

            # Initialize Groq client

            client = Groq(
                api_key=GROQ_API_KEY
            )


            # --------------------------------------------------
            # COMPANY CONTEXT FOR AI
            # --------------------------------------------------

            context_prompt = f"""

            You are an intelligent AI Stock Analysis Assistant.

            Your job is to help users understand stock markets,
            company financials and investment-related concepts.

            CURRENT COMPANY INFORMATION:

            Company Name: {long_name}

            Ticker Symbol: {ticker_input}

            Current Stock Price: {current_price}

            Original Currency: {base_currency}

            Selected Display Currency: {target_currency}

            COMPANY FINANCIAL INFORMATION:

            Market Capitalization:
            {info.get('marketCap', 'Not Available')}

            P/E Ratio:
            {info.get('trailingPE', 'Not Available')}

            52 Week High:
            {info.get('fiftyTwoWeekHigh', 'Not Available')}

            52 Week Low:
            {info.get('fiftyTwoWeekLow', 'Not Available')}

            Sector:
            {info.get('sector', 'Not Available')}

            Industry:
            {info.get('industry', 'Not Available')}


            INSTRUCTIONS:

            1. Answer questions clearly and professionally.

            2. Explain financial terminology in simple language.

            3. Analyze the selected company's available metrics.

            4. Explain potential risks and opportunities.

            5. Never invent financial figures.

            6. If information is unavailable, mention it.

            7. Do not guarantee stock market returns.

            8. Clearly distinguish factual information from opinions.

            9. Provide educational analysis rather than
               personalized investment instructions.

            """


            # --------------------------------------------------
            # GENERATE AI RESPONSE
            # --------------------------------------------------

            with st.chat_message("assistant"):

                with st.spinner(
                    "🤖 AI is analyzing your question..."
                ):

                    completion = client.chat.completions.create(

                        model="openai/gpt-oss-20b",

                        messages=[

                            {
                                "role": "system",

                                "content": context_prompt

                            },

                            *st.session_state.messages

                        ],

                        temperature=0.5,

                        max_completion_tokens=1500

                    )


                    # IMPORTANT: Correct response indexing

                    response_text = (
                        completion.choices[0].message.content
                    )


                    st.markdown(response_text)


            # --------------------------------------------------
            # SAVE AI RESPONSE
            # --------------------------------------------------

            st.session_state.messages.append({

                "role": "assistant",

                "content": response_text

            })


        except Exception as e:

            st.error(
                f"Groq AI Error: {str(e)}"
            )


# ==========================================================
# 9. FOOTER
# ==========================================================

st.write("---")

st.markdown(
    """
    <div style="text-align:center;">

    <h4>📈 Stock Analysis AI Agent</h4>

    <p>
    Powered by Streamlit, Yahoo Finance and Groq AI
    </p>

    <p>
    Financial data may be delayed or incomplete.
    This application is for educational and informational purposes.
    </p>

    </div>
    """,

    unsafe_allow_html=True
)