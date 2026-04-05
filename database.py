import pandas as pd
import sqlite3

# Load dataset
df = pd.read_csv("C:/Users/matha/Downloads/uber_eats_project/Zomato-data-.csv")

# Connect database
conn = sqlite3.connect("restaurants.db")

# Save dataframe to SQL
df.to_sql("restaurants", conn, if_exists="replace", index=False)

print("Database created successfully")

conn.close()