import streamlit as st
import pandas as pd
import mysql.connector

# -------------------------------
#  Database connection
# -------------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",   # Change if needed
        user="root",        # Your MySQL username
        password="zaid8765",  # Your MySQL password
        database="food_waste"   # Your DB name
    )

def run_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# -------------------------------
#  Streamlit UI
# -------------------------------
st.set_page_config(page_title="🍲 Food Donation Dashboard", layout="wide")
st.title("🍲 Food Donation Dashboard")
st.markdown("This dashboard runs **15 SQL queries** on the Food Distribution database and shows results as tables and charts.")

# -------------------------------
#  Queries dictionary
# -------------------------------
queries = {
    "1. Providers vs Receivers per City": """
        SELECT City,
               SUM(providers_count) AS providers_count,
               SUM(receivers_count) AS receivers_count
        FROM (
            SELECT City, COUNT(*) AS providers_count, 0 AS receivers_count 
            FROM providers GROUP BY City
            UNION ALL
            SELECT City, 0 AS providers_count, COUNT(*) AS receivers_count 
            FROM receivers GROUP BY City
        ) AS combined
        GROUP BY City
        ORDER BY City;
    """,

    "2. Provider type with most food listed": """
        SELECT Provider_Type, SUM(Quantity) AS total_quantity
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY Provider_Type
        ORDER BY total_quantity DESC
        LIMIT 1;
    """,

    "3. Top 5 most listed food items": """
        SELECT Food_Name, SUM(Quantity) AS total_quantity
        FROM food_listings
        GROUP BY Food_Name
        ORDER BY total_quantity DESC
        LIMIT 5;
    """,

    "4. Top 10 receivers by completed claims": """
        SELECT r.Receiver_ID, r.Name, r.Type, r.City,
               SUM(f.Quantity) AS total_quantity_claimed,
               COUNT(*) AS completed_claims
        FROM claims c
        JOIN receivers r ON r.Receiver_ID = c.Receiver_ID
        JOIN food_listings f ON f.Food_ID = c.Food_ID
        WHERE c.Status = 'Completed'
        GROUP BY r.Receiver_ID, r.Name, r.Type, r.City
        ORDER BY total_quantity_claimed DESC, completed_claims DESC
        LIMIT 10;
    """,

    "5. Total listed vs currently available food": """
        WITH total_listed AS (
          SELECT SUM(Quantity) AS total_qty FROM food_listings
        ),
        unexpired AS (
          SELECT Food_ID, Quantity
          FROM food_listings
          WHERE Expiry_Date IS NOT NULL AND DATE(Expiry_Date) >= CURDATE()
        ),
        claimed_completed AS (
          SELECT Food_ID FROM claims WHERE Status='Completed'
        )
        SELECT (SELECT total_qty FROM total_listed) AS total_listed_qty,
               (SELECT SUM(Quantity) FROM unexpired 
                WHERE Food_ID NOT IN (SELECT Food_ID FROM claimed_completed)) AS currently_available_qty;
    """,

    "6. Top 5 cities with most food listed": """
        SELECT location, SUM(Quantity) AS total_quantity
        FROM food_listings
        GROUP BY location
        ORDER BY total_quantity DESC
        LIMIT 5;
    """,

    "7. Top 10 most claimed food items": """
        SELECT f.Food_Name, COUNT(*) AS claim_count
        FROM claims c
        JOIN food_listings f ON f.Food_ID = c.Food_ID
        WHERE c.Status='Completed'
        GROUP BY f.Food_Name
        ORDER BY claim_count DESC
        LIMIT 10;
    """,

    "8. Providers with most completed claims": """
        SELECT p.Provider_ID, p.Name, p.Type AS Provider_Type, p.City,
       COUNT(*) AS completed_claims
FROM claims c
JOIN food_listings f ON f.Food_ID = c.Food_ID
JOIN providers p ON p.Provider_ID = f.Provider_ID
WHERE c.Status = 'Completed'
GROUP BY p.Provider_ID, p.Name, p.Type, p.City
ORDER BY completed_claims DESC
LIMIT 10;
    """,

    "9. Number of claims per status": """
        SELECT Status, COUNT(*) AS total_claims
        FROM claims
        GROUP BY Status;
    """,

    "10. Total food claimed by city": """
        SELECT r.City, SUM(f.Quantity) AS total_claimed
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN food_listings f ON f.Food_ID = c.Food_ID
        WHERE c.Status='Completed'
        GROUP BY r.City
        ORDER BY total_claimed DESC;
    """,

    "11. Receivers who claimed more than 5 times": """
        SELECT r.Receiver_ID, r.Name, r.City, COUNT(*) AS completed_claims
        FROM claims c
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
        WHERE c.Status='Completed'
        GROUP BY r.Receiver_ID, r.Name, r.City
        HAVING COUNT(*) > 5
        ORDER BY completed_claims DESC;
    """,

    "12. Providers who listed more than 100 items": """
        SELECT p.Provider_ID, p.Name, p.City, SUM(f.Quantity) AS total_listed
        FROM providers p
        JOIN food_listings f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Provider_ID, p.Name, p.City
        HAVING SUM(f.Quantity) > 100
        ORDER BY total_listed DESC;
    """,

    "13. Expired food items": """
        SELECT Food_Name, Quantity, Expiry_Date
        FROM food_listings
        WHERE Expiry_Date < CURDATE();
    """,

    "14. Claims made in last 30 days": """
        SELECT c.Claim_ID, c.Status, c.Timestamp,
       r.Name AS Receiver_Name, f.Food_Name, f.Quantity
FROM claims c
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
JOIN food_listings f ON c.Food_ID = f.Food_ID
WHERE c.Timestamp >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY c.Timestamp DESC;
    """,

    "15. Top providers by food type contribution": """
        SELECT p.Type, p.Name, SUM(f.Quantity) AS total_quantity
FROM providers p
JOIN food_listings f ON p.Provider_ID = f.Provider_ID
GROUP BY p.Type, p.Name
ORDER BY total_quantity DESC
LIMIT 10;
    """
}

# -------------------------------
#  Select and Run Query
# -------------------------------
choice = st.selectbox("🔎 Select Query", list(queries.keys()))

if st.button("Run Query"):
    df = run_query(queries[choice])
    st.subheader(f"Results: {choice}")
    st.dataframe(df)

    # Auto chart suggestion
    if not df.empty:
        if "City" in df.columns and "total_quantity" in df.columns:
            st.bar_chart(df.set_index("City")["total_quantity"])
        elif "Food_Name" in df.columns and ("total_quantity" in df.columns or "claim_count" in df.columns):
            st.bar_chart(df.set_index("Food_Name"))
        elif "Status" in df.columns and "total_claims" in df.columns:
            st.bar_chart(df.set_index("Status"))
        elif "Claim_Date" in df.columns:
            df_sorted = df.sort_values("Claim_Date")
            st.line_chart(df_sorted.set_index("Claim_Date")["Quantity"] if "Quantity" in df_sorted.columns else df_sorted.set_index("Claim_Date"))
        else:
            st.info("📊 No chart available for this query")
