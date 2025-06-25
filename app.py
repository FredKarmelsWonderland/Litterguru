import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# --- Data Loading ---
@st.cache_data
def load_data():
    # Construct a BigQuery client object from the service account secret
    try:
        # Use st.secrets to get the credentials
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = bigquery.Client(credentials=creds, project=creds.project_id)

        # --- Define your query here ---
        # Replace with your project_id, dataset_id, and table_id
        query = """
            SELECT *
            FROM `cat-litter-recommender.test_01.test_table_01`
        """
        
        # Execute the query and load results into a pandas DataFrame
        query_job = client.query(query)
        df = query_job.to_dataframe()
        
        # Data cleaning can be done here as well
        return df

    except Exception as e:
        st.error(f"An error occurred while connecting to BigQuery: {e}")
        st.info("Please ensure your `gcp_service_account` secret is correctly configured.")
        return pd.DataFrame()


# --- Main App ---
# Check for CSV file and create a sample if it doesn't exist
if not os.path.exists('my_data.csv'):
    st.title("Welcome to the Cat Litter Recommender! 🐾")
    st.write("It looks like you don't have a `my_data.csv` file yet.")
    st.write("Click the button below to create a sample CSV to get started. You can replace this with your own data later.")
    if st.button("Create Sample `my_data.csv`"):
        create_sample_csv()
else:
    # Load the data
    df = load_data('my_data.csv')

    if not df.empty:
        # --- Sidebar Filters ---
        st.sidebar.header('Filter and Sort Options')

        # Dropdown multi-selects for categorical data
        flushable_options = st.sidebar.multiselect(
            'Is it Flushable?',
            options=df['Flushable'].unique(),
            default=df['Flushable'].unique() # Default to all selected
        )

        material_options = st.sidebar.multiselect(
            'Litter Material:',
            options=df['Material'].unique(),
            default=df['Material'].unique()
        )

        location_options = st.sidebar.multiselect(
            'Manufacturing Location:',
            options=df['Mfg Location'].unique(),
            default=df['Mfg Location'].unique()
        )

        scented_options = st.sidebar.multiselect(
            'Is it Scented?',
            options=df['Scented'].unique(),
            default=df['Scented'].unique()
        )

        # Slider for the numeric rating
        rating_range = st.sidebar.slider(
            'Average Scraped Rating:',
            min_value=float(df['Mean_Scraped_Rating'].min()),
            max_value=float(df['Mean_Scraped_Rating'].max()),
            value=(float(df['Mean_Scraped_Rating'].min()), float(df['Mean_Scraped_Rating'].max())) # A tuple for range
        )

        # Multi-select for performance features (maps to boolean columns)
        performance_options = st.sidebar.multiselect(
            'Performance Features:',
            options=['Good Clumping', 'Good Odor Blocking']
        )

        # --- Filtering Logic ---
        # Start with the original dataframe and apply filters sequentially
        filtered_df = df[
            (df['Flushable'].isin(flushable_options)) &
            (df['Material'].isin(material_options)) &
            (df['Mfg Location'].isin(location_options)) &
            (df['Scented'].isin(scented_options)) &
            (df['Mean_Scraped_Rating'].between(rating_range[0], rating_range[1]))
        ]

        # Handle the special performance filter
        # This logic shows products that have ALL selected performance features (AND logic)
        # To change to OR logic (has AT LEAST ONE), you would need a more complex filter.
        if 'Good Clumping' in performance_options:
            filtered_df = filtered_df[filtered_df['Good Clumping'] == True]
        
        if 'Good Odor Blocking' in performance_options:
            filtered_df = filtered_df[filtered_df['Good Odor Blocking'] == True]


        # --- Main Page Display ---
        st.title("Cat Litter Recommendations")
        st.write("Use the filters on the left to narrow down your choices.")
        
        # Display the number of results found
        st.markdown(f"**Found {len(filtered_df)} matching products**")
        st.dataframe(
            filtered_df,
            # Hide the index column from the displayed dataframe
            hide_index=True,
            # You can also set column widths or other configurations here
            # column_config={ ... }
        )


