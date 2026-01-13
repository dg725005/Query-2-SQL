import openai
import dotenv
import pandas as pd
import sqlite3
import streamlit as st
import os

dotenv.load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
# Setup Client
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = openai.OpenAI(api_key=api_key)
OPENAI_MODEL = "gpt-3.5-turbo"

# Function to get schema from the dataframe directly
def get_schema_from_df(df, table_name):
    cols = ", ".join([f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)])
    return f"Table: {table_name}, Columns: {cols}"

def generate_sql_query(user_query, schema_string):    
    try:
        system_message = {
            "role": "system",
            "content": (
                f"You are an expert SQL generator. Translate natural language into SQLite queries. "
                f"The database schema is: {schema_string}. "
                "Only return the SQL code, no explanations."
            )
        }

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[system_message, {"role": "user", "content": user_query}],
            temperature=0,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# --- UI Setup ---
st.set_page_config(page_title="SQL Solver", layout="centered")
st.title("SQL Solver")
st.subheader("Upload a CSV and ask questions in plain English")

with st.form(key='submit_csv'):
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    user_query = st.text_input("What do you want to know? (e.g., 'Show me the top 5 rows')")
    submit_button = st.form_submit_button(label='Generate & Run SQL')

if submit_button:
    if uploaded_file and user_query:
        # 1. Load Data
        df = pd.read_csv(uploaded_file)
        table_name = 'tableQ'
        
        # 2. Create Schema for AI
        schema_string = get_schema_from_df(df, table_name)
        
        # 3. Generate SQL
        generated_sql = generate_sql_query(user_query, schema_string)
        
        # Clean SQL output (remove markdown code blocks if AI adds them)
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        st.code(generated_sql, language='sql')

        # 4. Execute SQL on the data
        try:
            conn = sqlite3.connect(":memory:") # Use memory for speed
            df.to_sql(table_name, conn, index=False, if_exists='replace')
            
            result_df = pd.read_sql_query(generated_sql, conn)
            
            st.success("Query Results:")
            st.dataframe(result_df)
            conn.close()
        except Exception as e:
            st.error(f"Failed to execute SQL: {e}")
    else:
        st.warning("Please upload a file and enter a query.")