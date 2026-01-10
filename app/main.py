"""
Investment Tracker V2 - Main Streamlit App.

Portfolio tracking dashboard with real-time pricing and analytics.
"""

import streamlit as st


# Page configuration
st.set_page_config(
    page_title="Investment Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .big-metric {
        font-size: 2rem !important;
        font-weight: bold;
    }
    .positive {
        color: #00c853;
    }
    .negative {
        color: #d32f2f;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Main page content
st.title("📊 Investment Tracker")
st.markdown("Track your portfolio across stocks, mutual funds, and more.")

st.info("👈 Use the sidebar to navigate between pages")

st.markdown("""
### Features
- 📈 **Dashboard**: Overview with KPIs and charts
- 💼 **Holdings**: Detailed view of all holdings
- 📊 **Trends**: Portfolio value over time
- ⬆️ **Upload**: Add new monthly data
- 📥 **Export**: Download reports
""")

st.markdown("---")
st.caption("Investment Tracker V2 - Built with Streamlit")
