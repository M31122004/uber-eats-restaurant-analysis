import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Uber Eats Intelligence", layout="wide")

DB_PATH = Path("restaurants.db")

ORDER_JSON_CANDIDATES = [
    Path(r"C:\Users\matha\Downloads\uber_eats_project\orders\orders.json"),
]


# ---------------- DATABASE ---------------- #

def get_connection():
    return sqlite3.connect(DB_PATH)


def table_exists(conn, table_name):
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """
    row = conn.execute(query, (table_name,)).fetchone()
    return row is not None


def get_distinct_values(conn, column_name):
    query = f'''
        SELECT DISTINCT "{column_name}" AS value
        FROM restaurants
        WHERE "{column_name}" IS NOT NULL
          AND TRIM(CAST("{column_name}" AS TEXT)) != ''
        ORDER BY value
    '''
    df = pd.read_sql(query, conn)
    return df["value"].tolist()


def load_dashboard_metrics(conn):
    total_query = "SELECT COUNT(*) AS total FROM restaurants"

    rating_query = """
        SELECT AVG(CAST(SUBSTR(rate, 1, 3) AS FLOAT)) AS avg_rating
        FROM restaurants
        WHERE rate NOT IN ('NEW', '-')
    """

    total = pd.read_sql(total_query, conn).iloc[0, 0]
    avg_rating = pd.read_sql(rating_query, conn).iloc[0, 0]

    return total, avg_rating


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


def get_business_query(question):

    queries = {

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

    }

    return queries[question]


# ---------------- SIDEBAR ---------------- #

st.sidebar.title("📌 Navigation")

page = st.sidebar.selectbox(

    "Go to",

    ["Dashboard", "Business Q&A"]

)

if not DB_PATH.exists():

    st.error("restaurants.db was not found.")

    st.stop()


# ---------------- DASHBOARD ---------------- #

if page == "Dashboard":

    st.title("🍔 Uber Eats Restaurant Intelligence Dashboard")

    st.success("Interactive Restaurant Analytics Platform")

    conn = get_connection()

    total, avg_rating = load_dashboard_metrics(conn)

    col1, col2 = st.columns(2)

    col1.metric("Total Restaurants", total)

    col2.metric("Average Rating", round(avg_rating, 2))

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

    # ---------------- CHART ---------------- #

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

    # ---------------- TABLE ---------------- #

    st.subheader("Filtered Restaurant Data")

    st.dataframe(filtered_df, use_container_width=True)

    conn.close()


# ---------------- BUSINESS Q&A ---------------- #

elif page == "Business Q&A":

    st.title("🔍 Business Questions Analysis")

    question = st.selectbox(

        "Select Business Question",

        get_business_questions()

    )

    conn = get_connection()

    try:

        query = get_business_query(question)

        df = pd.read_sql(query, conn)

        st.subheader(f"Results: {question}")

        st.dataframe(df, use_container_width=True)

    except Exception as e:

        st.error(f"Query Error: {e}")

    finally:

        conn.close()