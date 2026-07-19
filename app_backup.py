import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Orion Restaurant Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("restaurants.db")

# ---------------- DATABASE HELPERS ---------------- #

@st.cache_resource
def get_connection():
    """Return a cached SQLite connection (thread‑safe with check_same_thread=False)."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def get_table_columns(conn, table_name="restaurants"):
    """Return list of column names for the given table."""
    query = f"PRAGMA table_info({table_name})"
    df = pd.read_sql(query, conn)
    return df["name"].tolist()


def get_cost_column(conn):
    """Find the column that likely contains cost/price information."""
    columns = get_table_columns(conn)
    candidates = ["approx_cost_for_two_people", "approx_cost", "cost", "price", "avg_cost"]
    for col in candidates:
        if col in columns:
            return col
    return None  # Not found


def get_distinct_values(conn, column_name):
    """Get distinct non‑null values for a column."""
    query = f'''
        SELECT DISTINCT "{column_name}" AS value
        FROM restaurants
        WHERE "{column_name}" IS NOT NULL
          AND TRIM(CAST("{column_name}" AS TEXT)) != ''
        ORDER BY value
    '''
    df = pd.read_sql(query, conn)
    return df["value"].tolist()


# ---------------- FILTER QUERY ---------------- #

def build_filtered_restaurant_query(filters):
    base_query = 'SELECT * FROM restaurants WHERE 1 = 1'
    params = []

    if filters["restaurant_type"] != "All":
        base_query += ' AND "listed_in(type)" = ?'
        params.append(filters["restaurant_type"])

    if filters["online_order"] != "All":
        base_query += " AND online_order = ?"
        params.append(filters["online_order"])

    if filters["book_table"] != "All":
        base_query += " AND book_table = ?"
        params.append(filters["book_table"])

    if filters["min_votes"] > 0:
        base_query += " AND votes >= ?"
        params.append(filters["min_votes"])

    if filters["min_rating"] > 0:
        base_query += " AND rate NOT IN ('NEW', '-')"
        base_query += " AND CAST(SUBSTR(rate,1,3) AS FLOAT) >= ?"
        params.append(filters["min_rating"])

    if filters["search_name"] != "":
        base_query += " AND name LIKE ?"
        params.append(f"%{filters['search_name']}%")

    base_query += " ORDER BY votes DESC LIMIT 200"
    return base_query, params


# ---------------- BUSINESS QUESTIONS ---------------- #

def get_business_questions():
    return [
        "1. Highest Average Rating Restaurant Type",
        "2. Most Popular Restaurant Types",
        "3. Online Order Impact on Rating",
        "4. Table Booking Impact on Rating",
        "5. Best Price Range",
        "6. Most Common Restaurant Types",
        "7. Top Rated Restaurant Types",
        "8. Niche Opportunities",
        "9. Cost vs Rating Analysis",
        "10. Top Premium Restaurants",
        "11. Restaurants with Highest Votes",
        "12. High Rating & High Vote Restaurants",
        "13. Average Rating by Online Order",
        "14. Highest Rated Restaurant Types by Votes",
        "15. Most Common Price Range",
    ]


def get_business_query(question, cost_col):
    """Return SQL query for a business question, using the correct cost column."""
    base_queries = {
        "1. Highest Average Rating Restaurant Type": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY "listed_in(type)"
            ORDER BY Avg_Rating DESC
        """,
        "2. Most Popular Restaurant Types": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   COUNT(*) AS Total_Restaurants
            FROM restaurants
            GROUP BY "listed_in(type)"
            ORDER BY Total_Restaurants DESC
        """,
        "3. Online Order Impact on Rating": """
            SELECT online_order,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY online_order
        """,
        "4. Table Booking Impact on Rating": """
            SELECT book_table,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY book_table
        """,
        "5. Best Price Range": """
            SELECT {cost_col} AS Price_Range,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY {cost_col}
            ORDER BY Avg_Rating DESC
            LIMIT 10
        """,
        "6. Most Common Restaurant Types": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   COUNT(*) AS Frequency
            FROM restaurants
            GROUP BY "listed_in(type)"
            ORDER BY Frequency DESC
        """,
        "7. Top Rated Restaurant Types": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY "listed_in(type)"
            ORDER BY Avg_Rating DESC
            LIMIT 10
        """,
        "8. Niche Opportunities": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   COUNT(*) AS Count,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY "listed_in(type)"
            HAVING Count BETWEEN 5 AND 20
            ORDER BY Avg_Rating DESC
        """,
        "9. Cost vs Rating Analysis": """
            SELECT {cost_col} AS Cost,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY {cost_col}
            ORDER BY Cost
        """,
        "10. Top Premium Restaurants": """
            SELECT name,
                   {cost_col} AS Cost,
                   CAST(SUBSTR(rate,1,3) AS FLOAT) AS Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
              AND {cost_col} > 1000
            ORDER BY Rating DESC
            LIMIT 20
        """,
        "11. Restaurants with Highest Votes": """
            SELECT name,
                   votes,
                   CAST(SUBSTR(rate,1,3) AS FLOAT) AS Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            ORDER BY votes DESC
            LIMIT 20
        """,
        "12. High Rating & High Vote Restaurants": """
            SELECT name,
                   votes,
                   CAST(SUBSTR(rate,1,3) AS FLOAT) AS Rating
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
              AND votes > 500
              AND CAST(SUBSTR(rate,1,3) AS FLOAT) > 4.0
            ORDER BY Rating DESC, votes DESC
            LIMIT 20
        """,
        "13. Average Rating by Online Order": """
            SELECT online_order,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating,
                   COUNT(*) AS Count
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY online_order
        """,
        "14. Highest Rated Restaurant Types by Votes": """
            SELECT "listed_in(type)" AS Restaurant_Type,
                   AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating,
                   SUM(votes) AS Total_Votes
            FROM restaurants
            WHERE rate NOT IN ('NEW', '-')
            GROUP BY "listed_in(type)"
            HAVING Total_Votes > 1000
            ORDER BY Avg_Rating DESC
        """,
        "15. Most Common Price Range": """
            SELECT {cost_col} AS Price_Range,
                   COUNT(*) AS Frequency
            FROM restaurants
            GROUP BY {cost_col}
            ORDER BY Frequency DESC
            LIMIT 10
        """,
    }
    query = base_queries.get(question)
    if query and cost_col:
        query = query.format(cost_col=cost_col)
    return query


# ---------------- SIDEBAR ---------------- #

st.sidebar.title("🚀 Orion AI")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "🏠 Dashboard",
        "📊 Business Analytics",
        "🤖 AI Command Center",
        "📈 Sales Forecast",
        "📦 Inventory",
        "😊 Customer Insights",
        "🏪 Competitor Analysis",
        "⚙️ Settings",
    ]
)

if not DB_PATH.exists():
    st.error("restaurants.db not found. Please place the database file in the same directory.")
    st.stop()

# Open connection once per page load (cached, thread‑safe)
conn = get_connection()

# ---------------- DASHBOARD ---------------- #

if page == "🏠 Dashboard":
    st.title("🚀 Orion Restaurant Intelligence")
    st.caption("AI-Powered Restaurant Business Intelligence Platform")
    st.success("Welcome to Orion AI Command Center")

    # Detect cost column (do it here, not globally)
    cost_col = get_cost_column(conn)
    if cost_col is None:
        st.warning("Could not find a cost/price column. Some metrics may be unavailable.")

    # KPI Metrics
    total = pd.read_sql("SELECT COUNT(*) FROM restaurants", conn).iloc[0, 0]
    avg_rating = pd.read_sql("""
        SELECT AVG(CAST(SUBSTR(rate,1,3) AS FLOAT))
        FROM restaurants
        WHERE rate NOT IN ('NEW','-')
    """, conn).iloc[0, 0]

    avg_cost = None
    if cost_col:
        try:
            avg_cost = pd.read_sql(f"SELECT AVG({cost_col}) FROM restaurants", conn).iloc[0, 0]
        except Exception:
            pass

    online_orders = pd.read_sql("""
        SELECT COUNT(*)
        FROM restaurants
        WHERE online_order='Yes'
    """, conn).iloc[0, 0]
    online_percent = (online_orders / total) * 100 if total > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🍽 Restaurants", f"{total:,}")
    k2.metric("⭐ Rating", f"{avg_rating:.2f}" if avg_rating else "N/A")
    k3.metric("💰 Avg Cost", f"₹{avg_cost:.0f}" if avg_cost else "N/A")
    k4.metric("🛵 Online Orders", f"{online_percent:.1f}%")

    st.subheader("Restaurant Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    restaurant_type = filter_col1.selectbox(
        "Restaurant Type",
        ["All"] + get_distinct_values(conn, "listed_in(type)"),
    )
    online_order = filter_col2.selectbox(
        "Online Order",
        ["All"] + get_distinct_values(conn, "online_order"),
    )
    book_table = filter_col3.selectbox(
        "Table Booking",
        ["All"] + get_distinct_values(conn, "book_table"),
    )

    filter_col4, filter_col5 = st.columns(2)
    min_votes = int(
        filter_col4.number_input(
            "Minimum Votes",
            min_value=0,
            value=0,
            step=50
        )
    )
    min_rating = float(
        filter_col5.slider(
            "Minimum Rating",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.1
        )
    )
    search_name = st.text_input("🔍 Search Restaurant Name")

    filters = {
        "restaurant_type": restaurant_type,
        "online_order": online_order,
        "book_table": book_table,
        "min_votes": min_votes,
        "min_rating": min_rating,
        "search_name": search_name,
    }

    filtered_query, params = build_filtered_restaurant_query(filters)
    filtered_df = pd.read_sql(filtered_query, conn, params=params)

    # Chart: Top Restaurant Types
    chart_query = """
        SELECT "listed_in(type)" AS Restaurant_Type,
               COUNT(*) AS Total_Restaurants
        FROM restaurants
        GROUP BY "listed_in(type)"
        ORDER BY Total_Restaurants DESC
        LIMIT 10
    """
    chart_df = pd.read_sql(chart_query, conn)
    fig = px.bar(
        chart_df,
        x="Restaurant_Type",
        y="Total_Restaurants",
        title="Top Restaurant Types"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Filtered Restaurant Data")
    st.dataframe(filtered_df, use_container_width=True)

# ---------------- BUSINESS ANALYTICS ---------------- #

elif page == "📊 Business Analytics":
    st.title("🔍 Business Questions Analysis")
    question = st.selectbox(
        "Select Business Question",
        get_business_questions()
    )
    # Detect cost column for queries that need it
    cost_col = get_cost_column(conn)
    query = get_business_query(question, cost_col)
    if query is None:
        st.error("Query not implemented for this question or cost column missing.")
    else:
        try:
            df = pd.read_sql(query, conn)
            st.subheader(f"Results: {question}")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Query Error: {e}")

# ---------------- OTHER PAGES ---------------- #

elif page == "🤖 AI Command Center":
    st.title("🤖 Orion AI Command Center")
    st.info("Manage all AI agents from one place.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("📈 Sales Forecast")
        st.write("Predict future restaurant sales.")
        st.button("Open Sales Agent")
    with col2:
        st.success("📦 Inventory")
        st.write("Monitor stock and inventory.")
        st.button("Open Inventory Agent")
    with col3:
        st.success("😊 Customer Insights")
        st.write("Analyze customer behaviour.")
        st.button("Open Customer Agent")

elif page == "📈 Sales Forecast":
    st.title("📈 Sales Forecast")
    st.info("Coming Soon - AI Sales Prediction")

elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    st.info("Coming Soon - Smart Inventory Agent")

elif page == "😊 Customer Insights":
    st.title("😊 Customer Insights")
    st.info("Coming Soon - Customer Analytics")

elif page == "🏪 Competitor Analysis":
    st.title("🏪 Competitor Analysis")
    st.info("Coming Soon - Competitor Intelligence")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.write("Application settings will be available here.")

# Connection is automatically closed when script ends – but we can explicitly close if needed.
# (Streamlit will close it at the end of the run anyway)