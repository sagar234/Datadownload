# app.py
import streamlit as st
import pandas as pd
import psycopg2

# Function to create a connection to PostgreSQL database
def create_connection():
    try:
        # Replace the following connection string with your PostgreSQL connection details
        conn = psycopg2.connect(
            host="34.100.223.97",
            database="trips",
            user="postgres",
            password="theimm0rtaL",
            port="5432"
        )
        st.success("Connected to the PostgreSQL database")
        return conn
    except psycopg2.Error as e:
        st.error(f"Error connecting to the PostgreSQL database: {e}")
        return None

# Function to get a list of tables in the connected database
def get_table_list(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cursor.fetchall()
        return [table[0] for table in tables]
    except psycopg2.Error as e:
        st.error(f"Error fetching table list: {e}")
        return None

# Function to get unique values for a given column in a table
def get_unique_values(conn, table_name, column_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name};")
        values = cursor.fetchall()
        return ['All'] + [value[0] for value in values]
    except psycopg2.Error as e:
        st.error(f"Error fetching unique values: {e}")
        return None

# Function to get column names for a given table
def get_column_names(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        column_names = [desc[0] for desc in cursor.description]
        return column_names
    except psycopg2.Error as e:
        st.error(f"Error fetching column names: {e}")
        return None

# Function to get client list based on selected city
def get_clients_for_city(conn, table_name, city_code):
    try:
        cursor = conn.cursor()
        if city_code == 'All':
            cursor.execute(f"SELECT DISTINCT client FROM {table_name};")
        else:
            cursor.execute(f"SELECT DISTINCT client FROM {table_name} WHERE city_code = '{city_code}';")
        clients = cursor.fetchall()
        return ['All'] + [client[0] for client in clients]
    except psycopg2.Error as e:
        st.error(f"Error fetching clients for the selected city: {e}")
        return None

# Function to get client offices based on selected client
def get_client_offices_for_client(conn, table_name, client):
    try:
        cursor = conn.cursor()
        if client == 'All':
            cursor.execute(f"SELECT DISTINCT client_office FROM {table_name};")
        else:
            cursor.execute(f"SELECT DISTINCT client_office FROM {table_name} WHERE client = '{client}';")
        client_offices = cursor.fetchall()
        return ['All'] + [client_office[0] for client_office in client_offices]
    except psycopg2.Error as e:
        st.error(f"Error fetching client offices for the selected client: {e}")
        return None

# Function to perform a search based on user input
def perform_search(conn, table_name, city_code, start_date, end_date, billing_model, vehicle_reg_no, client, client_office):
    try:
        cursor = conn.cursor()

        # Build the SQL query based on user input
        query = f"SELECT * FROM {table_name} WHERE 1=1"

        # Add optional conditions
        if city_code and city_code != 'All':
            query += f" AND city_code = '{city_code}'"
        if start_date:
            query += f" AND trip_date >= '{start_date}'"
        if end_date:
            query += f" AND trip_date <= '{end_date}'"
        if billing_model:
            query += f" AND billing_model = '{billing_model}'"
        if vehicle_reg_no:
            query += f" AND vehicle_reg_no = '{vehicle_reg_no}'"
        if client and client != 'All':
            query += f" AND client = '{client}'"
        if client_office and client_office != 'All':
            query += f" AND client_office = '{client_office}'"

        # Execute the query
        cursor.execute(query)
        data = cursor.fetchall()

        return data
    except psycopg2.Error as e:
        st.error(f"Error executing the query: {e}")
        return None

def main():
    st.title("Search Data in PostgreSQL Database")
    st.write("Connecting to the database...")

    # Database connection
    conn = create_connection()

    # Continue if the connection is successful
    if conn:
        st.write("Connection successful!")

        # Get a list of tables in the connected database
        table_list = get_table_list(conn)

        # Display the list of tables in a dropdown
        if table_list:
            st.write("Tables in the database:")
            selected_table = st.selectbox("Select a table:", table_list)

            # User input for additional filters
            city_list = get_unique_values(conn, selected_table, 'city_code')
            city_code = st.selectbox("Select City Code:", city_list) if city_list else None

            # Dynamic dropdown for clients based on selected city
            client_list = get_clients_for_city(conn, selected_table, city_code) if city_code else []
            client = st.selectbox("Select Client:", client_list) if client_list else None

            # Dynamic dropdown for client offices based on selected client
            client_office_list = get_client_offices_for_client(conn, selected_table, client) if client else []
            client_office = st.selectbox("Select Client Office:", client_office_list) if client_office_list else None

            # Date range for trip_date
            start_date = st.date_input("Select Start Date (optional):")
            end_date = st.date_input("Select End Date (optional):")

            billing_model = st.text_input("Enter Billing Model (optional):")
            vehicle_reg_no = st.text_input("Enter Vehicle Registration Number (optional):")

            # Search button
            if st.button("Search"):
                # Perform the search
                result = perform_search(
                    conn,
                    selected_table,
                    city_code,
                    start_date.strftime("%Y-%m-%d") if start_date else None,
                    end_date.strftime("%Y-%m-%d") if end_date else None,
                    billing_model,
                    vehicle_reg_no,
                    client,
                    client_office
                )

                # Display the result in table format
                if result is not None:
                    if result:  # Check if result is not an empty list
                        st.write("Search Result:")
                        column_names = get_column_names(conn, selected_table)
                        if column_names:
                            df_result = pd.DataFrame(result, columns=column_names)
                            st.write(df_result)

                            # Download button for exporting to Excel
                            csv = df_result.to_csv(index=False, encoding="utf-8")
                            st.download_button(
                                label="Download Excel File",
                                data=csv,
                                file_name=f"{selected_table}_search_result.csv",
                                key=f"{selected_table}_search_result"
                            )
                        else:
                            st.write("Error fetching column names.")
                    else:
                        st.write("No results found.")
                else:
                    st.write("Error occurred during the search.")

if __name__ == "__main__":
    main()
