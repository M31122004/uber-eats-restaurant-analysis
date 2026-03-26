import streamlit as st
import pandas as pd
import mysql.connector

st.set_page_config(page_title="Uber Eats Intelligence System", layout="wide")

# -----------------------------
# MySQL Connection
# -----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mathankumar@63",
    database="uber_eats"
)

# -----------------------------
# TITLE
# -----------------------------
st.title("🍔 Uber Eats Bangalore Restaurant Intelligence System")

# -----------------------------
# DATASET PREVIEW
# -----------------------------
st.header("Restaurant Dataset Preview")

query = "SELECT * FROM restaurants"
df = pd.read_sql(query, conn)

st.dataframe(df.head(20))


# -----------------------------
# FILTER SECTION
# -----------------------------
st.sidebar.header("Filter Restaurants")

location = st.sidebar.selectbox(
    "Select Location",
    df["location"].dropna().unique()
)

query_filter = f"""
SELECT * FROM restaurants
WHERE location = '{location}'
LIMIT 20
"""

filtered_df = pd.read_sql(query_filter, conn)

st.header(f"Restaurants in {location}")
st.dataframe(filtered_df)


# -----------------------------
# BUSINESS QUESTIONS
# -----------------------------
st.header("📊 Business Insights")

# Question 1
st.subheader("1️⃣ Locations with Highest Average Ratings")

query1 = """
SELECT location, AVG(rate) AS avg_rating
FROM restaurants
GROUP BY location
ORDER BY avg_rating DESC
LIMIT 10
"""

df1 = pd.read_sql(query1, conn)
st.dataframe(df1)


# Question 2
st.subheader("2️⃣ Locations with Most Restaurants")

query2 = """
SELECT location, COUNT(*) AS total_restaurants
FROM restaurants
GROUP BY location
ORDER BY total_restaurants DESC
LIMIT 10
"""

df2 = pd.read_sql(query2, conn)
st.dataframe(df2)


# Question 3
st.subheader("3️⃣ Does Online Ordering Improve Ratings?")

query3 = """
SELECT online_order, AVG(rate) AS avg_rating
FROM restaurants
GROUP BY online_order
"""

df3 = pd.read_sql(query3, conn)
st.dataframe(df3)


# Question 4
st.subheader("4️⃣ Table Booking Impact on Ratings")

query4 = """
SELECT book_table, AVG(rate) AS avg_rating
FROM restaurants
GROUP BY book_table
"""

df4 = pd.read_sql(query4, conn)
st.dataframe(df4)


# Question 5
st.subheader("5️⃣ Average Cost vs Rating")

query5 = """
SELECT approx_cost_for_two, AVG(rate) AS avg_rating
FROM restaurants
GROUP BY approx_cost_for_two
ORDER BY approx_cost_for_two
LIMIT 10
"""

df5 = pd.read_sql(query5, conn)
st.dataframe(df5)


# Question 6
st.subheader("6️⃣ Most Common Cuisines")

query6 = """
SELECT cuisines, COUNT(*) AS total
FROM restaurants
GROUP BY cuisines
ORDER BY total DESC
LIMIT 10
"""

df6 = pd.read_sql(query6, conn)
st.dataframe(df6)


# Question 7
st.subheader("7️⃣ Highest Rated Restaurants")

query7 = """
SELECT restaurant_name, rate, location
FROM restaurants
ORDER BY rate DESC
LIMIT 10
"""

df7 = pd.read_sql(query7, conn)
st.dataframe(df7)


# Question 8
st.subheader("8️⃣ Restaurants Offering Online Ordering")

query8 = """
SELECT restaurant_name, location
FROM restaurants
WHERE online_order = 'Yes'
LIMIT 10
"""

df8 = pd.read_sql(query8, conn)
st.dataframe(df8)


# Question 9
st.subheader("9️⃣ Restaurants with Table Booking")

query9 = """
SELECT restaurant_name, location
FROM restaurants
WHERE book_table = 'Yes'
LIMIT 10
"""

df9 = pd.read_sql(query9, conn)
st.dataframe(df9)


# Question 10
st.subheader("🔟 Premium Restaurants (High Cost)")

query10 = """
SELECT restaurant_name, approx_cost_for_two
FROM restaurants
ORDER BY approx_cost_for_two DESC
LIMIT 10
"""

df10 = pd.read_sql(query10, conn)
st.dataframe(df10)