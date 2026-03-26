import pandas as pd
import mysql.connector

df = pd.read_csv("C:/Users/matha/Downloads/uber_eats_project/data/cleaned_uber_Eats_data.csv")

df['rate'] = df['rate'].astype(str).str.replace('/5', '', regex=False)
df['rate'] = df['rate'].str.extract(r'(\d+\.\d+|\d+)').astype(float) 

# Required columns
df = df[['name','location','cuisines','rate','approx_cost(for two people)','online_order','book_table']]

# Rename columns
df.columns = ['restaurant_name','location','cuisines','rate','approx_cost_for_two','online_order','book_table']

# Clean cost column (remove comma)
df['approx_cost_for_two'] = df['approx_cost_for_two'].astype(str).str.replace(',', '').astype(float)

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mathankumar@63",
    database="uber_eats"
)

cursor = conn.cursor()

sql = """
INSERT INTO restaurants
(restaurant_name, location, cuisines, rate, approx_cost_for_two, online_order, book_table)
VALUES (%s,%s,%s,%s,%s,%s,%s)
"""

for row in df.itertuples(index=False):
    cursor.execute(sql, tuple(row))

conn.commit()

print("Data inserted successfully!")