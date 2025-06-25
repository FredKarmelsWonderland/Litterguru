import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os # Although we are removing its use, it's good practice to keep standard imports if needed elsewhere.

# --- Page Configuration ---
# Must be the first Streamlit command in your script
st.set_page_config(
    page_title="Cat Litter Recommender",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Data Loading Function (from BigQuery) ---
# Caching the data loading function for performance
@st.cache_data
def load_data():
    """Loads data from Google BigQuery."""
    # Construct a BigQuery client object from the service account secret
    try:
        # Use st.secrets to get the credentials from your secrets.toml file
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        client = bigquery.Client(credentials=creds, project=creds.project_id)

        # --- Define your query here ---
        # Replace with your actual project_id, dataset_id, and table_id
        query = """
            SELECT *
            FROM `cat-litter-recommender.test_01.test_table_01`
        """
        
        # Execute the query and load results into a pandas DataFrame
        st.info("Querying data from Google BigQuery... this may take a moment.")
        query_job = client.query(query)
        df = query_job.to_dataframe()
        st.success("Data successfully loaded from BigQuery!")
        
        # --- Perform any initial data cleaning here ---
        # It's good practice to do this inside the cached function
        # Example: ensuring binary columns are consistent strings for multiselect
        if 'Flushable' in df.columns:
            df['Flushable'] = df['Flushable'].astype(str).str.strip().str.capitalize()
        if 'Scented' in df.columns:
            df['Scented'] = df['Scented'].astype(str).str.strip().str.capitalize()
        # ---
        
        return df

    except Exception as e:
        st.error(f"An error occurred while connecting to BigQuery: {e}")
        st.info("Please ensure your `gcp_service_account` secret is correctly configured and the BigQuery table exists.")
        return pd.DataFrame()


# --- Main App Logic ---

# Call the function to load data from BigQuery
df = load_data()

if not df.empty:
    st.title("Cat Litter Recommendations 🐾")
    
    # --- ADD YOUR IMAGE HERE ---
    # Replace with the direct link you created in Step 2
    john_cute_url = "https://drive.google.com/uc?id=1wD71MdwUScP809g0Eaz88688o9OWrZNO"
    tien_sleep_url = "https://drive.google.com/uc?id=16fWhmZz51J78lr4diEVNzhYGfQWdMt3l"


    st.image(
        john_cute_url,
        width=600  # Optional: set a width for the image
    )

    st.image(
        tien_sleep_url,
        width = 600
    )


# Only build the rest of the app if the dataframe was loaded successfully
if not df.empty:
    # --- Sidebar Filters ---
    st.sidebar.header('Filter and Sort Options')

    # Dropdown multi-selects for categorical data
    flushable_options = st.sidebar.multiselect(
        'Is it Flushable?',
        options=df['Flushable'].unique(),
        default=df['Flushable'].unique() # Default to all selected
    )

    composition_options = st.sidebar.multiselect(
        'Litter Composition:',
        options=df['Composition'].unique(),
        default=df['Composition'].unique()
    )

    location_options = st.sidebar.multiselect(
        'Manufacturing Location:',
        options=df['Mfg_Location'].unique(),
        default=df['Mfg_Location'].unique()
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
        (df['Composition'].isin(material_options)) &
        (df['Mfg_Location'].isin(location_options)) &
        (df['Scented'].isin(scented_options)) &
        (df['Mean_Scraped_Rating'].between(rating_range[0], rating_range[1]))
    ]

    # Handle the special performance filter (AND logic)
    if 'Good Clumping' in performance_options:
        filtered_df = filtered_df[filtered_df['Good Clumping'] == True]
    
    if 'Good Odor Blocking' in performance_options:
        filtered_df = filtered_df[filtered_df['Good Odor Blocking'] == True]


    # --- Main Page Display ---
    st.title("Cat Litter Recommendations 🐾")
    st.write("Use the filters on the left to narrow down your choices.")
    
    # Display the number of results found
    st.markdown(f"**Found {len(filtered_df)} matching products**")
    st.dataframe(
        filtered_df,
        hide_index=True,
    )
else:
    # This message will show if load_data() failed and returned an empty dataframe
    st.warning("Could not load data. Please check the error messages above.")

