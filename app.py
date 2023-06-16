import streamlit as st
import pandas as pd
import requests


DATATYPES = ["NUMBER","DECIMAL","NUMERIC","INT","INTEGER","BIGINT","SMALLINT","TINYINT","BYTEINT","FLOAT","FLOAT4","FLOAT8","DOUBLE","DOUBLE","PRECISION","REAL","VARCHAR","CHAR","CHARACTER","STRING","TEXT","BINARY","VARBINARY","BOOLEAN","DATE","DATETIME","TIME","TIMESTAMP","TIMESTAMP_LTZ","TIMESTAMP","TIMESTAMP_NTZ","TIMESTAMP","TIMESTAMP_TZ","TIMESTAMP","VARIANT","OBJECT","ARRAY","GEOGRAPHY","GEOMETRY"]

stacks = {
    "US": "https://connection.keboola.com/v2/storage/buckets/",
    "EU-N": "https://connection.north-europe.azure.keboola.com/v2/storage/buckets/",
    "EU-C": "https://connection.eu-central-1.keboola.com/v2/storage/buckets/"
    }

table_name = ""

help_body = """
    *Please check [Snowflake Datatype syntax](https://docs.snowflake.com/en/sql-reference/intro-summary-data-types)*
    """


# Define a class to represent a column
class Column:
    def __init__(self, name, data_type, length, nullable, primary_key):
        self.name = name
        self.data_type = data_type
        self.length = length
        self.nullable = nullable
        self.primary_key = primary_key

# Initialize an empty list to store the columns
st.cache_data(allow_output_mutation=True)
def get_columns():
    return []

# Generate API JSON from the columns
def generate_api_json(columns, table_name):
    primary_key_columns = [column.name for column in columns if column.primary_key]

    api_dict = {
        "name": table_name,
        "primaryKeysNames": primary_key_columns,
        "columns": []
    }

    for column in columns:
        if column.length:
            column_dict = {
                "name": column.name,
                "definition": {
                    "type": column.data_type,
                    "nullable": column.nullable,
                    "length": column.length
                }
            }
        else:
            column_dict = {
                "name": column.name,
                "definition": {
                    "type": column.data_type,
                    "nullable": column.nullable
                }
            }

        api_dict["columns"].append(column_dict)

    return api_dict

# Create the table using API
def create_table(api_url, api_json, storage_token):
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'X-StorageApi-Token': storage_token
    }

    response = requests.post(api_url, json=api_json, headers=headers, timeout=360)

    if response.status_code == 202:
        st.success('Table created successfully!')
    else:
        st.info("{}-{}".format(response, response.reason))
        st.error('Failed to create table. Please check the API endpoint and token.')
        st.info(response.text)


# Streamlit app
def main():

    # Sidebar
    st.sidebar.header("Keboola - Create Table Definition via API")
    stack = st.sidebar.radio("Select stack: ",["US", "EU-C", "EU-N"])
    storage_token = st.sidebar.text_input("Storage Token", type="password")
    table_name = st.sidebar.text_input('Table Name')
    bucket_name = st.sidebar.text_input('Bucket Name')

    # Set the title
    title = f"{bucket_name}.{table_name}"
    st.title(title)

    # Get the list of columns
    columns = get_columns()

    URL = stacks[stack]+title+"/tables-definition"

    if st.button('Clear All Rows', key='clear_rows_button'):
        columns.clear()

    # Add column form
    st.header('Add Column')
    st.markdown(help_body)
    column_name = st.text_input('Column Name')
    col1, col2 = st.columns(2)
    column_type = col1.selectbox('Data Type', options=DATATYPES)
    length = col2.text_input('Length')

    col3, col4 = st.columns(2)
    nullable = col3.checkbox('Nullable')
    primary_key = col4.checkbox('Primary Key')

    if st.button('Add'):
        # Validate column name and column type
        if not column_name or not column_type:
            st.warning('Please provide both Column Name and Column Type.')
        else:
            # Check for duplicate column name
            is_duplicate = any(column.name == column_name for column in columns)
            if is_duplicate:
                st.warning(f'A column with the name "{column_name}" already exists. Please choose a different name.')
            else:
                # Create a new column object and add it to the list
                column = Column(column_name, column_type, length, nullable, primary_key)
                columns.append(column)

    
    
    # Generate API JSON
    api_json = generate_api_json(columns, table_name)

    # Display the table of columns
    st.header('Columns')
    if columns:
        columns_df = pd.DataFrame(columns=[c.name for c in columns])
        columns_df = columns_df.append(pd.Series([c.data_type for c in columns], index=columns_df.columns), ignore_index=True)
        columns_df = columns_df.append(pd.Series([c.length for c in columns], index=columns_df.columns), ignore_index=True)
        columns_df = columns_df.append(pd.Series([str(c.nullable) for c in columns], index=columns_df.columns), ignore_index=True)
        columns_df = columns_df.append(pd.Series([str(c.primary_key) for c in columns], index=columns_df.columns), ignore_index=True)

        # Transpose the DataFrame to show records in rows and columns in columns
        columns_df = columns_df.T
        columns_df.columns = ['Data Type', 'Length', 'Nullable', 'Primary Key']

        st.table(columns_df)
    else:
        st.info('No columns added yet.')

    # Create Table button
    if st.button('Create Table'):
        if not table_name or not bucket_name:
            st.warning('Please provide both Table Name and Bucket Name.')
        else:
            create_table(URL, api_json, storage_token)

    # Display API endpoint and JSON
    with st.expander("geeky stuff", expanded=False):
        st.header('API Endpoint and JSON')
        st.write("API endpoint: {}".format(URL))
        st.info(api_json)

if __name__ == '__main__':
    main()