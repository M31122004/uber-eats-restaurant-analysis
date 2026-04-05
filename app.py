import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Uber Eats Intelligence", layout="wide")

# Database connection
def get_connection():
    return sqlite3.connect("restaurants.db")

# ---------------- DASHBOARD ---------------- #

st.sidebar.title("📌 Navigation")
page = st.sidebar.selectbox("Go to", ["Dashboard", "Business Q&A"])

if page == "Dashboard":

    st.title("📊 Uber Eats Bangalore Dashboard")

    conn = get_connection()

    col1,col2 = st.columns(2)

    total = pd.read_sql("SELECT COUNT(*) FROM restaurants",conn).iloc[0,0]

    avg_rating = pd.read_sql("""
    SELECT AVG(CAST(SUBSTR(rate,1,3) AS FLOAT))
    FROM restaurants
    WHERE rate NOT LIKE 'NEW'
    AND rate NOT LIKE '-'
    """,conn).iloc[0,0]

    col1.metric("Total Restaurants",total)
    col2.metric("Average Rating",round(avg_rating,2))

    st.subheader("Restaurant Data Preview")

    df = pd.read_sql("SELECT * FROM restaurants LIMIT 20",conn)

    st.dataframe(df)

    conn.close()

# ---------------- BUSINESS Q&A ---------------- #

elif page == "Business Q&A":

    st.title("🔍 Business Questions Analysis")

    question = st.selectbox(
        "Select Business Question",
        [
        "1. Highest Average Rating Restaurant Type",
        "2. Most Popular Restaurant Types",
        "3. Online Order Impact on Rating",
        "4. Table Booking Impact on Rating",
        "5. Best Price Range",
        "6. Most Common Restaurant Types",
        "7. Top Rated Restaurant Types",
        "8. Niche Opportunities",
        "9. Cost vs Rating Analysis",
        "10. Top Premium Restaurants"
        ]
    )

    conn = get_connection()

    try:

        if "1." in question:

            query = """
            SELECT "listed_in(type)" AS Restaurant_Type,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY "listed_in(type)"
            ORDER BY Avg_Rating DESC
            """

        elif "2." in question:

            query = """
            SELECT "listed_in(type)" AS Restaurant_Type,
            COUNT(*) AS Total_Restaurants
            FROM restaurants
            GROUP BY "listed_in(type)"
            ORDER BY Total_Restaurants DESC
            """

        elif "3." in question:

            query = """
            SELECT online_order,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY online_order
            """

        elif "4." in question:

            query = """
            SELECT book_table,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY book_table
            """

        elif "5." in question:

            query = """
            SELECT "approx_cost(for two people)" AS Cost,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY "approx_cost(for two people)"
            ORDER BY Avg_Rating DESC
            LIMIT 10
            """

        elif "6." in question:

            query = """
            SELECT "listed_in(type)" AS Category,
            COUNT(*) AS Count
            FROM restaurants
            GROUP BY "listed_in(type)"
            ORDER BY Count DESC
            """

        elif "7." in question:

            query = """
            SELECT "listed_in(type)" AS Category,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY "listed_in(type)"
            ORDER BY Avg_Rating DESC
            """

        elif "8." in question:

            query = """
            SELECT "listed_in(type)" AS Category,
            COUNT(*) AS Count,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY "listed_in(type)"
            HAVING Count < 10
            ORDER BY Avg_Rating DESC
            """

        elif "9." in question:

            query = """
            SELECT "approx_cost(for two people)" AS Cost,
            AVG(CAST(SUBSTR(rate,1,3) AS FLOAT)) AS Avg_Rating
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            GROUP BY "approx_cost(for two people)"
            ORDER BY Avg_Rating DESC
            """

        elif "10." in question:

            query = """
            SELECT name AS Name,
            CAST(SUBSTR(rate,1,3) AS FLOAT) AS Rating,
            "approx_cost(for two people)" AS Price_for_Two
            FROM restaurants
            WHERE rate NOT LIKE 'NEW'
            AND rate NOT LIKE '-'
            ORDER BY Rating DESC
            LIMIT 10
            """

        df = pd.read_sql(query,conn)

        st.subheader(f"Results: {question}")

        st.dataframe(df)

    except Exception as e:

        st.error(f"Query Error: {e}")

    finally:

        conn.close()